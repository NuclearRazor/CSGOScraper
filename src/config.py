# -*- coding: utf-8 -*-
import os
import pandas as pd
import io
import json

pd.options.mode.chained_assignment = None

instance = None


class MetaConfig():

    def __init__(self):
        super().__init__()
        self.initReTU()


    def initReTU(self):
        self.check_file_exist('options.ini')


    # parse all configurations from json stored into yours option's file
    # defalut filename: options.ini
    def parse_options(self):
        _file_dump = ''
        with io.open('options.ini', encoding='utf-8', errors='ignore') as f:
            _file_dump = json.load(f)

        _comission_list = [str(i) for i in _file_dump["comission"].values()]
        return _file_dump["scraping_config"], _comission_list, _file_dump["analyze_config"]


    # save parsed data to dataframe
    def save_data(self, file_headers, data, mag_fixed_price, mag_name):

        df = pd.DataFrame(list(map(list, zip(data['rows_num'], \
            data['names'], mag_fixed_price, data['qualities']))), columns = file_headers)

        file_name = mag_name + '.csv'
        df.to_csv(file_name, index=False)


    # evaluate prices in list
    def evaluate_price(self, prices_data, comission, cource_value):
        fixed_price = [round((float(p_item)*(1.0+comission))*cource_value, 2) for p_item in prices_data]
        return fixed_price


    # evaluate price value while scrape opskins items
    def evaluate_opskins_price(self, price_element, comission, cource_value):
        fixed_price = round((float(price_element)*(1.0+comission))*cource_value, 2)
        return fixed_price


    # check file coefficients.txt
    def check_file_exist(self, filename):
        directory = os.getcwd()
        file_path = os.path.join(directory, filename)

        if os.path.isfile(file_path):
            return True
        else:
            print('Cannot find file: ', filename)
            return False


# return instance of MetaConfig class
def createWidget():
    global instance
    if instance is not None:
        del instance
        return MetaConfig()   
    instance = MetaConfig()
    return instance