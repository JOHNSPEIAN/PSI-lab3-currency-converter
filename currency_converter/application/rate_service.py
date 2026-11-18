"""Rate lookup use case: decides which rate table is used for a requested date."""

from __future__ import annotations

import logging
from datetime import date

from currency_converter.application.lookup import (
    Notice, NoticeKind, RateLookup, RatesUnavailableError, SavedCopyInfo, SourceKind,
)
from currency_converter.domain.errors import (
    MalformedResponseError, NoSavedCopyError, SourceUnavailableError,
)
from currency_converter.domain.models import RateTable, SavedCopy
from currency_converter.ports import Clock, RateCache, RateProvider

log = logging.getLogger(__name__)


class RateService:
    def __init__(self, provider: RateProvider, cache: RateCache, clock: Clock) -> None:
        self._provider = provider
        self._cache = cache
        self._clock = clock

    def lookup(self, requested_date: date, *, use_saved: bool = False) -> RateLookup:
        if use_saved:
            return self._saved_lookup(requested_date)
        try:
            table = self._provider.fetch(requested_date)
        except (SourceUnavailableError, MalformedResponseError) as exc:
            raise RatesUnavailableError(exc, self.saved_copy_info()) from exc
        self._save(table)
        return RateLookup(table=table, requested_date=requested_date, source=SourceKind.LIVE)

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
