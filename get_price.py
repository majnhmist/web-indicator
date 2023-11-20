import ast
import asyncio
import logging
import os
from datetime import date

import aiohttp
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

start_date = '2000-01-01'
today = date.today().strftime("%Y-%m-%d")
########### FOR LOGGING ##############
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s","%d-%m-%y %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)
############GET COMPANY#####################



def get_all_com_token(cookies, headers):
    '''
    Get token session to make request to api
    '''
    sess = requests.Session()
    url = 'https://finance.vietstock.vn/doanh-nghiep-a-z?page=1'
    r= sess.get(url,headers=headers, cookies=cookies)
    soup = BeautifulSoup(r.content, 'html5lib')
    token = soup.findAll('input', attrs={'name':'__RequestVerificationToken'})[0]['value']
    return token

def make_all_com_form(exchange,token, page):
    '''
    Make form to call to api
    '''
    catID = {'all': '0' ,'hose':'1','hnx':'2','upcom':'5'}
 
    f = {'catID': catID[exchange],
    'industryID': '0',
    'page':str(page),
    'pageSize': '50',
    'code':'',
    'businessTypeID':'0',
    'orderBy': 'Code',
    'orderDir': 'ASC',
    '__RequestVerificationToken':token}
    return f

def get_all_com(exchange, cookies, headers):
    '''
    Return all companies on choosen exchange.
    
    '''
    url = 'https://finance.vietstock.vn/data/corporateaz'
    token = get_all_com_token(cookies,headers)
    page = 1
    result = []
    while True:
        f = make_all_com_form(exchange, token, page)
        r = requests.post(url, headers=headers,cookies=cookies,data=f)
        if len(r.json()) != 0:
            for com in r.json():
                result.append(com['Code'])
            page +=1
        else:
            break
    return result

##############GET PRICE#######################
def make_price_history_form(symbol, start, end):
    '''
    Making form to requests to market_price_url
    Paramaters
    ----------
    symbol: string, company symbol
    start: starting date
    end: ending date
    Retruns
    -------
    dict
    '''

    form = {'Code': symbol,
            'OrderBy': '',
            'OrderDirection': 'desc',
            'FromDate': start,
            'ToDate': end,
            'ExportType': 'excel',
            'Cols': 'MC,DC,CN,TN,GDC,TKLGD',
            'ExchangeID': 1}

    return form


def make_price_history_df(df):
    '''
    Formating price df 
    Paramaters
    ----------
    df: DataFrame, df reading from price_history_url
    Return
    ------
    DataFrame
    '''
    cols = ['Date', 'Volume', 'Open', 'Close', 'High',
           'Low', 'Adj Close']
    df.columns = cols
    # df = df.set_index('Date')
    df = df.reindex(['Date','High', 'Low', 'Open', 'Close', 'Volume',
                    'Adj Close',], axis='columns')
    df = df.reindex(index=df.index[::-1])
    df.reset_index(inplace=True, drop=True)
    df.fillna('-', inplace=True)
    return df
async def get_price_history(symbol,start,end):

    '''
    Take price history of specific company from start to end, coming with user cookies.
    Paramaters
    ----------
    symbol: string, company symbol, etc. 'fts', 'hpg'...
    start: string, starting date
    end: string, ending date
    cookies: dict, user cookies
    
    Return
    ------
    DataFrame
    '''
    url = 'https://finance.vietstock.vn/data/ExportTradingResult'
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.40'}
    form = make_price_history_form(symbol,start,end)
    async with aiohttp.ClientSession(trust_env = True) as session:
        async with session.get(url, headers=headers, data=form) as response:
            html = await response.text()
            df = pd.read_html(html)[1]
            result = make_price_history_df(df)    
    return result
async def get_price(exchange, com_list):
    '''
    Async requests to data source to upload to Github, return dict of DataFrame
    to use in gsheet requests
    '''
    df_dict = {}
    semaphore = asyncio.Semaphore(10)
    async def single_file(com):
        async with semaphore:
            logger.info(f'{com, exchange} DONE!')
            result = await get_price_history(com,start_date,today)
            result.to_csv(f'datas/{exchange}/{com}.csv')
            df_dict[com] = result

    coros = [single_file(com) for com in com_list]
    await asyncio.gather(*coros)
    return df_dict

def write_com(exchange,coms):
    with open(f'datas/{exchange}/com.txt', 'w') as f:
        for com in coms:
            f.write(com+',')
        f.close()


if __name__ == '__main__':

    cookie = {
        "language":"vi-VN", 
        "ASP.NET_SessionId":"irwbawc01arxrqnwjawnt2ny",
        "__RequestVerificationToken":"-1wS5MkrfH2wuqY7Jrt1VLsr8Nn-FdkOhLImvQyMI4Ki-V96gdlOooYAWeTJeb_HjRkxn-ipAhGTcIxYzNCzh6hUjj3qYZYAHdXyzQ_Onsw1",
        "__gpi":"UID=00000c7fd68b69ce:T=1699113940:RT=1699113940:S=ALNI_MZot-xbO_hbI3c0lDHfCHpg_pmFXQ",
        "Theme":"Light",
        "_gid":"GA1.2.2137659733.1699113966",
        "_pbjs_userid_consent_data":"3524755945110770",
        "__gads":"ID=cbd5046df6d12da3-22b393db6ae500f2:T=1699113940:RT=1699113966:S=ALNI_Mbm4iqKjvpnfY5HBiSfDYFmAaUOWQ",
        "isShowLogin":"true",
        "dable_uid":"undefined", 
        "AnonymousNotification":"",
        "vts_usr_lg":"D0AD1000AE8089BE9843DE460B20402C37AA63643654F5F4B57338C3480C4A3DEEDA2E054E01C8E78508205E3C858469457518D2ACC6A13B43AD8C8100CB85197642D9E95A944A00D03B0B6010C38EE6141142997664E52B04359AB444DD74BEA7CA14085E7947E59F215A5C745DC533D136FBF011B62119C63F8F9CDD1A9042",
        "vst_usr_lg_token":"8g1FyO+ulU+Oe7fHi9mDdw==",
        "_ga":"GA1.2.1833551307.1699113939",
        "_ga_EXMM0DKVEX":"GS1.1.1699113938.1.1.1699114059.7.0.0",
        "cto_bundle":"0NU8ZF9JWm43TTQ4M1Bic202aW83JTJCb2Vic3pvYk9qdk10R0VkdEYyWmFNc2x6REJaMzQlMkZyVktpN1YxWExITFJRRnVmbmg4OHBkcFMySmxBZXo3UkJjREpGMDVlWDJjTG8lMkI4YldRbjhIRmUlMkJ2N01aeVZZV0tzYVlIM3AlMkI2NDl5OFZGemJBMVc2N0wlMkIzY1dMQUlmZFpyZWt2YTRUT0ZkMHZJM0NBaEpVaXlLUyUyRnhLbyUzRA",
        "cto_bidid":"kVnBhF9ZRVNsJTJGJTJCRXJydjkzVlZqS3F3UjBGRjhTamZjVFQ1SkFNYUJMY3UlMkZwWHlIUmFJdFRqbGxjVFNjSWx2SzR1cWM1ZlhvNU9FNjY0UzhtS3Z0TGFuaWhXa3BOazJsNWYlMkJQMVltR3NjMXVJelVrJTNE"
    }
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.40'}
    
    
    hose_com = get_all_com('hose', cookie, header)
    logger.info('Load all com hose')
    hnx_com = get_all_com('hnx',cookie,header)
    logger.info('Load all com hnx')
    upcom_com = get_all_com('upcom',cookie, header)
    logger.info('Load all com upcom')


    write_com('hose',hose_com)
    write_com('hnx',hnx_com)
    write_com('upcom',upcom_com)


   
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_price('hose',hose_com))
    loop.run_until_complete(get_price('hnx',hnx_com))
    loop.run_until_complete(get_price('upcom',upcom_com))
