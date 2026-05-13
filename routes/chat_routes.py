from fastapi import APIRouter

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.post("/")
def send_message():
    return {"message": "Mensagem enviada"}