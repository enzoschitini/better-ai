from src.image_generation.edit import ImageGeneratorService
from src.image_generation.payload_builder import PayloadBuilder
from src.utils.unique_id_factory import IDGenerator
from src.database.mongo_manager import MongoDBManager

import os
import uuid
import json

# Load images

def load_image_bytes():
    base_image_paths = [
        "src/image_generation/backup/img1.jpeg",
        "src/image_generation/backup/img2.jpeg"
    ]

    images = []

    for path in base_image_paths:
        with open(path, "rb") as f:
            image_bytes = f.read()
        
        images.append(image_bytes)
    
    return images

def gen(images):
    editor = ImageGeneratorService(content_config={"number_of_images": 2})

    parts = editor.build_parts(
        user_prompt="Gere uma imagem seguindo o estilo dessas",
        instructions="Crie uma imagem que combine elementos de ambas as imagens fornecidas, mantendo um estilo artístico coeso e atraente.",
        images=images
    )

    config = editor.generate_config()
    response = editor.call_model(parts, config)
    responses_parsed = editor.parse_responses(response)

    return responses_parsed

def save_results(responses_parsed):
    print("Text Responses:", responses_parsed["text_responses"])
    print("Usage Metadata:", responses_parsed["usage_metadata"])
    print("Config:", responses_parsed["generate_config"])

    os.makedirs("img_test", exist_ok=True)

    for i, image in enumerate(responses_parsed["images"]):
        ext = image["mime_type"].split("/")[-1]  # png, jpeg, webp, etc
        filename = f"img_test/img_{i}_{uuid.uuid4().hex}.{ext}"

        with open(filename, "wb") as f:
            f.write(image["data"])

        print("Imagem salva em:", filename)
    
    """
    Objetivo,Exemplo de Código,Exemplo de Retorno
    UUID v4 (Padrão),IDGenerator.uuid(),784a0d9b-2b41-4c12-8877-6f8d92305381
    Timestamp (Numérico),IDGenerator.timestamp(),17391845120004561
    Timestamp + Prefixo,"IDGenerator.timestamp(prefix=""USR"", separator=""_"")",USR_17391845120008219
    Timestamp (Hex/Curto),IDGenerator.timestamp(as_hex=True),18f74d0a2bc5f1a39
    Token Seguro (URL),IDGenerator.token(length=12),A9x_L2mNq4W1
    Máscara Customizada,"IDGenerator.custom(""TAG-####-??"")",TAG-4821-KM
    Serial Alfanumérico,"IDGenerator.custom(""****-****"")",A7j2-9PqL
    """

def payloads(responses_parsed):
    payload_builder = PayloadBuilder(IDGenerator.timestamp(prefix="job_"), responses_parsed)
    mongo_payload, storage_payload, response_payload = payload_builder.generate_payloads()

    print(f"\n\nmongo_payload: {json.dumps(mongo_payload, indent=4)}")
    print(f"\n\nresponse_payload: {json.dumps(response_payload, indent=4)}")

"""
print(f"ID: {IDGenerator.timestamp(prefix="JOB-")}")

images = load_image_bytes()
responses_parsed = gen(images=images)
payloads(responses_parsed=responses_parsed)
save_results(responses_parsed)
"""















from typing import List, Dict, Optional, Tuple
from fastapi import FastAPI, UploadFile, HTTPException, Request, Form, Depends, Header, File
from fastapi.responses import JSONResponse
from src.utils.loader_files import FilesPayloadBuilder
from src.database.mongo_manager import MongoDBManager
from src.image_generation.utils.config import (
    BUCKET_NAME, STORAGE_BASE_PATH, DATABASE_NAME, COLLECTION_NAME
)
from src.storage.storage_repository import StorageRepository

import json

class ImageGenerate:
    def __init__(
        self,
        user_input: str,
        instructions: Optional[str] = None,
        config: Optional[str] = None,
        files: List[UploadFile] = None
    ):
        self.user_input = user_input
        self.instructions = instructions
        self.config = config
        self.files = files

    async def validate(self) -> Tuple[dict, List[bytes]]:
        config_dict = {}
        image_bytes = []

        # Validate config
        if self.config:
            try:
                config_dict = json.loads(self.config)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="config non è un JSON valido"
                )

        # Validate files
        if self.files:
            try:
                builder = FilesPayloadBuilder(
                    max_mb=10,
                    allowed_types=("image/jpeg", "image/png")
                )
                images_payload = await builder.build_images_payload(self.files)
                image_bytes = [x["bytes"][:50] for x in images_payload]

                for x in images_payload:
                    print(f"filename: {x['filename']} | type: {x['content_type']} | size: {x['size_bytes']} | bytes: {x["bytes"][:50]}")

            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Erro ao carregar as imagens: {str(e)}"
                )

        return config_dict, image_bytes


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
    
    # Salva il processo
    def save_process(responses_parsed):
        try:
            payload_builder = PayloadBuilder(IDGenerator.timestamp(prefix="job_"), responses_parsed)
            mongo_payload, storage_payload, response_payload = payload_builder.generate_payloads()
        
        except Exception as e:
            raise RuntimeError("Erro")

        try:
            mongo = MongoDBManager()

            result = mongo.save_payload(
                database_name=DATABASE_NAME,
                collection_name=COLLECTION_NAME,
                payload=mongo_payload
            )
        except Exception as e:
            raise RuntimeError("Erro ao salvar no mongo")

        try:
            repository = StorageRepository(
                base_path=STORAGE_BASE_PATH,
                bucket_name=BUCKET_NAME
            )

            for image in storage_payload:
                repository.upload_to_supabase(
                    file_name=image["id"],
                    byte_data=image["byte"]
                )

        except Exception as e:
            raise RuntimeError("Erro ao salvar no no storage")
        
        return response_payload

    async def runner(self):
        content_config, image_bytes = await self.validate()
        responses_parsed = self.generate(
            content_config,
            self.user_input,
            self.instructions,
            image_bytes
        )
        response_payload = self.save_process(responses_parsed)

        return response_payload


# python -m src.image_generation.module