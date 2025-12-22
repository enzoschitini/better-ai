import os
from io import BytesIO
from dotenv import load_dotenv
from typing import Tuple, Dict, List

from fastapi import UploadFile

from src.chat.utils.mongo_manage import MongoDBManager
from src.embedding.services.file_content_extractor import FileContentExtractor
from src.embedding.services.pinecone_vector_store import (
    PineconeClient,
    PineconeVectorService
)
from src.embedding.tokens_calculator.cost import EmbeddingCostCalculator
from src.embedding.tokens_calculator.business_plan_usage import BusinessPlanUsage

load_dotenv()

# ======================================================
# File Service
# ======================================================

class FileService:
    ALLOWED_EXTENSIONS = {
        "txt", "md", "markdown", "html",
        "pdf", "docx", "pptx",
        "csv", "xlsx", "json"
        # "doc", "ppt", "xls", "xml"
    }

    @staticmethod
    async def load(file: UploadFile) -> Tuple[str, str, BytesIO]:
        filename = file.filename

        if not filename or "." not in filename:
            raise ValueError("Invalid filename")

        extension = filename.lower().split(".")[-1]

        if extension not in FileService.ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported extension: .{extension}")

        file_bytes = await file.read()

        if not file_bytes:
            raise ValueError("Empty file")

        return filename, extension, BytesIO(file_bytes)


# ======================================================
# Content Extraction
# ======================================================

class ContentExtractorService:

    @staticmethod
    def extract(file_bytes: BytesIO, extension: str) -> Dict:
        extractor = FileContentExtractor(file_bytes, extension)
        return extractor.extract()


# ======================================================
# Embedding Transformer
# ======================================================

class EmbeddingTransformer:

    @staticmethod
    def transform(
        payload: dict,
        file_name: str,
        file_extension: str,
        extracted_content: dict
    ) -> Tuple[dict, dict]:

        additional_info = payload.get("metadata", {}).get("additional_information")

        embedding_content = {
            "file_name": file_name,
            "file_extension": file_extension,
            "file_content": extracted_content["response"]
        }

        if additional_info:
            embedding_content.update(additional_info)

        embedding_metadata = {
            "business_id": payload["business_id"],
            "file_id": payload["file_id"],
            "file_name": file_name,
            "file_extension": file_extension,
            **payload["metadata"]["filters"]
        }

        if additional_info:
            embedding_metadata.update(additional_info)

        return embedding_content, embedding_metadata


# ======================================================
# Embedding (Pinecone)
# ======================================================

class EmbeddingService:

    def __init__(self, embedding_settings: dict):
        self.embedding_settings = embedding_settings

        self.client = PineconeClient(
            index_name=os.getenv("PINECONE_INDEX_NAME"),
            namespace=os.getenv("PINECONE_NAMESPACE"),
            global_namespace=os.getenv("PINECONE_GLOBAL_NAMESPACE")
        )

        self.service = PineconeVectorService(
            vector_client=self.client,
            embedding_model_name=embedding_settings["llm_model"],
            dimensions=embedding_settings["dimensions"]
        )

    def embed(self, content: dict, metadata: dict) -> dict:
        return self.service.generate_vectors(
            text=content["file_content"],
            metadata=metadata,
            save_global=self.embedding_settings["global_namespace"],
            batch_size=self.embedding_settings["batch_size"]
        )


# ======================================================
# Usage / Cost Service
# ======================================================

class UsageService:

    def __init__(self, mongo: MongoDBManager):
        self.mongo = mongo
        self.database = "TokensUsage"
        self.collection = "BusinessAccountManage"

    def register_cost(
        self,
        business_id: str,
        text: str,
        model_name: str
    ) -> Dict | str:

        calculator = EmbeddingCostCalculator(model_name)
        cost = calculator.calculate_cost_json(text)

        business = self.mongo.buscar_documentos(
            self.database,
            self.collection,
            {"business_id": business_id}
        )[0]

        updated_plan = BusinessPlanUsage(
            plan=business["plan"]
        ).update_usage({"embedding_cost": cost})

        if updated_plan == "not_credits":
            return "not_credits"

        self.mongo.atualizar_documentos(
            self.database,
            self.collection,
            {"business_id": business_id},
            {"plan": updated_plan}
        )

        return {"embedding_cost": cost}


# ======================================================
# Persistence Service
# ======================================================

class EmbeddingPersistenceService:

    def __init__(self, mongo: MongoDBManager):
        self.mongo = mongo
        self.database = "embeddings"
        self.collection = "betterai_embeddings"

    def save(self, payload: dict, aggregates: List[dict]) -> str:
        data = payload.copy()

        for item in aggregates:
            if item:
                data.update(item)

        return self.mongo.salvar_payload(
            database_name=self.database,
            collection_name=self.collection,
            payload=data
        )


# ======================================================
# Orchestrator (replaces the "faz tudo" class)
# ======================================================

class EmbeddingModule:

    def __init__(self, payload: dict, file: UploadFile):
        self.payload = payload
        self.file = file
        self.mongo = MongoDBManager()
        self.embedding_settings = payload["embedding_settings"]

    async def execute(self) -> dict:
        # 1. Load file
        file_name, file_extension, file_bytes = await FileService.load(self.file)

        self.payload["file_name"] = file_name
        self.payload["file_extension"] = file_extension

        # 2. Extract content
        content = ContentExtractorService.extract(file_bytes, file_extension)

        # 3. Transform
        embedding_content, embedding_metadata = EmbeddingTransformer.transform(
            payload=self.payload,
            file_name=file_name,
            file_extension=file_extension,
            extracted_content=content
        )

        # 4. Embedding
        embedding_service = EmbeddingService(self.embedding_settings)
        vector_info = embedding_service.embed(
            embedding_content,
            embedding_metadata
        )

        # 5. Cost
        """
        usage_service = UsageService(self.mongo)
        cost = usage_service.register_cost(
            business_id=self.payload["business_id"],
            text=embedding_content["file_content"],
            model_name=self.embedding_settings["llm_model"]
        )

        if cost == "not_credits":
            raise RuntimeError("Insufficient credits")
        """
        
        cost = {"cost": "cost"}

        # 6. Persist
        persistence = EmbeddingPersistenceService(self.mongo)
        mongo_id = persistence.save(
            self.payload,
            [
                cost,
                {"vectorstore_information": vector_info["embedding_informations"]}
            ]
        )

        return {
            "status": "success",
            "file_id": self.payload["file_id"],
            "mongo_id": mongo_id["inserted_id"]
        }



"""
python -m src.embedding.embedding_module
"""
