from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import init_gateway_client, shutdown_gateway_client, global_exception_handler, get_settings, logger
from app.route import health_router, collector_router, debug_router

settings =get_settings()
tags_metadata = []



@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_gateway_client(app)
    yield
    await shutdown_gateway_client(app)


app = FastAPI(
    tags=tags_metadata,
    title="E2S(mt): Шлюз Самсон <-> ЕВМИАС {dbase version}",
    description="""
    Основная задача сервиса — получать данные пациента из МИС «Самсон», 
    запрашивать у МИС «ЕВМИАС» сведения о его медицинских исследованиях (УЗИ, рентген, анализы и т.д.) 
    и возвращать их обратно в «Самсон» для отображения врачу. 
    
    Дополнительно подключена база данных для хранения результатов и 
    предоставления возможности работы, при отсутствии связи с ЕВМИАС.
    """,
    lifespan=lifespan,
    version="0.0.1"
)

# app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(collector_router)

if settings.DEBUG_MODE:
    logger.debug("ВКЛЮЧЕН РЕЖИМ ОТКЛАДКИ!")
    app.include_router(debug_router)
