# Date. 2023-03-29
# Author: 박주원
# Description: 안동대학교 전화번호부 데이터 수집 및 내보내기

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

#board > div.t3.tac > table > tbody > tr:nth-child(8) > td:nth-child(1) - 대학본부
#board > div.t3.tac > table > tbody > tr:nth-child(8) > td:nth-child(2) > span - 교무처/교무과
#board > div.t3.tac > table > tbody > tr:nth-child(8) > td:nth-child(3) - 교육과정
#board > div.t3.tac > table > tbody > tr:nth-child(8) > td.tal - 전화번호


def getTableLink(pageNum):
    url = f'https://www.andong.ac.kr/main/board/index.do?menu_idx=104&manage_idx=45&board_idx=0&old_menu_idx=0&old_manage_idx=0&old_board_idx=0&group_depth=0&parent_idx=0&group_idx=0&search.category1=&search_type=title%2Buser_name%2Bcontent&search_text=&rowCount=10&viewPage={pageNum}&totalDataCount=744'
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
    for i in range(1,11,1):
        r = (pageNum-1)*10+i
        #print(r, end=' ')
        dept_name = ''

        tmp = soup.select_one(
            f'#board > div.t3.tac > table > tbody > tr:nth-child({i}) > td:nth-child(1)'
        ).text
        tmp += ' '
        dept_name += tmp.replace('\r','').replace('\t','').replace('\n','')

        tmp = soup.select_one(
            f'#board > div.t3.tac > table > tbody > tr:nth-child({i}) > td:nth-child(2) > span'
        ).text
        tmp += ' '
        dept_name += tmp.replace('\r','').replace('\t','').replace('\n','')

        tmp = soup.select_one(
            f'#board > div.t3.tac > table > tbody > tr:nth-child({i}) > td:nth-child(3)'
        ).text
        dept_name += tmp.replace('\r','').replace('\t','').replace('\n','')
        dept_name += '의 전화번호는 '

        tmp = soup.select_one(
            f'#board > div.t3.tac > table > tbody > tr:nth-child({i}) > td.tal'
        ).text
        tmp = tmp.replace('\r','').replace('\t','').replace('\n','')
        tmp = '054-820-' + tmp
        arr[r] = dept_name + tmp + '입니다.'

    return r

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

url = 'https://www.andong.ac.kr/main/board/index.do?menu_idx=104&manage_idx=45'

response = requests.get(url)

if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

number_count = soup.select_one(
    '#board > div.board_info > div.left > em:nth-child(1)'
)


number_count = int(number_count.text)
arr = [False for row in range(number_count)]
for n in tqdm(range(1, number_count//10, 1)):
    r = getTableLink(n)

arr = [elem for elem in arr if elem != False]

pprint(arr)

vectorize_by_arr(arr, 'anubot-unified')

'''
df = pd.DataFrame(arr, columns=['구분', '부서/학과', '직책/성명', '전화번호'])
df.to_csv('anubot_numb.csv', encoding='utf-8-sig',index=True ,header=None)
print(f'\n총 {r}개의 데이터를 수집했습니다. / 내보내기 완료.')
'''
