import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from src.web_services_network.auth import Authorization
from src.web_services_network.config import CONFIG

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

        @self.app.get(
            "/healthy-authorization",
            tags=["health"],
            dependencies=[Depends(Authorization.multikey)]
        )
        async def healthy_authorization():
            return {"status": "ok"}

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

