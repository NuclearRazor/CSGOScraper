import sqlite3
import time
import datetime
import random
import csv
import chardet
import os, errno
import re
import time

conn = None
c = None

class DataAnalyse():

    def __init__(self, all_data):
        super().__init__()

        self.initUI(all_data)

    def initUI(self, all_data):

        db_name = 'parsing_data'
        # Удаляем файл базы данных, если такой уже существует воизбежание перезаполнения данных и для увеличения скорости работы
        try:
            os.remove(db_name+'.db')
            #print('File removed: '+db_name+'.db')
        except:
            print("Can't remove database file")
            
        # Действием с директорией для цсв, чтобы не засорять папку со скриптом и входными данными
        dir = "./files"
        try:
            os.makedirs("./files")
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        coeff_mag = 0
        min_price = 1
        max_price = 8000
        mag_list = []
        self.result_tables_names = []

        min_profit = 25
        max_profit = 150

        compare_fx = repr(time.ctime())

        for index_i, i in enumerate(all_data):
            #parse each csv file
            #print('\nParse data from: ', all_data[index_i])
            mag_database = self.parse_info(db_name, all_data[index_i], 'index', 'c_market_name_en', 'c_price', 'c_quality', coeff_mag, min_price, max_price)
            mag_list.append(mag_database)
            for index_j, j in enumerate(all_data):
                if i != j:

                    what_to_cmpr = all_data[index_i].replace('.csv', '') + "_" + all_data[index_j].replace('.csv', '')

                    print("\nCompare " + all_data[index_i].replace('_data.csv', '') + " and " + all_data[index_j].replace('_data.csv', ''))

                    # Первой дб считаем ту, что в итерации главного цикла
                    first_database = mag_database
                    # Если в главном цикле итерация для первого магазина, то парсим информацию для j-го магазина
                    if all_data[index_i]==all_data[0]:
                        second_database = self.parse_info(db_name, all_data[index_j], 'index', 'c_market_name_en', 'c_price', 'c_quality', coeff_mag, min_price, max_price)
                    # Иначе считаем именем второго магазина имя файла - расширение
                    else:
                        second_database = all_data[index_j].replace('.csv', '')

                    self.create_result_table_from_select(db_name, what_to_cmpr, first_database, second_database)

                    # Записываем ее в файл
                    columns = ('Index', str(first_database + '_Name'), str(first_database + '_Price'), str(first_database + '_Quality'),\
                    
                    str(second_database + '_Name'), str(second_database + '_Price'), str(second_database + '_Quality'), str('Profit_' + first_database + '_TO_' + second_database))
                    
                    self.select_data_from_db(db_name, str(dir + "/" + what_to_cmpr), what_to_cmpr, columns)

                    self.result_tables_names.append(what_to_cmpr)

                    # Находим профиты среди всех выборок в диапазоне 
                    output_file_name = dir+"/interval_%s_to_%s" % (min_profit, max_profit)
                    self.find_profit_in_DB_in_range(db_name, min_profit, max_profit, self.result_tables_names, output_file_name)
        
        endcompare_fx = repr(time.ctime())

        print('\nStart compare: ', compare_fx)
        print('End compare: ', endcompare_fx)
 
        print('\nNumber of mag datas = ', len(mag_list))   

        self.get_comission()

    def delete_tb(self, db_name, table_name):
        parameter_name = 'DROP TABLE IF EXISTS %s' % (table_name)
        parameter_name = parameter_name.replace('\'', '"')
        conn = sqlite3.connect(db_name + '.db')
        #print('\ncsv file name = ', filename_csv)
        #print('schema = ', parameter_name)
        c = conn.cursor()
        c.execute(parameter_name)
        conn.commit()
        c.close()
        conn.close()

    def get_comission(self):
        num_pattern = r'\d+'
        num_coeff = []
        find_num = ''

        with open('coefficients.txt') as f:
            for line in f:
                find_num = re.findall(num_pattern, str(line))
                num_coeff.append(self.convert_to_str(find_num))

        return num_coeff

    def convert_to_str(self, numlist):
        try:
            if numlist != None:
                s = map(str, numlist)  # ['1','2','3']
                s = ''.join(s)  # '123'
            else:
                s = 'None'
                return s
        except (ValueError, TypeError, RuntimeError):
            print('\nEmpty object or none, continue, value = None\n')
            s = 'None'
            pass
        return s

    def parse_info(self, db_name, filename, col_index, col_name, col_price, col_quality, coeff, min_price, max_price):
            
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

        #print('\ncsv file name = ', filename_csv)
        #print('schema = ', parameter_name)
        #print('insert data schema = ', parameter_save)

        c = conn.cursor()

        c.execute(parameter_name)
        
        # Делаем проверку цен для входных аргументов функции. Возвращаемое значение - корректные границы цен
        correct_prices = self.check_prices(min_price, max_price)
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
    def check_prices(self, min_price, max_price):
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
    def select_data_from_db(self, db_name, filename, table_name, columns):
        new_fn = str(filename+"1.csv")
        
        # Запрос на выборку всех столбцов всех записей из бд с заданным названием
        parameter_name = 'SELECT * FROM %s' % (table_name)
        parameter_name = parameter_name.replace('\'', '"')

        conn = sqlite3.connect(db_name + '.db')

        # print('\ncsv file name = ', filename)
        # print('schema = ', parameter_name)

        c = conn.cursor()

        c.execute(parameter_name)
        with open(new_fn, 'w', newline='') as selected:
            wr = csv.writer(selected, quoting = csv.QUOTE_MINIMAL, dialect='excel')
            wr.writerow(columns)

            for row in c.fetchall():
                 wr.writerow(row)
            selected.close()

        # print ("Data written to"+repr(new_fn))
        conn.commit()
        c.close()
        conn.close()

    # Создает результирующую таблицу выборки двух таблиц
    def create_result_table_from_select(self, db_name, res_table_name, tb1, tb2):

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

            second_price = float(row[5]) #цены во втором магазине
            first_price = float(row[2])

            # print('second price = ', float(row[5][1:5]))
            # print('first price = ', float(row[2][1:5]))

            ###сравнение ----------------------------------------
            if second_price > first_price:

                k = float(first_price/second_price)
                check = None

                curProfit_1to2 = int(100*abs(1 - k))

                if curProfit_1to2 > 25:
                    
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
    def find_profit_in_DB_in_range(self, db_name, min_profit, max_profit, tables, output_filepath):
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

        #print ("Data written to"+repr(new_fn))
        conn.commit()
        c.close()
        conn.close()


if __name__ == "__main__":

    magasines_data = ['csgosell_data.csv', 'skinsjar_data.csv', 'csmoney_data.csv']
    db = DataAnalyse(magasines_data)

