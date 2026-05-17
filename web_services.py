from src.web_services_network.api import WebServiceAPI

from src.web_services_network.routes.main import router as MainRouter
from src.web_services_network.routes.chat_routes import router as chat_router
from src.web_services_network.routes.user_routes import router as user_router

web_service = WebServiceAPI()

app = web_service.initialize()
web_service._register_default_routes()

ROUTES = [
    MainRouter,
    chat_router,
    user_router
]

web_service.include_routers(ROUTES)



# uvicorn web_services:app --reload