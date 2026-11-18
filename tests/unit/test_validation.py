"""User input validation (FR-008): amounts, dates, currency codes, whole requests."""

from datetime import date
from decimal import Decimal

import pytest

from currency_converter.domain.errors import ValidationError
from currency_converter.domain.validation import (
    AmountParser, ConversionRequestValidator, RateDateParser,
)

TODAY = date(2026, 11, 18)


def error_codes(excinfo) -> list[str]:
    return [e.code for e in excinfo.value.errors]


class TestAmountParser:
    parser = AmountParser()

    @pytest.mark.parametrize("text, expected", [
        ("100", "100"),
        ("1500.5", "1500.5"),
        ("1500,5", "1500.5"),
        ("1 000,50", "1000.50"),
        ("1 000 000", "1000000"),
        ("  42  ", "42"),
        (",5", "0.5"),
        ("5.", "5"),
        ("+7", "7"),
        ("0.0001", "0.0001"),
        ("1000000000000", "1000000000000"),
    ])
    def test_accepts_human_formats(self, text, expected):
        assert self.parser.parse(text) == Decimal(expected)

    @pytest.mark.parametrize("text, code", [
        ("", "AMOUNT_EMPTY"),
        ("   ", "AMOUNT_EMPTY"),
        (None, "AMOUNT_EMPTY"),
        ("abc", "AMOUNT_NOT_A_NUMBER"),
        ("12a", "AMOUNT_NOT_A_NUMBER"),
        ("1,2,3", "AMOUNT_NOT_A_NUMBER"),
        ("1.2.3", "AMOUNT_NOT_A_NUMBER"),
        ("1e5", "AMOUNT_NOT_A_NUMBER"),
        ("NaN", "AMOUNT_NOT_A_NUMBER"),
        ("Infinity", "AMOUNT_NOT_A_NUMBER"),
        ("10 00", "AMOUNT_NOT_A_NUMBER"),
        ("--5", "AMOUNT_NOT_A_NUMBER"),
        (".", "AMOUNT_NOT_A_NUMBER"),
        ("0", "AMOUNT_ZERO"),
        ("0,00", "AMOUNT_ZERO"),
        ("-0", "AMOUNT_ZERO"),
        ("-5", "AMOUNT_NEGATIVE"),
        ("-0.01", "AMOUNT_NEGATIVE"),
        ("1.23456", "AMOUNT_TOO_MANY_DECIMALS"),
        ("1000000000000.01", "AMOUNT_TOO_LARGE"),
    ])
    def test_rejects_invalid_amounts(self, text, code):
        with pytest.raises(ValidationError) as excinfo:
            self.parser.parse(text)
        assert error_codes(excinfo) == [code]
        assert excinfo.value.errors[0].field == "amount"

    def test_trailing_zeros_do_not_count_as_decimals(self):
        assert self.parser.parse("1.500000") == Decimal("1.5")


class TestRateDateParser:
    parser = RateDateParser()

    @pytest.mark.parametrize("text, expected", [
        ("2026-11-18", date(2026, 11, 18)),
        ("18.11.2026", date(2026, 11, 18)),
        ("1.2.2026", date(2026, 2, 1)),
        ("2026-11-19", date(2026, 11, 19)),   # tomorrow is allowed
        ("2000-01-01", date(2000, 1, 1)),
    ])
    def test_accepts_iso_and_russian_formats(self, text, expected):
        assert self.parser.parse(text, TODAY) == expected

    @pytest.mark.parametrize("text, code", [
        ("", "DATE_EMPTY"),
        ("yesterday", "DATE_INVALID"),
        ("2026-13-01", "DATE_INVALID"),
        ("31.02.2026", "DATE_INVALID"),
        ("2026/11/18", "DATE_INVALID"),
        ("1999-12-31", "DATE_TOO_EARLY"),
        ("2026-11-20", "DATE_IN_FUTURE"),
    ])
    def test_rejects_invalid_dates(self, text, code):
        with pytest.raises(ValidationError) as excinfo:
            self.parser.parse(text, TODAY)
        assert error_codes(excinfo) == [code]


class TestConversionRequestValidator:
    validator = ConversionRequestValidator()

    def test_valid_request_is_normalised(self):
        request = self.validator.validate("1 000,5", " usd ", "mdl", "18.11.2026", TODAY)
        assert request.amount == Decimal("1000.5")
        assert (request.source, request.target) == ("USD", "MDL")
        assert request.rate_date == TODAY

    def test_identical_currencies_are_valid(self):
        request = self.validator.validate("10", "EUR", "EUR", "2026-11-18", TODAY)
        assert request.source == request.target == "EUR"

    def test_collects_errors_of_all_fields_at_once(self):
        with pytest.raises(ValidationError) as excinfo:
            self.validator.validate("-1", "", "US1", "2030-01-01", TODAY)
        assert [(e.field, e.code) for e in excinfo.value.errors] == [
            ("amount", "AMOUNT_NEGATIVE"),
            ("source", "CURRENCY_EMPTY"),
            ("target", "CURRENCY_INVALID"),
            ("date", "DATE_IN_FUTURE"),
        ]

    def test_error_parameters_are_provided_for_messages(self):
        with pytest.raises(ValidationError) as excinfo:
            self.validator.validate("10", "USD", "MDL", "2026-12-01", TODAY)
        assert excinfo.value.errors[0].params == {"latest": date(2026, 11, 19)}
