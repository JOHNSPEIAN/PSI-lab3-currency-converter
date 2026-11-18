"""Clock adapter backed by the computer's local time."""

from __future__ import annotations

from datetime import date, datetime


class SystemClock:
    def today(self) -> date:
        return date.today()

    def now(self) -> datetime:
        return datetime.now().replace(microsecond=0)
