# -*- coding: utf-8 -*-
import parser as pr
import telebot
import time
import sys
import logging
import os
import datetime as dt
import cfscrape
import json
import sqlite3
import re

API_TOKEN = ''

conn = None
c = None

bot = telebot.TeleBot(API_TOKEN)
#telebot.logger.setLevel(logging.DEBUG)

logging.basicConfig(filename='logging_data.log', level=logging.DEBUG)


def store_to_db(timer = None, data = None, table = None):
    global c
    global conn

    dbname = 'statisticsinfo.db'

    _TIME = 'TIME'
    _DATA = 'DATA'
    _TIMER = 'TIMER'

    # make column name to db or pass it
    parameter_name = 'CREATE TABLE IF NOT EXISTS %s(%s, %s, %s)' % (
        dbname.replace('.db', ''), repr(_TIME), repr(_TIMER), repr(_DATA))
    parameter_name = parameter_name.replace('\'', '"')

    # connect to database with statistical info
    # (for the first time store all passing data through bot without any filters)
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    c.execute(parameter_name)

    _time = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    parameter_save = 'INSERT INTO %s(%s, %s, %s) VALUES (?, ?, ?)' % (
        dbname.replace('.db', ''), repr(_TIME), repr(_TIMER), repr(_DATA))
    _store_data = list()
    _store_data.append((_time, timer, data))
    # store in db list with values to save
    c.executemany(parameter_save, _store_data)

    # store final table into database
    if table is not None:
        import pandas as pd

        try:
            df = pd.read_csv(table, engine='python')
            df.to_sql('DATA_TABLE', conn, if_exists='append', index=False)
        except Exception as e:
            logging.info('{}\tCan\'t store table data: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))

    conn.commit()
    # close cursor and db connector
    c.close()
    conn.close()


@bot.message_handler(commands=['help', 'get_last', 'rate', 'get_data'])
def handle_main(message):

    if 'help' in message.text:
        _help_text = u"\rType with separator '/' for use next commands:\n\n\
        - rate CUR: get csmoney exchange rate for typed currency (RUB as default)\n\n\
        - get_last: get last scraped final table\n\n\
        - get_data: start scraping all data\n\n\
        - set_mags: set mag names to scrape\n"
        bot.send_message(message.chat.id, _help_text)

    if 'get_last' in message.text:
        _path = os.getcwd()
        _data_path = os.path.join(_path, 'scraped_files')
        try:
            _files = [i for i in filter(lambda x: x.endswith('.csv'), os.listdir(_data_path))]
            _path = [item for item in _files if 'interval' in item]
            _filepath = os.path.join(_data_path, _path[0])
            doc = open(_filepath, 'rb')
            bot.send_document(message.chat.id, doc)
        except:
            bot.send_message(message.chat.id, "Can\'t send final table")
            logging.info('{}\tCan\'t send final table'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    if 'rate' in message.text:

        def get_rate(value="RUB"):
            try:
                money_url = 'https://cs.money/get_info?hash='
                scraper = cfscrape.create_scraper(delay=15)
                time_point = dt.datetime.now().strftime("%H:%M:%S")
                webpage = scraper.get(money_url).content
                json_mon = json.loads(webpage)
                convert_value_item = json_mon["list_currency"][value]["value"]
                return str(convert_value_item), time_point
            except:
                print('Alert: can\'t get exchange rate by get method')
                logging.info('{}\tCan\'t get exchange rate from cs.money source distanation'.format(
                    dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                return

        _evalue = ''
        _search_value_pattern = r'\w+'
        _searched = re.findall(_search_value_pattern, message.text)
        try:
            if _searched is not None:
                if len(_searched[1]) == 3:
                    _evalue = _searched[1]
        except Exception as e:
            logging.info('{}\tCan\'t parse currency: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))
            pass

        try:
            # default option
            if len(_evalue) == 0:
                bot.send_message(message.chat.id, 'Wrong typed currency or this is not in all currencies referer list, use RUB')
                # set default currency as RUB
                _evalue = "RUB"
            _mvalue = "USD"
            _rate, _time = get_rate(_evalue)
            _rate_course = 'Current ' + _mvalue + ' to ' +  _evalue + ' rate at ' + _time + ' is: ' + _rate
            bot.send_message(message.chat.id, _rate_course)
            store_to_db(data = _rate_course)
        except Exception as e:
            bot.send_message(message.chat.id, 'Currency was typed: {}'.format(_evalue))
            bot.send_message(message.chat.id, \
                             "Error while getting exchange rate.\nPlease report about this issue to:\nhttps://github.com/NuclearRazor/csgo_scraper/issues")
            logging.info('{}\tCan\'t scrape exchange rate: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))


    if 'get_data' in message.text:
        import scraper as pr
        try:
            _parser = pr.ParseMarkets()
            _fp = _parser.getFilePath()
            _tx = _parser.getTimeScrapingDuration()
            doc = open(_fp, 'rb')
            bot.send_document(message.chat.id, doc)
            store_to_db(timer=_tx, table = _fp)
        except Exception as e:
            bot.send_message(message.chat.id, \
                             "Error while getting all data.\nPlease report about this issue to:\nhttps://github.com/NuclearRazor/csgo_scraper/issues")
            logging.info('{}\tCan\'t get all data by scraper: {}'.format(
                        dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))


class BotUI():

    def __init__(self):
        super().__init__()
        self.initReTU()


    def initReTU(self):
        while True:
            try:
                bot.polling(none_stop=True)
            except Exception as e:
                logging.error(e)
                time.sleep(15)


if __name__ == '__main__':
    try:
        app = BotUI()
    except KeyboardInterrupt:
        print >> sys.stderr, '\nExiting by user request.\n'
        sys.exit(0)
