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


import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


class WebServiceAPI:
    def __init__(self, config: dict = CONFIG):
        self.config = config
        self.logger = logging.getLogger("uvicorn.error")
        self.app: FastAPI | None = None

    def _show_cover(self):
        banner = self.config.get("banner", "")
        
        if banner:
            self.logger.info("\n%s", banner)

        self.logger.info(
            "%s v%s initialized successfully.",
            self.config.get("app_name", "API"),
            self.config.get("version", "1.0.0")
        )

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        self._show_cover()

        yield

        self.logger.info("Shutting down application...")

    def initialize(self) -> FastAPI:
        self.app = FastAPI(
            title=self.config.get("app_name", "API"),
            description=self.config.get("description", ""),
            version=self.config.get("version", "1.0.0"),
            lifespan=self._lifespan
        )

        self._setup_middlewares()
        self._register_default_routes()

        return self.app

    def _setup_middlewares(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.get("origins", ["*"]),
            allow_credentials=True,
            allow_methods=self.config.get("allowed_methods", ["*"]),
            allow_headers=self.config.get("allowed_headers", ["*"]),
        )

    def _register_default_routes(self):
        @self.app.get("/health", tags=["health"])
        async def health():
            return {
                "status": "ok",
                "app": self.config.get("app_name"),
                "version": self.config.get("version")
            }

        @self.app.get("/", tags=["root"])
        async def root():
            return {
                "message": f"{self.config.get('app_name')} is running"
            }

    def include_routers(self, routers: list):
        if not self.app:
            raise RuntimeError(
                "Application not initialized. Call initialize() first."
            )

        for router in routers:
            self.app.include_router(router)

            self.logger.info(
                "Router included: %s",
                getattr(router, "prefix", "no-prefix")
            )

    def get_app(self) -> FastAPI:
        if not self.app:
            raise RuntimeError(
                "Application not initialized. Call initialize() first."
            )

        return self.app
