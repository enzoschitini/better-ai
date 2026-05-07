import os
from dotenv import load_dotenv

load_dotenv()

class GetConfig:
    def embedding_file(self):
        return {
            "vector_db_settings": {
                "index_name": "backai-vectorstore",
                "main_namespace": "embedding_file_agent",
                "global_namespace": "global_vectorstore",
                "save_global": True,

                "model": "text-embedding-3-large",
                "dimensions": 3072,
                "batch_size": 200,
            },

            "database_name": "embeddings",
            "collection_name": "embedding_file"
        }

    def delete_embeddings(self):
        return {
            "vector_db_settings": {
                "index_name": "backai-vectorstore",
                "main_namespace": "embedding_file_agent",
                "global_namespace": "global_vectorstore",
                "save_global": True,

                "model": "text-embedding-3-large",
                "dimensions": 3072,
                "batch_size": 200,
            },
        }

