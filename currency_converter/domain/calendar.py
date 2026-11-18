"""Business-day arithmetic (Saturday and Sunday are non-business days)."""

from __future__ import annotations

from datetime import date, timedelta

_ONE_DAY = timedelta(days=1)


def is_weekend(day: date) -> bool:
    return day.weekday() >= 5


def business_day_on_or_before(day: date) -> date:
    while is_weekend(day):
        day -= _ONE_DAY
    return day


def previous_business_day(day: date) -> date:
    return business_day_on_or_before(day - _ONE_DAY)
