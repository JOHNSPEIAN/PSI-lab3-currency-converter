"""Rate lookup use case: decides which rate table is used for a requested date."""

from __future__ import annotations

from datetime import date

from currency_converter.application.lookup import RateLookup, SourceKind
from currency_converter.ports import Clock, RateProvider


class RateService:
    def __init__(self, provider: RateProvider, clock: Clock) -> None:
        self._provider = provider
        self._clock = clock

    def lookup(self, requested_date: date) -> RateLookup:
        table = self._provider.fetch(requested_date)
        return RateLookup(table=table, requested_date=requested_date, source=SourceKind.LIVE)
