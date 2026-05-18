from src.web_services_network.api import WebServiceAPI

from src.web_services_network.routes.main import router as MainRouter
from src.web_services_network.routes.davinci import router as DavinciRouter
from src.web_services_network.routes.deep_research import router as DeepResearchRouter
from src.web_services_network.routes.parse_content import router as ParseContentRouter

web_service = WebServiceAPI()

app = web_service.initialize()
#web_service._register_default_routes()

ROUTES = [
    MainRouter,
    DavinciRouter,
    DeepResearchRouter,
    ParseContentRouter
]

web_service.include_routers(ROUTES)



# uvicorn web_services:app --reload