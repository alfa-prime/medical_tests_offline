from .health import router as health_router
from .collector import router as collector_router
from .debug import router as debug_router

__all__ = [
    "health_router",
    "collector_router",
    "debug_router"
]