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




@app.post("/parse-content",
          summary="Parse and extract structured content from files using schema")
async def text_parse(
    payload: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Endpoint per parsing testuale.
    Riceve:
    - payload: JSON string (schema, client_id, job_id, etc.)
    - file: file da analizzare (txt, pdf, ecc.)
    """

    # Parse payload JSON
    try:
        payload_dict = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload non è un JSON valido")

    # Inizializza il modulo
    module = TextParserModule(
        payload=payload_dict,
        file=file
    )

    # Esegui parsing
    try:
        result = await module.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "result": result
    }



