"""Shared fakes and fixtures. Tests never touch the network: every port has an in-memory fake."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable, Iterable

import pytest

from currency_converter.domain.errors import NoRatesPublishedError
from currency_converter.domain.models import Currency, ExchangeRate, RateTable, SavedCopy

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def make_table(rate_date: date, rates: Iterable[tuple[str, int, str]] | None = None) -> RateTable:
    """A small rate table: (code, nominal, MDL value for the nominal)."""
    rates = rates or [("USD", 1, "18.3383"), ("EUR", 1, "20.1538"), ("HUF", 100, "5.5244")]
    return RateTable(rate_date, tuple(
        ExchangeRate(Currency(code, f"name of {code}"), nominal, Decimal(value))
        for code, nominal, value in rates
    ))


class FakeClock:
    def __init__(self, now: datetime = datetime(2026, 11, 18, 12, 0, 0)) -> None:
        self.current = now

    def today(self) -> date:
        return self.current.date()

    def now(self) -> datetime:
        return self.current


class FakeProvider:
    """Answers from a dict date -> RateTable | Exception; dates not in the dict are "not published"."""

    source_id = "fake"

    def __init__(self, answers: dict[date, RateTable | Exception] | None = None,
                 default: Callable[[date], RateTable] | Exception | None = None) -> None:
        self.answers = answers or {}
        self.default = default
        self.calls: list[date] = []

    def fetch(self, rate_date: date) -> RateTable:
        self.calls.append(rate_date)
        answer = self.answers.get(rate_date, self.default)
        if answer is None:
            raise NoRatesPublishedError(rate_date)
        if isinstance(answer, Exception):
            raise answer
        if callable(answer):
            return answer(rate_date)
        return answer


class InMemoryCache:
    def __init__(self, copy: SavedCopy | None = None, fail_on_save: bool = False) -> None:
        self.copy = copy
        self.fail_on_save = fail_on_save
        self.saves = 0

    def load(self) -> SavedCopy | None:
        return self.copy

    def save(self, copy: SavedCopy) -> None:
        if self.fail_on_save:
            raise OSError("disk full")
        self.saves += 1
        self.copy = copy


class FakeHttpClient:
    def __init__(self, payload: bytes = b"", error: Exception | None = None) -> None:
        self.payload = payload
        self.error = error
        self.urls: list[str] = []

    def get(self, url: str) -> bytes:
        self.urls.append(url)
        if self.error:
            raise self.error
        return self.payload


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def table() -> RateTable:
    return make_table(date(2026, 11, 18))
