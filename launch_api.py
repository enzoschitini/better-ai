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

from src.image_generation.module import ImageGenerate, RequestProcessor


@app.post("/image-generation", 
          summary="--------------")
async def image_generation(
    user_input: str = Form(...),
    instructions: Optional[str] = Form(None),
    config: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Doc
    """

    processor = RequestProcessor(config=config, files=files)
    processor_result = await processor.process()

    config_dict = processor_result["config"]
    image_bytes = processor_result["image_bytes"]

    generator = ImageGenerate(
        user_input=user_input,
        instructions=instructions,
        config=config_dict,
        image_bytes=image_bytes
    )

    response = generator.runner()

    return {
        "status": 200,
        "data": response
    }

"""
curl --location 'http://127.0.0.1:8000/image-generation' \
--header 'accept: application/json' \
--form 'user_input="Migliora la qualità della foto"' \
--form 'instructions="Lo stile deve essere realistico"' \
--form 'config="{
    \"model\": \"gemini-2.5-flash-image\",
    \"temperature\": 0.75,
    \"top_p\": 0.85,
    \"max_output_tokens\": 1024,
    \"aspect_ratio\": \"1:1\",
    \"number_of_images\": 2
}"' \
--form 'files=@"/C:/Users/schit/Downloads/Linkedin Profilo.jpeg"' \
--form 'files=@"/C:/Users/schit/Downloads/IMG-20230714-WA0007.jpg"'
"""

