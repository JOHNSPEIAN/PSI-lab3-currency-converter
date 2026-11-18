"""Core entities. Immutable, Decimal-based, free of I/O."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from currency_converter.domain.errors import CurrencyNotAvailableError

_CODE_RE = re.compile(r"[A-Z]{3}")


@dataclass(frozen=True)
class Currency:
    code: str
    name: str

    def __post_init__(self) -> None:
        if not _CODE_RE.fullmatch(self.code):
            raise ValueError(f"invalid currency code: {self.code!r}")


MDL = Currency("MDL", "Молдавский лей")
"""Base currency of the National Bank of Moldova; every rate is expressed in MDL."""


@dataclass(frozen=True)
class ExchangeRate:
    """``value`` MDL are paid for ``nominal`` units of ``currency``."""

    currency: Currency
    nominal: int
    value: Decimal

    def __post_init__(self) -> None:
        if self.nominal <= 0:
            raise ValueError(f"nominal must be positive: {self.nominal}")
        if not self.value.is_finite() or self.value <= 0:
            raise ValueError(f"rate value must be positive: {self.value}")

    @property
    def per_unit(self) -> Decimal:
        """MDL for one unit of the currency."""
        return self.value / Decimal(self.nominal)


@dataclass(frozen=True)
class RateTable:
    """All rates published for one date. MDL is implicit and always available."""

    rate_date: date
    rates: tuple[ExchangeRate, ...]
    _index: dict[str, ExchangeRate] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.rates:
            raise ValueError("a rate table needs at least one rate")
        index: dict[str, ExchangeRate] = {}
        for rate in self.rates:
            code = rate.currency.code
            if code == MDL.code:
                raise ValueError("MDL is the base currency and must not be listed")
            if code in index:
                raise ValueError(f"duplicate currency {code}")
            index[code] = rate
        object.__setattr__(self, "_index", index)

    def currencies(self) -> tuple[Currency, ...]:
        """MDL first, then all quoted currencies sorted by code."""
        quoted = sorted((r.currency for r in self.rates), key=lambda c: c.code)
        return (MDL, *quoted)

    def rate_for(self, code: str) -> ExchangeRate | None:
        return self._index.get(code)

    def find(self, code: str) -> Currency:
        if code == MDL.code:
            return MDL
        rate = self._index.get(code)
        if rate is None:
            raise CurrencyNotAvailableError(code, self.rate_date)
        return rate.currency

    def per_unit(self, code: str) -> Decimal:
        """MDL for one unit of ``code`` (1 for MDL itself)."""
        if code == MDL.code:
            return Decimal(1)
        rate = self._index.get(code)
        if rate is None:
            raise CurrencyNotAvailableError(code, self.rate_date)
        return rate.per_unit


@dataclass(frozen=True)
class SavedCopy:
    """The last successful source response, kept locally for offline work."""

    table: RateTable
    saved_at: datetime
    source_id: str
