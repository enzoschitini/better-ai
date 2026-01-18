from src.vector_store.pinecone_client import PineconeClient
from src.vector_store.pinecone_retriever import PineconeRetriever

import json

client = PineconeClient(namespace="retrieval_test")
search_service = PineconeRetriever(client)

results = search_service.similarity_search(
    query="criaturas elegantes e misteriosas",
    k=5,
    filter_search={"file_id": ["gatos", "foguetes", "opera"]}
)

for item in results:
    print(json.dumps(item, indent=4, ensure_ascii=False))
 