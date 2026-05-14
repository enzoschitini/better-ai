from fastapi import APIRouter

router = APIRouter(
    #prefix="/",
    tags=["embedding"]
)

@router.post("/embedding")
def send_message():
    return {"message": "Mensagem enviada"}