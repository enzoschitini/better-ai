import os
import json
import uuid

from datetime import datetime, UTC
from typing import List, Dict, Any, Optional


class LocalNoSQLManager:
    """
    Gerenciador de banco NoSQL local baseado em arquivos JSON.

    Simula a estrutura de bancos e collections do MongoDB utilizando
    diretórios e arquivos JSON.

    Estrutura:
        base_path/
            database/
                collection.json

    :param base_path: Diretório base onde os dados serão armazenados.
    """

    def __init__(self, base_path: str = "data"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    # -------------------------
    # Helpers internos
    # -------------------------
    def _get_collection_path(self, database_name: str, collection_name: str) -> str:
        db_path = os.path.join(self.base_path, database_name)
        os.makedirs(db_path, exist_ok=True)

        return os.path.join(db_path, f"{collection_name}.json")

    def _load_collection(self, path: str) -> List[Dict]:
        if not os.path.exists(path):
            return []

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_collection(self, path: str, data: List[Dict]):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _match_filter(self, document: Dict, filter: Dict) -> bool:
        """
        Filtragem simples estilo MongoDB (igualdade).
        """
        for key, value in filter.items():
            if document.get(key) != value:
                return False
        return True

    # -------------------------
    # CRUD
    # -------------------------
    def save_payload(self, database_name: str, collection_name: str, payload: dict) -> Dict:
        path = self._get_collection_path(database_name, collection_name)
        data = self._load_collection(path)

        payload = payload.copy()
        payload["_id"] = str(uuid.uuid4())
        payload["_created_at"] = datetime.now(UTC).isoformat()

        data.append(payload)
        self._save_collection(path, data)

        return {"status": "success", "inserted_id": payload["_id"]}

    def fetch_documents(
        self,
        database_name: str,
        collection_name: str,
        filter: Optional[dict] = None,
        limit: int = 0
    ) -> List[Dict]:

        path = self._get_collection_path(database_name, collection_name)
        data = self._load_collection(path)

        filter = filter or {}

        results = [doc for doc in data if self._match_filter(doc, filter)]

        if limit > 0:
            results = results[:limit]

        return results

    def update_documents(
        self,
        database_name: str,
        collection_name: str,
        filter: dict,
        new_values: dict,
        multi: bool = False
    ) -> Dict:

        path = self._get_collection_path(database_name, collection_name)
        data = self._load_collection(path)

        new_values = new_values.copy()
        new_values.pop("_id", None)
        new_values["updated_at"] = datetime.now(UTC).isoformat()

        matched = 0
        modified = 0

        for doc in data:
            if self._match_filter(doc, filter):
                matched += 1

                for key, value in new_values.items():
                    doc[key] = value

                modified += 1

                if not multi:
                    break

        self._save_collection(path, data)

        return {
            "status": "success",
            "matched_count": matched,
            "modified_count": modified,
            "message": f"{modified} document(s) updated"
        }

    def delete_documents(
        self,
        database_name: str,
        collection_name: str,
        filter: dict,
        multi: bool = False
    ) -> Dict:

        path = self._get_collection_path(database_name, collection_name)
        data = self._load_collection(path)

        new_data = []
        deleted_count = 0

        for doc in data:
            if self._match_filter(doc, filter):
                if not multi and deleted_count == 1:
                    new_data.append(doc)
                else:
                    deleted_count += 1
            else:
                new_data.append(doc)

        self._save_collection(path, new_data)

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"{deleted_count} document(s) deleted"
        }


if __name__ == "__main__":
    manager = LocalNoSQLManager()

    """
    manager.save_payload("mydb", "users", {"name": "Enzo"})

    docs = manager.fetch_documents("mydb", "users", {"name": "Enzo"})
    print(json.dumps(docs, indent=4))

    manager.update_documents("mydb", "users", {"name": "Enzo"}, {"age": 25})

    manager.delete_documents("mydb", "users", {"name": "Enzo"})
    """

    manager.delete_documents("mydb", "users", {"name": "Enzo"})
