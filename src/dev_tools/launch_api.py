import json
import os
import uuid
import logging

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, HTTPException, Request, Form, Body, Depends, Header, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

class ASCII_API:
    def __init__(self):
        pass

    def standard(self):
        # 92m Verde
        # 97m Bianco

        logo = """
        \033[97m
        ╔═══════════════════════════════════════════════════════════════════════╗

            ██████╗ ███████╗████████╗████████╗███████╗██████╗      █████╗ ██╗ ✦
            ██╔══██╗██╔════╝╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗    ██╔══██╗██║
            ██████╔╝█████╗     ██║      ██║   █████╗  ██████╔╝    ███████║██║
            ██╔══██╗██╔══╝     ██║      ██║   ██╔══╝  ██╔══██╗    ██╔══██║██║
            ██████╔╝███████╗   ██║      ██║   ███████╗██║  ██║    ██║  ██║██║
            ╚═════╝ ╚══════╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝

        ╚═══════════════════════════════════════════════════════════════════════╝

                          ✦  Where intelligence finds purpose. ✦
        \033[0m
        """
        print(logo)



asci = ASCII_API()
asci.standard()

app = FastAPI()

@app.get("/healthy")
def healthy():
    return {"status": "ok"}

# uvicorn src.dev_tools.launch_api:app --reload 
# uvicorn app:app --reload  

# ------------------------------------------------- #
from src.utils.load_file.load_request_file import LoadRequestFile
from src.embedding.services.file_content_extractor import FileContentExtractor
from src.text_parse.content_parsing_agent import ContentParsingAgent

from fastapi import Form, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import json

@app.post("/parse-content")
async def parse_content(
    schema: str = Form(...),
    file: UploadFile = File(...),
    config: Optional[str] = Form(None),  # 👈 opcional
):
    try:
        loader = await LoadRequestFile(
            file=file,
            max_size_mb=5
        ).load()

        file_bytes = loader.bytes
        file_extension = loader.extension

        schema_data = json.loads(schema)

        default_config = {
            "model_provider": "OpenAI",
            "model_id": "gpt-4.1-mini",
            "debug_mode": True,
            "instructions": "Extraia dados do texto",
            "description": "Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos. Caso não encontre alguma informação, retorne null para aquele campo."
        }

        if config:
            try:
                config_input = json.loads(config)
                config_data = {**default_config, **config_input}
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in config")
        else:
            config_data = default_config

        extractor = FileContentExtractor(
            file_bytes=file_bytes,
            file_extension=file_extension
        )
        result_extract = extractor.extract()

        agent_parser = ContentParsingAgent(
            input_data={
                "file_content": result_extract["response"]
            },
            output_data=schema_data,
            config_data=config_data
        )

        content_parsed = agent_parser.run_agent()
        response = agent_parser.format_response(content_parsed)

        return JSONResponse(content={
            "status": "success",
            "response": response,
            "config_used": config_data
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
curl --location 'http://localhost:8000/parse-content' \
--header 'Accept: application/json' \
--form 'schema="{
  \"summary\": {
    \"type\": \"str\",
    \"description\": \"Resumo do conteúdo do arquivo\"
  }
}"' \
--form 'config="{
  \"model_provider\": \"OpenAI\",
  \"model_id\": \"gpt-4.1-mini\",
  \"debug_mode\": true,
  \"instructions\": \"Extraia dados do texto\",
  \"description\": \"Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos. Caso não encontre alguma informação, retorne null para aquele campo.\"
}"' \
--form 'file=@"/C:/Users/enzo_silva/Downloads/files/Fiat Test Chat/Endurance.pdf"'
"""

