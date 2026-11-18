"""Use-case facade for the delivery layer: validate → look up rates → convert."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from currency_converter.application.lookup import RateLookup
from currency_converter.domain.conversion import Conversion, CurrencyConverter
from currency_converter.domain.validation import ConversionRequestValidator
from currency_converter.ports import Clock


class RateLookupService(Protocol):
    def lookup(self, requested_date: date) -> RateLookup: ...


@dataclass(frozen=True)
class ConversionOutcome:
    conversion: Conversion
    lookup: RateLookup


class ConverterService:
    def __init__(self, rates: RateLookupService, converter: CurrencyConverter,
                 validator: ConversionRequestValidator, clock: Clock) -> None:
        self._rates = rates
        self._converter = converter
        self._validator = validator
        self._clock = clock

    def rates(self, rate_date: str | None) -> RateLookup:
        today = self._clock.today()
        day = self._validator.validate_date(rate_date, today) if rate_date else today
        return self._rates.lookup(day)

    def convert(self, amount: str | None, source: str | None, target: str | None,
                rate_date: str | None) -> ConversionOutcome:
        request = self._validator.validate(amount, source, target, rate_date, self._clock.today())
        lookup = self._rates.lookup(request.rate_date)
        conversion = self._converter.convert(request.amount, request.source, request.target,
                                             lookup.table)
        return ConversionOutcome(conversion, lookup)
