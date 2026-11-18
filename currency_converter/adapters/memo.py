"""In-memory memo in front of any RateProvider (Decorator: no change to the wrapped provider)."""

from __future__ import annotations

import threading
from collections import OrderedDict
from datetime import date, datetime, timedelta

from currency_converter.domain.models import RateTable
from currency_converter.ports import Clock, RateProvider

DEFAULT_TTL = timedelta(minutes=30)


class MemoizingRateProvider:
    """Remembers successful answers only; "not published" is never memoised (research R6)."""

    def __init__(self, inner: RateProvider, clock: Clock, ttl: timedelta = DEFAULT_TTL,
                 max_entries: int = 64) -> None:
        self._inner = inner
        self._clock = clock
        self._ttl = ttl
        self._max_entries = max_entries
        self._entries: OrderedDict[date, tuple[datetime, RateTable]] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def source_id(self) -> str:
        return self._inner.source_id

    def fetch(self, rate_date: date) -> RateTable:
        now = self._clock.now()
        with self._lock:
            entry = self._entries.get(rate_date)
            if entry is not None and now - entry[0] < self._ttl:
                self._entries.move_to_end(rate_date)
                return entry[1]
        table = self._inner.fetch(rate_date)  # outside the lock: slow network must not block others
        with self._lock:
            self._entries[rate_date] = (now, table)
            self._entries.move_to_end(rate_date)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)
        return table
