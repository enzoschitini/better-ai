import json

from src.vector_store.pinecone.pinecone_client import PineconeClient
from src.vector_store.pinecone.pinecone_retriever import PineconeRetriever
from src.vector_store.pinecone.pinecone_vectorstore_services import PineconeVectorService

class TestPineconeVectorStore:
    def __init__(self):
        pass

    def get_client(self):
        pine_client = PineconeClient(
            index_name="backai-vectorstore",
            main_namespace="test_namespace",
            global_namespace="global_namespace"
        )

        return pine_client

    def retriver(
            self, 
            query: str = "Quais arquivos estão na base?",
            filter_search: dict = {
                "file_id": [
                    "21d75dca2eec7b02080327f40220e20dxx2"
                ]
            },
            k: int = 5
        ):

        retriver = PineconeRetriever()

        result = retriver.similarity_search(
            query=query,
            filter_search=filter_search,
            k=k
        )

        print(json.dumps(result, indent=2))

        return result

    def embedding(self):
        pine_service = PineconeVectorService(embedding_model_name="text-embedding-3-large", dimensions=3072)

        embedding_content = """
    Embeddings are vector representations of data (such as text, documents, or images) that capture their semantic meaning in a numerical space.
    This technique allows for the comparison of content by similarity, enabling semantic searches, classification, recommendation, and information retrieval.
    By transforming unstructured data into vectors, embeddings make it possible to efficiently index and query large volumes of information in vector databases.
    """

        embedding_metadata = {"user_id": "user_1234567", "source": "embedding_test.py"}

        response = pine_service.generate_vectors(
            text=str(embedding_content),
            metadata=embedding_metadata,
            save_global=False,
            batch_size=200
        )

        print("✅ Vectors generated and saved to Pinecone:", response)

        return response

    def delete(self):
        pine_service = PineconeVectorService(embedding_model_name="text-embedding-3-large", dimensions=3072)

        delete = pine_service.delete_documents("source", "embedding_test.py", "betterai-embeddings-dev")
        print(f"\n{delete}\n")

        return delete

if __name__ == "__main__":
    tester = TestPineconeVectorStore()
    tester.retriver()

# python -m src.vector_store.pinecone.test