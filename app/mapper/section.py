from dataclasses import dataclass

@dataclass(frozen=True)  # frozen=True делает объект неизменяемым
class Section:
    prefix: str
    name: str

sections = {
    "3010101000003272": Section(prefix="x-ray", name="Рентгеновское отделение ММЦ"),
    "3010101000003273": Section(prefix="tests", name="Клинико-диагностическая лаборатория ММЦЦ"),
    "3010101000003274": Section(prefix="ultra_sound", name="Отделение ультразвуковой диагностики стационар ММЦ"),
    "3010101000003275": Section(prefix="functional", name="Отделение функциональной диагностики ММЦ"),
}

