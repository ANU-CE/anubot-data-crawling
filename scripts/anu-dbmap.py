import requests
import datetime
from bs4 import BeautifulSoup
import pandas as pd
import pyodbc
import sqlalchemy
import urllib

#for Dev
from dotenv import load_dotenv
import os

def getData(linkarr):
    fullarr = []
    cnt=0
    for link in linkarr:
        print(link)
        response = requests.get(link)
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
        tmparr = []
        id = linkarr[cnt].split('id=')[1]
        tmparr.append(id)

        try:
            roomname = soup.select_one('#thema_wrapper > div.at-container > div > div > div > div.item_view_box > div.item_info > div.item_title')
            roomname = roomname.text
            region = roomname.split(' ')[0]
            roomname = roomname.split(' ')[1]
        except:
            region = ''
            roomname = ''
        tmparr.append(region)
        tmparr.append(roomname)

        try:
            price = soup.select_one('#thema_wrapper > div.at-container > div > div > div > div.item_view_box > div.item_info > div.item_desc')
            price = price.text
        except:
            price = ''
        tmparr.append(price)
        
        tmpcnt = 1

        while True:
            try:
                info = soup.select_one(f'#tab1 > div:nth-child(3) > ul > li:nth-child({tmpcnt})').text
                tmparr.append(info)
                tmpcnt+=1
            except:
                break
        if tmpcnt < 9:
            for i in range(tmpcnt, 9):
                tmparr.append('')
        try:    
            description = soup.select('#tab1 > div:nth-child(6)')
            description = description.text
        except:
            description = ''
        tmparr.append(description)
        cnt+=1
        fullarr.append(tmparr)
    return fullarr

def exportData(dbname, fullarr):
    df = pd.DataFrame(fullarr, columns=['id', 'region', 'name', 'desc', 'info0', 'info1', 'info2', 'info3', 'info4', 'info5', 'info6', 'info7', 'info8'])
    df.to_csv(f'{dbname}.csv', index=False, encoding='utf-8-sig')
    # MSSQL DB에 업로드
    params = urllib.parse.quote_plus("DRIVER={ODBC Driver 17 for SQL Server};SERVER="+DB_HOST+","+DB_PORT+";DATABASE="+DB_DATABASE+";UID="+DB_USERNAME+";PWD="+DB_PASSWORD)
    engine = sqlalchemy.create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)
    conn = engine.connect()
    df.to_sql(dbname, con=engine, if_exists='replace', index=False)
    conn.close()

def getLinkArr(url):
    #url = 'https://dbmap.andong.ac.kr/bbs/room_list.php'
    response = requests.get(url)

    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

    linkarr = []
    cnt=1
    while True:
        a = soup.select_one(f'#thema_wrapper > div.at-container > div > ul.list_style.list > li:nth-child({cnt}) > a')
        cnt+=1
        if a == None:
            break
        linkarr.append(a["href"])
    return linkarr


load_dotenv(verbose=True)
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_DATABASE = os.getenv('DB_DATABASE')


'''
response = requests.get('https://dbmap.andong.ac.kr/bbs/room_view.php?id=270')
if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
info = soup.select_one('#tab1 > div:nth-child(3) > ul > li:nth-child(1)').text
print(info)


'''

roomlink = 'https://dbmap.andong.ac.kr/bbs/room_list.php'
linkarr = getLinkArr(roomlink)
fullarr = getData(linkarr)
exportData('anubot-dbmap-room', fullarr)

restaruantlink = 'https://dbmap.andong.ac.kr/bbs/restaurant_list.php'
linkarr = getLinkArr(restaruantlink)
fullarr = getData(linkarr)
exportData('anubot-dbmap-restaurant', fullarr)

tourlink = 'https://dbmap.andong.ac.kr/bbs/tour_list.php'
linkarr = getLinkArr(tourlink)
fullarr = getData(linkarr)
exportData('anubot-dbmap-tour', fullarr)

