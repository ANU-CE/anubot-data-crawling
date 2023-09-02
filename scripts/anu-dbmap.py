import requests
from datetime import datetime, timezone
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

def getData(linkarr):
    fullarr = []
    cnt=0
    for link in tqdm(linkarr):
        response = requests.get(link)
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
        tmp = ''
        id = linkarr[cnt].split('id=')[1]

        try:
            roomname = soup.select_one('#thema_wrapper > div.at-container > div > div > div > div.item_view_box > div.item_info > div.item_title')
            roomname = roomname.text
        except:
            roomname = ''
        tmp = roomname + '의 정보는 다음과 같습니다.'

        allinfo = ''
        try:
            price = soup.select_one('#thema_wrapper > div.at-container > div > div > div > div.item_view_box > div.item_info > div.item_desc')
            price = price.text
        except:
            price = ''
        allinfo += price
        allinfo += '\n'
        
        tmpcnt = 1

        while True:
            try:
                info = soup.select_one(f'#tab1 > div:nth-child(3) > ul > li:nth-child({tmpcnt})').text
                allinfo += info
                allinfo += '\n'
                tmpcnt+=1
            except:
                break
        try:    
            description = soup.select('#tab1 > div:nth-child(6)')
            description = description.text
        except:
            description = ''
        allinfo += description
        allinfo += '\n'
        tmp += allinfo
        cnt+=1
        fullarr.append(tmp)
    return fullarr


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

def recreateCollection(COLLECTION_NAME):
    client = QdrantClient(
        url=QDRANT_URL,
        port=6330, 
        #api_key=QDRANT_API_KEY
    )
    
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )

def vectorize(fullarr, COLLECTION_NAME):
    client = QdrantClient(
        url=QDRANT_URL,
        port=6330, 
        #api_key=QDRANT_API_KEY
    )

   
    points = list()
    for text in tqdm(fullarr): 
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

    #pprint(client.get_collections().collections) 


'''
response = requests.get('https://dbmap.andong.ac.kr/bbs/room_view.php?id=270')
if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
info = soup.select_one('#tab1 > div:nth-child(3) > ul > li:nth-child(1)').text
print(info)
'''

recreateCollection('anubot-unified')

roomlink = 'https://dbmap.andong.ac.kr/bbs/room_list.php'
linkarr = getLinkArr(roomlink)
fullarr = getData(linkarr)
vectorize(fullarr, 'anubot-unified')


restaruantlink = 'https://dbmap.andong.ac.kr/bbs/restaurant_list.php'
linkarr = getLinkArr(restaruantlink)
fullarr = getData(linkarr)
vectorize(fullarr, 'anubot-unified')

tourlink = 'https://dbmap.andong.ac.kr/bbs/tour_list.php'
linkarr = getLinkArr(tourlink)
fullarr = getData(linkarr)
vectorize(fullarr, 'anubot-unified')
