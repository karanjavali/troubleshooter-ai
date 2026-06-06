from fastapi import FastAPI

from app.api.troubleshoot import router as troubleshoot_router
from app.api.confluence import router as confluence_router
from app.api.health import router as health_router

app = FastAPI(title="Troubleshooter Assistant", version="1.0.0")

app.include_router(troubleshoot_router)
app.include_router(confluence_router)
app.include_router(health_router)
