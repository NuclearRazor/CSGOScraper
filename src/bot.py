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
import pandas as pd

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


def check_file(filename):
    directory = os.getcwd()
    file_path = os.path.join(directory, filename)
    if os.path.isfile(file_path):
        return True
    else:
        return False


@bot.message_handler(regexp = '/setconfig')
def function_name(message):
    '''
    update value for key in options.ini
    '''
    bot.reply_to(message, "\nChange keys and value as is:\n\n\
    1. Don\'t change keys name, only use it\n\
    2. Don\'t change structure of values if it list etc\n\
    3. Shops and exchangers must be not equal (compare unique data\'s)\n\
    4. Digits are always integers")

    _pattern = r'\w+'
    _searched = re.findall(_pattern, message.text)

    _key = ''
    _value = ''
    _validate = False

    if len(_searched) == 1:
        bot.send_message(message.chat.id, 'Was not entered key or value, please try again')
        return

    if 'shops' in message.text:
        _validate = True
        _value = list()
        _key = 'shops'
        try:
            for item in _searched[2:]:
                if item == 'csv' or item == '.csv':
                    continue
                _var = item + '.csv'
                _value.append(_var)
        except Exception as e:
            bot.send_message(message.chat.id, 'Can\'t handle values for shops key, please try again')
            logging.info('{}\tCan\'t handle values for shops key: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))
            return

    if 'exchangers' in message.text:
        _validate = True
        _value = list()
        _key = 'exchangers'
        try:
            for item in _searched[2:]:
                if item == 'csv' or item == '.csv':
                    continue
                _var = item + '.csv'
                _value.append(_var)
        except Exception as e:
            bot.send_message(message.chat.id, 'Can\'t handle values for exchangers key, please try again')
            logging.info('{}\tCan\'t handle values for exchangers key: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))
            return

    if 'opskins_config' in message.text:
        _validate = True
        _key = 'opskins_config'
        _lockeys = list()
        _locvalues = list()
        _j = 0
        try:
            for _ in _searched[2:]:
                if _j % 2 == 0:
                    _lockeys.append(_searched[2:][_j])
                else:
                    _locvalues.append(int(_searched[2:][_j]))
                _j += 1
            _value = dict(zip(_lockeys, _locvalues))
        except Exception as e:
            bot.send_message(message.chat.id, 'Can\'t handle values for opskins_config key, please try again')
            logging.info('{}\tCan\'t handle values for opskins_config key: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))
            return

    if _validate == False:
        try:
            if _searched is not None:
                if len(_searched) == 3:
                    _key = _searched[1]
                    _value = _searched[2]
        except Exception as e:
            bot.send_message(message.chat.id, 'Can\'t handle key and value, please try again')
            logging.info('{}\tCan\'t handle key and value: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))
            return

    _filename = 'options.ini'
    if check_file(_filename):
        import io
        _file_dump = ''
        with io.open(_filename, encoding='utf-8', errors='ignore') as f:
            _file_dump = json.load(f)

        _old_value = ''
        _checker = False

        try:
            for item in _file_dump:
                if _key in _file_dump[item]:
                    _old_value = _file_dump[item][_key]
                    _checker = True
                    if isinstance(_value, list):
                        _file_dump[item][_key] = _value
                    elif _value.isdigit():
                        _file_dump[item][_key] = int(_value)
                    elif _value.isdigit() == False:
                        _file_dump[item][_key] = _value

            if _checker:
                with open(_filename, 'w', encoding='utf-8', errors='ignore') as outfile:
                    json.dump(_file_dump, outfile, ensure_ascii=False)

                if _old_value is not None:
                    bot.send_message(message.chat.id, 'Value {} was updated for key {} to: {}'.format(_old_value, _key, _value))
            else:
                bot.send_message(message.chat.id, 'There no key: {} and value: {}'.format(_key, _value))
        except Exception as e:
            bot.send_message(message.chat.id, 'Can\'t work with file with it name: {}'.format(_filename))
            logging.error('{}\tError: Can\'t find file with name: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))

    else:
        print('Cannot find file: ', _filename)
        bot.send_message(message.chat.id, 'Can\'t find file with name: {}'.format(_filename))


@bot.message_handler(regexp = '/getconfig')
def function_name(message):
    '''
    get options.csv - table witk KEY and VALUE columns
    '''
    bot.send_message(message.chat.id, "Scraping config:")

    _filename = 'options.ini'

    if check_file(_filename):
        try:
            import io
            _file_dump = ''
            with io.open(_filename, encoding='utf-8', errors='ignore') as f:
                _file_dump = json.load(f)

            _headers = ['KEY', 'VALUE']
            _names = list()
            _values = list()
            for item in _file_dump:
                for it in _file_dump[item]:
                    _names.append(it)
                    _values.append(_file_dump[item][it])

            df = pd.DataFrame(list(map(list, zip(_names, _values))), columns=_headers)

            file_name = 'options.csv'
            df.to_csv(file_name, index=False)

            _filepath = os.path.join(os.getcwd(), file_name)
            doc = open(_filepath, 'rb')
            bot.send_document(message.chat.id, doc)
        except Exception as e:
            bot.send_message(message.chat.id, 'Can\'t work with file with it name: {}'.format(_filename))
            logging.error('{}\tError: Can\'t find file with name: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))
    else:
        print('Cannot find file: ', _filename)
        bot.send_message(message.chat.id, 'Can\'t find file with name: {}'.format(_filename))
        logging.info('{}\tCan\'t find file with name: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), _filename))


@bot.message_handler(commands=['help', 'getlast', 'rate', 'getdata'])
def handle_main(message):
    if 'help' in message.text:
        _help_text = u"\rType next commands to use the bot:\n\n\
        /rate CUR: get csmoney exchange rate for typed currency (RUB as default)\n\n\
        /getlast: get last scraped final table\n\n\
        /getdata: start scraping all data\n\n\
        /setconfig KEY VALUE: set options to scraper, keys must be named as is\n\n\
        /getconfig: get options table for scraping\n"
        bot.send_message(message.chat.id, _help_text)

    if 'getlast' in message.text:
        _path = os.getcwd()
        _data_path = os.path.join(_path, 'scraped_files')
        try:
            _files = [i for i in filter(lambda x: x.endswith('.csv'), os.listdir(_data_path))]
            _path = [item for item in _files if 'interval' in item]
            _filepath = os.path.join(_data_path, _path[0])
            doc = open(_filepath, 'rb')
            bot.send_document(message.chat.id, doc)
        except Exception as e:
            bot.send_message(message.chat.id, "Can\'t send final table")
            logging.error('{}\tCan\'t send final table: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))

    if 'rate' in message.text:

        def get_rate(value="RUB"):
            try:
                money_url = 'https://cs.money/get_info?hash='
                scraper = cfscrape.create_scraper(delay=15)
                time_point = dt.datetime.now().strftime("%H:%M:%S")
                webpage = scraper.get(money_url).content
                json_mon = json.loads(webpage)
                convert_value_item = json_mon["list_currency"][value]["value"]
                return str(round(float(convert_value_item), 2)), time_point
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


    if 'getdata' in message.text:
        import scraper as pr
        try:
            bot.reply_to(message, "Start scraping...")
            _parser = pr.ParseMarkets()
            _fp = _parser.getFilePath()
            _tx = _parser.getTimeScrapingDuration()
            bot.send_message(message.chat.id, "Time duration for current scraping: {}".format(_tx))
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
