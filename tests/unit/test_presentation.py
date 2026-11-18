"""Russian formatting and JSON presentation of results, notices and errors."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from currency_converter.application.lookup import (
    Notice, NoticeKind, RateLookup, RatesUnavailableError, SavedCopyInfo, SourceKind,
)
from currency_converter.domain.errors import (
    CurrencyNotAvailableError, FieldError, MalformedResponseError, NoSavedCopyError,
    RatesNotFoundError, SourceUnavailableError, ValidationError,
)
from currency_converter.presentation.formatting import (
    format_amount, format_date, format_datetime, format_rate, plain_decimal,
)
from currency_converter.presentation.json_presenter import JsonPresenter
from tests.conftest import make_table

NBSP = " "
presenter = JsonPresenter()


class TestFormatting:
    @pytest.mark.parametrize("value, expected", [
        ("0", "0,00"),
        ("1", "1,00"),
        ("1833.825", "1" + NBSP + "833,83"),       # ROUND_HALF_UP
        ("1234567.891", "1" + NBSP + "234" + NBSP + "567,89"),
        ("-1500", "-1" + NBSP + "500,00"),
        ("0.0034567", "0,0035"),                    # tiny values keep 2 significant digits
    ])
    def test_amounts(self, value, expected):
        assert format_amount(Decimal(value)) == expected

    def test_rates_have_four_places(self):
        assert format_rate(Decimal("18.33834")) == "18,3383"
        assert format_rate(Decimal("0.05454545")) == "0,0545"

    def test_plain_decimal_is_machine_readable(self):
        assert plain_decimal(Decimal("1833.825"), 2) == "1833.83"

    def test_dates(self):
        assert format_date(date(2026, 1, 5)) == "05.01.2026"
        assert format_datetime(datetime(2026, 11, 18, 9, 7, 59)) == "18.11.2026 09:07"


def test_lookup_payload_contains_date_and_source():
    lookup = RateLookup(make_table(date(2026, 11, 13)), date(2026, 11, 15), SourceKind.LIVE,
                        notices=(Notice(NoticeKind.WEEKEND, date(2026, 11, 15), date(2026, 11, 13)),))
    data = presenter.lookup(lookup)
    assert data["used_date"] == "2026-11-13"
    assert data["used_date_display"] == "13.11.2026"
    assert data["source"] == "live"
    assert data["source_label"] == "Национальный банк Молдовы"
    assert data["notices"][0]["kind"] == "weekend"
    assert "воскресенье" in data["notices"][0]["message"]
    assert "13.11.2026" in data["notices"][0]["message"]


def test_saved_copy_is_labelled_as_such():
    saved_at = datetime(2026, 11, 17, 9, 30)
    lookup = RateLookup(make_table(date(2026, 11, 17)), date(2026, 11, 18), SourceKind.SAVED,
                        saved_at=saved_at,
                        notices=(Notice(NoticeKind.SAVED_COPY, date(2026, 11, 18), date(2026, 11, 17), saved_at),))
    data = presenter.lookup(lookup)
    assert data["source_label"] == "Сохранённая копия"
    assert data["saved_at_display"] == "17.11.2026 09:30"
    assert data["notices"][0]["level"] == "warning"


def test_currency_list_starts_with_mdl_and_shows_rate_per_unit():
    currencies = presenter.currencies(make_table(date(2026, 11, 18)))
    assert currencies[0] == {"code": "MDL", "name": "Молдавский лей", "nominal": 1, "rate_display": "1,0000"}
    huf = next(c for c in currencies if c["code"] == "HUF")
    assert huf["nominal"] == 100
    assert huf["rate_display"] == "0,0552"


def test_validation_error_has_message_per_field():
    status, body = presenter.present_error(ValidationError([
        FieldError("amount", "AMOUNT_NEGATIVE"),
        FieldError("date", "DATE_IN_FUTURE", {"latest": date(2026, 11, 19)}),
    ]))
    assert status == 422
    fields = body["error"]["fields"]
    assert fields[0] == {"field": "amount", "code": "AMOUNT_NEGATIVE",
                         "message": "Сумма не может быть отрицательной."}
    assert "19.11.2026" in fields[1]["message"]


def test_every_validation_code_has_a_russian_message():
    from currency_converter.presentation.messages_ru import FIELD_MESSAGES
    codes = ["AMOUNT_EMPTY", "AMOUNT_NOT_A_NUMBER", "AMOUNT_ZERO", "AMOUNT_NEGATIVE",
             "AMOUNT_TOO_MANY_DECIMALS", "AMOUNT_TOO_LARGE", "CURRENCY_EMPTY", "CURRENCY_INVALID",
             "DATE_EMPTY", "DATE_INVALID", "DATE_TOO_EARLY", "DATE_IN_FUTURE"]
    assert set(codes) <= set(FIELD_MESSAGES)


def test_offline_error_offers_saved_copy():
    error = RatesUnavailableError(SourceUnavailableError("timed out"),
                                  SavedCopyInfo(date(2026, 11, 17), datetime(2026, 11, 17, 9, 30)))
    status, body = presenter.present_error(error)
    assert status == 503
    assert body["error"]["code"] == "SOURCE_UNAVAILABLE"
    assert body["error"]["saved"]["rate_date_display"] == "17.11.2026"
    assert "Нет связи" in body["error"]["message"]
    assert "17.11.2026" in body["error"]["message"]


def test_offline_error_without_saved_copy():
    status, body = presenter.present_error(RatesUnavailableError(SourceUnavailableError("x"), None))
    assert status == 503
    assert body["error"]["saved"] is None
    assert "Сохранённых курсов пока нет" in body["error"]["message"]


def test_malformed_answer_is_explained_differently():
    _, body = presenter.present_error(RatesUnavailableError(MalformedResponseError("x"), None))
    assert "некорректный ответ" in body["error"]["message"]


@pytest.mark.parametrize("error, status, code", [
    (RatesNotFoundError(date(2026, 11, 18), date(2026, 11, 8)), 404, "RATES_NOT_FOUND"),
    (NoSavedCopyError(), 404, "NO_SAVED_COPY"),
    (CurrencyNotAvailableError("XYZ", date(2026, 11, 18)), 422, "CURRENCY_NOT_AVAILABLE"),
])
def test_other_errors(error, status, code):
    actual_status, body = presenter.present_error(error)
    assert (actual_status, body["error"]["code"]) == (status, code)
    assert body["error"]["message"]
