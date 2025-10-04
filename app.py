from fastapi import FastAPI, UploadFile, HTTPException, Request, Form, Depends, Header, File
from pydantic import BaseModel

app = FastAPI() 
# uvicorn app:app --reload
# http://127.0.0.1:8000

def get_authorization_betterai_api(authorization: str = Header(...)):
    if authorization != "Bearer betterai-api-key":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return authorization

class CiSei(BaseModel):
    message: str
    valore: int

@app.post("/ci-sei", dependencies=[Depends(get_authorization_betterai_api)])
def ci_sei(request: CiSei):
    result = request.valore * 2 + 1
    return {"message": request.message, "result": result}

"""
curl -X POST "http://127.0.0.1:8000/ci-sei" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer betterai-api-key" \
  -d '{
    "message": "Olá, estou aqui!",
    "valore": 21
  }'
"""


# ✅ Endpoint health check
"""
curl -X GET "http://127.0.0.1:8000/healthy"

curl -X GET "http://127.0.0.1:8000/healthy-authorization" \
  -H "Authorization: Bearer betterai-api-key"
"""

@app.get("/healthy")
def healthy():
    return {"status": "ok"}

@app.get("/healthy-authorization", dependencies=[Depends(get_authorization_betterai_api)])
def healthy_authorization():
    return {"status": "ok"}



