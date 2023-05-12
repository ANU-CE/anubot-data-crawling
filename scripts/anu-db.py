import requests
import datetime
from bs4 import BeautifulSoup
import pandas as pd
import pyodbc
import sqlalchemy
import urllib

url = 'https://dbmap.andong.ac.kr/bbs/room_list.php'
response = requests.get(url)

if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

linkarr = []
roomarr = []
cnt=1
while True:
    a = soup.select_one(f'#thema_wrapper > div.at-container > div > ul.list_style.list > li:nth-child({cnt}) > a')
    cnt+=1
    if a == None:
        break
    linkarr.append(a["href"])

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
    
    info = 'asd'
    tmpcnt = 1

    while True:
        try:
            info = soup.select_one(f'#tab1 > div:nth-child(4) > ul > li:nth-child({tmpcnt})')
            info = info.text
            tmparr.append(info)
            tmpcnt+=1
        except:
            break

    try:    
        description = soup.select('#tab1 > div:nth-child(6) > p')
        description = description.text
    except:
        description = ''
    tmparr.append(description)
    cnt+=1
    roomarr.append(tmparr)

print(roomarr)

df = pd.DataFrame(roomarr, columns=['id', 'region', 'roomname', 'price', 'info'])
df.to_csv('anu-db.csv', index=False, encoding='utf-8-sig')