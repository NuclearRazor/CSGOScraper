# -*- coding: utf-8 -*-
import requests
import json

BOT_TOKEN = 'token'

def make_request(schema = None, bot_token = None):
    get_str = ''
    if schema is not None: get_str = 'http://api.telegram.org/bot' + BOT_TOKEN + '/' + schema
    else:
        get_str = 'http://api.telegram.org/bot' + BOT_TOKEN + '/' + 'getMe'
    get_r = requests.get(get_str)
    if get_r.status_code == 200 and get_r is not None: return get_r.text
    else: return None


def echo_request(usr_cmd = None, usr_text = None):
    # получить апдейт
    # загрузить в json: "id", "text"
    # если text = переданная в функцию команда usr_var
    # то отправить сообщение ИЛИ вызвать нужный метод

    _json_schema = json.loads(make_request('getupdates'))

    # -1 - ключ на последний апдейт
    if _json_schema["ok"]:
        _usr_id = _json_schema["result"][-1]["message"]["from"]["id"]
        _usr_text = _json_schema["result"][-1]["message"]["text"]
        _usr_name = _json_schema["result"][-1]["message"]["from"]["first_name"]
        print('schema id: {}'.format(_usr_id))
        print('schema text: {}'.format(_usr_text))

        if _usr_text == usr_cmd:
            _send_text = u'Hello\b' + _usr_name + '!'
            make_request('sendmessage?chat_id={}&text={}!'.format(_usr_id, _send_text))
        elif _usr_text != usr_cmd:
            make_request('sendmessage?chat_id={}&text=Wrong request!'.format(_usr_id))


        # _hash_params = {'csgotm_data.csv': comission_list[0],\
        #                 'opskins_data.csv': _opskins_config,\
        #                 'csgosell_data.csv': comission_list[3],\
        #                 'csmoney_data.csv': comission_list[1],\
        #                 'skinsjar_data.csv': comission_list[2]\
        #                }
        #
        # # associate shops/exhangers names with referencies to methods
        # _hash_data = {'csgotm_data.csv': self.parse_csgotmmarket,\
        #               'opskins_data.csv': op.Opskins_Market,\
        #               'csgosell_data.csv': self.parse_csgosellmarket,\
        #               'csmoney_data.csv': self.parse_csmoneymarket,\
        #               'skinsjar_data.csv': self.parse_skinsjarmarket\
        #              }
        #
        # if _data["opskins_config"]:
        #     _data.pop('opskins_config', None)
        #     [[_hash_data[_item](_hash_params[_item]) for _item in _data[_key]] for _key in _data]

if __name__ == "__main__":

    # print('Test request getMe: {}'.format(make_request()))
    # #getUdates - некий лог связанный с запросами пользователя
    #print('Test request getupdates: {}'.format(make_request('getupdates')))

    #TODO 1
    #Все переменные вывести в файл options.ini +
    #Внутреннее представление - json
    #Инстанцировать в MetaConfig чтение/запись в config.ini

    #читать updates
    #если пришла корректная команда то ответить на нее 1 раз
    #иначе вывести сообщение об ошибке
    #изменить структуру данных в coefficients.txt на json и в config.py изменить парсер
    #составить полный каталог программ
    #реализовать и проверить get методы
    #реализовать и проверить set методы
    #добавить поиск профита только для X предмета

    echo_request('Hello')