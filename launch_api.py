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

from src.utils.loader_files import FilesPayloadBuilder
from src.image_generation.module import ImageGenerate


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

    try:
        config_dict = json.loads(config)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="config non è un JSON valido")
    
    try:
        builder = FilesPayloadBuilder(max_mb=10, allowed_types=("image/jpeg", "image/png"))
        images_payload = await builder.build_images_payload(files)
        image_bytes = [x["bytes"] for x in images_payload]
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar as imagens: {e}")

    print(f"\n\nUser input: {user_input}")
    print(f"\nInstructions: {instructions}")
    print(f"\nConfig: {config_dict}")

    for x in images_payload:
        print(f"filename: {x['filename']} | type: {x['content_type']} | size: {x['size_bytes']} | bytes: {x["bytes"][:50]}")

    return {
        "status": 200,
        "files_received": len(images_payload)
    }




