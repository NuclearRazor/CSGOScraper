import requests
from bs4 import BeautifulSoup
from random import choice
from time import sleep
from random import uniform
import re
from http.server import BaseHTTPRequestHandler
from collections import defaultdict

import csv
import json
from lxml import html
import codecs
import pandas as pd

import cfscrape

pd.options.mode.chained_assignment = None

class ParseMarkets():

    def __init__(self):

        #INIT URLS
        self.initUI()

    def initUI(self):
        pass

        #метод записи данных в файл
        #метод чтения данных из файла

        #метод get_safe запросов
        #метод get_regular запросов

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

    def check_file_exist(self, filename):
        directory = os.getcwd()

        file_path = directory + '\\' + 'filename'

        #if os.path.isfile(file_path) == False:
        pass

    def get_comission(self):
        num_pattern = r'\d+'
        num_coeff = []
        find_num = ''

        with open('coefficients.txt') as f:
            for line in f:
                find_num = re.findall(num_pattern, str(line))
                num_coeff.append(self.convert_to_str(find_num))

        print(num_coeff)
        return num_coeff

    def get_regular(self, link):
        get_r = requests.get(link)

        webpage = get_r.content.decode('utf-8')

        return webpage

# def magic_str(numList):
#     try:
#         if numList != None:
#             s = map(str, numList)  # ['1','2','3']
#             s = ''.join(s)  # '123'
#         else:
#             s = 'None'
#             return s
#     except (ValueError, TypeError, RuntimeError):
#         print('\nEmpty object or none, continue, value = None\n')
#         s = 'None'
#         pass
#     return s


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


def csgo_market(cs_go_tm_comission):

    csgo_url = 'https://market.csgo.com/itemdb/current_730.json'
    r = requests.get('https://market.csgo.com/itemdb/current_730.json')

    csgotm_header = ["index", "c_market_name_en", "c_price", "c_quality"]

    data = json.loads(r.content)

    file_name = 'https://market.csgo.com/itemdb/' + data['db']

    r = requests.get(file_name)

    with open('csgotm_full_data.csv', 'wb') as file:
        file.write(r.content)
        file.close()

    print('\nURL of csgotm database: ', file_name)

    print('\nEditing csgotm database')

    f = pd.read_csv('csgotm_full_data.csv', delimiter=";")

    keep_col = ['c_market_name_en', 'c_price', 'c_offers', 'c_popularity', 'c_rarity', 'c_quality']

    new_file = f[keep_col]

    COMISSION = int(cs_go_tm_comission)/100

    print("\nComission: ", COMISSION)

    new_file['c_price'] = new_file['c_price'].apply(
        lambda x: round(float((x) * (1 + COMISSION)), 2))  # + учет комиссии

    csgotm_csv_db = new_file.reset_index()

    csgotm_csv_db.to_csv('csgotm_data.csv', index=False)

    print('\n=====Csgotm parsing is done=====\n')


def csmoney_market(cs_money_comission):
    csmoney_url = 'https://cs.money/load_bots_inventory?hash='

    r = requests.get(csmoney_url)

    webpage = r.content.decode('utf-8')

    data = []
    name = []
    quality = []
    price = []
    csshellpriceToWrite = []
    float_val = []
    row_index = []
    row_value = 0

    data = json.loads(webpage)

    for each in data:
        if 'm' in each:
            name.append(each['m'])
            row_index.append(row_value)
            row_value += 1
        if 'e' in each:
            quality.append(each['e'])
        if 'p' in each:
            price.append(each['p'])
        if 'f' in each:
            float_val.append(each['f'])

    COMISSION = int(cs_money_comission)/100
    
    print("\nComission: ", COMISSION)

    money_url = 'https://cs.money/get_info?hash='

    money_pattern = r'(\d+\.\d+)'

    r = requests.get(money_url)

    money_webpage = r.content.decode('utf-8')

    money_value = re.findall(money_pattern, money_webpage)

    print('TEST = ', float(money_value[1]))

    convert_value_item = float(money_value[1])

    for price_element in price:
        price_value = float(price_element)*(1+COMISSION)*convert_value_item
        price_value = round(price_value, 2)
        csshellpriceToWrite.append(price_value)

    csmoney_header = ["index", "c_market_name_en", "c_price", "c_quality"]
    csmoney_df = pd.DataFrame(list(map(list, zip(row_index, name, csshellpriceToWrite, quality))), columns = csmoney_header)
    csmoney_df.to_csv('csmoney_data.csv', index=False)

    return convert_value_item

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


def csgosell_market(convert_value, csgosell_comission):
    csgosell_url = 'https://csgosell.com/phpLoaders/forceBotUpdate/all.txt'

    data = []
    name = []
    quality = []
    price = []
    csshellpriceToWrite = []
    float_val = []
    row_index = []
    row_value = 0

    scraper = cfscrape.create_scraper()
    r = scraper.get(csgosell_url).content
    data = json.loads(r)

    for each in data:
        if 'h' in each:
            name.append(each['h'])
            row_index.append(row_value)
            row_value += 1
        if 'e' in each:
            quality.append(each['e'])
        if 'p' in each:
            price.append(each['p'])
        if 'f' in each:
            float_val.append(each['f'])

    print('\nURL of https://csgosell.com database: ', csgosell_url)

    COMISSION = int(csgosell_comission) / 100
    print("\nComission: ", COMISSION)

    for price_element in price:
        price_value = float(price_element) * (1 + COMISSION) * convert_value
        price_value = round(price_value, 2)
        csshellpriceToWrite.append(price_value)

    csgosell_header = ["index", "c_market_name_en", "c_price", "c_quality"]
    my_df = pd.DataFrame(list(map(list, zip(row_index, name, csshellpriceToWrite, quality))), columns=csgosell_header)
    my_df.to_csv('csgosell_data.csv', index=False)

    print('\n=====Csgosell parsing is done=====\n')


def get_comission():
    num_pattern = r'\d+'
    num_coeff = []
    find_num = ''

    with open('coefficients.txt') as f:
        for line in f:
            # data = line.split()
            find_num = re.findall(num_pattern, str(line))
            num_coeff.append(magic_str(find_num))

    return num_coeff

# добавить функцию для проверки кода отклика сервера
if __name__ == '__main__':
    # convert_usd = ''

    # comission_list = get_comission()

    MainApp = ParseMarkets()

    check = MainApp.get_comission()

    # print('\n=====Parse data from https://cs.money/=====')
    # convert_usd = csmoney_market(comission_list[1])


    # print('\n=====Parse data from https://market.csgo.com/=====')
    # csgo_market(comission_list[0])


    # print('\n=====Parse data from https://csgosell.com/=====')
    # csgosell_market(convert_usd, comission_list[3])