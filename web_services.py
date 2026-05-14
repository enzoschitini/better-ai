from src.web_services_network.api import API
from src.web_services_network.routes_pack import ROUTES

api = API()
app = api.create()
api.include_routers(ROUTES)


# ================================================
# HEALTHCHECK
# ================================================

@app.get("/healthy")
def healthy():
    return {"status": "ok"}


# uvicorn web_services:app --reload