# -*- coding: utf-8 -*-
import sqlite3
import csv
import os, errno
import re
import io

conn = None
c = None


class DataAnalyse():

    def __init__(self, *args):
        super().__init__()

        if len(args) != 0:
            for item in args[0]:
                setattr(self, item, args[0][item])
        else:
            return

        self.initUI()

    def initUI(self):


        db_name = 'parsing_data'
        # delete file for speed boost
        try:
            os.remove(db_name+'.db')
        except:
            print("Can't remove database file")
            
        # make new directory
        dir = "./scraped_files"
        try:
            os.makedirs("./scraped_files")
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        shops_db_names = []
        exhangers_db_names = []
        self.result_tables_names = []

        #1. parse shops
        for index_i, i in enumerate(self.shops):
            shop_db = self.parse_info(db_name, self.shops[index_i], \
                                      'index', 'c_market_name_en', 'c_price', 'c_quality', 'URL', self.overall_rate, self.min_price, self.max_price)
            shops_db_names.append(shop_db)
        #2. parse exhangers
        for index_i, i in enumerate(self.exchangers):
            exchanger_db = self.parse_info(db_name, self.exchangers[index_i], \
                                           'index', 'c_market_name_en', 'c_price', 'c_quality', 'URL', self.overall_rate, self.min_price, self.max_price)
            exhangers_db_names.append(exchanger_db)
        #3. for each shop..
        for index_i, i in enumerate(shops_db_names):
            #3.1. remember current shop
            first_database = shops_db_names[index_i]
            #3.2. for each exchanger..
            for index_j, j in enumerate(exhangers_db_names):
                #3.2.1. remember current exchanger
                second_database = exhangers_db_names[index_j]
                #3.2.2. make string for filename
                what_to_cmpr = first_database.replace('_data', '')+ "_" + second_database.replace('_data', '')
                #3.2.3. find profit for sale from current shop to current exhanger
                # --quality_matters-- defines if analyzer should compare items only with same quality
                self.create_result_table_from_select(db_name, what_to_cmpr, first_database, second_database, self.compare_equal, self.min_profit, self.bound_profit)

                #3.2.4. write into file
                columns = ('Index', str(first_database + '_Name'), str(first_database + '_Price'), str(first_database + '_Quality'),\

                str(second_database + '_Name'), str(second_database + '_Price'), str(second_database + '_Quality'), str('Profit_' + first_database + '_TO_' + second_database))

                self.select_data_from_db(db_name, str(dir + "/" + what_to_cmpr), what_to_cmpr, columns)
                self.result_tables_names.append(what_to_cmpr)

        #4. find profit in profit range
        output_file_name = dir+"/interval_%s_to_%s" % (self.min_profit, self.max_profit)
        self.find_profit_in_DB_in_range(db_name, self.min_profit, self.max_profit, self.result_tables_names, output_file_name, self.sort_flag)

        self.get_comission()


    def delete_tb(self, db_name, table_name):
        parameter_name = 'DROP TABLE IF EXISTS %s' % (table_name)
        parameter_name = parameter_name.replace('\'', '"')
        conn = sqlite3.connect(db_name + '.db')
        c = conn.cursor()
        c.execute(parameter_name)
        conn.commit()
        c.close()
        conn.close()


    def get_comission(self):
        num_pattern = r'\d+'
        num_coeff = []
        find_num = ''

        with io.open('coefficients.txt', encoding='utf-8', errors='ignore') as f:
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


    def parse_info(self, db_name, filename, col_index, col_name, col_price, col_quality, col_url, coeff, min_price, max_price):
            
        global c
        global conn

        filename_csv = filename
        filename = filename.replace('.csv', '')

        #repr() to convert objects into string
        parameter_name = 'CREATE TABLE IF NOT EXISTS %s(%s, %s, %s, %s, %s)' % (filename, repr(col_index), repr(col_name), repr(col_price), repr(col_quality), repr(col_url))
        parameter_save = 'INSERT INTO %s(%s, %s, %s, %s, %s) VALUES (?, ?, ?, ?, ?)' % (filename, repr(col_index), repr(col_name), repr(col_price), repr(col_quality), repr(col_url))
        parameter_name = parameter_name.replace('\'', '"')
        parameter_save = parameter_save.replace('\'', '"')

        conn = sqlite3.connect(db_name + '.db')
        c = conn.cursor()
        c.execute(parameter_name)
        
        correct_prices = self.check_prices(min_price, max_price)
        if filename_csv == 'csgotm_data.csv':
            with io.open(filename_csv, 'r', encoding='utf-8', errors='ignore') as fin:
                dr = csv.DictReader(fin) # comma is default delimiter                
                to_db=self.parse_items(dr, correct_prices, coeff, col_index, col_name, col_price, col_quality, col_url, True)
        else:
            with io.open(filename_csv, 'r', encoding='utf-8', errors='ignore') as fin:
                dr = csv.DictReader(fin) # comma is default delimiter
                to_db=self.parse_items(dr, correct_prices, coeff, col_index, col_name, col_price, col_quality, col_url, False)

        c.executemany(parameter_save, to_db)
        conn.commit()
        c.close()
        conn.close()
        return filename


    def parse_items(self, dr, prices, coeff, col_index, col_name, col_price, col_quality, col_url, translate):
        to_db = []
        # float(i[col_price])+float(i[col_price])*coeff
        fields = dr.fieldnames
        if prices[0]==None:
            if translate:
                to_db = [(i[col_index], i[col_name], repr(round(float(i[col_price])+float(i[col_price])*coeff,4)), self.translate_csgotm_qual(i[col_quality]), self.get_item_url(fields, i, col_url)) for i in dr]
            else:
                to_db = [(i[col_index], i[col_name], repr(round(float(i[col_price])+float(i[col_price])*coeff,4)), self.check_default_qual(i[col_quality]), self.get_item_url(fields, i, col_url)) for i in dr]
        else:
            to_db=[]
            for i in dr:
                #except non price values like 'High Grade Key', '99.000.00' etc
                try:
                    price = round(float(i[col_price])+float(i[col_price])*coeff, 4)
                except ValueError:
                    price = 0.0
                if price>=prices[0] and price<=prices[1]:
                    if translate:
                        to_db.append((i[col_index], i[col_name], repr(price), self.translate_csgotm_qual(i[col_quality]), self.get_item_url(fields, i, col_url)))
                    else:
                        to_db.append((i[col_index], i[col_name], repr(price), self.check_default_qual(i[col_quality]), self.get_item_url(fields, i, col_url)))
        return to_db

    # checks if current item has url
    def get_item_url(self, dr_fields, cur_item, url_col):
        if url_col in dr_fields:
            return cur_item[url_col]
        return "--"

    # checks and converts default quality
    def check_default_qual(this, quality):
        if quality == '':
            return '--'
        return quality


    def check_prices(self, min_price, max_price):
        if min_price==None or max_price==None or float(min_price)<0 or float(max_price)<0:
            return [None, None]
        l_min = float(min_price)
        l_max = float(max_price)
        if l_min>l_max:
            return [l_max, l_min]
        else:
            return [l_min, l_max]


    def select_data_from_db(self, db_name, filename, table_name, columns):
        new_fn = str(filename+"_selected.csv")
        
        parameter_name = 'SELECT * FROM %s' % (table_name)
        parameter_name = parameter_name.replace('\'', '"')

        conn = sqlite3.connect(db_name + '.db')
        c = conn.cursor()

        c.execute(parameter_name)
        with io.open(new_fn, 'w', newline='', encoding='utf-8', errors='ignore') as selected:
            wr = csv.writer(selected, quoting = csv.QUOTE_MINIMAL, dialect='excel')
            wr.writerow(columns)
            [wr.writerow(row) for row in c.fetchall()]

        conn.commit()
        c.close()
        conn.close()


    # --quality_matters-- defines if analyzer should compare items only with same quality
    def create_result_table_from_select(self, db_name, res_table_name, tb1, tb2, quality_matters, min_profit, absolute_profit):

        conn = sqlite3.connect(db_name + '.db')

        c = conn.cursor()
        #result table name
        name = res_table_name
        parameter_name = '''CREATE TABLE IF NOT EXISTS 
        %s(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''' % (name, '`index`', 'name1', 'price1', 'quality1', 'name2', 'price2', 'quality2', 'profit1to2', 'url1', 'url2')
        parameter_name = parameter_name.replace('\'', '"')
        #create a table
        c.execute(parameter_name)
        
        #buffer table name
        my_table_name = res_table_name+'_my'
        parameter_name = '''CREATE TABLE IF NOT EXISTS 
        %s(%s, %s, %s, %s, %s)''' % (my_table_name, '`index`', 'name', 'price1', 'price2', 'profit1to2')
        parameter_name = parameter_name.replace('\'', '"')
        #create buffer table
        c.execute(parameter_name)

        parameter_name = """SELECT DISTINCT %s.%s,%s.%s,%s.%s,%s.%s,%s.%s,%s.%s,%s.%s,%s.%s,%s.%s FROM %s, %s 
        WHERE %s.%s=%s.%s""" % (tb1, '`index`', tb1, 'c_market_name_en', tb1, 'c_price', tb1, 'c_quality', tb2, 'c_market_name_en', tb2, 'c_price', tb2, 'c_quality', tb1, 'URL',  tb2, 'URL', tb1, tb2, tb1, 'c_market_name_en', tb2, 'c_market_name_en')
        parameter_name = parameter_name.replace('\'', '"')
        c.execute(parameter_name)

        curProfit_1to2 = 0
        curProfit_2to1 = 0

        for row in c.fetchall():

            second_price = float(row[5]) #prices in secong mag/exchanger
            first_price = float(row[2])
            first_qual = repr(row[3])
            second_qual = repr(row[6])

            ###Comparing START
            if (second_price > first_price and quality_matters==False ) or (second_price > first_price and quality_matters and first_qual==second_qual):

                k = float(second_price/first_price)

                curProfit_1to2 = int(abs(k - 1)*100)

                if curProfit_1to2 > min_profit and curProfit_1to2 <= absolute_profit: #25 - empiric value
                    
                    #find item in buffer table
                    parameter_name = """SELECT * FROM %s WHERE name = %s""" % (my_table_name, repr(row[1]))
                    c.execute(parameter_name)
                    result = c.fetchone()

                    # 1. If it is not in buffer table
                    if result==None:
                        # 1.1. Write it a in buffer table
                        parameter_save = '''INSERT OR IGNORE INTO %s(`index`, name, price1, price2, profit1to2) 
                    VALUES (%s, %s, %s, %s, %d)''' % (my_table_name, repr(row[0]), repr(row[1]), repr(row[2]), repr(second_price), curProfit_1to2)
                        c.execute(parameter_save)
                        # 1.2. Write it a in result table
                        parameter_save = '''INSERT OR IGNORE INTO %s(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %d, %s, %s)''' % (name, '`index`', 'name1', 'price1', 'quality1', 'name2', 'price2', 'quality2', 'profit1to2', 'url1', 'url2', repr(row[0]), repr(row[1]), repr(row[2]), repr(row[3]), repr(row[4]), repr(second_price), repr(row[6]), curProfit_1to2, repr(row[7]), repr(row[8]))
                        c.execute(parameter_save)
                    # 2. if item exist
                    else:           
                        # 2.1. it's profit
                        profit_in_bd = result[4]
                        # 2.1.1. if it's max profit - continue
                        if profit_in_bd>=curProfit_1to2:
                            continue
                        # 2.1.2. if it's non max profit
                        else:
                            # 2.1.2.1. rewrite value in buffer table                  
                            parameter_save = '''UPDATE %s SET `index` = %s, price1 = %s, price2 = %s, profit1to2 = %d 
                            WHERE `index` = %s AND name = %s''' % (my_table_name, repr(row[0]), repr(row[2]), repr(second_price), curProfit_1to2, repr(result[0]), repr(result[1]))
                            c.execute(parameter_save)
                            # 2.1.2.1. rewrite value in result table
                            #(name, '`index`', 'name1', 'price1', 'quality1', 'name2', 'price2', 'quality2', 'profit1to2')
                            parameter_save = '''UPDATE %s SET `index` = %s, price1 = %s, quality1 = %s, price2 = %s, quality2 = %s, profit1to2 = %d, url1 = %s, url2 = %s
                            WHERE `index` = %s AND name1 = %s''' % (name, repr(row[0]), repr(row[2]), repr(row[3]), repr(second_price), repr(row[6]), curProfit_1to2, repr(row[7]), repr(row[8]), repr(result[0]), repr(result[1]))
                            c.execute(parameter_save)

            ###Comparing END
        conn.commit()
        c.close()
        conn.close()


    #ru quality to universal quality
    def translate_csgotm_qual(self, current_qual):
        if current_qual == 'Закаленное в боях':
            return u'BS'
        if current_qual == 'Поношенное':
            return u'WW'
        if current_qual == 'После полевых испытаний':
            return u'FT'
        if current_qual == 'Немного поношенное':
            return u'MW'
        if current_qual == 'Прямо с завода':
            return u'FN'
        return ''


    #make a result table with current profits
    # --profit_and_price2-- defines the way analyzer should sort items
    def find_profit_in_DB_in_range(self, db_name, min_profit, max_profit, tables, output_filepath, profit_and_price2):
        #safety
        loc_min_pr = int(min_profit)
        loc_max_pr = int(max_profit)
        #check profits bounds
        if loc_min_pr<0 or loc_max_pr<0:
            print ("Profits can't be < 0. Check your profits: min_profit = " + repr(loc_min_pr) + "; and max_profit = " + repr(loc_max_pr))
            return None
        if loc_min_pr>loc_max_pr:
            tmp = loc_max_pr
            loc_max_pr = loc_min_pr
            loc_min_pr = tmp
            
        new_fn = output_filepath+".csv"
        columns = ('Index', 'Name1', 'Price1', 'Quality1', 'Name2', 'Price2', 'Quality2', 'Profit_1_TO_2', 'FROM_TO', 'URL1', 'URL2')
        
        conn = sqlite3.connect(db_name + '.db')
        c = conn.cursor()
        tn = 'interval_table'
        parameter_name = '''CREATE TABLE IF NOT EXISTS 
        %s(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''' % (tn, 'Ind', 'Name1', 'Price1', 'Quality1', 'Name2', 'Price2', 'Quality2', 'Profit_1_TO_2', 'FROM_TO', 'URL1', 'URL2')
        parameter_name = parameter_name.replace('\'', '"')
        c.execute(parameter_name)
        
        for cur_table in tables:
            #find profits
            parameter_name = """SELECT * FROM %s WHERE profit1to2<=%d AND profit1to2>=%d""" % (cur_table, max_profit, min_profit)
            parameter_name = parameter_name.replace('\'', '"')
            
            c.execute(parameter_name)   
            results = c.fetchall()
            if len(results) == 0:
                continue
            else:
                for element in results:
                    insert_str = '''INSERT INTO %s(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, 
        %d, %s, %s, %s)''' % (tn, 'Ind', 'Name1', 'Price1', 'Quality1', 'Name2', 'Price2', 'Quality2', 'Profit_1_TO_2', 'FROM_TO', 'URL1', 'URL2', repr(element[0]), repr(element[1]), repr(element[2]), repr(element[3]), repr(element[4]), repr(element[5]), repr(element[6]), element[7], repr(cur_table), repr(element[8]), repr(element[9]))
                    c.execute(insert_str)
        parameter_name = self.get_select_with_sort_param(profit_and_price2, tn)
        parameter_name = parameter_name.replace('\'', '"')
        c.execute(parameter_name)
        
        with io.open(new_fn, 'w', newline='', encoding='utf-8', errors='ignore') as selected:
            wr = csv.writer(selected, quoting = csv.QUOTE_MINIMAL, dialect='excel')
            wr.writerow(columns)
            [wr.writerow(row) for row in c.fetchall()]

        conn.commit()
        c.close()
        conn.close()
    

    #sort data controller
    def get_select_with_sort_param(self, param, table_name):
        #sort by price from second shop/exchanger by asc
        if param == 'priceASC':
            return 'SELECT * FROM %s ORDER BY Price2 ASC' % (table_name)
        #sort by price from second shop/exchanger by desc
        if param == 'priceDESC':
            return 'SELECT * FROM %s ORDER BY Price2 DESC' % (table_name)
        #sort by price and profit from second shop/exchanger by asc
        if param == 'profit_priceASC':
            return 'SELECT * FROM %s ORDER BY Profit_1_TO_2 DESC, Price2 ASC' % (table_name)
        #sort by price and profit from second shop/exchanger by desc (default)
        return 'SELECT * FROM %s ORDER BY Profit_1_TO_2 DESC, Price2 DESC' % (table_name)