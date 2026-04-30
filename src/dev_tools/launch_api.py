import json
import os
import uuid
import logging

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from dotenv import load_dotenv

import json
from fastapi import Form, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from fastapi import FastAPI, UploadFile, HTTPException, Request, Form, Body, Depends, Header, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Utils
from src.utils.load_file.load_request_file import LoadRequestFile

class ASCII_API:
    def __init__(self):
        pass

    def standard(self):
        # 92m Verde
        # 97m Bianco

        logo = """
        
        \033[1;36m╔═══════════════════════════════════════════════════════════════════════╗

            ██████╗ ███████╗████████╗████████╗███████╗██████╗      █████╗ ██╗ ✦
            ██╔══██╗██╔════╝╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗    ██╔══██╗██║
            ██████╔╝█████╗     ██║      ██║   █████╗  ██████╔╝    ███████║██║
            ██╔══██╗██╔══╝     ██║      ██║   ██╔══╝  ██╔══██╗    ██╔══██║██║
            ██████╔╝███████╗   ██║      ██║   ███████╗██║  ██║    ██║  ██║██║
            ╚═════╝ ╚══════╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝

        ╚═══════════════════════════════════════════════════════════════════════╝\033[0m

                          \033[1;32m✦ Where intelligence finds purpose. ✦\033[0m


        """
        print(logo)



asci = ASCII_API()
asci.standard()

app = FastAPI()

@app.get("/healthy")
def healthy():
    return {"status": "ok"}

# curl -X GET "http://localhost:8000/healthy"
# uvicorn src.dev_tools.launch_api:app --reload
# uvicorn app:app --reload

# ------------------------------------------------- #

from src.embedding.modules.embedding_file import EmbeddingFile

@app.post(
    "/vector-store/embedding-file",
    #dependencies=[Depends(Authorization.multikey)],
    summary="Process a file upload, generates embeddings, and stores vectors with metadata."
)

async def embedding_file(
    payload: str = Form(...),
    file: UploadFile = File(...),
):
    try:
        embedding_payload = json.loads(payload)
        allowed_extensions = [
            "txt", "md", "pdf", "doc", "docx", "odt", "rtf", 
            "csv", "xls", "xlsx", 
            "ppt", "pptx",
        ]

        loader = await LoadRequestFile(
            file=file,
            allowed_extensions=allowed_extensions,
            max_size_mb=50
        ).load()

        #erro = 1 / 0

        file_info = {
            "name": loader.filename,
            "extension": loader.extension,
            "mime_type": loader.mimetype,
            "size_bytes": loader.size_bytes,
            "size_mb": round(loader.size_mb, 2),
            "bytes": loader.bytes
        }

        embedding_payload["file_info"] = file_info

        embedder = EmbeddingFile(embedding_payload)
        embedder._init_tracking()
        response = embedder.run()
        embedder.save()

        return JSONResponse(content=response)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "status_code": 500,
                "job_id": embedding_payload.get("job_id", "unknown"),
                "detail": f"Error: {str(e)}"
            }
        )

# CULR:
"""
curl --location 'http://localhost:8000/vector-store/embedding-file' \
--header 'accept: application/json' \
--form 'payload="{\"job_id\":\"job_12345\"}"' \
--form 'file=@"/C:/Users/enzo_silva/Downloads/files/Fiat Test Chat/Titan Oranch.pdf"'
"""

