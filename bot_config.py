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


def make_echo_by_cmd(usr_cmd = None, usr_text = None):
    # получить апдейт
    # загрузить в json: "id", "text"
    # если text = переданная в функцию команда usr_var
    # то отправить сообщение ИЛИ вызвать нужный метод

    while True:
        _json_schema = json.loads(make_request('getupdates'))

        # -1 - ключ на последний апдейт
        if _json_schema["ok"]:
            _usr_id = _json_schema["result"][-1]["message"]["from"]["id"]
            _usr_text = _json_schema["result"][-1]["message"]["text"]
            _usr_name = _json_schema["result"][-1]["message"]["from"]["first_name"]
            print('schema id: {}'.format(_usr_id))
            print('schema text: {}'.format(_usr_text))

            if _usr_text == usr_cmd:
                _send_text = u'Слышь ты че\b' + _usr_name + '\bпопутал?'
                make_request('sendmessage?chat_id={}&text={}!'.format(_usr_id, _send_text))
            elif _usr_text != usr_cmd:
                pass


if __name__ == "__main__":

    # print('Test request getMe: {}'.format(make_request()))
    # #getUdates - некий лог связанный с запросами пользователя
    # print('Test request getupdates: {}'.format(make_request('getupdates')))

    make_echo_by_cmd('Hello')