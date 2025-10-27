from typing import Optional
from pydantic import BaseModel

class TestResultResponse(BaseModel):
    last_name: str
    first_name: str
    middle_name: str
    birthday: str
    service_date: str
    service_name: str
    service_code: str
    department_prefix: str
    result_id: str
    result: Optional[str] = None # Результат может отсутствовать или прийти с ошибкой
    prefix: Optional[str] = None


