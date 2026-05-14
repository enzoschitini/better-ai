import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

CONFIG = {
    "app_name": "BetterAI Chat API",
    "description": """
    API para interação com o agente de IA BetterAI 🤖
    Permite o envio de mensagens e manutenção de contexto de sessão entre interações.
    """,
    "version": "1.0.0",
    "origins": [
        "https://better-ai.up.railway.app",
        "https://better-ai-homol.up.railway.app",
        "https://better-ai-dev.up.railway.app",
        "http://127.0.0.1:8000",
    ],
    "allowed_methods": ["GET", "POST"],
    "allowed_headers": ["Authorization", "Content-Type"],
}

class API:
    def create(self):
        app = FastAPI(
            title=CONFIG["app_name"],
            description=CONFIG["description"],
            version=CONFIG["version"]
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=CONFIG["origins"],
            allow_credentials=True,
            allow_methods=CONFIG["allowed_methods"],
            allow_headers=CONFIG["allowed_headers"],
        )

        self.app = app

        return app
    
    def include_routers(self, routers: list, app: FastAPI = None):
        if app is None:
            app = self.app
        for router in routers:
            app.include_router(router)