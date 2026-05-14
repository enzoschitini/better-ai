from src.web_services_network.api import API

api = API()
app = api.create()

# ================================================
# HEALTHCHECK
# ================================================

@app.get("/healthy")
def healthy():
    return {"status": "ok"}

# ================================================
# ROUTES
# ================================================

"""
from src.web_services_network.routes.chat_routes import router as chat_router
from src.web_services_network.routes.user_routes import router as user_router

app.include_router(chat_router)
app.include_router(user_router)
"""

# uvicorn web_services:app --reload