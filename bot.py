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

API_TOKEN = ''

bot = telebot.TeleBot(API_TOKEN)
#telebot.logger.setLevel(logging.DEBUG)

logging.basicConfig(filename='logging_data.log', level=logging.DEBUG)


@bot.message_handler(commands=['help', 'get_last', 'rate', 'get_data'])
def handle_main(message):

    if 'help' in message.text:
        _help_text = u"type:\n\
        - rate: get csmoney USD-RUB course\n\
        - get_last: get last scraped final table\n \
        - get_data: start scraping all data\n\
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
        _time = dt.datetime.now().strftime("%H:%M:%S")

        def get_rate(value="RUB"):
            try:
                money_url = 'https://cs.money/get_info?hash='
                scraper = cfscrape.create_scraper(delay=15)
                webpage = scraper.get(money_url).content
                json_mon = json.loads(webpage)
                convert_value_item = float(json_mon["list_currency"][value]["value"])
                return convert_value_item
            except:
                print('Alert: can\'t get exchange rate by get method')
                logging.info('{}\tCan\'t get exchange rate from cs.money source distanation'.format(
                    dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                return

        try:
            #TODO
            #add rate by stdcin user cmd
            _rate = get_rate("RUB")
            _rate_course = 'Course at ' + _time + ' is: ' + str(_rate)
            bot.send_message(message.chat.id, _rate_course)
        except:
            bot.send_message(message.chat.id, \
                             "Error while getting exchange rate.\nPlease report about this issue to:\nhttps://github.com/NuclearRazor/csgo_scraper/issues")

    if 'get_data' in message.text:
        ###DEBUG METHOD START
        #TODO
        #ERRORS HANDLER
        import scraper as pr
        print('GET DATA CMD OK')
        _parser = pr.createWidget()
        _fp = _parser.getFilePath()
        doc = open(_fp, 'rb')
        print('fp = {}'.format(_fp))
        bot.send_document(message.chat.id, doc)
        ###DEBUG METHOD END
        ###NO TRY/EXCEPT STATEMENT


class BotUI():

    def __init__(self):
        super().__init__()
        self.initReTU()


    def initReTU(self):
        bot.polling(True)
        while True:
            time.sleep(3)


if __name__ == '__main__':
    try:
        app = BotUI()
    except KeyboardInterrupt:
        print >> sys.stderr, '\nExiting by user request.\n'
        sys.exit(0)
