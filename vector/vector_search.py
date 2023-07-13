import openai

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
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_PORT = os.getenv("QDRANT_PORT")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

print(QDRANT_API_KEY, QDRANT_URL)

COLLECTION_NAME = 'anubot-dbmap-room'

qdrant_client = QdrantClient(
    url = QDRANT_URL,
    port= QDRANT_PORT, 
)

retrieval_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

openai.api_key = OPENAI_API_KEY

def build_prompt(question: str, references: list) -> tuple[str, str]:
    prompt = f"""
    다음과 같은 질문을 한 친구에게 조언을 하고 있습니다.: '{question}'

    글에서 가장 관련성이 높은 구절을 선택하여 답변의 출처로 사용할겁니다. 당신의 대답에 그것들을 인용하세요.

    가장 관련성이 높은 구절에 링크가 있는 경우 링크를 반드시 첨부하세요.

    References:
    """.strip()

    references_text = ""

    for i, reference in enumerate(references, start=1):
        text = reference.payload["text"].strip()
        references_text += f"\n[{i}]: {text}"

    prompt += (
        references_text
        + "\n참고문헌 인용 방법: 이것은 인용문[1]입니다. 이것도 [3]. 그리고 이것은 인용문이 많은 문장입니다 [2][3].\n답:"
    )
    return prompt, references_text

def ask(question: str):
    similar_docs = qdrant_client.search(
        collection_name='anubot-unified',
        query_vector=retrieval_model.encode(question),
        limit=3,
        append_payload=True,
    )

    prompt, references = build_prompt(question, similar_docs)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "user", "content": prompt},
        ],
        max_tokens=250,
        temperature=0.2,
    )

    return {
        "response": response["choices"][0]["message"]["content"],
        "references": references,
    }

print(ask("안동대 맛집을 추천해줘~!"))
print(qdrant_client.get_collections())