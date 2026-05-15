from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel


app = FastAPI()

class RequestBody(BaseModel):
    message: str

@app.post("/test-authorization")
def healthy_authorization(
    body: RequestBody,
    #auth=Depends(SecureAuthorization.validate)
):

    return {
        "status": "ok",
        #"client": auth["client"],
        #"project": auth["project"],
        "message": body.message
    }

# uvicorn secrete_api:app --reload