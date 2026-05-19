from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel

from src.web_services_network.request_resource import RequestResorse, Authorization, LoadRequestFile
from src.content_parse.module.applications import DocumentParse

router = APIRouter(
    prefix="/parse-content",
    tags=["parse-content"]
)

@router.post("/document-parse", 
    summary="Parse and extract structured content from files using schema",
    #dependencies=[Depends(Authorization.validate_api_key)]
)
async def document_parse(
    job_id: str = Form(...),
    metadata: str = Form(...),
    document_schema: str = Form(...),
    file: UploadFile = File(...),
    config: Optional[str] = Form(None),
):
    try:
        resource = RequestResorse()

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
        result = {
            "job_id": job_id,
            "content": result
        }

        return resource.success_response(result)

    except Exception as e:
        return resource.error_response(e)

"""
curl --location 'http://localhost:8000/parse-content/document-parse' \
--header 'Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--header 'Client: BETTERAI' \
--header 'SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1' \
--form 'job_id="teste"' \
--form 'metadata="{\"value1\": \"value3\"}"' \
--form 'document_schema="{
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
