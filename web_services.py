from src.web_services_network.api import WebServiceAPI

web_service = WebServiceAPI()

app = web_service.initialize()

ROUTES = web_service.collect_routers(
    "src.web_services_network.routes"
)

from src.web_services_network.routes.agents import router as Agents

#web_service.include_routers(ROUTES)
web_service.test_routers([Agents])

# uvicorn web_services:app --reload