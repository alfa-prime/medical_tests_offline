from .health import router as health_router
from .dbase import router as collector_router
from .debug import router as debug_router
from .service import router as service_router

__all__ = [
    "health_router",
    "collector_router",
    "debug_router",
    "service_router"
]