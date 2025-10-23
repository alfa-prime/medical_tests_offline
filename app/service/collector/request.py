from app.core import logger
from app.model import RequestPeriod
from app.service import GatewayService


async def fetch_period_data(dates: RequestPeriod, gateway_service: GatewayService) -> list:
    # Получает список исследований за период
    payload = {
        "params": {"c": "Search", "m": "searchData"},
        "data": {
            "PersonPeriodicType_id": "1",
            "SearchFormType": "EvnUslugaPar",
            "EvnUslugaPar_setDate_Range": dates.date_range,
        }
    }
    logger.info(f"Начат процесс получения данных за период {dates.date_range}")
    response = await gateway_service.make_request(method="post", json=payload)
    logger.info("Данные получены")
    return response.get("data", [])



async def fetch_test_result(result_id: str, gateway_service: GatewayService) -> dict:
    # Получает результат исследований по id
    payload = {
        "params": {"c": "EvnXml", "m": "doLoadData"},
        "data": {"EvnXml_id": result_id}
    }

    response = await gateway_service.make_request(method="post", json=payload)
    return response
