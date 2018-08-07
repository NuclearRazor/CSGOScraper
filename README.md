## CSGO SCRAPER

This scraper get data from the next sites and compare item prices for the best profit:

- csgotm
- csgosell
- csmoney
- skinsjar
- opskins

**options.ini** allows you to edit eny scraping parameter.
The price of goods is indicated in **rubles**

##  **Dependencies:**

- pyTelegramBotAPI (if you want to use Telegram bot)
- cfscrape
- requests
- selenium
- pandas
- lxml

*Project includes Dockerfile and requirements.txt

##  **Usage:**

Software was tested on Windows 8.1, x64, i486, MSC v.1900 (AMD 64).

1. Install Anaconda python from original website, minimum version is:
	-	Anaconda 4.4.0 (64-bit) 
    
2. Install all dependencies
    
3. _Start scraping_ items by following command in your terminal:
	-	python scraper.py
    
    3.1 Or you can use your _telegram bot_ instance and make all through it:
    	-	python bot.py
    
4. Open .csv files in folder 'scraped_files' for analytical usage or use your telegram bot instance

## **Advantages**

1. All evaluations take amount of ~ 3 - 10 minutes (a lot of scrapers with payment pass it in 10 - 50 minutes):

2. Result table include URL links to each good item on opskins market

3. You can take a control on market and exchanges commission and its scraping options in options.ini

4. You can get item info in final table by /getitem NAME bot command

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

### The table data correspond to a small sample of 10 tests:

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

## Bot usage

(*) To use bot please make your own API Telegram token

(**) type /help to get this list of commands in your bot dialog

**Supported commands:**

**/rate** CUR: get csmoney exchange rate for typed currency (RUB as default)

**/getlast**: get last compared final table

**/getdata**: start scraping all data (it will return resul table)

**/getscraped**: get all scraped tables for shops and exchangers

**/getcompared**: get all compared tables for shops and exchangers

**/setconfig** KEY VALUE: set options to scraper, keys must be named as is

**/getconfig**: get options table for scraping

**/getitem** NAME: get info in last final table for entered item name

**/template** each command on newline: bot will handle all your listed commands (that are supported)

## **License**

MIT

##  **For informational purposes only**
