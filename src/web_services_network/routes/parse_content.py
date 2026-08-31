from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel

from src.web_services_network.utils.request_resource import RequestResorse, Authorization, LoadRequestFile
from src.content_parse.module.applications import DocumentParse

router = APIRouter(
    prefix="/parse-content",
    tags=["parse-content"]
)

@router.post("/document-parse", 
    summary="Parse and extract structured content from files using schema",
    description="This endpoint accepts a file along with metadata, a document schema, and optional configuration. It processes the file according to the provided schema and returns structured content based on the extracted information.",
    #dependencies=[Depends(Authorization.validate_api_key)]
)
async def document_parse(
    metadata: str = Form(..., title="Metadata", description="JSON string containing document metadata"),
    document_schema: str = Form(..., title="Document Schema", description="JSON schema used to structure extracted content"),
    file: UploadFile = File(..., title="Document File", description="Supported formats: txt, md, pdf, docx"),
    config: Optional[str] = Form(None, title="Config", description="Optional parser configuration as JSON string"),
):
    try:
        resource = RequestResorse()
        job_id = resource.job_id

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

        parsed_result = parser.run()
        content = parsed_result.get("content", parsed_result)

        response = resource.success_response(content)
        response["content"] = response.pop("result")

        return response

    except Exception as e:
        return resource.error_response(e)
