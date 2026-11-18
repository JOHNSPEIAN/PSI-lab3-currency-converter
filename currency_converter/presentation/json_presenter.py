"""Turns application results and errors into JSON-ready dicts (contracts/http-api.md)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from http import HTTPStatus
from typing import Any

from currency_converter.application.converter_service import ConversionOutcome
from currency_converter.application.lookup import (
    Notice, NoticeKind, RateLookup, RatesUnavailableError, SavedCopyInfo,
)
from currency_converter.domain.conversion import Conversion
from currency_converter.domain.errors import (
    ConverterError, CurrencyNotAvailableError, FieldError, MalformedResponseError,
    NoSavedCopyError, RateSourceError, ValidationError,
)
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
            fields = [{"field": e.field, "code": e.code, "message": self.field_message(e)}
                      for e in error.errors]
            return HTTPStatus.UNPROCESSABLE_ENTITY, self.error(
                "VALIDATION", ru.VALIDATION_SUMMARY, fields=fields)
        if isinstance(error, CurrencyNotAvailableError):
            message = ru.CURRENCY_NOT_AVAILABLE.format(code=error.code, date=format_date(error.rate_date))
            return HTTPStatus.UNPROCESSABLE_ENTITY, self.error(
                "CURRENCY_NOT_AVAILABLE", message, currency=error.code)
        if isinstance(error, RatesUnavailableError):
            reason = (ru.SOURCE_MALFORMED if isinstance(error.cause, MalformedResponseError)
                      else ru.SOURCE_NETWORK)
            saved = self.saved_info(error.saved)
            offer = (ru.OFFER_SAVED_COPY.format(rate_date=saved["rate_date_display"],
                                                saved_at=saved["saved_at_display"])
                     if saved else ru.NO_SAVED_COPY_YET)
            return HTTPStatus.SERVICE_UNAVAILABLE, self.error(
                "SOURCE_UNAVAILABLE", f"{reason} {offer}", saved=saved)
        if isinstance(error, NoSavedCopyError):
            return HTTPStatus.NOT_FOUND, self.error("NO_SAVED_COPY", ru.NO_SAVED_COPY)
        if isinstance(error, RateSourceError):
            return HTTPStatus.SERVICE_UNAVAILABLE, self.error(
                "SOURCE_UNAVAILABLE", ru.GENERIC_SOURCE_ERROR, saved=None)
        return HTTPStatus.INTERNAL_SERVER_ERROR, self.error("INTERNAL", ru.INTERNAL)

    @staticmethod
    def field_message(error: FieldError) -> str:
        template = ru.FIELD_MESSAGES.get(error.code, ru.GENERIC_INVALID_INPUT)
        params = {key: JsonPresenter._display(value) for key, value in error.params.items()}
        return template.format(**params)

    @staticmethod
    def _display(value: Any) -> str:
        if isinstance(value, date):
            return format_date(value)
        if isinstance(value, Decimal):
            return format_amount(value).removesuffix(",00")
        return str(value)

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
            "notices": [self.notice(n) for n in lookup.notices],
        }

    @staticmethod
    def saved_info(info: SavedCopyInfo | None) -> Json | None:
        if info is None:
            return None
        return {
            "rate_date": info.rate_date.isoformat(),
            "rate_date_display": format_date(info.rate_date),
            "saved_at": info.saved_at.isoformat(),
            "saved_at_display": format_datetime(info.saved_at),
        }

    @staticmethod
    def notice(notice: Notice) -> Json:
        template = ru.NOTICE_MESSAGES[notice.kind.value]
        message = template.format(
            requested=format_date(notice.requested_date),
            used=format_date(notice.used_date),
            saved_at=format_datetime(notice.saved_at) if notice.saved_at else "",
        )
        level = "warning" if notice.kind is NoticeKind.SAVED_COPY else "info"
        return {"kind": notice.kind.value, "level": level, "message": message}

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
