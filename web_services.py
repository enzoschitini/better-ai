from src.web_services_network.api import WebServiceAPI

web_service = WebServiceAPI()

app = web_service.initialize()

ROUTES = web_service.collect_routers(
    "src.web_services_network.routes"
)

web_service.include_routers(ROUTES)


# uvicorn web_services:app --reload