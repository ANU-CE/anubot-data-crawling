from uuid import uuid4
from pprint import pprint

import requests
import asyncio

from flask import Flask, request, jsonify


#for vector database   
from qdrant_client import QdrantClient

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

COLLECTION_NAME = 'anubot-unified'

qdrant_client = QdrantClient(
    url = QDRANT_URL,
    port= QDRANT_PORT, 
)



def build_prompt(question: str, references: list) -> tuple[str, str]:
    prompt = f"""
    다음과 같은 질문을 한 친구에게 조언을 하고 있습니다.: '{question}'

    글에서 가장 관련성이 높은 구절을 선택하여 답변의 출처로 사용할겁니다. 당신의 대답에 그것들을 인용하세요.

    가장 관련성이 높은 구절에 링크가 있는 경우 링크를 반드시 첨부하세요.

    참고자료:
    """.strip()

    references_text = ""

    for i, reference in enumerate(references, start=1):
        text = reference.payload["plain_text"].strip()
        references_text += f"\n[{i}]: {text}"

    prompt += (
        references_text
        + ""
    )
    return prompt, references_text


async def prompt_ask(question: str, callback_url: str):
    similar_docs = qdrant_client.search(
        collection_name='anubot-unified',
        query_vector=openai.Embedding.create(input=question, model=EMBEDDING_MODEL)["data"][0]["embedding"],
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
    final_response = response["choices"][0]["message"]["content"]
    responseBody = jsonify({
        "version" : "2.0",
        "template" : {
            "outputs" : [
                {
                    "simpleText" : {
                        "text" : final_response
                    }
                }
            ]
        }
    })
    responseCode = requests.post(callback_url, json=responseBody)
    print(responseCode)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/')
def default_route():
    return 'Hello World!'

@app.route('/api/v1/ask', methods=['POST'])
def ask():
    request_data = request.json.get('userRequest', {})
    callback_url = request_data.get('callbackUrl')
    try:
        question = request_data['utterance']
        asyncio.create_task(prompt_ask(question, callback_url))
    except requests.exceptions.ReadTimeout:
        pass
    return jsonify({
        "version" : "2.0",
        "useCallback" : True
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

