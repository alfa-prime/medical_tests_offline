from pydantic import BaseModel, Field
from typing import Dict, Any

class RequestParams(BaseModel):
    c: str = Field(..., description="Класс")
    m: str = Field(..., description="Метод")

class GatewayRequest(BaseModel):
    params: RequestParams
    data: Dict[str, Any]
