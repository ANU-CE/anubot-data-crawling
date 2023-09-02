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

def vectorize_by_arr(arr, COLLECTION_NAME):
    client = QdrantClient(
        url=QDRANT_URL,
        port=6330, 
        #api_key=QDRANT_API_KEY
    )

    points = list()
    for text in tqdm(arr): 
        embedding = openai.Embedding.create(input=text, model=EMBEDDING_MODEL)["data"][0]["embedding"]
        point = PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                "plain_text": text,
                "created_datetime": datetime.now(timezone.utc).isoformat(timespec='seconds'),
            }
        )
        points.append(point)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

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

arr = []


for i in range(0, 7, 1):
    nowdate = startdate + timedelta(days=i)
    nowdate = nowdate.strftime('%Y/%m/%d')
    dorm_menu_arr[i][0] = nowdate
    dorm_menu_arr[i][1] = yoil_text[i]
    dorm_menu_arr[i][2] = soup.findAll('table')[1].findAll('tr')[i*3].text.replace("아침","").replace("\n",", ").replace("  "," ").replace("\r","").replace(f'{yoil_text[i]}','')
    dorm_menu_arr[i][3] = soup.findAll('table')[1].findAll('tr')[i*3+1].text.replace("점심","").replace("\n",", ").replace("\r","")
    dorm_menu_arr[i][4] = soup.findAll('table')[1].findAll('tr')[i*3+2].text.replace("저녁","").replace("\n",", ").replace("\r","")
    if len(dorm_menu_arr[i][2]) >= 10:
        string = f'{dorm_menu_arr[i][0]} {dorm_menu_arr[i][1]}의 기숙사 아침메뉴는 {dorm_menu_arr[i][2]} 입니다.'
        arr.append(string)
    else:
        string = f'{dorm_menu_arr[i][0]} {dorm_menu_arr[i][1]}의 기숙사 아침메뉴는 제공되지 않거나 확인되지 않았습니다.'
        arr.append(string)

    if len(dorm_menu_arr[i][3]) >= 10:
        string = f'{dorm_menu_arr[i][0]} {dorm_menu_arr[i][1]}의 기숙사 점심메뉴는 {dorm_menu_arr[i][3]} 입니다.'
        arr.append(string)
    else:
        string = f'{dorm_menu_arr[i][0]} {dorm_menu_arr[i][1]}의 기숙사 점심메뉴는 제공되지 않거나 확인되지 않았습니다.'
        arr.append(string)

    if len(dorm_menu_arr[i][4]) >= 10:
        string = f'{dorm_menu_arr[i][0]} {dorm_menu_arr[i][1]}의 기숙사 저녁메뉴는 {dorm_menu_arr[i][4]} 입니다.'
        arr.append(string)
    else:
        string = f'{dorm_menu_arr[i][0]} {dorm_menu_arr[i][1]}의 기숙사 저녁메뉴는 제공되지 않거나 확인되지 않았습니다.'
        arr.append(string)
        
vectorize_by_arr(arr, 'anubot-unified')