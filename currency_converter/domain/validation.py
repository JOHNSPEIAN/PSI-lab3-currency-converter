"""User input validation (FR-008). Produces typed field errors, never user-facing text."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Callable, TypeVar

from currency_converter.domain.errors import FieldError, ValidationError

AMOUNT_MAX = Decimal("1000000000000")
AMOUNT_MAX_DECIMALS = 4
MIN_RATE_DATE = date(2000, 1, 1)
MAX_DAYS_AHEAD = 1

_GROUP_SEPARATORS = "   "
# 1500 | 1 500 | 1500,5 | 1 500.50 | ,5 | -3 ; at least one digit is checked separately
_AMOUNT_RE = re.compile(r"[+-]?(?:\d{1,3}(?:[   ]\d{3})+|\d*)(?:[.,]\d*)?")
_ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_RU_DATE_RE = re.compile(r"\d{1,2}\.\d{1,2}\.\d{4}")
_CODE_RE = re.compile(r"[A-Z]{3}")

T = TypeVar("T")


def _fail(field: str, code: str, **params: object) -> ValidationError:
    return ValidationError([FieldError(field, code, params)])


class AmountParser:
    """Parses an amount typed by a person: '1 000,50', '1000.5', ',5'."""

    def __init__(self, maximum: Decimal = AMOUNT_MAX, max_decimals: int = AMOUNT_MAX_DECIMALS) -> None:
        self._maximum = maximum
        self._max_decimals = max_decimals

    def parse(self, text: str | None) -> Decimal:
        raw = (text or "").strip()
        if not raw:
            raise _fail("amount", "AMOUNT_EMPTY")
        if not _AMOUNT_RE.fullmatch(raw) or not any(ch.isdigit() for ch in raw):
            raise _fail("amount", "AMOUNT_NOT_A_NUMBER")
        normalized = raw.translate({ord(ch): None for ch in _GROUP_SEPARATORS}).replace(",", ".")
        if normalized.endswith("."):
            normalized = normalized[:-1]
        try:
            value = Decimal(normalized)
        except InvalidOperation:
            raise _fail("amount", "AMOUNT_NOT_A_NUMBER") from None
        if value == 0:
            raise _fail("amount", "AMOUNT_ZERO")
        if value < 0:
            raise _fail("amount", "AMOUNT_NEGATIVE")
        exponent = value.normalize().as_tuple().exponent
        decimals = -exponent if isinstance(exponent, int) and exponent < 0 else 0
        if decimals > self._max_decimals:
            raise _fail("amount", "AMOUNT_TOO_MANY_DECIMALS", max_decimals=self._max_decimals)
        if value > self._maximum:
            raise _fail("amount", "AMOUNT_TOO_LARGE", maximum=self._maximum)
        return value


class RateDateParser:
    """Accepts ISO dates (from the date picker) and DD.MM.YYYY; checks the allowed range."""

    def __init__(self, earliest: date = MIN_RATE_DATE, days_ahead: int = MAX_DAYS_AHEAD) -> None:
        self._earliest = earliest
        self._days_ahead = days_ahead

    def latest(self, today: date) -> date:
        return today + timedelta(days=self._days_ahead)

    def parse(self, text: str | None, today: date) -> date:
        raw = (text or "").strip()
        if not raw:
            raise _fail("date", "DATE_EMPTY")
        try:
            if _ISO_DATE_RE.fullmatch(raw):
                value = date.fromisoformat(raw)
            elif _RU_DATE_RE.fullmatch(raw):
                value = datetime.strptime(raw, "%d.%m.%Y").date()
            else:
                raise ValueError(raw)
        except ValueError:
            raise _fail("date", "DATE_INVALID") from None
        if value < self._earliest:
            raise _fail("date", "DATE_TOO_EARLY", earliest=self._earliest)
        latest = self.latest(today)
        if value > latest:
            raise _fail("date", "DATE_IN_FUTURE", latest=latest)
        return value


@dataclass(frozen=True)
class ConversionRequest:
    """A conversion request whose every field has been validated."""

    amount: Decimal
    source: str
    target: str
    rate_date: date


class ConversionRequestValidator:
    """Validates all fields at once so the user sees every problem in one go."""

    def __init__(
        self, amount_parser: AmountParser | None = None, date_parser: RateDateParser | None = None
    ) -> None:
        self._amounts = amount_parser or AmountParser()
        self._dates = date_parser or RateDateParser()

    def validate(
        self, amount: str | None, source: str | None, target: str | None,
        rate_date: str | None, today: date,
    ) -> ConversionRequest:
        errors: list[FieldError] = []
        value = self._collect(errors, lambda: self._amounts.parse(amount))
        source_code = self._collect(errors, lambda: self.currency_code("source", source))
        target_code = self._collect(errors, lambda: self.currency_code("target", target))
        day = self._collect(errors, lambda: self._dates.parse(rate_date, today))
        if errors:
            raise ValidationError(errors)
        return ConversionRequest(value, source_code, target_code, day)  # type: ignore[arg-type]

    def validate_date(self, rate_date: str | None, today: date) -> date:
        return self._dates.parse(rate_date, today)

    @staticmethod
    def currency_code(field: str, text: str | None) -> str:
        code = (text or "").strip().upper()
        if not code:
            raise _fail(field, "CURRENCY_EMPTY")
        if not _CODE_RE.fullmatch(code):
            raise _fail(field, "CURRENCY_INVALID")
        return code

    @staticmethod
    def _collect(errors: list[FieldError], parse: Callable[[], T]) -> T | None:
        try:
            return parse()
        except ValidationError as exc:
            errors.extend(exc.errors)
            return None
