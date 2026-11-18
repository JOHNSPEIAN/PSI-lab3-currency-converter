"""Ports: the small interfaces the application depends on (Dependency Inversion).

Each protocol has exactly one responsibility (Interface Segregation); adapters in
``currency_converter.adapters`` implement them and are wired in ``bootstrap.py``.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol

from currency_converter.domain.models import RateTable, SavedCopy


class Clock(Protocol):
    def today(self) -> date: ...

    def now(self) -> datetime: ...


class HttpClient(Protocol):
    def get(self, url: str) -> bytes:
        """Return the response body; raise SourceUnavailableError on any transport failure."""
        ...


class RateTableParser(Protocol):
    def parse(self, payload: bytes, requested_date: date) -> RateTable:
        """Raise NoRatesPublishedError for an empty answer, MalformedResponseError if broken."""
        ...


class RateProvider(Protocol):
    @property
    def source_id(self) -> str: ...

    def fetch(self, rate_date: date) -> RateTable:
        """Rates for exactly this date; raises RateSourceError subclasses."""
        ...


class RateCache(Protocol):
    def load(self) -> SavedCopy | None:
        """The saved copy, or None when there is none or it is unreadable."""
        ...

    def save(self, copy: SavedCopy) -> None:
        """Persist the copy; may raise OSError."""
        ...


class BrowserLauncher(Protocol):
    def open(self, url: str) -> bool:
        """Open the URL; return False when this launcher could not do it."""
        ...
