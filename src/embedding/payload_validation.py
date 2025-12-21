import uuid
from typing import Dict, Any


class PayloadValidationError(Exception):
    pass


class PayloadProcessor:
    """
    Classe responsabile per:
    - validare il payload
    - completare i campi mancanti
    - garantire uno schema consistente
    """

    ALLOWED_ROOT_KEYS = {
        "company_id",
        "file_id",
        "file_url",
        "metadata",
        "embedding_settings",
    }

    DEFAULT_EMBEDDING_SETTINGS = {
        "llm_model": "text-embedding-3-large",
        "dimensions": 3072,
        "global_namespace": True,
        "batch_size": 200,
    }

    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload

    # ======================================================
    # PUBLIC
    # ======================================================

    def process(self) -> Dict[str, Any]:
        self._validate_root_keys()
        self._validate_company_id()

        self._ensure_file_id()
        self._ensure_metadata()
        self._ensure_embedding_settings()

        self._validate_no_null_values()

        return self.payload

    # ======================================================
    # VALIDATIONS
    # ======================================================

    def _validate_root_keys(self):
        extra_keys = set(self.payload.keys()) - self.ALLOWED_ROOT_KEYS
        if extra_keys:
            raise PayloadValidationError(
                f"Chiavi non ammesse nel payload: {extra_keys}"
            )

    def _validate_company_id(self):
        if "company_id" not in self.payload:
            raise PayloadValidationError("company_id è obbligatorio")

    def _validate_no_null_values(self):
        def check_dict(d: Dict[str, Any], path="root"):
            for k, v in d.items():
                if v in (None, "", {}):
                    raise PayloadValidationError(
                        f"Valore non valido per '{path}.{k}'"
                    )
                if isinstance(v, dict):
                    check_dict(v, f"{path}.{k}")

        check_dict(self.payload)

    # ======================================================
    # COMPLETION LOGIC
    # ======================================================

    def _ensure_file_id(self):
        if "file_id" not in self.payload:
            self.payload["file_id"] = f"{self.payload["company_id"]}-{uuid.uuid4()}"

    def _ensure_metadata(self):
        if "metadata" not in self.payload:
            self.payload["metadata"] = {
                "filters": {
                    "file_id": self.payload["file_id"]
                }
            }

        self._validate_metadata_structure()

    def _ensure_embedding_settings(self):
        embedding = self.payload.get("embedding_settings", {})

        if not isinstance(embedding, dict):
            raise PayloadValidationError("embedding_settings deve essere un oggetto")

        for key, value in self.DEFAULT_EMBEDDING_SETTINGS.items():
            embedding.setdefault(key, value)

        self._validate_flat_dict(embedding, "embedding_settings")

        self.payload["embedding_settings"] = embedding

    # ======================================================
    # STRUCTURE VALIDATION
    # ======================================================

    def _validate_metadata_structure(self):
        metadata = self.payload["metadata"]

        if not isinstance(metadata, dict):
            raise PayloadValidationError("metadata deve essere un oggetto")

        for section in ("filters", "additional_information"):
            if section in metadata:
                self._validate_flat_dict(metadata[section], f"metadata.{section}")

    def _validate_flat_dict(self, obj: Dict[str, Any], path: str):
        if not isinstance(obj, dict):
            raise PayloadValidationError(f"{path} deve essere un oggetto")

        for k, v in obj.items():
            if isinstance(v, dict):
                raise PayloadValidationError(
                    f"{path}.{k} non può contenere JSON annidati"
                )


def test():
  payload = {
    "company_id": "1",
    #"file_id": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
    "file_url": "https://domain.com/docs/21d75dca2eec7b02080327f40220e20dxx2.pdf",
    
    "metadata": {

      "filters": {
        "id_collection": "id_collection_01",
        "id_series": "id_series_01",
        "id_client": "id_client_01",
        "id_user": "id_user_01",
        "id_workspace": "id_workspace_01"
      },

      "additional_information": {
        "collection_name": "BetterAI Repo"
      }
    },
    
    "embedding_settings": {
      "llm_model": "text-embedding-3-large",
      "dimensions": 3072,
      "global_namespace": True,
      "batch_size": 100
    }
  }

  import json

  processor = PayloadProcessor(payload)
  final_payload = processor.process()

  print(json.dumps(final_payload, indent=4))

test()