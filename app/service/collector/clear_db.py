from sqlmodel import SQLModel
from fastapi import HTTPException, status
from app.core.database import engine
from app.core.logger_setup import logger


async def reset_entire_database():
    """Очищает все таблицы в БД"""
    try:
        logger.warning("Attempting to reset the entire database...")
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)

        message = "The entire database has been successfully reset."
        logger.info(message)
        return {"status": "ok", "message": message}
    except Exception as e:
        logger.error(f"Failed to reset the database: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not reset the database due to an error."
        )
