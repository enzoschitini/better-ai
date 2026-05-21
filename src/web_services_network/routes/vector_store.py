import json

from typing import Optional, List
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import JSONResponse

from src.web_services_network.utils.request_resource import RequestResorse, Authorization, LoadRequestFile 
from src.embedding.applications import EmbeddingFile

router = APIRouter(
    prefix="/vector-store",
    tags=["vector-store", "embedding", "file-processing"]
)

@router.post(
    "/embedding-file",
    
    summary="Process a file upload, generates embeddings, and stores vectors with metadata.",
    #dependencies=[Depends(Authorization.multikey)],
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
