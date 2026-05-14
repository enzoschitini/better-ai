from src.web_services_network.api import API
from src.web_services_network.routes_pack import ROUTES

api = API()
app = api.initialize()
api.include_routers(ROUTES)
api.healthcheck()


# uvicorn web_services:app --reload