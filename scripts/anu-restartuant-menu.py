import requests
import datetime
from bs4 import BeautifulSoup
import pandas as pd
import pyodbc
import sqlalchemy
import urllib

# body > div.container.page-content > div.w3-responsive > table > tbody > tr:nth-child(1) > th:nth-child(1) 월요일
# body > div.container.page-content > div.w3-responsive > table > tbody > tr:nth-child(1) > th:nth-child(2) 아침
# body > div.container.page-content > div.w3-responsive > table > tbody > tr:nth-child(1) > td 메뉴~~~


url = 'https://dorm.andong.ac.kr/2019//food_menu/food_menu.htm'
response = requests.get(url)

if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

startday = 'body > div.container.page-content > b > span'
startday = soup.select_one(startday).text
startdate = startday.replace('월','/').replace('일','').replace(' ','').replace('년','/').replace('『','').split('~')[0]

dorm_menu_arr = [[0 for col in range(5)] for row in range(7)]
yoil_text = ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"]

startdate = datetime.datetime.strptime(startdate, '%Y/%m/%d')
nowdate = startdate

for i in range(0, 7, 1):
    nowdate = startdate + datetime.timedelta(days=i)
    nowdate = nowdate.strftime('%Y/%m/%d')
    dorm_menu_arr[i][0] = nowdate
    dorm_menu_arr[i][1] = yoil_text[i]
    dorm_menu_arr[i][2] = soup.findAll('table')[1].findAll('tr')[i*3].text.replace("아침","").replace(" ",", ").replace("\n",", ").replace("\r","").replace(f'{yoil_text[i]}','')
    dorm_menu_arr[i][3] = soup.findAll('table')[1].findAll('tr')[i*3+1].text.replace("점심","").replace(" ",", ").replace("\n",", ").replace("\r","")
    dorm_menu_arr[i][4] = soup.findAll('table')[1].findAll('tr')[i*3+2].text.replace("저녁","").replace(" ",", ").replace("\n",", ").replace("\r","")

df = pd.DataFrame(dorm_menu_arr, columns=['date', 'day', 'breakfast', 'lunch', 'dinner'])
df.to_csv('dorm_menu.csv', index=False, encoding='utf-8-sig')

#upload to mssql server


# MSSQL 접속


# DB 접속 엔진
engine = sqlalchemy.create_engine(f"mssql+pymssql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}?charset=utf8mb4",echo=True)

# DB 테이블에 데이터프레임 추가, 열 이름은 영어로
df.to_sql(name='data_dorm_menu', con=engine, if_exists='replace', index=False, index_label='date', method=None)


# MSSQL 접속 종료
engine.dispose()
