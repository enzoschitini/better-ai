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

        self.pine_client = pine_client

        return pine_client

    def retriever(
        self, 
        query: str = "Quais arquivos estão na base?",
        filter_search: dict = {
            "source": [
                "example_text.txt",
            ]
        },
        k: int = 5
        ):

        retriver = PineconeRetriever(client=self.pine_client)

        result = retriver.similarity_search(
            query=query,
            filter_search=filter_search,
            k=k
        )
        
        print("✅ Similarity Search Results:")
        print(json.dumps(result, indent=2))

        return result

    def embedding(
        self,
        embedding_content: str = None,
        embedding_metadata: dict = {"file_id": "file_1234567890", "user_id": "user_1234567", "source": "example_text.txt"}
    ):
        pine_service = PineconeEmbedding(
            vector_client=self.pine_client,
            embedding_model_name=self.embedding_model_name, 
            dimensions=self.dimensions
        )

        if embedding_content == None:
            with open("src/vector_store/pinecone/test/example_text.txt", "r", encoding="utf-8") as file:
                embedding_content = file.read()

        response = pine_service.generate_vectors(
            text=str(embedding_content),
            metadata=embedding_metadata,
            save_global=False,
            batch_size=200
        )

        print("✅ Vectors generated and saved to Pinecone:")
        print(json.dumps(response, indent=4, default=str))

        return response

    def delete(
        self,
        target_feature: str = "source",
        target_id: str = "example_text.txt",
        namespace: str = None,
        features: list = ["file_id", "source"]
    ):
        if namespace is None:
            namespace = self.main_namespace
            
        pine_service = PineconeEmbedding(
            vector_client=self.pine_client,
            embedding_model_name=self.embedding_model_name,
            dimensions=self.dimensions
        )

        delete = pine_service.delete_documents(target_feature, target_id, namespace, features)
        
        print(f"✅ Vectors with {target_feature}='{target_id}' deleted from namespace '{namespace}'.")
        print(json.dumps(delete, indent=4, default=str))

        return delete

if __name__ == "__main__":
    tester = TestPineconeVectorStore()
    tester.get_client()
    tester.embedding()
    #tester.retriever()
    #tester.delete()

# python -m src.vector_store.pinecone.test.test_services