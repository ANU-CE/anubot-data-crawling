import requests
import datetime
from bs4 import BeautifulSoup
import pandas as pd
import pyodbc
import sqlalchemy
import urllib
import numpy as np
import uuid

#for vector database   
import torch

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

from tqdm import tqdm

#for Dev
from dotenv import load_dotenv
import os

load_dotenv(verbose=True)
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_DATABASE = os.getenv('DB_DATABASE')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL')
QDRANT_PORT = os.getenv('QDRANT_PORT')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')

model = SentenceTransformer(
    'jhgan/ko-sroberta-multitask',
    device="cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu",
)

def getData(linkarr):
    fullarr = []
    cnt=0
    for link in tqdm(linkarr):
        #print(link)
        response = requests.get(link)
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
        tmparr = []
        id = linkarr[cnt].split('id=')[1]
        #tmparr.append(id)

        try:
            roomname = soup.select_one('#thema_wrapper > div.at-container > div > div > div > div.item_view_box > div.item_info > div.item_title')
            roomname = roomname.text
            #region = roomname.split(' ')[0]
            #roomname = roomname.split(' ')[1]
        except:
            #region = ''
            roomname = ''
        #tmparr.append(region)
        tmparr.append(roomname)

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
                #tmparr.append(info)
                allinfo += info
                allinfo += '\n'
                tmpcnt+=1
            except:
                break
            '''
        if tmpcnt < 9:
            for i in range(tmpcnt, 9):
                tmparr.append('')'''
        try:    
            description = soup.select('#tab1 > div:nth-child(6)')
            description = description.text
        except:
            description = ''
        allinfo += description
        allinfo += '\n'
        tmparr.append(allinfo)
        cnt+=1
        fullarr.append(tmparr)
    return fullarr

def exportData(dbname, fullarr):
    #df = pd.DataFrame(fullarr, columns=['id', 'region', 'name', 'desc', 'info0', 'info1', 'info2', 'info3', 'info4', 'info5', 'info6', 'info7', 'info8'])
    df = pd.DataFrame(fullarr, columns=['name', 'info'])
    df.to_csv(f'{dbname}.csv', index=False, encoding='utf-8-sig')
    '''# MSSQL DB에 업로드
    params = urllib.parse.quote_plus("DRIVER={ODBC Driver 17 for SQL Server};SERVER="+DB_HOST+","+DB_PORT+";DATABASE="+DB_DATABASE+";UID="+DB_USERNAME+";PWD="+DB_PASSWORD)
    engine = sqlalchemy.create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)
    conn = engine.connect()
    df.to_sql(dbname, con=engine, if_exists='replace', index=False)
    conn.close()'''
    print(f'{dbname} export complete')
    return df

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

def vectorize(df, COLLECTION_NAME):
    client = QdrantClient(
        url=QDRANT_URL,
        port=6333, 
        api_key=QDRANT_API_KEY
    )

    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=768, 
            distance=models.Distance.COSINE
        ),
    )
    vectors = []
    batch_size = 512
    batch = []

    for doc in tqdm(df["info"].to_list()):
        batch.append(doc)
        
        if len(batch) >= batch_size:
            vectors.append(model.encode(batch))
            batch = []

    if len(batch) > 0:
        vectors.append(model.encode(batch))
        batch = []
        
    vectors = np.concatenate(vectors)

    place_name = df["name"]

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=models.Batch(
            ids=[i for i in range(df.shape[0])],
            payloads=[
                {
                    "text": row["info"],
                    "name": row["name"] + f", {place_name}",
                }
                for _, row in df.iterrows()
            ],
            vectors=[v.tolist() for v in vectors],
        ),
    )

    #print(client.count(collection_name=COLLECTION_NAME))
    #print(client.get_collections())


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
df = exportData('anubot-dbmap-room', fullarr)
vectorize(df, 'anubot-dbmap-room')


restaruantlink = 'https://dbmap.andong.ac.kr/bbs/restaurant_list.php'
linkarr = getLinkArr(restaruantlink)
fullarr = getData(linkarr)
df = exportData('anubot-dbmap-restaurant', fullarr)
vectorize(df, 'anubot-dbmap-restaurant')

tourlink = 'https://dbmap.andong.ac.kr/bbs/tour_list.php'
linkarr = getLinkArr(tourlink)
fullarr = getData(linkarr)
df = exportData('anubot-dbmap-tour', fullarr)
vectorize(df, 'anubot-dbmap-tour')
