from dataclasses import dataclass


@dataclass(frozen=True)  # frozen=True делает объект неизменяемым
class Department:
    id: str
    prefix: str
    name: str


DEPARTMENTS = (
    Department(id="3010101000003272", prefix="x-ray", name="Рентгеновское отделение ММЦ"),
    Department(id="3010101000003273", prefix="tests", name="Клинико-диагностическая лаборатория ММЦЦ"),
    Department(id="3010101000003274", prefix="ultra_sound", name="Отделение ультразвуковой диагностики стационар ММЦ"),
    Department(id="3010101000003275", prefix="functional", name="Отделение функциональной диагностики ММЦ"),
)
