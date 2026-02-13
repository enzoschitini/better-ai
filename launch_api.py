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




from typing import List
from fastapi import UploadFile, File, Form, HTTPException
import json

MAX_MB = 10
ALLOWED_TYPES = {"image/jpeg", "image/png"}

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

    images_payload: list[dict] = []

    for f in files:
        content = await f.read()

        # ✅ Validação de tipo
        if f.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Formato não suportado: {f.content_type}. Aceitos: jpeg, png."
            )

        # ✅ Validação de tamanho (10MB)
        if len(content) > MAX_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo muito grande: {f.filename}. Máx: {MAX_MB}MB."
            )

        images_payload.append({
            "filename": f.filename,
            "content_type": f.content_type,
            "size_bytes": len(content),
            "bytes": content
        })

        print(
            f"\nFile: {f.filename} | "
            f"type: {f.content_type} | "
            f"size(bytes): {len(content)}"
        )

    print(f"\nTotal files loaded: {len(images_payload)}")

    return {
        "status": 200,
        "files_received": len(images_payload)
    }




