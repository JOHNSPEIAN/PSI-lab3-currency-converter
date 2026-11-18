"""Parsing of the National Bank of Moldova XML feed (recorded real answers + broken variants)."""

from datetime import date
from decimal import Decimal

import pytest

from currency_converter.adapters.bnm import BnmXmlParser
from currency_converter.domain.errors import MalformedResponseError, NoRatesPublishedError
from tests.conftest import fixture_bytes

REQUESTED = date(2026, 11, 18)


@pytest.fixture
def parser() -> BnmXmlParser:
    return BnmXmlParser()


def test_parses_recorded_business_day(parser):
    table = parser.parse(fixture_bytes("bnm_2026-11-18_business_day.xml"), REQUESTED)

    assert table.rate_date == date(2026, 11, 18)
    assert len(table.rates) == 40
    usd = table.rate_for("USD")
    assert usd.currency.name == "Доллар США"
    assert usd.nominal == 1
    assert usd.value == Decimal("18.3383")


def test_values_are_decimal_not_float(parser):
    table = parser.parse(fixture_bytes("bnm_2026-11-18_business_day.xml"), REQUESTED)
    assert all(isinstance(rate.value, Decimal) for rate in table.rates)


def test_nominal_other_than_one_is_normalised_per_unit(parser):
    table = parser.parse(fixture_bytes("bnm_2026-11-18_business_day.xml"), REQUESTED)
    huf = table.rate_for("HUF")
    assert huf.nominal == 100
    assert huf.per_unit == Decimal("0.055244")


def test_mdl_is_available_as_base_currency(parser):
    table = parser.parse(fixture_bytes("bnm_2026-11-18_business_day.xml"), REQUESTED)
    assert table.currencies()[0].code == "MDL"
    assert table.per_unit("MDL") == Decimal(1)


def test_rate_date_comes_from_the_document(parser):
    table = parser.parse(fixture_bytes("bnm_2026-11-15_sunday.xml"), date(2026, 11, 15))
    assert table.rate_date == date(2026, 11, 15)


def test_missing_date_attribute_falls_back_to_requested_date(parser):
    payload = b'<ValCurs><Valute><CharCode>USD</CharCode><Nominal>1</Nominal>' \
              b'<Name>Dollar</Name><Value>18.1</Value></Valute></ValCurs>'
    assert parser.parse(payload, REQUESTED).rate_date == REQUESTED


def test_decimal_comma_in_value_is_accepted(parser):
    payload = '<ValCurs Date="18.11.2026"><Valute><CharCode>USD</CharCode><Nominal>1</Nominal>' \
              '<Name>Доллар</Name><Value>18,3383</Value></Valute></ValCurs>'.encode()
    assert parser.parse(payload, REQUESTED).rate_for("USD").value == Decimal("18.3383")


@pytest.mark.parametrize("payload", [b"", b"   \n", fixture_bytes("bnm_empty.xml")])
def test_empty_answer_means_not_published(parser, payload):
    with pytest.raises(NoRatesPublishedError) as error:
        parser.parse(payload, REQUESTED)
    assert error.value.rate_date == REQUESTED


def test_document_without_currencies_means_not_published(parser):
    with pytest.raises(NoRatesPublishedError):
        parser.parse(fixture_bytes("bnm_no_valute.xml"), date(2026, 11, 19))


@pytest.mark.parametrize("fixture", [
    "bnm_malformed.xml",       # truncated XML
    "bnm_missing_value.xml",   # <Valute> without <Value>
    "bnm_bad_value.xml",       # <Value>n/a</Value>
    "bnm_html_page.xml",       # maintenance HTML page instead of the feed
])
def test_broken_answers_are_malformed(parser, fixture):
    with pytest.raises(MalformedResponseError):
        parser.parse(fixture_bytes(fixture), REQUESTED)


@pytest.mark.parametrize("valute", [
    "<CharCode>US</CharCode><Nominal>1</Nominal><Name>x</Name><Value>1</Value>",      # bad code
    "<CharCode>USD</CharCode><Nominal>0</Nominal><Name>x</Name><Value>1</Value>",     # zero nominal
    "<CharCode>USD</CharCode><Nominal>one</Nominal><Name>x</Name><Value>1</Value>",   # text nominal
    "<CharCode>USD</CharCode><Nominal>1</Nominal><Name>x</Name><Value>-1</Value>",    # negative
])
def test_invalid_currency_entries_are_malformed(parser, valute):
    payload = f'<ValCurs Date="18.11.2026"><Valute>{valute}</Valute></ValCurs>'.encode()
    with pytest.raises(MalformedResponseError):
        parser.parse(payload, REQUESTED)


def test_duplicate_currency_is_malformed(parser):
    one = "<Valute><CharCode>USD</CharCode><Nominal>1</Nominal><Name>x</Name><Value>1</Value></Valute>"
    with pytest.raises(MalformedResponseError):
        parser.parse(f'<ValCurs Date="18.11.2026">{one}{one}</ValCurs>'.encode(), REQUESTED)


def test_invalid_date_attribute_is_malformed(parser):
    payload = b'<ValCurs Date="2026/11/18"><Valute><CharCode>USD</CharCode><Nominal>1</Nominal>' \
              b'<Name>x</Name><Value>1</Value></Valute></ValCurs>'
    with pytest.raises(MalformedResponseError):
        parser.parse(payload, REQUESTED)
