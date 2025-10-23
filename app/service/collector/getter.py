from app.core import logger
from app.service import GatewayService, fetch_test_result
from app.service.utils.utils import parse_html_test_result


async def get_tests_results(src_data: list, gateway_service: GatewayService ) -> list:
    result = src_data.copy()
    total_records = len(result)
    counter = 1
    for each in result:
        test_id = each.get("result_id", "")

        if test_id:
            test_result_raw = await fetch_test_result(test_id, gateway_service)
            test_result_html_content = test_result_raw.get("html")
            test_result_html_content_pure = await parse_html_test_result(test_result_html_content)
            each.update({"result": test_result_html_content_pure})
            logger.debug(f"запись {str(counter).zfill(2)}/{total_records}")
            counter += 1
        else:
            logger.warning("Не найден result_id")
    logger.info("Результаты исследований получены")
    return result