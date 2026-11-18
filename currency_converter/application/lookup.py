"""Result objects of a rate lookup: where the rates came from and what the user must be told."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from currency_converter.domain.errors import ConverterError, RateSourceError
from currency_converter.domain.models import RateTable


class SourceKind(str, Enum):
    LIVE = "live"
    SAVED = "saved"


class NoticeKind(str, Enum):
    WEEKEND = "weekend"
    NOT_PUBLISHED = "not_published"
    NOT_YET_PUBLISHED = "not_yet_published"
    SAVED_COPY = "saved_copy"


@dataclass(frozen=True)
class Notice:
    """Something the user must know about the rate that is used (FR-011, FR-012, FR-013)."""

    kind: NoticeKind
    requested_date: date
    used_date: date
    saved_at: datetime | None = None


@dataclass(frozen=True)
class SavedCopyInfo:
    rate_date: date
    saved_at: datetime


@dataclass(frozen=True)
class RateLookup:
    table: RateTable
    requested_date: date
    source: SourceKind
    saved_at: datetime | None = None
    notices: tuple[Notice, ...] = ()

    @property
    def used_date(self) -> date:
        return self.table.rate_date


class RatesUnavailableError(ConverterError):
    """The source failed; ``saved`` describes the saved copy the user may switch to."""

    def __init__(self, cause: RateSourceError, saved: SavedCopyInfo | None) -> None:
        self.cause = cause
        self.saved = saved
        super().__init__(str(cause))
