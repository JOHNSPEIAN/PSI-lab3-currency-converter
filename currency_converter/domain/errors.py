"""Typed errors. Each one is turned into a user message by the presentation layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Mapping, Sequence


class ConverterError(Exception):
    """Base class for every expected (non-bug) failure of the application."""


@dataclass(frozen=True)
class FieldError:
    """One invalid input field: which field, a machine-readable code and message parameters."""

    field: str
    code: str
    params: Mapping[str, Any] = field(default_factory=dict)


class ValidationError(ConverterError):
    def __init__(self, errors: Sequence[FieldError]) -> None:
        if not errors:
            raise ValueError("ValidationError needs at least one FieldError")
        self.errors: tuple[FieldError, ...] = tuple(errors)
        super().__init__("; ".join(f"{e.field}: {e.code}" for e in self.errors))


class CurrencyNotAvailableError(ConverterError):
    def __init__(self, code: str, rate_date: date) -> None:
        self.code = code
        self.rate_date = rate_date
        super().__init__(f"currency {code} is not quoted on {rate_date.isoformat()}")


class RateSourceError(ConverterError):
    """The rate source could not provide a usable rate table."""


class SourceUnavailableError(RateSourceError):
    """Network failure, timeout or HTTP error status."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"rate source unavailable: {reason}")


class MalformedResponseError(RateSourceError):
    """The source answered, but the answer cannot be understood."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"malformed rate source response: {reason}")


class NoRatesPublishedError(RateSourceError):
    """The source has no rates for the date (empty answer or no currencies)."""

    def __init__(self, rate_date: date) -> None:
        self.rate_date = rate_date
        super().__init__(f"no rates published for {rate_date.isoformat()}")


class RatesNotFoundError(RateSourceError):
    """No date in the fallback window had published rates."""

    def __init__(self, requested_date: date, earliest_tried: date) -> None:
        self.requested_date = requested_date
        self.earliest_tried = earliest_tried
        super().__init__(
            f"no rates between {earliest_tried.isoformat()} and {requested_date.isoformat()}"
        )


class NoSavedCopyError(RateSourceError):
    """Saved rates were requested, but nothing has been saved yet."""

    def __init__(self) -> None:
        super().__init__("no saved copy of the rates")
