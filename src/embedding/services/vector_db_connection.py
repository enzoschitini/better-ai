
from src.vector_store.pinecone.client import PineconeClient
from src.vector_store.pinecone.embedding import PineconeEmbedding

class VectorDBConnection(PineconeClient, PineconeEmbedding):
    def __init__(self, vector_db_settings, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.vector_db_settings = vector_db_settings
        self.pinecone_client = None
        self.pinecone_embedding = None

    def get_pinecone_vector_db(self):
        """
        Initializes and configures the Pinecone vector database client and service
        using the vector store settings from the payload or config.

        Raises:
                RuntimeError: If loading the vector store database fails.
        """
        try:
            self.pinecone_client = PineconeClient(
                index_name=self.vector_db_settings.get("index_name", "backai-vectorstore"),
                main_namespace=self.vector_db_settings.get("main_namespace", "embedding_file"),
                global_namespace=self.vector_db_settings.get("global_namespace", "global_vectorstore"),
                embedding_model=self.vector_db_settings.get("model", "text-embedding-3-large"),
            )

            self.pinecone_embedding = PineconeEmbedding(
                vector_client=self.pinecone_client,
                embedding_model_name=self.vector_db_settings.get("model", "text-embedding-3-large"), 
                dimensions=self.vector_db_settings.get("dimensions", 3072),
            )

            return self.pinecone_client, self.pinecone_embedding

        except Exception as e:
            raise RuntimeError(f"Failed to load vector store database: {str(e)}")


# python -m src.embedding.services.vector_db_connection