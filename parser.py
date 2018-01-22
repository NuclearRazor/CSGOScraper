# -*- coding: utf-8 -*-
import datetime
import re
import json

import pandas as pd
import requests
import config as mc
import opskins_core as op
import db as da

import cfscrape

pd.options.mode.chained_assignment = None


class ParseMarkets(mc.MetaConfig):

    def __init__(self, _data):
        super().__init__()

        self.initUI(_data)


    def initUI(self, _data):
        self.quazi_hash_func(_data)


    def quazi_hash_func(self, _data):

        _hash_data = {}

        comission_list = self.get_comission()

        # associate shops/exhangers names with referencies to methods
        _hash_data = {'csgotm_data.csv': self.parse_csgotmmarket,\
                      'opskins_data.csv': op.Opskins_Market,\
                      'csgosell_data.csv': self.parse_csgosellmarket,\
                      'csmoney_data.csv': self.parse_csmoneymarket,\
                      'skinsjar_data.csv': self.parse_skinsjarmarket\
                     }

        # associate shops/exhangers names with commision values
        _hash_params = {'csgotm_data.csv': comission_list[0],\
                        'opskins_data.csv': comission_list[4],\
                        'csgosell_data.csv': comission_list[3],\
                        'csmoney_data.csv': comission_list[1],\
                        'skinsjar_data.csv': comission_list[2]\
                       }

        for _list in _data:
            for _item in _list:
                if _item in _hash_data and _item in _hash_params:
                    _hash_data[_item](_hash_params[_item])


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


    def get_comission(self):
        num_pattern = r'\d+'
        num_coeff = []
        find_num = ''

        with open('coefficients.txt') as f:
            find_num = [re.findall(num_pattern, str(line)) for line in f]
            [num_coeff.append(self.convert_to_str(item)) for item in find_num]

        return num_coeff


    def get_url_regular(self, link):
        get_r = requests.get(link)
        webpage = get_r.content
        return webpage


    def get_url_safe(self, link):
        scraper = cfscrape.create_scraper()
        webpage = scraper.get(link).content
        return webpage


    def parse_csgotmmarket(self, site_comission = 1):

        csgo_url = 'https://market.csgo.com/itemdb/current_730.json'
        site_data = self.get_url_regular(csgo_url)
        data = json.loads(site_data)
        file_name = 'https://market.csgo.com/itemdb/' + data['db']
        site_data = self.get_url_regular(file_name)

        with open('csgotm_full_data.csv', 'wb') as file:
            file.write(site_data)

        origin_file = pd.read_csv('csgotm_full_data.csv', delimiter=";")
        keep_col = ['c_market_name_en', 'c_price', 'c_offers', 'c_popularity', 'c_rarity', 'c_quality']
        new_file = origin_file[keep_col]
        comission = int(site_comission)/100
        new_file['c_price'] = new_file['c_price'].apply(lambda x: round(float(x/100)*(1 + comission), 2))
        new_file['c_market_name_en'] = new_file['c_market_name_en'].str.replace(r"\(.*\)", "")
        csgotm_csv_db = new_file.reset_index()
        csgotm_csv_db.to_csv('csgotm_data.csv', index=False)


    def parse_csmoneymarket(self, site_comission = 1):

        csmoney_url = 'https://cs.money/load_bots_inventory?hash='
        site_data = self.get_url_safe(csmoney_url)
        clear_data = self.json_filter(site_data, 'm', 'e', 'p', 'f')
        convert_course = self.csmoney_usd_course()
        csmoney_comission = int(site_comission)/100
        csmoney_fixed_price = self.evaluate_price(clear_data['prices'], csmoney_comission, convert_course)
        csmoney_header = ["index", "c_market_name_en", "c_price", "c_quality"]
        self.save_data(csmoney_header, clear_data, csmoney_fixed_price, 'csmoney_data')


    def parse_csgosellmarket(self, site_comission = 1):

        csgosell_url = 'https://csgosell.com/phpLoaders/forceBotUpdate/all.txt'
        site_data = self.get_url_safe(csgosell_url)
        clear_data = self.json_filter(site_data, 'h', 'e', 'p', 'f')
        convert_course = self.csmoney_usd_course()
        csgosell_comission = int(site_comission)/100
        csgosell_fixed_price = self.evaluate_price(clear_data['prices'], csgosell_comission, convert_course)
        csgosell_header = ["index", "c_market_name_en", "c_price", "c_quality"]
        self.save_data(csgosell_header, clear_data, csgosell_fixed_price, 'csgosell_data')


    def parse_skinsjarmarket(self, site_comission = 1):

        skinsjar_url = 'https://skinsjar.com/api/v3/load/bots?refresh=0&v=0'

        site_data = self.get_url_regular(skinsjar_url)

        #name = []
        short_name = []
        price = []
        each_el = []
        float_val = []
        ext = []
        row_index = []
        row_value = 0
        data = json.loads(site_data)

        for each in data['items']:
            each_el.append(each)
            '''
            item names with qualities
            # if 'name' in each:
            #     name.append(each['name'])
            #     row_index.append(row_value)
            #     row_value += 1
            '''
            if 'shortName' in each:
                #item names without qualities
                short_name.append(each['shortName'])
                row_index.append(row_value)
                row_value += 1
            if 'exterior' in each:
                ext.append(each['exterior'])

        for item in each_el:
            if 'price' in item:
                price.append(item['price'])
            if 'floatMax' in item:
                float_val.append(item['floatMax'])

        convert_course = self.csmoney_usd_course()
        skinsjar_comission = int(site_comission)/100
        skinsjar_fixed_price = self.evaluate_price(price, skinsjar_comission, convert_course)
        skinsjar_header = ["index", "c_market_name_en", "c_price", "c_quality"]
        my_df = pd.DataFrame(list(map(list, zip(row_index, short_name, skinsjar_fixed_price, ext))), columns=skinsjar_header)
        my_df.to_csv('skinsjar_data.csv', index=False)


    def csmoney_usd_course(self):
        money_url = 'https://cs.money/get_info?hash='
        json_mon = json.loads(self.get_url_safe(money_url))
       	convert_value_item = float(json_mon["list_currency"]["RUB"]["value"])
        return convert_value_item


    def json_filter(self, webpage, name, quality, price, flt):

        name_items = []
        quality_items = []
        price_items = []
        float_items = []

        row_index = []
        row_value = 0

        data = json.loads(webpage)

        for each in data:
            if name in each:
                # cut item quality in item name string
                val = each[name].split('(')[0]
                name_items.append(val)
                row_index.append(row_value)
                row_value += 1
            if quality in each:
                quality_items.append(each[quality])
            if price in each:
                price_items.append(each[price])
            if flt in each:
                float_items.append(each[flt])

        json_dict = {'rows_num': row_index, 'names': name_items, \
        'qualitys': quality_items, 'prices': price_items, 'floats': float_items}

        return json_dict


if __name__ == '__main__':

    start_fx = datetime.datetime.now().replace(microsecond=0)

    shops = ['csgotm_data.csv', 'opskins_data.csv']
    exchangers = ['csgosell_data.csv', 'csmoney_data.csv']
    # temporary site fix from skinsjar side
    # 'skinsjar_data.csv']
    data_to_scrape = list()

    data_to_scrape.append(shops)
    data_to_scrape.append(exchangers)

    MetaApp = mc.createWidget()
    MainApp = ParseMarkets(data_to_scrape)

    coeff_mag = 0
    min_price = 1
    max_price = 1000
    min_profit = 25
    max_profit = 150
    sort_flag = 'profit_priceDESC'
    compare_equal_qualities = True
    empiric_profit_bound = 150

    db = da.DataAnalyse(shops, exchangers, compare_equal_qualities,\
    coeff_mag, min_price, max_price, min_profit, max_profit, sort_flag, empiric_profit_bound)

    finish_fx = datetime.datetime.now().replace(microsecond = 0)

    print("\nStarted. TIME: " + str(start_fx))
    print("Finished. TIME: " + str(finish_fx))
    print("Elapsed. Time:", str((finish_fx - start_fx)))