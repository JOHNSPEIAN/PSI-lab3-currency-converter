"""Conversion maths: direct, reverse, cross rates, nominals and identical currencies (FR-009, FR-010)."""

from datetime import date
from decimal import Decimal

import pytest

from currency_converter.domain.conversion import CurrencyConverter
from currency_converter.domain.errors import CurrencyNotAvailableError
from currency_converter.presentation.formatting import quantize
from tests.conftest import make_table

converter = CurrencyConverter()


def test_foreign_to_mdl(table):
    result = converter.convert(Decimal("100"), "USD", "MDL", table)
    assert result.result == Decimal("1833.83")
    assert result.rate == Decimal("18.3383")


def test_mdl_to_foreign_reverse_direction(table):
    result = converter.convert(Decimal("1833.83"), "MDL", "USD", table)
    assert quantize(result.result, 2) == Decimal("100.00")


def test_rate_and_inverse_rate_are_reciprocal(table):
    result = converter.convert(Decimal("1"), "USD", "MDL", table)
    assert quantize(result.rate * result.inverse_rate, 12) == Decimal(1)
    assert quantize(result.inverse_rate, 4) == Decimal("0.0545")


def test_cross_rate_through_mdl(table):
    result = converter.convert(Decimal("100"), "EUR", "USD", table)
    expected = Decimal("100") * Decimal("20.1538") / Decimal("18.3383")
    assert result.result == expected
    assert quantize(result.result, 2) == Decimal("109.90")


def test_nominal_is_taken_into_account(table):
    # BNM quotes HUF per 100 units: 5.5244 MDL for 100 HUF.
    assert converter.convert(Decimal("1000"), "HUF", "MDL", table).result == Decimal("55.244")
    assert quantize(converter.convert(Decimal("1"), "MDL", "HUF", table).result, 2) == Decimal("18.10")


@pytest.mark.parametrize("code", ["MDL", "USD", "HUF"])
def test_same_currency_returns_amount_with_rate_one(table, code):
    result = converter.convert(Decimal("123.45"), code, code, table)
    assert result.result == Decimal("123.45")
    assert result.rate == result.inverse_rate == Decimal(1)


@pytest.mark.parametrize("amount", ["0.01", "1", "99.99", "1000000", "123456789.1234"])
@pytest.mark.parametrize("pair", [("USD", "MDL"), ("MDL", "EUR"), ("EUR", "HUF"), ("HUF", "USD")])
def test_round_trip_with_unrounded_result_is_exact(table, amount, pair):
    source, target = pair
    there = converter.convert(Decimal(amount), source, target, table)
    back = converter.convert(there.result, target, source, table)
    assert abs(back.result - Decimal(amount)) < Decimal("1e-15")


def test_round_trip_of_displayed_result_returns_original_amount(table):
    # The example from the user guide: 100 USD -> 1 833,83 MDL -> 100,00 USD.
    there = converter.convert(Decimal("100"), "USD", "MDL", table)
    back = converter.convert(quantize(there.result, 2), "MDL", "USD", table)
    assert quantize(back.result, 2) == Decimal("100.00")


def test_rounding_the_intermediate_result_can_exceed_one_cent(table):
    # Documents a limit of SC-004 (see REPORT.md): 100 HUF = 0.30 USD after rounding to cents,
    # and 0.30 USD converts back to 99.59 HUF, not 100.00.
    there = converter.convert(Decimal("100"), "HUF", "USD", table)
    back = converter.convert(quantize(there.result, 2), "USD", "HUF", table)
    assert quantize(there.result, 2) == Decimal("0.30")
    assert abs(back.result - Decimal("100")) > Decimal("0.01")


def test_unknown_currency_is_reported(table):
    with pytest.raises(CurrencyNotAvailableError) as error:
        converter.convert(Decimal("1"), "XYZ", "MDL", table)
    assert error.value.code == "XYZ"
    assert error.value.rate_date == date(2026, 11, 18)


def test_result_uses_exact_decimal_arithmetic():
    table = make_table(date(2026, 11, 18), [("AAA", 1, "0.1"), ("BBB", 1, "0.3")])
    # with floats 0.1 * 3 != 0.3; with Decimal the conversion is exact
    assert converter.convert(Decimal("3"), "AAA", "MDL", table).result == Decimal("0.3")
