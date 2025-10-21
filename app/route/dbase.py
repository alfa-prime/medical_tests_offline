from typing import Annotated

from fastapi import APIRouter, Depends

from app.core import get_gateway_service, get_api_key
from app.model import GatewayRequest
from app.service import GatewayService

router = APIRouter(prefix="/dbase", tags=["Work with dbase"], dependencies=[Depends(get_api_key)])


@router.post(
    "/gateway",
    summary="Проверка связи со шлюзом API",
    description="Отправляет тестовый запрос на API-шлюз для проверки связи и аутентификации."
)
async def check_gateway_connection(
        gateway_service: Annotated[GatewayService, Depends(get_gateway_service)]
):
    payload_dict = {
        "params": {"c": "Common", "m": "getCurrentDateTime"},
        "data": {"is_activerulles": "true"}
    }

    validated_payload = GatewayRequest.model_validate(payload_dict)

    response = await gateway_service.make_request(
        'post',
        json=validated_payload.model_dump()
    )

    return response
