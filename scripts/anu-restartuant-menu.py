import requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
import pandas as pd
import urllib
import numpy as np

from uuid import uuid4
from pprint import pprint

#for vector database   
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

from tqdm import tqdm

import openai

#for Dev
from dotenv import load_dotenv
import os

load_dotenv(verbose=True)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL')
QDRANT_PORT = os.getenv('QDRANT_PORT')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')

EMBEDDING_MODEL = 'text-embedding-ada-002'
EMBEDDING_CTX_LENGTH = 8191
EMBEDDING_ENCODING = 'cl100k_base'

openai.api_key = OPENAI_API_KEY

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

startdate = datetime.strptime(startdate, '%Y/%m/%d')
nowdate = startdate

for i in range(0, 7, 1):
    nowdate = startdate + timedelta(days=i)
    nowdate = nowdate.strftime('%Y/%m/%d')
    dorm_menu_arr[i][0] = nowdate
    dorm_menu_arr[i][1] = yoil_text[i]
    dorm_menu_arr[i][2] = soup.findAll('table')[1].findAll('tr')[i*3].text.replace("아침","").replace(" ",", ").replace("\n",", ").replace("\r","").replace(f'{yoil_text[i]}','')
    dorm_menu_arr[i][3] = soup.findAll('table')[1].findAll('tr')[i*3+1].text.replace("점심","").replace(" ",", ").replace("\n",", ").replace("\r","")
    dorm_menu_arr[i][4] = soup.findAll('table')[1].findAll('tr')[i*3+2].text.replace("저녁","").replace(" ",", ").replace("\n",", ").replace("\r","")

arr = []
arr += [(elem[0], elem[1], elem[2]) for elem in dorm_menu_arr]
arr += [(elem[0], elem[1], elem[3]) for elem in dorm_menu_arr]
arr += [(elem[0], elem[1], elem[4]) for elem in dorm_menu_arr]

pprint(arr)
