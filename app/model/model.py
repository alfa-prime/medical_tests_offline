from pydantic import BaseModel, Field, model_validator
from typing import Dict, Any, Optional
from datetime import datetime


class RequestParams(BaseModel):
    c: str = Field(..., description="Класс")
    m: str = Field(..., description="Метод")


class GatewayRequest(BaseModel):
    params: RequestParams
    data: Dict[str, Any]


class RequestPeriod(BaseModel):
    date_start: str = Field(..., description="Дата начала периода в формате DD.MM.YYYY", examples=["01.01.2025"])
    date_end: str = Field(..., description="Дата окончания периода в формате DD.MM.YYYY", examples=["17.01.2025"])
    date_range: Optional[str] = Field(None, description="Диапазон дат", examples = [""])


    @model_validator(mode="before") # noqa
    @classmethod
    def validate_and_format_date_range(cls, data: dict) -> dict:
        date_start = data.get("date_start")
        date_end = data.get("date_end")

        if date_start and date_end:
            try:
                start = datetime.strptime(date_start, "%d.%m.%Y")
                end = datetime.strptime(date_end, "%d.%m.%Y")

                if start > end:
                    raise ValueError("Дата начала не может быть позже даты окончания")

                data["date_range"] = f"{start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}"

            except ValueError as e:
                raise ValueError(f"Ошибка в диапазоне дат: {e}")
        return data