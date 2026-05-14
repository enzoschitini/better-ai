from src.web_services_network.routes.chat_routes import router as chat_router
from src.web_services_network.routes.user_routes import router as user_router

ROUTES = [
    chat_router,
    user_router
]