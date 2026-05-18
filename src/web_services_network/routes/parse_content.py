import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel

from src.web_services_network.request_resource import RequestResorse, Authorization
from src.content_parse.module.applications import DocumentParse
from src.utils.load_file.load_request_file import LoadRequestFile

router = APIRouter(
    prefix="/parse-content",
    tags=["parse-content"]
)

load_dotenv()

@router.post("/document-parse", dependencies=[Depends(Authorization.multikey)],
          summary="Parse and extract structured content from files using schema")
async def document_parse(
    job_id: str = Form(...),
    metadata: str = Form(...),
    document_schema: str = Form(...),
    file: UploadFile = File(...),
    config: Optional[str] = Form(None),
):
    try:
        loader = await LoadRequestFile(
            file=file,
            allowed_extensions=["txt", "md", "pdf", "docx"],
            max_size_mb=50
        ).load()

        file_bytes = loader.bytes
        file_extension = loader.extension

        parser = DocumentParse(
            job_id=job_id,
            metadata=metadata,
            schema=document_schema,
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


