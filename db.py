import sqlite3
import time
import datetime
import random
import csv
import chardet
import os, errno
import time

conn = None
c = None

def parse_info(db_name, filename, col_index, col_name, col_price, col_quality, coeff, min_price, max_price):
		
	global c
	global conn

	filename_csv = filename
	filename = filename.replace('.csv', '')

	# Добавлены вызовы функции repr() для преобразования объектов в строки
	parameter_name = 'CREATE TABLE IF NOT EXISTS %s(%s, %s, %s, %s)' % (filename, repr(col_index), repr(col_name), repr(col_price), repr(col_quality))
	parameter_save = 'INSERT INTO %s(%s, %s, %s, %s) VALUES (?, ?, ?, ?)' % (filename, repr(col_index), repr(col_name), repr(col_price), repr(col_quality))
	parameter_name = parameter_name.replace('\'', '"')
	parameter_save = parameter_save.replace('\'', '"')

	conn = sqlite3.connect(db_name + '.db')

	print('\ncsv file name = ', filename_csv)
	print('schema = ', parameter_name)
	print('insert data schema = ', parameter_save)

	c = conn.cursor()

	c.execute(parameter_name)
	
	# Делаем проверку цен для входных аргументов функции. Возвращаемое значение - корректные границы цен
	correct_prices = check_prices(min_price, max_price)
	with open(filename_csv,'r') as fin: 
		dr = csv.DictReader(fin) # comma is default delimiter
		# float(i[col_price])+float(i[col_price])*coeff - прибавление к цене товара комиссии самого магазина на покупку/продажу
		# Если нет границ для цены, то добавляем в бд все записи
		if correct_prices[0]==None:
			to_db = [(i[col_index], i[col_name], repr(round(float(i[col_price])+float(i[col_price])*coeff,4)), i[col_quality]) for i in dr]
		# Иначе добавляем в бд лишь те записи, у которых цены лежат в заданном промежутке
		else:
			to_db=[]
			for i in dr:
				price = round(float(i[col_price])+float(i[col_price])*coeff, 4)
				if price>=correct_prices[0] and price<=correct_prices[1]:
					to_db.append((i[col_index], i[col_name], repr(price), i[col_quality]))
		fin.close()

	c.executemany(parameter_save, to_db)

	conn.commit()

	c.close()
	conn.close()
	return filename

# Проверяет цены
def check_prices(min_price, max_price):
	# Если цены не указаны или имеют отрицательное значение, то считаем, что цен нет
	if min_price==None or max_price==None or float(min_price)<0 or float(max_price)<0:
		return [None, None]
	# Запоминаем значение цен
	l_min = float(min_price)
	l_max = float(max_price)
	# Если цены "перевернуты", то возвращаем их "наоборот"
	if l_min>l_max:
		return [l_max, l_min]
	# Иначе возвращаем цены как есть
	else:
		return [l_min, l_max]
		
# Делает выборку всех данных из бд и записывает их в файл с именем "имя_таблицы+1.csv"
def select_data_from_db(db_name, filename, table_name, columns):
	new_fn = str(filename+"1.csv")
	
	# Запрос на выборку всех столбцов всех записей из бд с заданным названием
	parameter_name = 'SELECT * FROM %s' % (table_name)
	parameter_name = parameter_name.replace('\'', '"')

	conn = sqlite3.connect(db_name + '.db')

	print('\ncsv file name = ', filename)
	print('schema = ', parameter_name)

	c = conn.cursor()

	c.execute(parameter_name)
	with open(new_fn, 'w', newline='') as selected:
		wr = csv.writer(selected, quoting = csv.QUOTE_MINIMAL, dialect='excel')
		wr.writerow(columns)

		for row in c.fetchall():
			 wr.writerow(row)
		selected.close()

	print ("Data written to"+repr(new_fn))
	conn.commit()
	c.close()
	conn.close()

# Создает результирующую таблицу выборки двух таблиц
def create_result_table_from_select(db_name, res_table_name, tb1, tb2):

	conn = sqlite3.connect(db_name + '.db')

	c = conn.cursor()
	# Имя результирующей таблицы
	name = res_table_name
	# Команда на создание таблицы
	parameter_name = '''CREATE TABLE IF NOT EXISTS 
	%s(%s, %s, %s, %s, %s, %s, %s, %s)''' % (name, '`index`', 'name1', 'price1', 'quality1', 'name2', 'price2', 'quality2', 'profit1to2')
	parameter_name = parameter_name.replace('\'', '"')
	# Создаем таблицу
	c.execute(parameter_name)
	
	# Команда на создание подпольной таблицы
	my_table_name = res_table_name+'_my'
	parameter_name = '''CREATE TABLE IF NOT EXISTS 
	%s(%s, %s, %s, %s, %s)''' % (my_table_name, '`index`', 'name', 'price1', 'price2', 'profit1to2')
	parameter_name = parameter_name.replace('\'', '"')
	# Создаем таблицу
	c.execute(parameter_name)

	# Команда выборки
	parameter_name = """SELECT DISTINCT %s.%s,%s.%s,%s.%s,%s.%s,%s.%s,%s.%s,%s.%s FROM %s, %s 
	WHERE %s.%s=%s.%s""" % (tb1, '`index`', tb1, 'c_market_name_en', tb1, 'c_price', tb1, 'c_quality', tb2, 'c_market_name_en', tb2, 'c_price', tb2, 'c_quality', tb1, tb2, tb1, 'c_market_name_en', tb2, 'c_market_name_en')
	parameter_name = parameter_name.replace('\'', '"')
	c.execute(parameter_name)
	# Для каждого элемента выборки
	curProfit_1to2 = 0
	curProfit_2to1 = 0
	for row in c.fetchall():
		# Рассчитываем текущую выгоду
		# Остаток процентов из 8 (3 уже учитываются)
		second_price = float(row[5])+0.05*float(row[5])
		curProfit_1to2 = int(100*(1-abs(float(row[2])/second_price)))
		#curProfit_2to1 = int(100*(1-abs(float(row[5])/float(row[2]))))
		
		# Ищем товар в подпольной таблице
		parameter_name = """SELECT * FROM %s WHERE name = %s""" % (my_table_name, repr(row[1]))
		#parameter_name = parameter_name.replace('\'', '"')
		c.execute(parameter_name)
		result = c.fetchone()

		# 1. Если такого товара нет в "подпольной" таблице
		if result==None:
			# 1.1. Записываем товар в подпольную таблицу
			parameter_save = '''INSERT OR IGNORE INTO %s(`index`, name, price1, price2, profit1to2) 
		VALUES (%s, %s, %s, %s, %d)''' % (my_table_name, repr(row[0]), repr(row[1]), repr(row[2]), repr(second_price), curProfit_1to2)
			c.execute(parameter_save)
			# 1.2. Записываем товар в результирующую таблицу
			parameter_save = '''INSERT OR IGNORE INTO %s(%s, %s, %s, %s, %s, %s, %s, %s) 
		VALUES (%s, %s, %s, %s, %s, %s, %s, %d)''' % (name, '`index`', 'name1', 'price1', 'quality1', 'name2', 'price2', 'quality2', 'profit1to2', repr(row[0]), repr(row[1]), repr(row[2]), repr(row[3]), repr(row[4]), repr(second_price), repr(row[6]), curProfit_1to2)
			c.execute(parameter_save)
		# 2. Если такой товар есть
		else:			
			# 2.1. Запрашиваем какие у него выгоды
			profit_in_bd = result[4]
			# 2.1.1. Если выгоды лучше, чем на текущий момент, то мы игнорим эту запись и не добавляем ее в результат вообще
			if profit_in_bd>=curProfit_1to2:
				continue
			# 2.1.2. Если выгоды хуже, чем на текущий момент
			else:
				# 2.1.2.1. Обновляем значения в подпольной таблице					
				parameter_save = '''UPDATE %s SET `index` = %s, price1 = %s, price2 = %s, profit1to2 = %d 
				WHERE `index` = %s AND name = %s''' % (my_table_name, repr(row[0]), repr(row[2]), repr(second_price), curProfit_1to2, repr(result[0]), repr(result[1]))
				c.execute(parameter_save)
				# 2.1.2.1. Обновляем значения в результирующей таблице
				#(name, '`index`', 'name1', 'price1', 'quality1', 'name2', 'price2', 'quality2', 'profit1to2')
				parameter_save = '''UPDATE %s SET `index` = %s, price1 = %s, quality1 = %s, price2 = %s, quality2 = %s, profit1to2 = %d
				WHERE `index` = %s AND name1 = %s''' % (name, repr(row[0]), repr(row[2]), repr(row[3]), repr(second_price), repr(row[6]), curProfit_1to2, repr(result[0]), repr(result[1]))
				c.execute(parameter_save)
	conn.commit()
	c.close()
	conn.close()
	
# Создает общую таблицу профитов в заданных границах
def find_profit_in_DB_in_range(db_name, min_profit, max_profit, tables, output_filepath):
	# Всегда приводим входной аргумент к int для безопасности
	loc_min_pr = int(min_profit)
	loc_max_pr = int(max_profit)
	# Проверяем, что выгоды - адекватные числа
	if loc_min_pr<0 or loc_max_pr<0:
		print ("Profits can't be < 0. Check your profits: min_profit = " + repr(loc_min_pr) + "; and max_profit = " + repr(loc_max_pr))
		return None
	# Если минимальная выгода больше максимальной, то меняем их местами
	if loc_min_pr>loc_max_pr:
		tmp = loc_max_pr
		loc_max_pr = loc_min_pr
		loc_min_pr = tmp
		
	new_fn = output_filepath+".csv"
	columns = ('Index', 'Name1', 'Price1', 'Quality1', 'Name2', 'Price2', 'Quality2', 'Profit_1_TO_2', 'FROM_TO')
	
	conn = sqlite3.connect(db_name + '.db')
	c = conn.cursor()
	# Команда на создание таблицы
	tn = 'interval_table'
	parameter_name = '''CREATE TABLE IF NOT EXISTS 
	%s(%s, %s, %s, %s, %s, %s, %s, %s, %s)''' % (tn, 'Ind', 'Name1', 'Price1', 'Quality1', 'Name2', 'Price2', 'Quality2', 'Profit_1_TO_2', 'FROM_TO')
	parameter_name = parameter_name.replace('\'', '"')
	# Создаем таблицу
	c.execute(parameter_name)
	
	# Для каждой таблицы..
	for cur_table in tables:
		# Найти выгодные записи в заданных рамках
		# Команда выборки
		parameter_name = """SELECT * FROM %s WHERE profit1to2<=%d AND profit1to2>=%d""" % (cur_table, max_profit, min_profit)
		parameter_name = parameter_name.replace('\'', '"')
		
		c.execute(parameter_name)	
		results = c.fetchall()
		# Если таких записей нет, переходим к следующей итерации цикла
		if len(results) == 0:
			continue
		# Иначе
		else:
			#Записываем каждый элемент выборки
			for element in results:
				insert_str = '''INSERT INTO %s(%s, %s, %s, %s, %s, %s, %s, %s, %s) 
VALUES (%s, %s, %s, %s, %s, %s, %s, 
%d, %s)''' % (tn, 'Ind', 'Name1', 'Price1', 'Quality1', 'Name2', 'Price2', 'Quality2', 'Profit_1_TO_2', 'FROM_TO', repr(element[0]), repr(element[1]), repr(element[2]), repr(element[3]), repr(element[4]), repr(element[5]), repr(element[6]), element[7], repr(cur_table))
				c.execute(insert_str)
	# Выбираем из получившихся записей все, сортируя их по цене во втором магазине
	parameter_name = 'SELECT * FROM %s ORDER BY Price2 DESC' % (tn)
	parameter_name = parameter_name.replace('\'', '"')
	c.execute(parameter_name)
	with open(new_fn, 'w', newline='') as selected:
		wr = csv.writer(selected, quoting = csv.QUOTE_MINIMAL, dialect='excel')
		wr.writerow(columns)

		for row in c.fetchall():
			 wr.writerow(row)
		selected.close()

	print ("Data written to"+repr(new_fn))
	conn.commit()
	c.close()
	conn.close()
	
	
# Удаляет таблицу	
def delete_tb(db_name, table_name):
	parameter_name = 'DROP TABLE IF EXISTS %s' % (table_name)
	parameter_name = parameter_name.replace('\'', '"')
	conn = sqlite3.connect(db_name + '.db')
	#print('\ncsv file name = ', filename_csv)
	print('schema = ', parameter_name)
	c = conn.cursor()
	c.execute(parameter_name)
	conn.commit()
	c.close()
	conn.close()

db_name = 'parsing_data'
# Удаляем файл базы данных, если такой уже существует воизбежание перезаполнения данных и для увеличения скорости работы
try:
	os.remove(db_name+'.db')
	print('File removed: '+db_name+'.db')
except:
	print("Can't remove database file")
	
# Действием с директорией для цсв, чтобы не засорять папку со скриптом и входными данными
dir = "./files"
try:
    os.makedirs("./files")
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

# Наполняем базу данных информацией
coeff_csgotm = 0.1
min_price = 100
max_price = 500
coeff_csmoney = 0.03
csgotm_database = parse_info(db_name, 'csgotm_data.csv', 'index', 'c_market_name_en', 'c_price', 'c_quality', coeff_csgotm, min_price, max_price)
sj_database = parse_info(db_name, 'csgosell_data.csv', 'index', 'c_market_name_en', 'c_price', 'c_quality', coeff_csmoney, min_price, max_price)
csmoney_database = parse_info(db_name, 'csmoney_data.csv', 'index', 'c_market_name_en', 'c_price', 'c_quality', coeff_csmoney, min_price, max_price) 

result_tables_names=[]
# ------------------------------------------------------ СРАВНЕНИЯ ДЛЯ csgotm ----------------------------------------------------------------------------
# --------- Сравниваем csgotm к csmoney ----------------------------

print("\nStarted csgotm_csmoney. TIME: "+repr(time.ctime()))
# Получаем таблицу - объединение
res_table_name = "csgotm_csmoney"
create_result_table_from_select(db_name, res_table_name, csgotm_database, csmoney_database)
# Записываем ее в файл
columns = ('Index', str(csgotm_database+'_Name'), str(csgotm_database+'_Price'), str(csgotm_database+'_Quality'), str(csmoney_database+'_Name'), str(csmoney_database+'_Price'), str(csmoney_database+'_Quality'), str('Profit_'+csgotm_database+'_TO_'+csmoney_database))
select_data_from_db(db_name, str(dir+"/"+res_table_name), res_table_name, columns)
print("Finished. TIME: "+repr(time.ctime()))
result_tables_names.append(res_table_name)

# ------------------------------------------------------------------
# --------- Сравниваем csgotm к csgosell ---------------------------

print("\nStarted csgotm_csgosell. TIME: "+repr(time.ctime()))
# Получаем таблицу - объединение
res_table_name = "csgotm_csgosell"
create_result_table_from_select(db_name, res_table_name, csgotm_database, sj_database)
# Записываем ее в файл
columns = ('Index', str(csgotm_database+'_Name'), str(csgotm_database+'_Price'), str(csgotm_database+'_Quality'), str(sj_database+'_Name'), str(sj_database+'_Price'), str(sj_database+'_Quality'), str('Profit_'+csgotm_database+'_TO_'+sj_database))
select_data_from_db(db_name, str(dir+"/"+res_table_name), res_table_name, columns)
print("Finished. TIME: "+repr(time.ctime()))
result_tables_names.append(res_table_name)

# ------------------------------------------------------------------
# ------------------------------------------------------ СРАВНЕНИЯ ДЛЯ csmoney ----------------------------------------------------------------------------
# --------- Сравниваем csmoney к csgotm ----------------------------

print("\nStarted csmoney_csgotm. TIME: "+repr(time.ctime()))
# Получаем таблицу - объединение
res_table_name = "csmoney_csgotm"
create_result_table_from_select(db_name, res_table_name, csmoney_database, csgotm_database)
# Записываем ее в файл
columns = ('Index', str(csmoney_database+'_Name'), str(csmoney_database+'_Price'), str(csmoney_database+'_Quality'), str(csgotm_database+'_Name'), str(csgotm_database+'_Price'), str(csgotm_database+'_Quality'), str('Profit_'+csmoney_database+'_TO_'+csgotm_database))
select_data_from_db(db_name, str(dir+"/"+res_table_name), res_table_name, columns)
print("Finished. TIME: "+repr(time.ctime()))
result_tables_names.append(res_table_name)

# -------------------------------------------------------------------
# --------- Сравниваем csmoney к csgosell ---------------------------

print("\nStarted csmoney_csgosell. TIME: "+repr(time.ctime()))
# Получаем таблицу - объединение
res_table_name = "csmoney_csgosell"
create_result_table_from_select(db_name, res_table_name, csmoney_database, sj_database)
# Записываем ее в файл
columns = ('Index', str(csmoney_database+'_Name'), str(csmoney_database+'_Price'), str(csmoney_database+'_Quality'), str(sj_database+'_Name'), str(sj_database+'_Price'), str(sj_database+'_Quality'), str('Profit_'+csmoney_database+'_TO_'+sj_database))
select_data_from_db(db_name, str(dir+"/"+res_table_name), res_table_name, columns)
print("Finished. TIME: "+repr(time.ctime()))
result_tables_names.append(res_table_name)

# ------------------------------------------------------------------
# ------------------------------------------------------ СРАВНЕНИЯ ДЛЯ csgosell ----------------------------------------------------------------------------
# --------- Сравниваем csgosell к csgotm ---------------------------

print("\nStarted csgosell_csgotm. TIME: "+repr(time.ctime()))
# Получаем таблицу - объединение
res_table_name = "csgosell_csgotm"
create_result_table_from_select(db_name, res_table_name, sj_database, csgotm_database)
# Записываем ее в файл
columns = ('Index', str(sj_database+'_Name'), str(sj_database+'_Price'), str(sj_database+'_Quality'), str(csgotm_database+'_Name'), str(csgotm_database+'_Price'), str(csgotm_database+'_Quality'), str('Profit_'+sj_database+'_TO_'+csgotm_database))
select_data_from_db(db_name, str(dir+"/"+res_table_name), res_table_name, columns)
print("Finished. TIME: "+repr(time.ctime()))
result_tables_names.append(res_table_name)

# ------------------------------------------------------------------
# --------- Сравниваем csgosell к csmoney ---------------------------
print("\nStarted csgosell_csmoney. TIME: "+repr(time.ctime()))
# Получаем таблицу - объединение
res_table_name = "csgosell_csmoney"
create_result_table_from_select(db_name, res_table_name, sj_database, csmoney_database)
# Записываем ее в файл
columns = ('Index', str(sj_database+'_Name'), str(sj_database+'_Price'), str(sj_database+'_Quality'), str(csmoney_database+'_Name'), str(csmoney_database+'_Price'), str(csmoney_database+'_Quality'), str('Profit_'+sj_database+'_TO_'+csmoney_database))
select_data_from_db(db_name, str(dir+"/"+res_table_name), res_table_name, columns)
print("Finished. TIME: "+repr(time.ctime()))
result_tables_names.append(res_table_name)

# Находим профиты среди всех выборок в диапазоне 20-60%
output_file_name = dir+"/interval_20_to_60"
find_profit_in_DB_in_range(db_name, 20, 60, result_tables_names, output_file_name)