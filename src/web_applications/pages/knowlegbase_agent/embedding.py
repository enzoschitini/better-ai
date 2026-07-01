from io import BytesIO

import streamlit as st

import json

from io import BytesIO
from src.embedding.modules.embedding_file import EmbeddingFile

def embedding():
    with st.sidebar:
        st.markdown("Embedding")
    


class FileProcessor:
    def __init__(self):
        pass

    def _load_file(self, path):
        # Implement the logic to load and process the file
        with open(path, "rb") as f:
            file_bytes = BytesIO(f.read())
        return file_bytes

    def get_file_information(self, file):
        # Implement the logic to extract file information
        return {
            "name": "example.pdf",
            "extension": "pdf",
            "mime_type": "application/pdf",
            "size_bytes": 204800,
            "size_kb": 200,
            "size_mb": 0.2,
            "bytes": file
        }

    def build_embedding_payload(
        self, 
        job_id: str,
        user_id: str,
        source: str
    ):

        payload = {
            "job_id": "job_12345",

            "identifiers": {
                "client_id": "client_abc",
                "workspace_id": "workspace_001",
                "user_id": "user_789",
                "file_id": "file_xyz" # Può essere creato
            },

            "pipeline": {
                "generate_tags": True,
            },

            "embedding_metadata": {
                "source": "uploaded_file",
                "origin": "web_app",
                "language": "en",
                "tags": "#finance, #report, #2026"
            },

            "embedding_settings": {
                "model": "text-embedding-3-large",
                "dimensions": 3072,
                "chunk_size": 500,
                "chunk_overlap": 50,
                "normalize": True,
                "batch_size": 200,
            },

            "vector_db_settings": {
                "save_global": False,
                "main_namespace": "default_main_namespace",
            },

            "file_info": {
                "name": "example.pdf",
                "extension": "pdf",
                "mime_type": "application/pdf",
                "size_bytes": 204800,
                "size_kb": 200,
                "size_mb": 0.2,
                "bytes": self._load_file("Credencial Sesc.pdf")
            }
        }

        return payload


    def embedding_file(self, payload):
        embedder = EmbeddingFile(payload)
        embedder._init_tracking()
        embedder.run()
        embedder.save()


if __name__ == "__main__":
    embedding_processor = FileProcessor()
    payload = embedding_processor.build_embedding_payload(
        job_id="job_12345",
        user_id="user_789",
        source="uploaded_file"
    )
    #embedding_processor.embedding_file(payload)

# python -m src.web_applications.pages.knowlegbase_agent.embedding