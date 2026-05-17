from fastapi import APIRouter, Depends
from pydantic import BaseModel
import time
import json
import traceback

from src.web_services_network.auth import Authorization

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
        jobId = "12345"  # Simulate a job ID for tracking
        start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        parser = FakeParse()
        parse_result = parser.run()

        end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        duration = time.mktime(time.strptime(end_time, "%Y-%m-%d %H:%M:%S")) - time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M:%S"))

        response = {
            "jobId": jobId,
            "status": "success",
            "status_code": 200,
            "result": parse_result,
            "time": {
                "start": start_time,
                "end": end_time,
                "duration_seconds": duration
            }
        }

        print(json.dumps(response, indent=4))  # Log the response in a readable format

        return response

    except Exception as e:
        end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        duration = time.mktime(time.strptime(end_time, "%Y-%m-%d %H:%M:%S")) - time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M:%S"))

        response = {
            "jobId": jobId,
            "status": "error",
            "status_code": 500,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            },
            "time": {
                "start": start_time,
                "end": end_time,
                "duration_seconds": duration
            }
        }
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