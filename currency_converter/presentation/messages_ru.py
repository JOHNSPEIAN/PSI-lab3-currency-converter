"""All Russian texts shown to the user (FR-018). Code and API fields stay in English."""

from __future__ import annotations

from currency_converter.application.lookup import SourceKind

SOURCE_LABELS = {
    SourceKind.LIVE: "Национальный банк Молдовы",
    SourceKind.SAVED: "Сохранённая копия",
}

GENERIC_INVALID_INPUT = "Проверьте введённые данные."
GENERIC_SOURCE_ERROR = "Не удалось получить курсы Национального банка Молдовы."
BAD_REQUEST = "Некорректный запрос."
NOT_FOUND = "Не найдено."
INTERNAL = "Внутренняя ошибка приложения. Подробности записаны в журнал."

FIELD_MESSAGES = {
    "AMOUNT_EMPTY": "Введите сумму.",
    "AMOUNT_NOT_A_NUMBER": "Сумма должна быть числом, например 1500 или 1 500,50.",
    "AMOUNT_ZERO": "Сумма должна быть больше нуля.",
    "AMOUNT_NEGATIVE": "Сумма не может быть отрицательной.",
    "AMOUNT_TOO_MANY_DECIMALS": "Не больше {max_decimals} знаков после запятой.",
    "AMOUNT_TOO_LARGE": "Слишком большая сумма: максимум {maximum}.",
    "CURRENCY_EMPTY": "Выберите валюту.",
    "CURRENCY_INVALID": "Неизвестный код валюты.",
    "DATE_EMPTY": "Укажите дату курса.",
    "DATE_INVALID": "Некорректная дата. Формат: ДД.ММ.ГГГГ.",
    "DATE_TOO_EARLY": "Курсы доступны начиная с {earliest}.",
    "DATE_IN_FUTURE": "Курс на эту дату ещё не опубликован. Самая поздняя дата — {latest}.",
}

VALIDATION_SUMMARY = "Исправьте отмеченные поля — конвертация не выполнена."
CURRENCY_NOT_AVAILABLE = "Валюта {code} отсутствует в курсах НБМ на {date}."
