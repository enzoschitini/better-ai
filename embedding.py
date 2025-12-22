import json
import os

from io import BytesIO
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

from fastapi import FastAPI, UploadFile, HTTPException, Request, Form, Depends, Header, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.embedding.embedding_module import EmbeddingModule
from src.embedding.services.payload_validation import PayloadProcessor
from src.embedding.services.pinecone_vector_store import PineconeClient, PineconeVectorService

app = FastAPI()


class EmbeddingPayload(BaseModel):
    data: Dict[str, Any]

    class Config:
        extra = "allow"

class EmbeddingResponse(BaseModel):
    status: str
    file_id: str
    mongo_id: str

@app.post("/embedding-file", response_model=EmbeddingResponse)
async def upload_file(
    request: Request,
    payload: str = Form(...),
    file: UploadFile = File(...)
):
    # Ensures that only 1 file was sent.
    form = await request.form()
    files = form.getlist("file")

    if len(files) > 1:
        raise HTTPException(
            status_code=400,
            detail="Only one file is allowed"
        )

    # Validates if the payload is valid JSON.
    try:
        payload_dict = json.loads(payload)
        payload_obj = EmbeddingPayload(data=payload_dict)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payload JSON: {str(e)}"
        )

    # Checks if the file has arrived.
    if not file or not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File is required"
        )

    # Process file
    try:
        payload_processor = PayloadProcessor(payload_obj.data)
        valid_payload = payload_processor.process()

        module = EmbeddingModule(
            payload=valid_payload,
            file=file
        )
        
        result = await module.execute()
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


"""
curl -X POST http://127.0.0.1:8000/embedding-file \
  -F 'payload={
  "business_id": "0011",
  "file_id": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
  "file_url": "https://domain.com/docs/21d75dca2eec7b02080327f40220e20dxx2.pdf",
  "metadata": {
    "filters": {
      "id_collection": "id_collection_01",
      "id_series": "id_series_01",
      "id_client": "id_client_01",
      "id_user": "id_user_01",
      "id_workspace": "id_workspace_01"
    },
    "additional_information": {
      "collection_name": "BetterAI Repo"
    }
  },
  "embedding_settings": {
    "llm_model": "text-embedding-3-large",
    "dimensions": 3072,
    "global_namespace": true,
    "batch_size": 100
  }
}

' \
  -F "file=@document.pdf"

# uvicorn app:app --reload
# uvicorn embedding:app --reload
# http://127.0.0.1:8000
"""















# Endpoint health check:

@app.get("/healthy")
def healthy():
    return {"status": "ok"}

# Author: Enzo Schitini