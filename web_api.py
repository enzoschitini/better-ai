import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ================================================
# API SETTINGS
# ================================================

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(filename)s - line: %(lineno)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="BetterAI Chat API",
    description="""
API para interação com o agente de IA BetterAI 🤖
Permite o envio de mensagens e manutenção de contexto de sessão entre interações.
    """,
    version="1.0.0"
)

origins = [
    "https://better-ai.up.railway.app",
    "https://better-ai-homol.up.railway.app",
    "https://better-ai-dev.up.railway.app",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# ================================================
# HEALTHCHECK
# ================================================

@app.get("/healthy")
def healthy():
    return {"status": "ok"}

# ================================================
# ROUTES
# ================================================
from src.web_services_network.routes.chat_routes import router as chat_router
from src.web_services_network.routes.user_routes import router as user_router

app.include_router(chat_router)
app.include_router(user_router)

# uvicorn web_api:app --reload