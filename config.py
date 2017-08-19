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


    def save_data(self, file_headers, data, mag_fixed_price, mag_name):

        df = pd.DataFrame(list(map(list, zip(data['rows_num'], \
            data['names'], mag_fixed_price, data['qualitys']))), columns = file_headers)

        file_name = mag_name + '.csv'

        df.to_csv(file_name, index=False)


    def evaluate_price(self, prices_data, comission, cource_value):

        fixed_price = []

        for price_element in prices_data:
            price_value = float(price_element)*(1+comission)*cource_value
            price_value = round(price_value, 2)
            fixed_price.append(price_value)

        return fixed_price


    def check_file_exist(self, filename):
        directory = os.getcwd()

        file_path = directory + '\\' + filename

        if os.path.isfile(file_path) == False:
            print('Cannot find file: ', filename)
            return False
        else:
            return True

def createWidget():
    global instance
    if instance != None:
         return None   
    instance = MetaConfig()
    return instance