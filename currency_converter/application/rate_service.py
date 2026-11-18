"""Rate lookup use case: decides which rate table is used for a requested date."""

from __future__ import annotations

import logging
from datetime import date, timedelta

from currency_converter.application.lookup import (
    Notice, NoticeKind, RateLookup, RatesUnavailableError, SavedCopyInfo, SourceKind,
)
from currency_converter.domain.calendar import (
    business_day_on_or_before, is_weekend, previous_business_day,
)
from currency_converter.domain.errors import (
    MalformedResponseError, NoRatesPublishedError, NoSavedCopyError, RatesNotFoundError,
    SourceUnavailableError,
)
from currency_converter.domain.models import RateTable, SavedCopy
from currency_converter.ports import Clock, RateCache, RateProvider

log = logging.getLogger(__name__)

MAX_FALLBACK_DAYS = 10


class RateService:
    def __init__(self, provider: RateProvider, cache: RateCache, clock: Clock,
                 max_fallback_days: int = MAX_FALLBACK_DAYS) -> None:
        self._provider = provider
        self._cache = cache
        self._clock = clock
        self._max_fallback_days = max_fallback_days

    def lookup(self, requested_date: date, *, use_saved: bool = False) -> RateLookup:
        if use_saved:
            return self._saved_lookup(requested_date)
        try:
            table = self._fetch_with_fallback(requested_date)
        except (SourceUnavailableError, MalformedResponseError) as exc:
            raise RatesUnavailableError(exc, self.saved_copy_info()) from exc
        self._save(table)
        return RateLookup(table=table, requested_date=requested_date, source=SourceKind.LIVE,
                          notices=self._notices(requested_date, table.rate_date))

    def _fetch_with_fallback(self, requested_date: date) -> RateTable:
        """Weekends go to the previous business day; unpublished dates step back (FR-011/012)."""
        earliest = requested_date - timedelta(days=self._max_fallback_days)
        candidate = business_day_on_or_before(requested_date)
        while candidate >= earliest:
            try:
                return self._provider.fetch(candidate)
            except NoRatesPublishedError:
                log.info("no rates published for %s, stepping back", candidate)
                candidate = previous_business_day(candidate)
        raise RatesNotFoundError(requested_date, earliest)

    def _notices(self, requested_date: date, used_date: date) -> tuple[Notice, ...]:
        if is_weekend(requested_date):
            return (Notice(NoticeKind.WEEKEND, requested_date, used_date),)
        if used_date != requested_date:
            kind = (NoticeKind.NOT_YET_PUBLISHED if requested_date > self._clock.today()
                    else NoticeKind.NOT_PUBLISHED)
            return (Notice(kind, requested_date, used_date),)
        return ()

    def saved_copy_info(self) -> SavedCopyInfo | None:
        copy = self._cache.load()
        return SavedCopyInfo(copy.table.rate_date, copy.saved_at) if copy else None

    def _saved_lookup(self, requested_date: date) -> RateLookup:
        copy = self._cache.load()
        if copy is None:
            raise NoSavedCopyError()
        notice = Notice(NoticeKind.SAVED_COPY, requested_date, copy.table.rate_date, copy.saved_at)
        return RateLookup(table=copy.table, requested_date=requested_date, source=SourceKind.SAVED,
                          saved_at=copy.saved_at, notices=(notice,))

    def _save(self, table: RateTable) -> None:
        copy = SavedCopy(table=table, saved_at=self._clock.now(), source_id=self._provider.source_id)
        try:
            self._cache.save(copy)
        except OSError as exc:  # a full disk must not break a successful conversion
            log.warning("could not save rates locally: %s", exc)
