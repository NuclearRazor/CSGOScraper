# -*- coding: utf-8 -*-
import os
import pandas as pd

pd.options.mode.chained_assignment = None

instance = None


class MetaConfig():

    def __init__(self):
        super().__init__()

        self.initReTU()


    def initReTU(self):
        self.check_file_exist('coefficients.txt')

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
        file_path = directory + '\\' + filename
        if os.path.isfile(file_path) == False:
            print('Cannot find file: ', filename)
            return False
        else:
            return True

# return instance of MetaConfig class
def createWidget():
    global instance
    if instance != None:
         return None   
    instance = MetaConfig()
    return instance