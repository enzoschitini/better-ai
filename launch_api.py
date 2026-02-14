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
    instructions: Optional[str] = Form(None),
    config: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Doc
    """

    generater = ImageGenerate(
        user_input,
        instructions,
        config,
        files
    )

    response = await generater.runner()

    return {
        "status": 200
    }




