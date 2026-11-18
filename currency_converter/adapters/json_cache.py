"""Saved copy of the last successful response in a JSON file (research R6, FR-014)."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from currency_converter.domain.models import Currency, ExchangeRate, RateTable, SavedCopy

log = logging.getLogger(__name__)

SCHEMA_VERSION = 1


class JsonFileRateCache:
    """Atomic writes (temp file + os.replace); unreadable files are treated as "no copy"."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> SavedCopy | None:
        try:
            raw = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except OSError as exc:
            log.warning("cannot read saved rates %s: %s", self._path, exc)
            return None
        try:
            return self._decode(json.loads(raw))
        except (ValueError, KeyError, TypeError, InvalidOperation) as exc:
            log.warning("ignoring unreadable saved rates %s: %s", self._path, exc)
            return None

    def save(self, copy: SavedCopy) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".rates-", suffix=".tmp", dir=self._path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(self._encode(copy), stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self._path)
        except BaseException:
            Path(temp_name).unlink(missing_ok=True)
            raise

    @staticmethod
    def _encode(copy: SavedCopy) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "source_id": copy.source_id,
            "saved_at": copy.saved_at.isoformat(timespec="seconds"),
            "rate_date": copy.table.rate_date.isoformat(),
            "rates": [
                {"code": r.currency.code, "name": r.currency.name,
                 "nominal": r.nominal, "value": str(r.value)}
                for r in copy.table.rates
            ],
        }

    @staticmethod
    def _decode(data: Any) -> SavedCopy | None:
        if not isinstance(data, dict) or data.get("schema") != SCHEMA_VERSION:
            return None
        rates = tuple(
            ExchangeRate(Currency(item["code"], item["name"]), int(item["nominal"]), Decimal(item["value"]))
            for item in data["rates"]
        )
        return SavedCopy(
            table=RateTable(date.fromisoformat(data["rate_date"]), rates),
            saved_at=datetime.fromisoformat(data["saved_at"]),
            source_id=str(data["source_id"]),
        )
