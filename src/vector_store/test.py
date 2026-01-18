import json

from src.vector_store.pinecone_client import PineconeClient
from src.vector_store.pinecone_retriever import PineconeRetriever

client = PineconeClient(
    namespace="betterai-embeddings-dev",
    embedding_model="text-embedding-3-large"
)

retriever = PineconeRetriever(client)

def test_similarity_search():
    results = retriever.similarity_search(
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



def test_get_all_docs_by_metadata():
    vectors = retriever.get_all_docs_by_metadata(
        target_value=["xxxxxx", "21d75dca2eec7b02080327f40220e20dxx2"]
    )

    print(len(vectors))

    #print(f"\n\n{json.dumps(vectors, indent=4)}\n\n")



# python -m src.vector_store.test