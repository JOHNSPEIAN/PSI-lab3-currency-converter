"""National Bank of Moldova adapter: XML parser and rate provider (research R1, R2).

Feed format::

    <ValCurs Date="18.11.2026" name="Обменные ставки">
      <Valute ID="44"><NumCode>840</NumCode><CharCode>USD</CharCode>
        <Nominal>1</Nominal><Name>Доллар США</Name><Value>18.3383</Value></Valute>
      ...
    </ValCurs>

An empty body means that nothing is published for the date.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from xml.etree import ElementTree

from currency_converter.config import DEFAULT_SOURCE_URL
from currency_converter.domain.errors import MalformedResponseError, NoRatesPublishedError
from currency_converter.domain.models import MDL, Currency, ExchangeRate, RateTable
from currency_converter.ports import HttpClient, RateTableParser

BNM_DATE_FORMAT = "%d.%m.%Y"


class BnmXmlParser:
    def parse(self, payload: bytes, requested_date: date) -> RateTable:
        if not payload.strip():
            raise NoRatesPublishedError(requested_date)
        try:
            root = ElementTree.fromstring(payload)
        except ElementTree.ParseError as exc:
            raise MalformedResponseError(f"invalid XML: {exc}") from exc
        if root.tag != "ValCurs":
            raise MalformedResponseError(f"unexpected root element <{root.tag}>")
        valutes = root.findall("Valute")
        if not valutes:
            raise NoRatesPublishedError(requested_date)
        rate_date = self._parse_date(root.get("Date"), requested_date)
        rates = tuple(
            rate for rate in (self._parse_valute(v) for v in valutes)
            if rate.currency.code != MDL.code
        )
        try:
            return RateTable(rate_date, rates)
        except ValueError as exc:
            raise MalformedResponseError(str(exc)) from exc

    @staticmethod
    def _parse_date(text: str | None, fallback: date) -> date:
        if not text:
            return fallback
        try:
            return datetime.strptime(text.strip(), BNM_DATE_FORMAT).date()
        except ValueError as exc:
            raise MalformedResponseError(f"invalid Date attribute {text!r}") from exc

    @staticmethod
    def _parse_valute(element: ElementTree.Element) -> ExchangeRate:
        def text(tag: str) -> str:
            value = element.findtext(tag)
            if value is None or not value.strip():
                raise MalformedResponseError(f"<Valute> without <{tag}>")
            return value.strip()

        try:
            code = text("CharCode").upper()
            return ExchangeRate(
                currency=Currency(code, text("Name")),
                nominal=int(text("Nominal")),
                value=Decimal(text("Value").replace(",", ".")),
            )
        except (ValueError, InvalidOperation) as exc:
            raise MalformedResponseError(f"invalid <Valute>: {exc}") from exc


class BnmRateProvider:
    """Downloads the official rates for one date. Knows URLs, not XML (SRP)."""

    source_id = "bnm"

    def __init__(self, http: HttpClient, parser: RateTableParser,
                 base_url: str = DEFAULT_SOURCE_URL) -> None:
        self._http = http
        self._parser = parser
        self._base_url = base_url

    def url_for(self, rate_date: date) -> str:
        query = urlencode({"get_xml": 1, "date": rate_date.strftime(BNM_DATE_FORMAT)})
        return f"{self._base_url}?{query}"

    def fetch(self, rate_date: date) -> RateTable:
        return self._parser.parse(self._http.get(self.url_for(rate_date)), rate_date)
