"""JSON API controller wired with real services and fake adapters (no network, no HTTP server)."""

import json
from datetime import date, datetime

import pytest

from currency_converter.application.converter_service import ConverterService
from currency_converter.application.rate_service import RateService
from currency_converter.domain.conversion import CurrencyConverter
from currency_converter.domain.errors import SourceUnavailableError
from currency_converter.domain.models import SavedCopy
from currency_converter.domain.validation import ConversionRequestValidator
from currency_converter.presentation.json_presenter import JsonPresenter
from currency_converter.web.api import ApiController
from currency_converter.web.responses import ApiRequest
from tests.conftest import FakeClock, FakeProvider, InMemoryCache, make_table

WED = date(2026, 11, 18)


def controller(provider: FakeProvider, cache: InMemoryCache | None = None) -> ApiController:
    clock = FakeClock(datetime(2026, 11, 18, 12, 0))
    rates = RateService(provider, cache or InMemoryCache(), clock)
    service = ConverterService(rates, CurrencyConverter(), ConversionRequestValidator(), clock)
    return ApiController(service, JsonPresenter(), version="test")


def post(api: ApiController, **body) -> tuple[int, dict]:
    response = api.handle(ApiRequest("POST", "/api/convert", body=json.dumps(body).encode()))
    return response.status, dict(response.body)


@pytest.fixture
def online() -> ApiController:
    return controller(FakeProvider({WED: make_table(WED)}))


def test_health(online):
    response = online.handle(ApiRequest("GET", "/api/health"))
    assert response.status == 200
    assert response.body == {"status": "ok", "version": "test"}


def test_rates_endpoint_lists_currencies(online):
    response = online.handle(ApiRequest("GET", "/api/rates", query={"date": "2026-11-18"}))
    assert response.status == 200
    assert [c["code"] for c in response.body["currencies"]] == ["MDL", "EUR", "HUF", "USD"]


def test_convert_returns_result_rates_date_and_source(online):
    status, body = post(online, amount="100", source="USD", target="MDL", date="2026-11-18")
    assert status == 200
    conversion = body["conversion"]
    assert conversion["result"] == "1833.83"
    assert conversion["result_display"] == "1 833,83"
    assert conversion["rate_display"] == "18,3383"
    assert conversion["inverse_rate_display"] == "0,0545"
    assert body["lookup"]["used_date_display"] == "18.11.2026"
    assert body["lookup"]["source_label"] == "Национальный банк Молдовы"


def test_convert_same_currency(online):
    status, body = post(online, amount="50", source="EUR", target="EUR", date="2026-11-18")
    assert status == 200
    assert body["conversion"]["result"] == "50.00"


@pytest.mark.parametrize("amount", ["-5", "0", "abc", "", "   "])
def test_invalid_amount_is_rejected_without_conversion(amount):
    provider = FakeProvider({WED: make_table(WED)})
    status, body = post(controller(provider), amount=amount, source="USD", target="MDL", date="2026-11-18")
    assert status == 422
    assert body["error"]["code"] == "VALIDATION"
    assert body["error"]["fields"][0]["field"] == "amount"
    assert provider.calls == []  # invalid input never reaches the source


def test_unknown_currency(online):
    status, body = post(online, amount="1", source="XYZ", target="MDL", date="2026-11-18")
    assert status == 422
    assert body["error"]["code"] == "CURRENCY_NOT_AVAILABLE"


def test_offline_with_saved_copy_then_saved_mode():
    saved = SavedCopy(make_table(date(2026, 11, 17)), datetime(2026, 11, 17, 9, 30), "fake")
    api = controller(FakeProvider(default=SourceUnavailableError("offline")), InMemoryCache(saved))

    status, body = post(api, amount="100", source="USD", target="MDL", date="2026-11-18")
    assert status == 503
    assert body["error"]["saved"]["rate_date"] == "2026-11-17"

    status, body = post(api, amount="100", source="USD", target="MDL", date="2026-11-18", mode="saved")
    assert status == 200
    assert body["lookup"]["source"] == "saved"
    assert body["lookup"]["used_date_display"] == "17.11.2026"


def test_saved_mode_without_saved_copy():
    api = controller(FakeProvider())
    response = api.handle(ApiRequest("GET", "/api/rates", query={"mode": "saved"}))
    assert response.status == 404
    assert response.body["error"]["code"] == "NO_SAVED_COPY"


@pytest.mark.parametrize("body", [b"{not json", b"[1, 2]", b'{"amount": ["1"]}', b'{"mode": "turbo"}'])
def test_bad_requests(online, body):
    response = online.handle(ApiRequest("POST", "/api/convert", body=body))
    assert response.status == 400
    assert response.body["error"]["code"] == "BAD_REQUEST"


def test_unknown_route(online):
    assert online.handle(ApiRequest("GET", "/api/nope")).status == 404


def test_unexpected_exception_becomes_500_not_a_crash():
    api = controller(FakeProvider(default=RuntimeError("bug")))
    status, body = post(api, amount="1", source="USD", target="MDL", date="2026-11-18")
    assert status == 500
    assert body["error"]["code"] == "INTERNAL"
    assert "Traceback" not in body["error"]["message"]
