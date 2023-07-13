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


def exportData(dbname, fullarr):
    df = pd.DataFrame(fullarr, columns=['name', 'info'])
    #df.to_csv(f'{dbname}.csv', index=False, encoding='utf-8-sig')
    print(f'{dbname} export complete')
    return df

def getData(pageArr, url):

    response = requests.get(url)

    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

    for cnt in range(1,11,1):
        boardindex = soup.select_one(f'#board > div.board_list > table > tbody > tr:nth-child({cnt}) > td:nth-child(2) > a')
        boardindex = boardindex["onclick"][10:-2]
        boardurl = f'https://www.anu.ac.kr/main/board/view.do?menu_idx=333&manage_idx=1&board_idx={boardindex}&old_menu_idx=0&old_manage_idx=0&old_board_idx=0&group_depth=0&parent_idx=0&group_idx=0&search.category1=107'
        if boardurl == None:
            break
        response_board = requests.get(boardurl)
        if response_board.status_code == 200:
            html_board = response_board.text
            soup_board = BeautifulSoup(html_board, 'html.parser')
        tmparr = []
        try:
            title = soup_board.select_one('#body_content > div.board_view > div.title')
            title = title.text
        except:
            title = ''
        tmparr.append(title)
        try:
            info = soup_board.select_one('#body_content > div.board_view > div.cont')
            info = info.text + '링크 : ' + boardurl
        except:
            info = '' 
        tmparr.append(info)
        pageArr.append(tmparr)

    return pageArr

def vectorize(df, COLLECTION_NAME):
    client = QdrantClient(
        url=QDRANT_URL,
        port=QDRANT_PORT, 
        #api_key=QDRANT_API_KEY
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
                    "name": row["name"],
                }
                for _, row in df.iterrows()
            ],
            vectors=[v.tolist() for v in vectors],
        ),
    )

    #print(client.count(collection_name=COLLECTION_NAME))
    #print(client.get_collections())


'''
response = requests.get('https://www.anu.ac.kr/main/board/index.do?menu_idx=333&manage_idx=1&board_idx=0&old_menu_idx=0&old_manage_idx=0&old_board_idx=0&group_depth=0&parent_idx=0&group_idx=0&search.category1=107&rowCount=10&viewPage=1')
if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
info = soup.select_one('#board > div.board_list > table > tbody > tr:nth-child(1) > td:nth-child(2) > a')
print(info["onclick"][10:-2])
'''

pagearr = []

for i in tqdm(range(1, 16, 1)):
    url = f'https://www.anu.ac.kr/main/board/index.do?menu_idx=333&manage_idx=1&board_idx=0&old_menu_idx=0&old_manage_idx=0&old_board_idx=0&group_depth=0&parent_idx=0&group_idx=0&search.category1=107&rowCount=10&viewPage={i}'
    pagearr = getData(pagearr, url)

df = exportData('anubot-board-janghak', pagearr)
vectorize(df, 'anubot-unified')