import os
import json

from dotenv import load_dotenv

from src.vector_store.pinecone.client import PineconeClient
from src.vector_store.pinecone.retriever import PineconeRetriever

load_dotenv()

pine_client = PineconeClient(
    index_name="backai-vectorstore",
    main_namespace="main_namespace",
)

retriver = PineconeRetriever(client=pine_client)

similarity_search_result = retriver.similarity_search(
    query="Quais arquivos estão na base?",
    k=5
)

print("✅ Similarity Search Results:")
print(json.dumps(similarity_search_result, indent=2))


# python -m src.vector_store.pinecone.fts