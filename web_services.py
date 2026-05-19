from src.web_services_network.api import WebServiceAPI

web_service = WebServiceAPI()

app = web_service.initialize()
#web_service._register_default_routes()

ROUTES = web_service.collect_routers("src.web_services_network.routes")

web_service.include_routers(ROUTES)




# 1. Tipagem dos endpoints para facilitar a integração com outras linguagens e sistemas
# 2. Implementar suporte para documentação automática dos endpoints
# 3. Documentar os endpoints usando docstrings e as classes
# 4. Revisar o módulo


# uvicorn web_services:app --reload