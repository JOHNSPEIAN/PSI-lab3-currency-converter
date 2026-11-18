"""Turns application results and errors into JSON-ready dicts (contracts/http-api.md)."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from currency_converter.application.converter_service import ConversionOutcome
from currency_converter.application.lookup import RateLookup
from currency_converter.domain.conversion import Conversion
from currency_converter.domain.errors import ConverterError, RateSourceError, ValidationError
from currency_converter.domain.models import Currency, RateTable
from currency_converter.presentation import messages_ru as ru
from currency_converter.presentation.formatting import (
    AMOUNT_PLACES, RATE_PLACES, format_amount, format_date, format_datetime, format_rate,
    plain_decimal,
)

Json = dict[str, Any]


class JsonPresenter:
    def present_rates(self, lookup: RateLookup) -> Json:
        return {"status": "ok", "lookup": self.lookup(lookup), "currencies": self.currencies(lookup.table)}

    def present_conversion(self, outcome: ConversionOutcome) -> Json:
        return {"status": "ok", "conversion": self.conversion(outcome.conversion),
                "lookup": self.lookup(outcome.lookup)}

    def present_error(self, error: ConverterError) -> tuple[int, Json]:
        if isinstance(error, ValidationError):
            fields = [{"field": e.field, "code": e.code, "message": ru.GENERIC_INVALID_INPUT}
                      for e in error.errors]
            return HTTPStatus.UNPROCESSABLE_ENTITY, self.error(
                "VALIDATION", ru.GENERIC_INVALID_INPUT, fields=fields)
        if isinstance(error, RateSourceError):
            return HTTPStatus.SERVICE_UNAVAILABLE, self.error(
                "SOURCE_UNAVAILABLE", ru.GENERIC_SOURCE_ERROR, saved=None)
        return HTTPStatus.INTERNAL_SERVER_ERROR, self.error("INTERNAL", ru.INTERNAL)

    @staticmethod
    def error(code: str, message: str, **extra: Any) -> Json:
        return {"status": "error", "error": {"code": code, "message": message, **extra}}

    def lookup(self, lookup: RateLookup) -> Json:
        return {
            "requested_date": lookup.requested_date.isoformat(),
            "used_date": lookup.used_date.isoformat(),
            "used_date_display": format_date(lookup.used_date),
            "source": lookup.source.value,
            "source_label": ru.SOURCE_LABELS[lookup.source],
            "saved_at": lookup.saved_at.isoformat() if lookup.saved_at else None,
            "saved_at_display": format_datetime(lookup.saved_at) if lookup.saved_at else None,
            "notices": [],
        }

    @staticmethod
    def currencies(table: RateTable) -> list[Json]:
        items = []
        for currency in table.currencies():
            rate = table.rate_for(currency.code)
            items.append({
                "code": currency.code,
                "name": currency.name,
                "nominal": rate.nominal if rate else 1,
                "rate_display": format_rate(table.per_unit(currency.code)),
            })
        return items

    @staticmethod
    def currency(currency: Currency) -> Json:
        return {"code": currency.code, "name": currency.name}

    def conversion(self, conversion: Conversion) -> Json:
        return {
            "amount": plain_decimal(conversion.amount, 4),
            "amount_display": format_amount(conversion.amount),
            "source": self.currency(conversion.source),
            "target": self.currency(conversion.target),
            "result": plain_decimal(conversion.result, AMOUNT_PLACES),
            "result_display": format_amount(conversion.result),
            "rate": plain_decimal(conversion.rate, RATE_PLACES),
            "rate_display": format_rate(conversion.rate),
            "inverse_rate": plain_decimal(conversion.inverse_rate, RATE_PLACES),
            "inverse_rate_display": format_rate(conversion.inverse_rate),
        }
