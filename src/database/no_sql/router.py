import os

from typing import Optional
from src.database.no_sql.local_manager import LocalManager
from src.database.no_sql.mongo_manager import MongoDBManager


class DocumentStore:
    """
    Router para escolher dinamicamente o backend NoSQL.

    Pode alternar entre:
    - MongoDB
    - Local JSON storage
    """

    def __init__(self, backend: Optional[str] = None):
        self.backend = backend or os.getenv("NOSQL_BACKEND", "local")
        self.manager = self._initialize_manager()

    def _initialize_manager(self):
        if self.backend == "mongo":
            return MongoDBManager()
        elif self.backend == "local":
            return LocalManager()
        else:
            raise ValueError(f"Invalid backend: {self.backend}")

    # -------------------------
    # Proxy methods
    # -------------------------
    def save_payload(self, *args, **kwargs):
        return self.manager.save_payload(*args, **kwargs)

    def fetch_documents(self, *args, **kwargs):
        return self.manager.fetch_documents(*args, **kwargs)

    def update_documents(self, *args, **kwargs):
        return self.manager.update_documents(*args, **kwargs)

    def delete_documents(self, *args, **kwargs):
        return self.manager.delete_documents(*args, **kwargs)
