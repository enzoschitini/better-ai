from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.web_services_network.auth import Authorization

router = APIRouter(
    tags=["parses"]
)

class FakeParse:
    def __init__(self):
        pass

    def run(self):
        return {"message": "Documento processado"}

class DocumentParseRequest(BaseModel):
    text: str
    model: str
    max_pages: int

@router.post(
    "/document-parse",
    summary="Parse a document",
    #dependencies=[Depends(Authorization.validate_api_key)],
)
def parse_document(body: DocumentParseRequest):
    try:
        erro = 1 / 0
        parser = FakeParse()
        response = parser.run()
        return response

    except Exception as e:
        return {"error": str(e)}