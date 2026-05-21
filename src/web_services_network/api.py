import logging
import time
import os
import importlib
import pkgutil

from dotenv import load_dotenv
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from src.web_services_network.utils.auth import Authorization
from src.web_services_network.config import CONFIG

load_dotenv()

class WebServiceAPI:
    """
    This class serves as a configurable FastAPI web service wrapper, handling initialization,
    middleware setup, default routes registration, and dynamic router inclusion.
    It also logs important runtime information such as banner, app version, and domain.

    Args:
        config (dict): Configuration settings for the web service API. Default is CONFIG.

    Methods:
        initialize(): Creates and configures the FastAPI application instance.
        include_routers(routers): Adds a list of routers to the FastAPI app after initialization.
        test_routers(routers): Similar to include_routers, allows testing or adding routers.
        collect_routers(package_name): Dynamically discovers and collects routers from a package.
        get_app(): Returns the initialized FastAPI application instance.
    """
    def __init__(self, config: dict = CONFIG):
        self.config = config
        self.logger = logging.getLogger("uvicorn.error")
        self.app: FastAPI | None = None
        self.domain = os.getenv("DOMAIN", "http://localhost:8000")

    def _show_cover(self):
        """
        Logs the application start-up banner and key information such as app name,
        initialization time, version, domain, and API documentation URL.
        """
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        banner = self.config.get("banner", "")
        
        if banner:
            self.logger.info("\n%s", banner)
        
        self.logger.info(f"{self.config.get("app_name", "API")} initialized successfully at {current_time}.")
        self.logger.info(f"Version: {self.config.get('version', '1.0.0')}")
        self.logger.info(f"Domain: {self.domain}")
        self.logger.info(f"Documentation available at: {self.domain}/docs")

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """
        Manages startup and shutdown lifecycle events of the FastAPI application by
        displaying the app banner on startup and logging shutdown message on exit.

        Args: 
            app (FastAPI): The FastAPI app instance.

        Yields:
            None
        """
        self._show_cover()

        yield

        self.logger.info("Shutting down application...")

    def initialize(self) -> FastAPI:
        """
        Initializes the FastAPI application by configuring its title, description, version,
        lifespan handler, CORS middleware, and default routes.

        Returns:
            FastAPI: The initialized FastAPI app instance.
        """
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
        """
        Configures the CORS middleware for the FastAPI application using settings from config.
        """
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.get("origins", ["*"]),
            allow_credentials=True,
            allow_methods=self.config.get("allowed_methods", ["*"]),
            allow_headers=self.config.get("allowed_headers", ["*"]),
        )

    def _register_default_routes(self):
        """
        Registers default health check and root routes to the FastAPI application,
        including a health authorization route protected by API key dependency.
        """
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
            "/health-authorization",
            tags=["health"],
            dependencies=[Depends(Authorization.validate_api_key)]
        )
        async def healthy_authorization():
            return {"status": "ok"}

    def include_routers(self, routers: list):
        """
        Includes a list of FastAPI routers into the initialized application instance.
        Logs each router inclusion by its prefix.

        Args:
            routers (list): List of FastAPI router instances to be included.

        Raises:
            RuntimeError: If the application is not initialized prior to including routers.
        """
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

    def test_routers(self, routers: list):
        """
        Includes routers similarly to include_routers, intended possibly for testing purposes.
        Logs each router inclusion by its prefix.

        Args:
            routers (list): List of FastAPI router instances to be included for testing.

        Raises:
            RuntimeError: If the application is not initialized prior to including routers.
        """
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

    def collect_routers(self, package_name: str):
        """
        Dynamically imports and collects router objects named 'router' from all modules in the specified package.

        Args:
            package_name (str): The dotted path of the package to search for routers.

        Returns:
            list: A list of router instances discovered in the package modules.
        """
        routers = []

        package = importlib.import_module(package_name)

        for _, module_name, is_pkg in pkgutil.walk_packages(
            package.__path__,
            package.__name__ + "."
        ):
            if is_pkg:
                continue

            module = importlib.import_module(module_name)
            router = getattr(module, "router", None)

            if router:
                routers.append(router)

        return routers

    def get_app(self) -> FastAPI:
        """
        Retrieves the initialized FastAPI application instance.

        Returns:
            FastAPI: The initialized FastAPI app.

        Raises:
            RuntimeError: If requested before the application is initialized.
        """
        if not self.app:
            raise RuntimeError(
                "Application not initialized. Call initialize() first."
            )

        return self.app

"""
curl --location 'http://localhost:8000/health'

curl --location 'http://localhost:8000/health-authorization' \
--header 'X-API-Key: betterai-dev'
"""
