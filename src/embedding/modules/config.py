import os
from dotenv import load_dotenv

load_dotenv()

class GetConfig:
    def vector_db_settings(self):
        return {
            "index_name": "backai-vectorstore",
            "main_namespace": os.getenv("PINECONE_NAMESPACE"),
            "global_namespace": os.getenv("PINECONE_GLOBAL_NAMESPACE"),
            "save_global": True,

            "model": "text-embedding-3-large",
            "dimensions": 3072,
            "batch_size": 200,
        }
    def embedding_file(self):
        return {
            "vector_db_settings": self.vector_db_settings(),

            "database_name": "embeddings",
            "collection_name": "embedding_file"
        }


