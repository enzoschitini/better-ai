from src.web_services_network.api import API

from src.web_services_network.routes.main import router as main_router
from src.web_services_network.routes.chat_routes import router as chat_router
from src.web_services_network.routes.user_routes import router as user_router

api = API()
app = api.initialize()
api.healthcheck()

ROUTES = [
    main_router,
    chat_router,
    user_router
]

api.include_routers(ROUTES)



# uvicorn web_services:app --reload