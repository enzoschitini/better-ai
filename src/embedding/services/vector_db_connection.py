
from src.vector_store.pinecone.client import PineconeClient
from src.vector_store.pinecone.embedding import PineconeEmbedding
from src.embedding.modules.config import GetConfig

class VectorDBConnection(PineconeClient, PineconeEmbedding):
    def __init__(self, vector_db_settings=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = GetConfig()
        default_settings = self.config.vector_db_settings()

        self.vector_db_settings = {
            **default_settings,
            **(vector_db_settings or {})
        }

        self.pinecone_client = None
        self.pinecone_embedding = None

    def get_vector_db(self):
        """
        Initializes and configures the Pinecone vector database client and service
        using the vector store settings from the payload or config.

        Raises:
                RuntimeError: If loading the vector store database fails.
        """
        try:
            self.pinecone_client = PineconeClient(
                index_name=self.vector_db_settings.get("index_name"),
                main_namespace=self.vector_db_settings.get("main_namespace"),
                global_namespace=self.vector_db_settings.get("global_namespace"),
                embedding_model=self.vector_db_settings.get("model"),
            )

            self.pinecone_embedding = PineconeEmbedding(
                vector_client=self.pinecone_client,
                embedding_model_name=self.vector_db_settings.get("model"), 
                dimensions=self.vector_db_settings.get("dimensions"),
            )

            return self.pinecone_client, self.pinecone_embedding

        except Exception as e:
            raise RuntimeError(f"Failed to load vector store database: {str(e)}")


# python -m src.embedding.services.vector_db_connection