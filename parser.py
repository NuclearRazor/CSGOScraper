import time
import datetime
import re
import csv
import json

from lxml import html
import pandas as pd
import requests
from bs4 import BeautifulSoup
import config as mc

import cfscrape

pd.options.mode.chained_assignment = None


class ParseMarkets(mc.MetaConfig):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        print("\nStarted. TIME: "+repr(time.ctime()))

        comission_list = self.get_comission()

        check_csgotm = self.parse_csgotmmarket(comission_list[0])

        check_csmoney = self.parse_csmoneymarket(comission_list[1])

        check_csgosell = self.parse_csgosellmarket(comission_list[3])

        print("Finished. TIME: "+repr(time.ctime()))


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
            for line in f:
                find_num = re.findall(num_pattern, str(line))
                num_coeff.append(self.convert_to_str(find_num))

        return num_coeff


    def get_url_regular(self, link):
        get_r = requests.get(link)

        webpage = get_r.content

        return webpage


    def get_url_safe(self, link):
        scraper = cfscrape.create_scraper()
        webpage = scraper.get(link).content
        
        return webpage


    def parse_csgotmmarket(self, site_comission):
        print('\n=====Parse data from https://market.csgo.com/=====')

        csgo_url = 'https://market.csgo.com/itemdb/current_730.json'

        site_data = self.get_url_regular(csgo_url)

        csgotm_header = ["index", "c_market_name_en", "c_price", "c_quality"]

        data = json.loads(site_data)

        file_name = 'https://market.csgo.com/itemdb/' + data['db']

        site_data = self.get_url_regular(file_name)

        with open('csgotm_full_data.csv', 'wb') as file:
            file.write(site_data)

        #print('\nURL of csgotm database: ', file_name)

        #print('\nEditing csgotm database')

        origin_file = pd.read_csv('csgotm_full_data.csv', delimiter=";")

        keep_col = ['c_market_name_en', 'c_price', 'c_offers', 'c_popularity', 'c_rarity', 'c_quality']

        new_file = origin_file[keep_col]

        comission = int(site_comission)/100

        #print("\nComission: ", comission)

        new_file['c_price'] = new_file['c_price'].apply(lambda x: round(float((x) * (1 + comission)), 2))

        csgotm_csv_db = new_file.reset_index()

        csgotm_csv_db.to_csv('csgotm_data.csv', index=False)

        print('\n=====Csgotm parsing is done=====\n')


    def parse_csmoneymarket(self, site_comission):
        print('\n=====Parse data from https://cs.money/=====')

        csmoney_url = 'https://cs.money/load_bots_inventory?hash='

        site_data = self.get_url_regular(csmoney_url)

        clear_data = self.json_filter(site_data, 'm', 'e', 'p', 'f')

        convert_course = self.csmoney_usd_course()

        csmoney_comission = int(site_comission)/100
        
        #print("\nComission: ", csmoney_comission)

        csmoney_fixed_price = self.evaluate_price(clear_data['prices'], csmoney_comission, convert_course)

        csmoney_header = ["index", "c_market_name_en", "c_price", "c_quality"]

        self.save_data(csmoney_header, clear_data, csmoney_fixed_price, 'csmoney_data')

        print('\n=====Cs.money parsing is done=====\n')


    def parse_csgosellmarket(self, site_comission):
        print('\n=====Parse data from https://csgosell.com/=====')

        csgosell_url = 'https://csgosell.com/phpLoaders/forceBotUpdate/all.txt'

        site_data = self.get_url_safe(csgosell_url)

        clear_data = self.json_filter(site_data, 'h', 'e', 'p', 'f')

        convert_course = self.csmoney_usd_course()

        #print('\nURL of https://csgosell.com database: ', csgosell_url)

        csgosell_comission = int(site_comission) / 100

        #print("\nComission: ", csgosell_comission)

        csgosell_fixed_price = self.evaluate_price(clear_data['prices'], csgosell_comission, convert_course)

        csgosell_header = ["index", "c_market_name_en", "c_price", "c_quality"]

        self.save_data(csgosell_header, clear_data, csgosell_fixed_price, 'csgosell_data')

        print('\n=====Csgosell parsing is done=====\n')


    def csmoney_usd_course(self):

        money_url = 'https://cs.money/get_info?hash='

        money_pattern = r'(\d+\.\d+)'

        r = requests.get(money_url)

        money_webpage = self.get_url_regular(money_url)

        money_value = re.findall(money_pattern, money_webpage.decode('utf-8'))

        convert_value_item = float(money_value[1])

        return convert_value_item


    def json_filter(self, webpage, name, quality, price, flt):

        data = []
        name_items = []
        quality_items = []
        price_items = []
        csshellpriceToWrite = []
        float_items = []

        row_index = []
        row_value = 0

        data = json.loads(webpage)

        for each in data:
            if name in each:
                name_items.append(each[name])
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

# def show_ip():
#     try:
#         url = 'http://whatismycountry.com'
#         r = requests.Session()
#         page = r.get(url)
#         soup = BeautifulSoup(page.content, 'html5lib')
#         h3 = soup.find('h3')
#         strong = soup.find('strong')
#         print('\nCountry: ', str(h3.get_text()).strip())
#         print('\nIP: ', str(strong.get_text()).strip())
#     except:
#         print('\nCannot parse IP, continue')

#site banned
def skinsjar_market(convert_value, skinsjar_comission):
    skinsjar_url = 'https://skinsjar.com/api/v3/load/bots?refresh=0&v=0'

    r = requests.get(skinsjar_url)

    webpage = r.content.decode('utf-8')

    data = []
    name = []
    short_name = []
    price = []
    each_el = []
    float_val = []
    ext = []
    priceToWrite = []
    row_index = []
    row_value = 0
    data = json.loads(webpage)

    for each in data['items']:
        each_el.append(each)
        if 'name' in each:
            name.append(each['name'])
            row_index.append(row_value)
            row_value += 1
        if 'shortName' in each:
            short_name.append(each['shortName'])
        if 'exterior' in each:
            ext.append(each['exterior'])

    for item in each_el:
        if 'price' in item:
            price.append(item['price'])
        if 'floatMax' in item:
            float_val.append(item['floatMax'])

    print('\nURL of skinsjar.com/ru/ database: ', skinsjar_url)

    COMISSION = int(skinsjar_comission) / 100
    print("\nComission: ", COMISSION)

    for price_element in price:
        price_value = float(price_element) * (1 + COMISSION) * convert_value
        price_value = round(price_value, 2)
        priceToWrite.append(price_value)

    skinsjar_header = ["index", "c_market_name_en", "c_price", "c_quality"]
    my_df = pd.DataFrame(list(map(list, zip(row_index, short_name, priceToWrite, ext))), columns=skinsjar_header)
    my_df.to_csv('skinsjar_data.csv', index=False)

    print('\n=====Skinsjar parsing is done=====\n')


if __name__ == '__main__':

    MetaApp = mc.createWidget()
    MainApp = ParseMarkets()