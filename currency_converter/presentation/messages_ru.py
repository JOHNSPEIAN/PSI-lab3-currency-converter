"""All Russian texts shown to the user (FR-018). Code and API fields stay in English."""

from __future__ import annotations

from currency_converter.application.lookup import SourceKind

SOURCE_LABELS = {
    SourceKind.LIVE: "Национальный банк Молдовы",
    SourceKind.SAVED: "Сохранённая копия",
}

GENERIC_INVALID_INPUT = "Проверьте введённые данные."
GENERIC_SOURCE_ERROR = "Не удалось получить курсы Национального банка Молдовы."
SOURCE_NETWORK = "Нет связи с Национальным банком Молдовы."
SOURCE_MALFORMED = "Национальный банк Молдовы вернул некорректный ответ."
OFFER_SAVED_COPY = "Можно продолжить с сохранённым курсом от {rate_date} (сохранён {saved_at})."
NO_SAVED_COPY_YET = "Сохранённых курсов пока нет — проверьте подключение к интернету и повторите попытку."
NO_SAVED_COPY = "Сохранённых курсов пока нет: нужен хотя бы один успешный запрос к НБМ."
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

RATES_NOT_FOUND = "НБМ не публиковал курсы с {earliest} по {requested}. Выберите другую дату."

WEEKDAYS = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")

NOTICE_MESSAGES = {
    "weekend": "{requested} — {weekday}: в выходные НБМ не публикует курс. "
               "Используется курс последнего рабочего дня — {used}.",
    "not_published": "Курс на {requested} не опубликован (праздник или нерабочий день НБМ). "
                     "Используется последний доступный курс — от {used}.",
    "not_yet_published": "Курс на {requested} ещё не опубликован — НБМ обычно публикует его после "
                         "13:00 по времени Кишинёва. Используется последний доступный курс — от {used}.",
    "saved_copy": "Используется сохранённая копия курса от {used} (сохранена {saved_at}). "
                  "Это не актуальные данные НБМ.",
}
