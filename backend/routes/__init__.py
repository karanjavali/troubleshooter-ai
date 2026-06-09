"""Routes package"""
from .troubleshoot import router as troubleshoot_router
from .sync import router as sync_router
from .health import router as health_router

__all__ = ["troubleshoot_router", "sync_router", "health_router"]