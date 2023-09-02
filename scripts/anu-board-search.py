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
        try:
            title = soup_board.select_one('#body_content > div.board_view > div.title')
            title = title.text
        except:
            title = ''
        tmp = title + '에 대한 정보는 다음과 같습니다. '
        try:
            info = soup_board.select_one('#body_content > div.board_view > div.cont')
            info = info.text + '링크 : ' + boardurl
        except:
            info = '' 
        tmp += info
        pageArr.append(tmp)

    return pageArr

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

pagearr = []

for i in tqdm(range(1, 16, 1)):
    url = f'https://www.anu.ac.kr/main/board/index.do?menu_idx=333&manage_idx=1&board_idx=0&old_menu_idx=0&old_manage_idx=0&old_board_idx=0&group_depth=0&parent_idx=0&group_idx=0&search.category1=107&rowCount=10&viewPage={i}'
    pagearr = getData(pagearr, url)

vectorize_by_arr(pagearr, 'anubot-unified')