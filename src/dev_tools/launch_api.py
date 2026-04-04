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

import json
from fastapi import Form, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from src.utils.load_file.load_request_file import LoadRequestFile
from src.content_parse.module.applications import DocumentParse


@app.post("/parse-content/document-parse")
async def document_parse(
    job_id: str = Form(...),
    metadata: str = Form(...),
    schema: str = Form(...),
    file: UploadFile = File(...),
    config: Optional[str] = Form(None),
):
    try:
        loader = await LoadRequestFile(
            file=file,
            allowed_extensions=["txt", "md", "pdf", "docx"],
            max_size_mb=5
        ).load()

        file_bytes = loader.bytes
        file_extension = loader.extension

        parser = DocumentParse(
            job_id=job_id,
            metadata=metadata,
            schema=schema,
            config=config,
            file_bytes=file_bytes,
            file_extension=file_extension
        )

        result = parser.run()

        return JSONResponse(content={
            "status": "success",
            "job_id": result.get("job_id"),
            "result": result.get("content")
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
curl --location 'http://localhost:8000/parse-content/simple-file-parse' \
--form 'job_id="teste"' \
--form 'metadata="{\"value1\": \"value3\"}"' \
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
--form 'file=@"c:\\Users\\schit\\better-ai\\src\\text_parse\\module\\Endurance.pdf"''
"""

