## **csgo parser**

This parser get and compare data from the next sites:

- csgotm
- csgosell
- csmoney
- skinsjar
- opskins

_File **coefficients.txt** allows to edit sites comission.
The price of goods is indicated in **rubles**_

### **Usage**

Software was tested on Windows 8.1, x64, i486, MSC v.1900 (AMD 64).

1. Install Anaconda python from original website:
	-	Anaconda 4.4.0 (64-bit) 
    
2. Start scraping items by following command in your terminal:
	-	python parser.py
    
3. Open .csv files in folder 'scraped_files' for analytical usage

**Advantages**

1. Scrape and compare data take amount of 1 minute (a lot of scrapers with payment pass it in 10 - 50 minutes):

2. In result table you can see URL link's to each good item on opskins market

3. You can controll market and exchangers comission and it's scraping options in _parser.py_:

**shops**, **exchangers** - to determinate what kind of data you want to store, comparison occurs between every unique shop and all exhangers, like:

opskins <--> csgosell, opskins <--> skinsjar, opskins <--> csmoney, ..., etc

**scraping_config** - dict data type with opskins config dict, exchange rate for opskins is defined in main scope, but it converts to real value by csmoney usd/rub course. You can also change this logic.

**analyze_config** - dict data type in order to choose a price comparison range, sort the data and change the value of the maximum allowable profit (because there (on shops/exchangers may be boost items with artificially high prices that are much higher than the average for the current market).

**_Sort flags_** - sort_flag key in analyze_config:

1. sort by price relative to second store/exchanger by ascending order: 'priceASC'
2. sort by price relative to second store/exchanger by descending order: 'priceDESC'
3. sort by price and profit relative to second shop/exchanger in ascending order: 'profit_priceASC'
4. sort by price and profit relative to second shop/exchanger in descending order: default (without flag)

For p.1, main influence for time scraping is coming from **record_count** parameter for Opskins scraping if timeout values are constant.
The table data correspond to a small sample of 10 tests:

| Record count  | Average time | Min(timeout), const | Max(timeout), const |
| ------------- | ------------ | ------------------- | ------------------- |
| 100  			|	  01:09    |		  3          |         150         | 
| 200  			|	  01:35    |		  3          |         150         |
| 300  			|	  01:42    |		  3          |         150         |
| 400  			|	  01:54    |		  3          |         150         |
| 500  			|	  02:02    |		  3          |         150         |

Parameters for test:

shops = ['csgotm_data.csv', 'opskins_data.csv']

exchangers = ['csgosell_data.csv', 'csmoney_data.csv', 'skinsjar_data.csv']

scraping_config = {"shops": shops, "exchangers": exchangers, "opskins_config": {"comission": 1, "exchange_rate": 60, "record_count": 500, "mint": 3, "maxt": 150}}

analyze_config = {"shops": shops, "exchangers": exchangers, "overall_rate": 0, "min_price": 1, "max_price": 1000, "min_profit": 30, "max_profit": 150, "sort_flag": 'profit_priceDESC', "compare_equal": True, "bound_profit": 150}


**Coming feauture**

- search and parse info about item by name from steam-analyst - standalone module at now
- telegram bot for simple UI (API)

**License**

MIT

### **For informational purposes only**
