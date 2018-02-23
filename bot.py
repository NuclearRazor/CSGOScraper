# -*- coding: utf-8 -*-
import telebot
import time
import sys
import logging
import os
import parser as pr
import datetime as dt
import cfscrape
import json

API_TOKEN = ''

bot = telebot.TeleBot(API_TOKEN)
#telebot.logger.setLevel(logging.DEBUG)


class BotUI():

    def __init__(self):
        super().__init__()
        self.initReTU()


    def initReTU(self):

        bot.polling(True)
        while True:
            time.sleep(3)


    @bot.message_handler(commands=['help', 'get_final', 'rate'])
    def handle_main(message):
        if 'help' in message.text:
            _help_text = u"type:\n\
            - rate: get csmoney USD-RUB course\n\
            - get_final: get final table\n"
            bot.send_message(message.chat.id, _help_text)
        if 'get_final' in message.text:
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
        if 'rate' in message.text:
            _time = dt.datetime.now().strftime("%H:%M:%S")

            def get_rate(self, value = "RUB"):
                money_url = 'https://cs.money/get_info?hash='
                scraper = cfscrape.create_scraper()
                webpage = scraper.get(money_url).content
                json_mon = json.loads(webpage)
                convert_value_item = float(json_mon["list_currency"][value]["value"])
                return convert_value_item

            _rate = get_rate("RUB")

            _rate_course = 'Course at ' + _time + ' is: ' + str(_rate)

            bot.send_message(message.chat.id, _rate_course)


if __name__ == '__main__':
    try:
        BotUI()
    except KeyboardInterrupt:
        print >> sys.stderr, '\nExiting by user request.\n'
        sys.exit(0)
