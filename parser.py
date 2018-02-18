# -*- coding: utf-8 -*-
import datetime
import json
import pandas as pd
import requests
import config as mc
import opskins_core as op
import db as da

import cfscrape

pd.options.mode.chained_assignment = None


class ParseMarkets(mc.MetaConfig):

    def __init__(self, _data, _comission):
        super().__init__()

        self.initUI(_data, _comission)


    def initUI(self, _data, _comission):
        self.quazi_hash(_data, _comission)


    def quazi_hash(self, _data, _comission):

        _opskins_config = {}
        comission_list = _comission

        # for the purity of comparison, we will adopt
        # a constant exchange rate at the time of information scraping
        self.convert_course = self.csmoney_usd_course()

        # config opskins
        if "opskins_config" in _data and len(_data) != 0:
            _opskins_config = _data["opskins_config"]
            _opskins_config["comission"] = comission_list[4]
            _opskins_config["exchange_rate"] = self.convert_course
        else:
            return

        # associate each shop/exhanger with it config variables
        _hash_params = {'csgotm_data.csv': comission_list[0],\
                        'opskins_data.csv': _opskins_config,\
                        'csgosell_data.csv': comission_list[3],\
                        'csmoney_data.csv': comission_list[1],\
                        'skinsjar_data.csv': comission_list[2]\
                       }

        # associate shops/exhangers names with referencies to methods
        _hash_data = {'csgotm_data.csv': self.parse_csgotmmarket,\
                      'opskins_data.csv': op.Opskins_Market,\
                      'csgosell_data.csv': self.parse_csgosellmarket,\
                      'csmoney_data.csv': self.parse_csmoneymarket,\
                      'skinsjar_data.csv': self.parse_skinsjarmarket\
                     }

        if _data["opskins_config"]:
            _data.pop('opskins_config', None)
            [[_hash_data[_item](_hash_params[_item]) for _item in _data[_key]] for _key in _data]


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
        csmoney_comission = int(site_comission)/100
        csmoney_fixed_price = self.evaluate_price(clear_data['prices'], csmoney_comission, self.convert_course)
        csmoney_header = ["index", "c_market_name_en", "c_price", "c_quality"]
        self.save_data(csmoney_header, clear_data, csmoney_fixed_price, 'csmoney_data')


    def parse_csgosellmarket(self, site_comission = 1):

        csgosell_url = 'https://csgosell.com/phpLoaders/forceBotUpdate/all.txt'
        site_data = self.get_url_safe(csgosell_url)
        clear_data = self.json_filter(site_data, 'h', 'e', 'p', 'f')
        csgosell_comission = int(site_comission)/100
        csgosell_fixed_price = self.evaluate_price(clear_data['prices'], csgosell_comission, self.convert_course)
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

        skinsjar_comission = int(site_comission)/100
        skinsjar_fixed_price = self.evaluate_price(price, skinsjar_comission, self.convert_course)
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
        'qualities': quality_items, 'prices': price_items, 'floats': float_items}

        return json_dict


if __name__ == '__main__':

    start_fx = datetime.datetime.now().replace(microsecond = 0)

    MetaApp = mc.createWidget()
    scraping_config, fee, analyze_config = MetaApp.parse_options()
    MainApp = ParseMarkets(scraping_config, fee)
    db = da.DataAnalyse(analyze_config)

    print("\nStarted. TIME: " + str(start_fx))
    finish_fx = datetime.datetime.now().replace(microsecond = 0)
    print("Finished. TIME: " + str(finish_fx))
    print("Elapsed. Time:", str((finish_fx - start_fx)))