# -*- coding: utf-8 -*-
import os
import pandas as pd
import io
import re

pd.options.mode.chained_assignment = None

instance = None


class MetaConfig():

    def __init__(self):
        super().__init__()

        self.initReTU()


    def initReTU(self):
        self.check_file_exist('coefficients.txt')


    def get_comission(self):
        num_pattern = r'\d+'
        num_coeff = []
        find_num = ''

        with io.open('coefficients.txt', encoding='utf-8', errors='ignore') as f:
            find_num = [re.findall(num_pattern, str(line)) for line in f]
            [num_coeff.append(self.convert_to_str(item)) for item in find_num]

        return num_coeff


    # save parsed data to dataframe
    def save_data(self, file_headers, data, mag_fixed_price, mag_name):

        df = pd.DataFrame(list(map(list, zip(data['rows_num'], \
            data['names'], mag_fixed_price, data['qualitys']))), columns = file_headers)

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
    if instance != None:
         return None   
    instance = MetaConfig()
    return instance