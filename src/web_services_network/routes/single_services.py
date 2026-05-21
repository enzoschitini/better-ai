from fastapi import APIRouter, Depends
from pydantic import BaseModel
import time
import json

from src.web_services_network.utils.request_resource import RequestResorse, Authorization

router = APIRouter(
    tags=["parses"]
)
class FakeParse:
    def __init__(self):
        pass

    def run(self):
        try:
            time.sleep(2)  # Simulate processing time
            erro = 1 / 0 # Forçar um erro para testar o tratamento de exceções
            return {"message": "Documento processado"}
        except Exception as e:
            raise Exception(f"Erro ao processar o documento: {str(e)}")

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
        resource = RequestResorse()
        
        parser = FakeParse()
        parse_result = parser.run()

        response = resource.success_response(parse_result)
        print(json.dumps(response, indent=4))  # Log the response in a readable format

        return response

    except Exception as e:
        response = resource.error_response(e)
        print(json.dumps(response, indent=4))  # Log the response in a readable format

        return response

"""
curl -X POST "http://localhost:8000/document-parse" \
-H "Content-Type: application/json" \
-d '{
    "text": "Conteúdo do documento",
    "model": "gpt-4",
    "max_pages": 10
}'
"""