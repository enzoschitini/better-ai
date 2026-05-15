from fastapi import FastAPI, Header,  Depends, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel


app = FastAPI()

class Authorization:
    @staticmethod
    def _get_header_authorization(
        authorization: str = Header(...)
    ):
        print("Authorization Header:", authorization)

        # validação besta
        if not authorization:
            return {"valid": False}

        return {
            "valid": True,
            "token": authorization
        }


class RequestBody(BaseModel):
    message: str


@app.post("/test-authorization")
def healthy_authorization(
    body: RequestBody,
    auth=Depends(Authorization._get_header_authorization)
):
    return {
        "status": "ok",
        "authorization": auth,
        "message": body.message
    }

# uvicorn secrete_api:app --reload