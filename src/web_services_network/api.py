import logging
import os
from fastapi import FastAPI, Header, HTTPException, Depends
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

    "banner": """
    \033[97m
    ╔═════════════════════════════════════════════════════════════════════════╗

        ██████╗ ███████╗████████╗████████╗███████╗██████╗      █████╗ ██╗ ✦
        ██╔══██╗██╔════╝╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗    ██╔══██╗██║
        ██████╔╝█████╗     ██║      ██║   █████╗  ██████╔╝    ███████║██║
        ██╔══██╗██╔══╝     ██║      ██║   ██╔══╝  ██╔══██╗    ██╔══██║██║
        ██████╔╝███████╗   ██║      ██║   ███████╗██║  ██║    ██║  ██║██║
        ╚═════╝ ╚══════╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝

    ╚═════════════════════════════════════════════════════════════════════════╝

                        ✦  Where intelligence finds purpose. ✦
    \033[0m
    """

}

class AuthService:
    @staticmethod
    def validate_betterai_key(authorization: str):
        back_end_api_key = os.getenv("BACK_END_API_KEY")

        if authorization != f"Bearer {back_end_api_key}":
            raise HTTPException(status_code=401, detail="Invalid Authorization Key")

    @staticmethod
    def validate_company_secret(client: str, secret_key: str):
        env_key_name = f"{client.upper()}_SECRET_KEY"
        secret_key_env = os.getenv(env_key_name)

        if secret_key_env is None:
            raise HTTPException(
                status_code=401,
                detail=f"Secret Key not found for client: {client}"
            )

        if secret_key != f"Bearer {secret_key_env}":
            raise HTTPException(status_code=401, detail="Invalid Company Secret Key")

class Authorization:
    @staticmethod
    def back_end_api_key(
        authorization: str = Header(...)
    ):
        AuthService.validate_betterai_key(authorization)
        return True

    @staticmethod
    def multikey(
        authorization: str = Header(...),
        client: str = Header(..., alias="Client"),
        secret_key: str = Header(..., alias="SecretKey"),
    ):
        # Valida chave master (BETTERAI_API_KEY)
        AuthService.validate_betterai_key(authorization)

        # Valida chave de empresa
        AuthService.validate_company_secret(client, secret_key)

        return True


class API:
    def __init__(self):
        self.logger = logging.getLogger("uvicorn.error")

    def _show_cover(self):
        self.logger.info(CONFIG["banner"])
        self.logger.info("Web services network initialized successfully.")

    def initialize(self):
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
        self._show_cover()

        return app
    
    def include_routers(self, routers: list):
        for router in routers:
            self.app.include_router(router)
    
    def healthcheck(self):
        @self.app.get("/healthy")
        def healthy():
            return {"status": "ok"}