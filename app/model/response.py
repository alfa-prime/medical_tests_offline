from typing import Optional
from pydantic import BaseModel
from datetime import date

class TestResultResponse(BaseModel):
    prefix: Optional[str] = None
    last_name: str
    first_name: str
    middle_name: str
    birthday: date
    service_date: date
    service_code: str
    service_name: str
    result: Optional[str] = None



