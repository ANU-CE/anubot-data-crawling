import openai

def query_qdrant(query, collection_name, vector_name="title", top_k=20):
    # Creates embedding vector from user query
    embedded_query = openai.Embedding.create(
        input=query,
        model="text-embedding-ada-002",
    )["data"][0]["embedding"]

    query_results = client.search(
        collection_name=collection_name,
        query_vector=(
            vector_name, embedded_query
        ),
        limit=top_k,
    )

    return query_results

'''query_results = query_qdrant("솔뫼에 있는 방 중 아무거나", "ANU_Rooms")
for i, article in enumerate(query_results):
    print(f"{i + 1}. {article.payload['name']} (Score: {round(article.score, 3)})")'''


query_results = query_qdrant("난방 가능한 집", "ANU_Rooms", "info")
for i, article in enumerate(query_results):
    print(f"{i + 1}. {article.payload['title']} (Score: {round(article.score, 3)})")