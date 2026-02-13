import json
import os
import uuid
import logging

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, HTTPException, Request, Form, Depends, Header, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="BetterAI API LAUNCH",
    description="""
API para interação com o agente de IA BetterAI 🤖  
Permite o envio de mensagens e manutenção de contexto de sessão entre interações.
    """,
    version="1.0.0"
)

# uvicorn launch_api:app --reload  



MAX_MB = 10
ALLOWED_TYPES = {"image/jpeg", "image/png"}



from typing import List, Iterable
from fastapi import UploadFile, HTTPException

class FilesPayloadBuilder:
    def __init__(self, max_mb: int = 10, allowed_types: Iterable[str] = ("image/jpeg", "image/png")):
        self.max_bytes = max_mb * 1024 * 1024
        self.allowed_types = set(allowed_types)

    async def build_images_payload(self, files: List[UploadFile]) -> list[dict]:
        """
        Valida e transforma UploadFile em payload estruturado.

        :param files: Lista de arquivos enviados via multipart/form-data
        :type files: List[UploadFile]

        :return: Lista de dicionários com bytes e metadados
        :rtype: list[dict]
        """

        payload: list[dict] = []

        for f in files:
            content = await f.read()

            # ✅ Validação de tipo (header HTTP)
            if f.content_type not in self.allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Formato não suportado: {f.content_type}. Aceitos: {', '.join(self.allowed_types)}."
                )

            # ✅ Validação de tamanho
            if len(content) > self.max_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Arquivo muito grande: {f.filename}. Máx: {self.max_bytes // (1024 * 1024)}MB."
                )

            payload.append({
                "filename": f.filename,
                "content_type": f.content_type,
                "size_bytes": len(content),
                "bytes": content,
            })

        return payload


@app.post("/image-generation", summary="--------------")
async def image_generation(
    user_input: str = Form(...),
    instructions: str = Form(...),
    config: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Doc
    """

    # Parse config JSON
    try:
        config_dict = json.loads(config)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="config non è un JSON valido")

    print(f"\n\nUser input: {user_input}")
    print(f"\nInstructions: {instructions}")
    print(f"\nConfig: {config_dict}")

    builder = FilesPayloadBuilder(max_mb=10, allowed_types=("image/jpeg", "image/png"))

    images_payload = await builder.build_images_payload(files)


    for x in images_payload:
        print(f"filename: {x['filename']} | type: {x['content_type']} | size: {x['size_bytes']}")

    print(f"\nTotal files loaded: {len(images_payload)}")

    return {
        "status": 200,
        "files_received": len(images_payload)
    }




