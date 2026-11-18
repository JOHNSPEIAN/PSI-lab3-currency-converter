"""Saved copy on disk: survives a restart, tolerates broken files, writes atomically (FR-014)."""

import json
from datetime import date, datetime
from decimal import Decimal

import pytest

from currency_converter.adapters.json_cache import JsonFileRateCache
from currency_converter.domain.models import SavedCopy
from tests.conftest import make_table

COPY = SavedCopy(make_table(date(2026, 11, 18)), datetime(2026, 11, 18, 12, 30, 5), "bnm")


@pytest.fixture
def path(tmp_path):
    return tmp_path / "data" / "rates-cache.json"


def test_missing_file_means_no_saved_copy(path):
    assert JsonFileRateCache(path).load() is None


def test_round_trip_preserves_every_value(path):
    JsonFileRateCache(path).save(COPY)
    loaded = JsonFileRateCache(path).load()
    assert loaded == COPY
    assert loaded.table.rate_for("HUF").value == Decimal("5.5244")


def test_saved_copy_survives_restart(path):
    """A new cache object (= a new process) reads what the previous one saved."""
    JsonFileRateCache(path).save(COPY)
    restarted = JsonFileRateCache(path)
    assert restarted.load().table.rate_date == date(2026, 11, 18)


def test_creates_missing_directories(path):
    JsonFileRateCache(path).save(COPY)
    assert path.is_file()


def test_newer_save_replaces_older_one(path):
    cache = JsonFileRateCache(path)
    cache.save(COPY)
    newer = SavedCopy(make_table(date(2026, 11, 19)), datetime(2026, 11, 19, 14, 0), "bnm")
    cache.save(newer)
    assert cache.load() == newer


def test_decimals_are_stored_as_strings(path):
    JsonFileRateCache(path).save(COPY)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema"] == 1
    assert data["rates"][0]["value"] == "18.3383"


def test_no_temporary_files_are_left_behind(path):
    JsonFileRateCache(path).save(COPY)
    assert [p.name for p in path.parent.iterdir()] == ["rates-cache.json"]


@pytest.mark.parametrize("content", [
    "",
    "{not json",
    "[]",
    '{"schema": 99, "rates": []}',
    '{"schema": 1, "rates": []}',
    '{"schema": 1, "source_id": "bnm", "saved_at": "2026-11-18T12:00:00", "rate_date": "2026-11-18",'
    ' "rates": [{"code": "USD", "name": "x", "nominal": 1, "value": "abc"}]}',
])
def test_corrupted_or_foreign_file_is_ignored(path, content):
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")
    assert JsonFileRateCache(path).load() is None


def test_failed_write_keeps_previous_copy(path, monkeypatch):
    cache = JsonFileRateCache(path)
    cache.save(COPY)

    def broken_replace(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("currency_converter.adapters.json_cache.os.replace", broken_replace)
    with pytest.raises(OSError):
        cache.save(SavedCopy(make_table(date(2026, 11, 19)), datetime(2026, 11, 19), "bnm"))
    assert cache.load() == COPY
    assert [p.name for p in path.parent.iterdir()] == ["rates-cache.json"]
