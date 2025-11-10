from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

settings = get_settings()

# engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG_MODE, future=True)
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator:
    async with AsyncSession(engine) as session:
        yield session