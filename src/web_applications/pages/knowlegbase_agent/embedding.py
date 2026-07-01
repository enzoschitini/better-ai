import os
import mimetypes
from io import BytesIO

import streamlit as st

import json

from io import BytesIO
from src.embedding.modules.embedding_file import EmbeddingFile


class FileProcessor:
    def __init__(self):
        pass

    def _load_file(self, path):
        # Implement the logic to load and process the file
        with open(path, "rb") as f:
            file_bytes = BytesIO(f.read())
        return file_bytes

    def get_file_information(self, file):
        name = os.path.basename(file)
        extension = os.path.splitext(name)[1].lstrip(".").lower()
        mime_type, _ = mimetypes.guess_type(file)
        size_bytes = os.path.getsize(file)
        return {
            "name": name,
            "extension": extension,
            "mime_type": mime_type or "application/octet-stream",
            "size_bytes": size_bytes,
            "size_kb": round(size_bytes / 1024, 2),
            "size_mb": round(size_bytes / (1024 * 1024), 4),
            "bytes": self._load_file(file)
        }

    def build_embedding_payload(
        self, 
        job_id: str,
        user_id: str,
        source: str,
        knoledgebase_id: str,
        file_info: dict,
    ):
        payload = {
            "job_id": job_id,

            "identifiers": {
                "user_id": user_id,
            },

            "embedding_metadata": {
                "source": source,
                "knoledgebase_id": knoledgebase_id,
                "origin": "web_app",
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

            "file_info": file_info
        }

        return payload


    def embedding_file(self, payload):
        embedder = EmbeddingFile(payload)
        embedder._init_tracking()
        result = embedder.run()
        embedder.save()
        return {
            "status": "success",
            "file_id": result["file_id"]
        }


def embedding():
    with st.sidebar:
        st.markdown("Embedding")



if __name__ == "__main__":
    embedding_processor = FileProcessor()

    file_info = embedding_processor.get_file_information("Credencial Sesc.pdf")
    payload = embedding_processor.build_embedding_payload(
        job_id="job_12345",
        user_id="user_789",
        source="uploaded_file",
        knoledgebase_id="knoledgebase_001",
        file_info=file_info
    )
    result = embedding_processor.embedding_file(payload)

    print("Embedding process completed successfully.")
    print(f"Status: {result['status']}")
    print(f"File ID: {result['file_id']}")

# python -m src.web_applications.pages.knowlegbase_agent.embedding