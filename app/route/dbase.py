from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorator import route_handle
from app.core.dependencies import get_session, get_api_key
from app.model import RequestByPatient
from app.service.dbase.find_patient import find_records_by_patient

router = APIRouter(prefix="/find", tags=["Find"], dependencies=[Depends(get_api_key)])


@router.post(
    "/patient",
    summary="Найти все исследования по данным пациента",
    description="Выполняет поиск по ФИО и дате рождения. Возвращает список всех найденных исследований.",
)
@route_handle
async def find_by_patient(
        patient_data: RequestByPatient,
        session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Ищет и возвращает все записи о результатах исследований для указанного пациента.
    """
    return await find_records_by_patient(patient_data, session)



