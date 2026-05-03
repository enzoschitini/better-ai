```python
import json

from src.vector_store.pinecone.client import PineconeClient
from src.vector_store.pinecone.retriever import PineconeRetriever
from src.vector_store.pinecone.embedding import PineconeEmbedding

class TestPineconeVectorStore:
    """
    This class provides a set of methods to interact with a Pinecone vector store, including client initialization,
    vector embedding generation, retrieval using similarity search, and deletion of vectors based on metadata filters.

    Args: 
    :param index_name (str): The name of the Pinecone index to connect to (Default is "backai-vectorstore").
    :param main_namespace (str): The main namespace for storing vectors (Default is "main_namespace").
    :param global_namespace (str): The global namespace for storing vectors (Default is "global_namespace").
    :param embedding_model_name (str): The model name used for generating embeddings (Default is "text-embedding-3-large").
    :param dimensions (int): Number of dimensions for the embedding vectors (Default is 3072).

    Methods:
            get_client(): Initializes and returns a Pinecone client configured for the given index and namespaces.
            retriever(): Performs a similarity search on the Pinecone index using a query and optional filters.
            embedding(): Generates embeddings for input text and saves them to the Pinecone vector store.
            delete(): Deletes vectors from the Pinecone store based on a target feature and target ID within a namespace.
    """

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
        """
        Performs a similarity search against the Pinecone vector store to retrieve the most relevant vectors/documents
        based on the provided query and filter criteria.

        Args:
        query (str): The text query used to perform similarity search (Default is "Quais arquivos estão na base?").
        filter_search (dict): Dictionary defining filters on metadata fields for narrowing down the search (Default filters by source "example_text.txt").
        k (int): The number of top similar results to retrieve (Default is 5).

        Returns:
                list: A list of results from the similarity search containing relevant vectors and metadata.
        """
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
        """
        Generates vector embeddings for the provided text content and saves them into the Pinecone vector store 
        with associated metadata. If no content is provided, a default example file is read and used.

        Args:
        embedding_content (str): Text content to be embedded. If None, reads from a default example file (Default is None).
        embedding_metadata (dict): Metadata to associate with the embeddings for indexing and retrieval (Default includes file_id, user_id, and source).

        Returns:
                dict: The response from Pinecone after saving the generated vectors, typically including status details.
        """
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
        """
        Deletes vectors/documents from the Pinecone vector store filtered by a specific metadata feature and value within a specified namespace.

        Args:
        target_feature (str): The metadata field name used to filter vectors for deletion (Default is "source").
        target_id (str): The specific value of the target feature to identify vectors to delete (Default is "example_text.txt").
        namespace (str): The namespace within the Pinecone index to target for deletion; uses main_namespace if not specified (Default is None).
        features (list): List of metadata features to consider during deletion (Default is ["file_id", "source"]).

        Returns:
                dict: The response from Pinecone confirming deletion status and details.
        """
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
    tester.retriever()
    tester.delete()

# python -m src.vector_store.pinecone.test.test_services
```