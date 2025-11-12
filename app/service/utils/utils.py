import json
import re
from pathlib import Path
import htmlmin
from bs4 import BeautifulSoup
from datetime import date
from app.core import get_settings
import datetime

settings = get_settings()


def date_generator(year: int, month: int):
    """Создает генератор, который выдает по одному дню из заданного месяца и года"""
    if month == 12:
        next_month_date = datetime.date(year + 1, 1, 1)
    else:
        next_month_date = datetime.date(year, month + 1, 1)
    last_day_of_month = (next_month_date - datetime.timedelta(days=1)).day
    for day in range(1, last_day_of_month + 1):
        yield datetime.date(year, month, day)


def json_serial_date(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()  # Преобразуем дату в строку формата 'YYYY-MM-DD'
    raise TypeError(f"Type {type(obj)} not serializable")


def save_json(filename: str, data: list | dict):
    debug_folder = Path(settings.FOLDER_DEBUG)
    debug_folder.mkdir(parents=True, exist_ok=True)
    file_path = debug_folder / filename

    with open(file_path, "w", encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False, default=json_serial_date)  # noqa


async def parse_html_test_result(html_raw: str) -> str:
    """Очищает HTML-код результата теста от лишних тегов и стилей."""
    soup = BeautifulSoup(html_raw, "lxml")

    # Удаляем ненужные теги
    for tag in soup(["script", "style", "form", "meta"]):
        tag.decompose()

    # Удаляем div'ы с классами, которые не несут полезной информации
    for tag in soup.find_all("div", class_=["parametervalue", "combobox-parameter", "input-area"]):
        tag.decompose()

    # "Разворачиваем" теги без атрибутов
    for tag in soup.find_all(["span", "div"]):
        if not tag.attrs:
            tag.unwrap()

    # Удаляем все атрибуты, кроме базовых
    for tag in soup.find_all(True):
        tag.attrs = {k: v for k, v in tag.attrs.items() if k not in ["style", "class", "id", "data-mce-style"]}

    html_code = soup.prettify()
    # Минимизируем и очищаем HTML
    html_code = re.sub(r"\n\s*\n", "\n", html_code).strip()
    html_code = htmlmin.minify(html_code, remove_empty_space=True)
    return html_code
