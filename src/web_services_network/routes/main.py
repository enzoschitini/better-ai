from fastapi import APIRouter, Depends
from pydantic import BaseModel
import time
import json
import traceback

from src.web_services_network.auth import Authorization

router = APIRouter(
    tags=["parses"]
)

class RequestResorse:
    def __init__(self):
        self.jobId = "12345"  # Simulate a job ID for tracking
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def _finalize(self):
        self.end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.duration = time.mktime(time.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")) - time.mktime(time.strptime(self.start_time, "%Y-%m-%d %H:%M:%S"))

    def success_response(self, result):
        self._finalize()
        return {
            "jobId": self.jobId,
            "status": "success",
            "status_code": 200,
            "result": result,
            "time": {
                "start": self.start_time,
                "end": self.end_time,
                "duration_seconds": self.duration
            }
        }
    
    def error_response(self, error):
        self._finalize()
        return {
            "jobId": self.jobId,
            "status": "error",
            "status_code": 500,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            },
            "time": {
                "start": self.start_time,
                "end": self.end_time,
                "duration_seconds": self.duration
            }
        }

class FakeParse:
    def __init__(self):
        pass

    def run(self):
        try:
            time.sleep(2)  # Simulate processing time
            #erro = 1 / 0 # Forçar um erro para testar o tratamento de exceções
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