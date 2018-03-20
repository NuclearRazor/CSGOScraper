# -*- coding: utf-8 -*-
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


def similar(a, b):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio()


def filterfiles(nec_files, todel_files):
    return [file for file in nec_files if file not in todel_files]


@bot.message_handler(regexp = '/setconfig')
def handle_cmd(message):
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
                    elif isinstance(_value, dict):
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
def handle_cmd(message):
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


@bot.message_handler(regexp = '/getitem')
def handle_cmd(message):

    bot.reply_to(message, "\nSearching info in final table for entered item name:\n\n\
    1. Use maximally similar names to item names in tables\n\
    2. This method works only with last final table\n")

    _pattern = r'[\w\D]+'
    _searcheditem = re.findall(_pattern, message.text)

    if _searcheditem is not None:
        try:
            _itemname = _searcheditem[0].split()
            _searchitem = _itemname[1]
        except IndexError:
            bot.send_message(message.chat.id, 'Incorrect item name')
            return
    else:
        _searchitem = ''

    if sys.platform == 'win32':
        sys._enablelegacywindowsfsencoding()

    _path = os.getcwd()
    _data_path = os.path.join(_path, 'scraped_files')
    _files = [os.path.join(_data_path, i) for i in filter(lambda x: x.endswith('.csv'), os.listdir(_data_path))]
    _newest = sorted(_files, key=lambda x: os.path.getmtime(x))[-1]
    origin_file = pd.read_csv(_newest, sep=',')

    _index = 0
    _index_list = list()
    _names_first = list()
    _prices_first = list()
    _qualities_first = list()
    _names_second = list()
    _prices_second = list()
    _qualities_second = list()
    _profit = list()
    _from_to_box = list()
    _url_first = list()
    _url_second = list()

    try:
        # minimum checker for one column name
        if "Name1" in origin_file:
            for item in origin_file["Name1"]:

                _check = similar(_searchitem, item)

                if _check >= 0.35:
                    _index_list.append(_index)
                    _names_first.append(item)
                    _prices_first.append(origin_file.loc[origin_file['Name1'] == item, 'Price1'].values[0])
                    _qualities_first.append(origin_file.loc[origin_file['Name1'] == item, 'Quality1'].values[0])
                    _names_second.append(origin_file.loc[origin_file['Name1'] == item, 'Name2'].values[0])
                    _prices_second.append(origin_file.loc[origin_file['Name1'] == item, 'Price2'].values[0])
                    _qualities_second.append(origin_file.loc[origin_file['Name1'] == item, 'Quality2'].values[0])
                    _profit.append(origin_file.loc[origin_file['Name1'] == item, 'Profit_1_TO_2'].values[0])
                    _from_to_box.append(origin_file.loc[origin_file['Name1'] == item, 'FROM_TO'].values[0])
                    _url_first.append(origin_file.loc[origin_file['Name1'] == item, 'URL1'].values[0])
                    _url_second.append(origin_file.loc[origin_file['Name1'] == item, 'URL2'].values[0])
                    _index += 1

        if len(_index_list) == 0:
            bot.send_message(message.chat.id, 'No item information found')
            return
        _headers = ['Index', 'Name1', 'Price1', 'Quality1', 'Name2', 'Price2', 'Quality2', 'Profit_1_TO_2', 'FROM_TO', 'URL1', 'URL2']
        df = pd.DataFrame(list(map(list, zip(_index_list, _names_first, _prices_first, _qualities_first, _names_second,
                                             _prices_second, _qualities_second, _profit, _from_to_box, _url_first, _url_second))), columns=_headers)
        file_name = 'iteminfo.csv'
        df.to_csv(file_name, index=False)
        _path_final = os.getcwd()
        _iteminfo_path = os.path.join(_path_final, file_name)
        doc = open(_iteminfo_path, 'rb')
        bot.send_document(message.chat.id, doc)
        store_to_db(table=_iteminfo_path)
    except Exception as e:
        bot.send_message(message.chat.id, 'Can\'t find info for item: {}'.format(_searchitem))
        logging.error(
            '{}\tError: {} Can\'t find info for item: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e, _searchitem))


@bot.message_handler(commands=['help', 'getlast', 'rate', 'getdata', 'getscraped', 'getcompared'])
def handle_main(message):
    time.sleep(0.5)
    if 'help' in message.text:
        _help_text = u"\rType next commands to use the bot:\n\n\
        /rate CUR: get csmoney exchange rate for typed currency (RUB as default)\n\n\
        /getlast: get last compared final table\n\n\
        /getdata: start scraping all data\n\n\
        /getscraped: get all scraped tables for shops and exchangers\n\n\
        /getcompared: get all compared tables for shops and exchangers\n\n\
        /setconfig KEY VALUE: set options to scraper, keys must be named as is\n\n\
        /getconfig: get options table for scraping\n\n\
        /getitem NAME: get info in last final table for entered item name\n"
        bot.send_message(message.chat.id, _help_text)


    if 'getcompared' in message.text:
        try:
            _path = os.getcwd()
            _data_path = os.path.join(_path, 'scraped_files')
            _files = [i for i in  os.listdir(_data_path)]
            _markfiles = ', '.join(_files)
            bot.reply_to(message, 'Send files: {}'.format(_markfiles))

            if len(_files) != 0:
                _files = [os.path.join(_data_path, i) for i in os.listdir(_data_path)]
                for file_path in _files:
                    doc = open(file_path, 'rb')
                    bot.send_document(message.chat.id, doc)
            else:
                bot.send_document(message.chat.id, 'There no compared files')
        except Exception as e:
            bot.send_message(message.chat.id, "Can\'t send compared files")
            logging.error('{}\tCan\'t send compared files: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))


    if 'getscraped' in message.text:
        try:
            _path = os.getcwd()
            _files = [i for i in filter(lambda x: x.endswith('.csv'), os.listdir(_path))]
            _unnecessary = ['options.csv', 'iteminfo.csv']
            _filteredfiles = filterfiles(_files, _unnecessary)
            _markfiles = ', '.join(_filteredfiles)
            bot.reply_to(message, 'Send files: {}'.format(_markfiles))

            if len(_filteredfiles) != 0:
                _filteredfiles = [os.path.join(_path, i) for i in _filteredfiles]
                for file_path in _filteredfiles:
                    doc = open(file_path, 'rb')
                    bot.send_document(message.chat.id, doc)
            else:
                bot.send_document(message.chat.id, 'There no scraped files')
        except Exception as e:
            bot.send_message(message.chat.id, "Can\'t send scraped files")
            logging.error('{}\tCan\'t send scraped files: {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))


    if 'getlast' in message.text:
        try:
            _path = os.getcwd()
            _data_path = os.path.join(_path, 'scraped_files')
            _files = [os.path.join(_data_path, i) for i in filter(lambda x: x.endswith('.csv'), os.listdir(_data_path))]
            _newest = sorted(_files, key=lambda x: os.path.getmtime(x))[-1]
            doc = open(_newest, 'rb')
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
                _allkeys = list(json_mon["list_currency"].keys())
                _allkeys = ', '.join(_allkeys)
                if value not in _allkeys:
                    bot.reply_to(message, 'There is no supported currency: {}\n\nAll supported currencies:\n\n{}\n'.format(value, _allkeys))
                    return
                convert_value_item = json_mon["list_currency"][value]["value"]
                return str(round(float(convert_value_item), 2)), time_point
            except Exception as e:
                print('Alert: can\'t get exchange rate by get method')
                logging.info('{}\tCan\'t get exchange rate from cs.money source distanation: {}'.format(
                    dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e))
                return

        _evalue = ''
        _search_value_pattern = r'\w+'
        _searched = re.findall(_search_value_pattern, message.text)

        try:
            if _searched is not None:
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
            try:
                _rate, _time = get_rate(_evalue)
            # finally if cannot scrape currency function will be return None -> NoneType
            except TypeError:
                return
            _rate_course = 'Current ' + _mvalue + ' to ' +  _evalue + ' rate at ' + _time + ' is: ' + _rate
            bot.send_message(message.chat.id, _rate_course)
            store_to_db(data = _rate_course)
        except Exception as e:
            bot.send_message(message.chat.id, 'Currency was typed: {}'.format(_evalue))
            bot.send_message(message.chat.id,
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
