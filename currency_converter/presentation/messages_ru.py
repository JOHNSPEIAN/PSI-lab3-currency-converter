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
