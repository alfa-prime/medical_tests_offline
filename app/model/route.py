from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Dict, Any, Optional
import datetime


class RequestParams(BaseModel):
    c: str = Field(..., description="Класс")
    m: str = Field(..., description="Метод")


class GatewayRequest(BaseModel):
    params: RequestParams
    data: Dict[str, Any]


class RequestPeriod(BaseModel):
    date_start: str = Field(..., description="Дата начала периода в формате DD.MM.YYYY", examples=["02.01.2025"])
    date_end: str = Field(..., description="Дата окончания периода в формате DD.MM.YYYY", examples=["02.01.2025"])
    date_range: Optional[str] = Field(None, description="Диапазон дат", examples=[""])

    @model_validator(mode="before")  # noqa
    @classmethod
    def validate_and_format_date_range(cls, data: dict) -> dict:
        date_start = data.get("date_start")
        date_end = data.get("date_end")

        if date_start and date_end:
            try:
                start = datetime.datetime.strptime(date_start, "%d.%m.%Y")
                end = datetime.datetime.strptime(date_end, "%d.%m.%Y")

                if start > end:
                    raise ValueError("Дата начала не может быть позже даты окончания")

                data["date_range"] = f"{start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}"

            except ValueError as e:
                raise ValueError(f"Ошибка в диапазоне дат: {e}")
        return data


class RequestByDay(BaseModel):
    """Модель запроса по дню с валидацией даты."""
    date: str = Field(..., description="Дата в формате ДД.ММ.ГГГГ", examples=["02.01.2025"])

    @field_validator('date')  # noqa
    @classmethod
    def check_date_is_valid(cls, v: str):
        """Проверяет, что строка является корректной датой в формате ДД.ММ.ГГГГ."""
        try:
            datetime.datetime.strptime(v, '%d.%m.%Y')
        except ValueError:
            raise ValueError("Неверный формат даты, ожидается ДД.ММ.ГГГГ")
        return v


class RequestByMonth(BaseModel):
    """Модель для запроса по месяцам"""
    year: int = Field(..., ge=2022, le=2030, description="Год в формате ГГГГ", examples=[2024])
    month: int = Field(..., ge=1, le=12, description="Номер месяца (от 1 до 12)", examples=[1])


class RequestByPatient(BaseModel):
    """Модель для поиска записей по данным пациента."""
    last_name: str = Field(..., description="Фамилия", examples=["Хайбулина"])
    first_name: str = Field(..., description="Имя", examples=["Надежда"])
    middle_name: str | None = Field(default=None, description="Отчество (необязательно)", examples=["Олеговна"])
    # birthday: datetime.date = Field(..., description="Дата рождения в формате ГГГГ-ММ-ДД", examples=["1967-03-15"])
    birthday: str = Field(..., description="Дата рождения в формате ДД.ММ.ГГГГ", examples=["15.03.1967"])

    @field_validator('birthday') # noqa
    @staticmethod
    def validate_birthday_format(v: str) -> str:
        try:
            datetime.datetime.strptime(v, '%d.%m.%Y')
        except ValueError:
            raise ValueError("Неверный формат даты. Ожидается ДД.ММ.ГГГГ")
        return v
