import json
from src.vector_store.pinecone.pinecone_retriever import PineconeRetriever

retriver = PineconeRetriever()
results = retriver.get_all_docs_by_metadata(
    target_key="collection_id",
    target_value="collection_01"
)

print(json.dumps(results, indent=4))

"""
    target_key="file_id",
    target_value="candidatura"
    target_key="collection_id",
    target_value="collection_01"
"""
# ["candidatura", "tenerezza", "cucinare"]
# "hshshs"

# python -m src.vector_store.pinecone.all_files