import json

from src.vector_store.pinecone.client import PineconeClient
from src.vector_store.pinecone.retriever import PineconeRetriever
from src.vector_store.pinecone.embedding import PineconeEmbedding

class TestPineconeVectorStore:
    def __init__(
        self,
        index_name: str = None,
        main_namespace: str = None,
        global_namespace: str = None,
        embedding_model_name: str = None,
        dimensions: int = None
    ):
        self.index_name = index_name or "backai-vectorstore"
        self.main_namespace = main_namespace or "main_namespace"
        self.global_namespace = global_namespace or "global_namespace"

        self.embedding_model_name = embedding_model_name or "text-embedding-3-large"
        self.dimensions = dimensions or 3072

    def get_client(self):
        pine_client = PineconeClient(
            index_name=self.index_name,
            main_namespace=self.main_namespace,
            global_namespace=self.global_namespace
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

    def embedding(
        self,
        embedding_content: str = None,
        embedding_metadata: dict = {"user_id": "user_1234567", "source": "embedding_test.py"}
    ):
        pine_service = PineconeEmbedding(embedding_model_name=self.embedding_model_name, dimensions=self.dimensions)

        if embedding_content == None:
            with open("src/vector_store/pinecone/test/example_text.txt", "r") as file:
                embedding_content = file.read()

        response = pine_service.generate_vectors(
            text=str(embedding_content),
            metadata=embedding_metadata,
            save_global=False,
            batch_size=200
        )

        print("✅ Vectors generated and saved to Pinecone:", response)

        return response

    def delete(
        self,
        target_feature: str = "source",
        target_id: str = "embedding_test.py",
        namespace: str = None
    ):
        if namespace is None:
            namespace = self.main_namespace
            
        pine_service = PineconeEmbedding(embedding_model_name=self.embedding_model_name, dimensions=self.dimensions)

        delete = pine_service.delete_documents(target_feature, target_id, namespace)
        print(f"\n{delete}\n")

        return delete

if __name__ == "__main__":
    tester = TestPineconeVectorStore()
    tester.embedding()

# python -m src.vector_store.pinecone.test.test_services