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


# ================================================
# API SETTINGS
# ================================================

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - line: %(lineno)d - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="BetterAI Chat API",
    description="""
API para interação com o agente de IA BetterAI 🤖  
Permite o envio de mensagens e manutenção de contexto de sessão entre interações.
    """,
    version="1.0.0"
)

# Lista de domínios confiáveis (coloca aqui apenas os que realmente vão acessar a API)
origins = [
    "https://better-ai.up.railway.app",
    "https://better-ai-homol.up.railway.app",
    "https://better-ai-dev.up.railway.app",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         # apenas origens confiáveis
    allow_credentials=True,        # habilita envio de cookies/autenticação
    allow_methods=["GET", "POST"], # apenas os métodos realmente usados
    allow_headers=["Authorization", "Content-Type"],  # cabeçalhos necessários
)

load_dotenv()

# uvicorn web_api:app --reload

@app.get("/healthy1")
def healthy():
    return {"status": "ok"}