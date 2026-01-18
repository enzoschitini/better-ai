from src.vector_store.pinecone_client import PineconeClient
from src.vector_store.pinecone_retriever import PineconeRetriever

import json

client = PineconeClient(
    namespace="betterai-embeddings-dev",
    embedding_model="text-embedding-3-large"
)

search_service = PineconeRetriever(client)

results = search_service.similarity_search(
    query="criaturas elegantes e misteriosas",
    k=5,
    filter_search={"file_id": ["21d75dca2eec7b02080327f40220e20dxx2"]}
)

def generate_text_contex(chunks: dict):
    for item in chunks:
        item.pop("id", None)
        item.pop("metadata", None)
    
    return chunks

for item in results:
    print(json.dumps(item, indent=4, ensure_ascii=False))

print("\n\n")

results = generate_text_contex(results)

for item in results:
    print(json.dumps(item, indent=4, ensure_ascii=False))
# python -m src.vector_store.test