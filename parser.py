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
import pprint
import pandas as pd

import cfscrape

global get_method

pd.options.mode.chained_assignment = None


def magic_str(numList):  # вспомогательная функция
    try:
        if numList != None:
            s = map(str, numList)  # ['1','2','3']
            s = ''.join(s)  # '123'
        else:
            s = 'None'
            return s
    except (ValueError, TypeError, RuntimeError):
        print('\nEmpty object or none, continue, value = None\n')
        s = 'None'
        pass
    return s

def show_ip():
    try:
        url = 'http://whatismycountry.com'
        r = requests.Session()
        page = r.get(url)
        soup = BeautifulSoup(page.content, 'html5lib')
        h3 = soup.find('h3')
        strong = soup.find('strong')
        print('\nCountry: ', str(h3.get_text()).strip())
        print('\nIP: ', str(strong.get_text()).strip())
    except:
        print('\nCannot parse IP, continue')

def csgo_market(cs_go_tm_comission):
    try:

        csgo_url = 'https://market.csgo.com/itemdb/current_730.json'
        r = requests.get('https://market.csgo.com/itemdb/current_730.json')

        data = []
        data = json.loads(r.content.decode('utf-8'))

        for item in data:
            try:
                if item == 'db':  # get from json db index
                    print('\nDatabase csgotm name: ', data[item])
                    table_data = 'https://market.csgo.com/itemdb/' + data[item]
            except:
                print('\nCannot parse JSON data')

        print('\nURL of csgotm database: ', table_data)

        r = requests.get(table_data)

        with open('csgotm_full_data.csv', 'wb') as file:
            file.write(r.content)
            file.close()
    except:

        print('\nCannot parse data from https://market.csgo.com/')

    # try:
    print('\nEditing csgotm database')
    f = pd.read_csv('csgotm_full_data.csv', delimiter=";")

    keep_col = ['c_market_name_en', 'c_price', 'c_offers', 'c_popularity', 'c_rarity', 'c_quality']

    new_file = f[keep_col]

    COMISSION = int(cs_go_tm_comission) / 100

    print("\nComission: ", COMISSION)

    new_file['c_price'] = new_file['c_price'].apply(
        lambda x: round(float(str((x) * 0.01 * (1 + COMISSION))), 2))  # + учет комиссии

    csgotm_csv_db = new_file.reset_index()

    csgotm_csv_db.to_csv('csgotm_data.csv', index=False)

    print('\n=====Csgotm parsing is done=====\n')
    # except:
    # print('\nEdit database error')


def csmoney_market(cs_money_comission):
    csmoney_url = 'https://cs.money/load_bots_inventory?hash='

    money_url = 'https://cs.money/get_info?hash='

    money_pattern = r'(\d+\.\d+)'

    find_pattern = r'\{(.*?)\}'

    name_pattern = r'\"m\"\:(.*?)\,\"'

    quality_pattern = r'\"e\"\:(.*?)\,\"'

    price_pattern = r'\"p\"\:(\d+\.\d+)'

    # float_pattern = r'\"(\d+\.\d+)\"'
    # convert to json algorithm

    r = requests.get(csmoney_url)
    rr = requests.get(money_url)

    webpage = str(r.content.decode('utf-8'))

    money_webpage = str(rr.content.decode('utf-8'))

    find_value = re.findall(find_pattern, webpage)
    money_value = re.findall(money_pattern, money_webpage)
    name = re.findall(name_pattern, str(find_value))
    quality = re.findall(quality_pattern, str(find_value))
    price_value = re.findall(price_pattern, str(find_value))

    print('\nURL of cs.money database: ', csmoney_url)
    print('\nRouble course in Csmoney = ', (money_value[1]))

    listToWrite = []

    COMISSION = int(cs_money_comission) / 100
    print("\nComission: ", COMISSION)

    name_items = []
    quality_items = []
    row_index = []
    row_value = 0

    for name_item in name:
        name_value = magic_str(name_item)
        name_clear = name_value.replace('"', '')
        name_items.append(name_clear)
        row_index.append(row_value)
        row_value += 1

    for quality_item in quality:
        quality_value = magic_str(quality_item)
        quality_clear = quality_value.replace('"', '')
        quality_items.append(quality_clear)

    for item in price_value:
        price = float(magic_str(item)) * (1 + COMISSION) * float(money_value[1])
        price = round(price, 2)
        listToWrite.append(price)

    csmoney_header = ["index", "c_market_name_en", "c_price", "c_quality"]
    my_df = pd.DataFrame(list(map(list, zip(row_index, name_items, listToWrite, quality_items))),
                         columns=csmoney_header)
    my_df.to_csv('csmoney_data.csv', index=False)

    print('\n=====Cs.money parsing is done=====\n')

    convert_value_item = float(money_value[1])

    return convert_value_item


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
    convert_usd = ''

    comission_list = get_comission()

    # print('\nYour info:')
    # show_ip()
    print('\n=====Parse data from https://market.csgo.com/=====')
    csgo_market(comission_list[0])

    # print('\nYour info:')
    # show_ip()
    print('\n=====Parse data from https://cs.money/=====')
    convert_usd = csmoney_market(comission_list[1])

    # print('\nYour info:')
    # show_ip()
    # print('\n=====Parse data from https://skinsjar.com/ru/=====')
    # skinsjar_market(convert_usd, comission_list[2])

    # print('\nYour info:')
    # show_ip()
    print('\n=====Parse data from https://csgosell.com/=====')
    csgosell_market(convert_usd, comission_list[3])

    '''

    try:
        print('\nYour info:')
        show_ip()
        print('\n=====Parse data from https://market.csgo.com/=====')
        csgo_market()
    except:
        print('\n!!!Cannot parse data from https://market.csgo.com/!!!')

    try:
        print('\nYour info:')
        show_ip()
        print('\n=====Parse data from https://cs.money/=====')
        convert_usd = csmoney_market()
    except:
        print('\n!!!Cannot parse data from https://cs.money/!!!')

    try:
        print('\nYour info:')
        show_ip()
        print('\n=====Parse data from https://skinsjar.com/ru/=====')
        skinsjar_market(convert_usd)
    except:
        print('\n!!!Cannot parse data from https://skinsjar.com/ru/!!!')

    try:
        print('\nYour info:')
        show_ip()
        print('\n=====Parse data from https://csgosell.com/=====')
        csgosell_market(convert_usd)
    except:
        print('\n!!!Cannot parse data from https://csgosell.com/!!!')
    '''
