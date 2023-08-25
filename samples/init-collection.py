import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from pprint import pprint

qdrant_url = os.getenv('QDRANT_URL')
qdrant_port = os.getenv('QDRANT_PORT')

client = QdrantClient(qdrant_url, port=qdrant_port)

# 참조: https://platform.openai.com/docs/guides/embeddings
client.recreate_collection(
    collection_name="openai_ada_2",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

pprint(client.get_collections().collections)