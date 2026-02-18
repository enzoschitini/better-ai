# Standard library
import json
import os
import uuid
from typing import Any, Dict, List, Optional

# FastAPI
from fastapi import UploadFile, HTTPException

# Project modules
from src.image_generation.image_generator_service import ImageGeneratorService
from src.image_generation.utils.payload_builder import PayloadBuilder
from src.image_generation.utils.config import (
    BUCKET_NAME,
    STORAGE_BASE_PATH,
    DATABASE_NAME,
    COLLECTION_NAME
)

from src.utils.unique_id_factory import IDGenerator
from src.utils.loader_files import FilesPayloadBuilder

from src.database.mongo_manager import MongoDBManager
from src.database.LocalNoSQLMenager import LocalNoSQLManager
from src.storage.storage_repository import StorageRepository

class RequestProcessor:
    def __init__(
        self,
        config: Optional[str] = None,
        files: Optional[List[UploadFile]] = None
    ):
        self.config_raw = config
        self.files = files

        self.config_dict: Optional[Dict[str, Any]] = None
        self.image_bytes: Optional[List[bytes]] = None

    async def process(self) -> Dict[str, Any]:
        """
        Processa config e arquivos, retornando estrutura validada.
        """
        self._process_config()
        await self._process_files()

        return {
            "config": self.config_dict,
            "image_bytes": self.image_bytes
        }

    def _process_config(self) -> None:
        """
        Valida e converte o config JSON.
        """
        if not self.config_raw:
            return

        try:
            self.config_dict = json.loads(self.config_raw)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="config non è un JSON valido"
            )

    async def _process_files(self) -> None:
        """
        Processa e valida arquivos de imagem.
        """
        if not self.files:
            return

        try:
            builder = FilesPayloadBuilder(
                max_mb=10,
                allowed_types=("image/jpeg", "image/png")
            )

            images_payload = await builder.build_images_payload(self.files)
            self.image_bytes = [x["bytes"] for x in images_payload]

            """
            for x in images_payload:
                print(
                    f"filename: {x['filename']} | "
                    f"type: {x['content_type']} | "
                    f"size: {x['size_bytes']} | "
                    f"bytes: {x['bytes'][:50]}\n"
                )
            """

        except Exception as e:
            raise RuntimeError(f"Erro ao carregar as imagens: {e}")


class ImageGenerate:
    def __init__(
        self,
        user_input: str,
        instructions: Optional[str] = None,
        config: Optional[str] = None,
        image_bytes: List[str] = None
    ):
        self.user_input = user_input
        self.instructions = instructions
        self.config = config
        self.image_bytes = image_bytes


    # Genera Immagine
    def generate(self, content_config, user_prompt, instructions, images):
        editor = ImageGeneratorService(content_config=content_config)

        parts = editor.build_parts(
            user_prompt=user_prompt,
            instructions=instructions,
            images=images
        )

        config = editor.generate_config()
        response = editor.call_model(parts, config)
        responses_parsed = editor.parse_responses(response)

        return responses_parsed

    def build_payloads(self, responses_parsed):
        try:
            payload_builder = PayloadBuilder(IDGenerator.timestamp(prefix="job_"), responses_parsed)
            mongo_payload, storage_payload, response_payload = payload_builder.generate_payloads()

            #print(f"\n\nmongo_payload: {json.dumps(mongo_payload, indent=4)}")
            #print(f"\n\nresponse_payload: {json.dumps(response_payload, indent=4)}")

            return mongo_payload, storage_payload, response_payload
        except Exception as e:
            raise RuntimeError("Erro ao montar os payloads")
    
    def save_to_mongoDB(self, mongo_payload):
        try:
            mongo = LocalNoSQLManager()

            result = mongo.save_payload(
                database_name=DATABASE_NAME,
                collection_name=COLLECTION_NAME,
                payload=mongo_payload
            )
        except Exception as e:
            raise RuntimeError("Erro ao salvar no mongo")
    
    def save_to_supabase(self, images):
        try:
            repository = StorageRepository(
                base_path=STORAGE_BASE_PATH,
                bucket_name=BUCKET_NAME
            )

            for image in images:
                repository.upload_to_supabase(
                    file_name=image["id"],
                    byte_data=image["byte"]
                )

        except Exception as e:
            raise RuntimeError("Erro ao salvar no no storage")

    def save_results_local(self, responses_parsed):
        os.makedirs("img_test", exist_ok=True)

        for i, image in enumerate(responses_parsed["images"]):
            ext = image["mime_type"].split("/")[-1]
            filename = f"img_test/img_{i}_{uuid.uuid4().hex}.{ext}"

            with open(filename, "wb") as f:
                f.write(image["data"])

            print("Imagem salva em:", filename)

    def runner(self):
        responses_parsed = self.generate(
            self.config,
            self.user_input,
            self.instructions,
            self.image_bytes
        )
        mongo_payload, storage_payload, response_payload = self.build_payloads(responses_parsed)
        self.save_to_mongoDB(mongo_payload)
        self.save_to_supabase(storage_payload)

        return response_payload



# python -m src.image_generation.module