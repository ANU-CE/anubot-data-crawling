from datetime import datetime, timezone
import os 
import numpy as np
from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

qdrant_url = os.getenv('QDRANT_URL')
qdrant_port = os.getenv('QDRANT_PORT')

points = list()
for sample_text in ["hello world", "foo bar", "lorem ipsum"]: # TODO: 크롤링한 for문으로 대체
    embedding = np.random.rand(100) # TODO: OpenAI Embedding으로 대체
    point = PointStruct(
        id=str(uuid4()),
        vector=embedding,
        payload={
            "plain_text": sample_text,
            "created_datetime": datetime.now(timezone.utc).isoformat(timespec='seconds'),
        }
    )
    points.append(point)

# Qdrant에 업로드
client = QdrantClient(qdrant_url, port=qdrant_port)
client.upsert(
    collection_name="openai_ada_2",
    points=points,
)