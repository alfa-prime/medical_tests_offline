from typing import Optional
from pydantic import BaseModel
from datetime import date

class TestResultResponse(BaseModel):
    prefix: Optional[str] = None
    last_name: str
    first_name: str
    middle_name: str
    birthday: date
    test_date: date
    test_code: str
    test_name: str
    test_result: Optional[str] = None



