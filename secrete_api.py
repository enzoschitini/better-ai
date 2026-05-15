from fastapi import FastAPI, Depends, Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Header esperado
api_key_scheme = APIKeyHeader(name="X-API-Key")


class Authorization:
    @staticmethod
    def _get_header_authorization(
        authorization: str = Header(...),
        user: str = Header(..., alias="user")
    ):
        print("Authorization Header:", authorization)
        print("User Header:", user)

        # validação besta
        if not authorization:
            return {"valid": False}

        return {
            "valid": True,
            "token": authorization
        }
    
    @staticmethod
    def validate_api_key(
        api_key: str = Security(api_key_scheme)
    ):
        expected_api_key = os.getenv("API_KEY")

        print("API KEY RECEBIDA:", api_key)
        print("API KEY ESPERADA:", expected_api_key)

        if api_key == expected_api_key:
            return True

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key"
        )


class RequestBody(BaseModel):
    message: str


@app.post("/test-authorization")
def healthy_authorization(
    body: RequestBody,
    auth=Depends(Authorization.validate_api_key)
):
    return {
        "status": "ok",
        "authorization": auth,
        "message": body.message
    }

# uvicorn secrete_api:app --reload