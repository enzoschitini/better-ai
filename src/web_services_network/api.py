import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware




class API:
    def get(self):
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

        return app