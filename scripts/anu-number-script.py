# Date. 2023-03-29
# Author: 박주원
# Description: 안동대학교 전화번호부 데이터 수집 및 내보내기

import requests
from bs4 import BeautifulSoup
import pandas as pd

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
        arr[r][0] = soup.select_one(
            f'#board > div.t3.tac > table > tbody > tr:nth-child({i}) > td:nth-child(1)'
        ).text
        arr[r][0] = arr[r][0].replace('\r','').replace('\t','').replace('\n','')
        arr[r][1] = soup.select_one(
            f'#board > div.t3.tac > table > tbody > tr:nth-child({i}) > td:nth-child(2) > span'
        ).text
        arr[r][1] = arr[r][1].replace('\r','').replace('\t','').replace('\n','')
        arr[r][2] = soup.select_one(
            f'#board > div.t3.tac > table > tbody > tr:nth-child({i}) > td:nth-child(3)'
        ).text
        arr[r][2] = arr[r][2].replace('\r','').replace('\t','').replace('\n','')
        arr[r][3] = soup.select_one(
            f'#board > div.t3.tac > table > tbody > tr:nth-child({i}) > td.tal'
        ).text
        arr[r][3] = arr[r][3].replace('\r','').replace('\t','').replace('\n','')
    return r


url = 'https://www.andong.ac.kr/main/board/index.do?menu_idx=104&manage_idx=45'

response = requests.get(url)

if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

number_count = soup.select_one(
    '#board > div.board_info > div.left > em:nth-child(1)'
)


number_count = int(number_count.text)
arr = [[False for col in range(4)] for row in range(number_count)]
for n in range(1, number_count//10, 1):
    r = getTableLink(n)
    print(n, end=' ')

df = pd.DataFrame(arr, columns=['구분', '부서/학과', '직책/성명', '전화번호'])
df.to_csv('anubot_numb.csv', encoding='utf-8-sig',index=True ,header=None)
print(f'\n총 {r}개의 데이터를 수집했습니다. / 내보내기 완료.')