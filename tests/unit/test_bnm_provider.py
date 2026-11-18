"""BNM provider (URL, status mapping), HTTP client error mapping and the memo decorator."""

from datetime import date, timedelta

import pytest

from currency_converter.adapters.bnm import BnmRateProvider, BnmXmlParser
from currency_converter.adapters.http_client import UrllibHttpClient
from currency_converter.adapters.memo import MemoizingRateProvider
from currency_converter.domain.errors import (
    HttpStatusError, MalformedResponseError, NoRatesPublishedError, SourceUnavailableError,
)
from tests.conftest import FakeHttpClient, FakeProvider, fixture_bytes, make_table

DAY = date(2026, 11, 18)


def provider_with(http: FakeHttpClient) -> BnmRateProvider:
    return BnmRateProvider(http, BnmXmlParser(), base_url="https://example.test/rates")


def test_url_contains_the_date_in_bnm_format():
    http = FakeHttpClient(fixture_bytes("bnm_2026-11-18_business_day.xml"))
    provider_with(http).fetch(date(2026, 1, 5))
    assert http.urls == ["https://example.test/rates?get_xml=1&date=05.01.2026"]


def test_fetch_returns_parsed_table():
    http = FakeHttpClient(fixture_bytes("bnm_2026-11-18_business_day.xml"))
    table = provider_with(http).fetch(DAY)
    assert table.rate_for("EUR") is not None


def test_http_404_means_rates_not_published():
    # Observed on bnm.md: unpublished dates (e.g. tomorrow before 13:00) return 404 + empty body.
    provider = provider_with(FakeHttpClient(error=HttpStatusError(404)))
    with pytest.raises(NoRatesPublishedError):
        provider.fetch(DAY)


@pytest.mark.parametrize("status", [500, 502, 503, 403])
def test_other_http_errors_mean_source_unavailable(status):
    provider = provider_with(FakeHttpClient(error=HttpStatusError(status)))
    with pytest.raises(SourceUnavailableError) as error:
        provider.fetch(DAY)
    assert not isinstance(error.value, NoRatesPublishedError)


def test_network_errors_propagate_as_source_unavailable():
    provider = provider_with(FakeHttpClient(error=SourceUnavailableError("timed out")))
    with pytest.raises(SourceUnavailableError):
        provider.fetch(DAY)


def test_malformed_payload_propagates():
    provider = provider_with(FakeHttpClient(fixture_bytes("bnm_malformed.xml")))
    with pytest.raises(MalformedResponseError):
        provider.fetch(DAY)


def test_urllib_client_maps_refused_connection_to_source_unavailable():
    # Port 9 (discard) on localhost is closed: no internet access needed for this test.
    client = UrllibHttpClient(timeout=2, user_agent="tests")
    with pytest.raises(SourceUnavailableError):
        client.get("http://127.0.0.1:9/rates")


def test_urllib_client_maps_invalid_url_to_source_unavailable():
    client = UrllibHttpClient(timeout=2, user_agent="tests")
    with pytest.raises(SourceUnavailableError):
        client.get("not a url")


class TestMemoizingRateProvider:
    def test_second_request_for_same_date_is_served_from_memory(self, clock):
        inner = FakeProvider({DAY: make_table(DAY)})
        memo = MemoizingRateProvider(inner, clock)
        assert memo.fetch(DAY) is memo.fetch(DAY)
        assert inner.calls == [DAY]

    def test_entry_expires_after_ttl(self, clock):
        inner = FakeProvider({DAY: make_table(DAY)})
        memo = MemoizingRateProvider(inner, clock, ttl=timedelta(minutes=30))
        memo.fetch(DAY)
        clock.current += timedelta(minutes=31)
        memo.fetch(DAY)
        assert inner.calls == [DAY, DAY]

    def test_not_published_answers_are_not_memoised(self, clock):
        inner = FakeProvider()  # nothing published
        memo = MemoizingRateProvider(inner, clock)
        for _ in range(2):
            with pytest.raises(NoRatesPublishedError):
                memo.fetch(DAY)
        assert inner.calls == [DAY, DAY]

    def test_keeps_source_id_of_wrapped_provider(self, clock):
        assert MemoizingRateProvider(FakeProvider(), clock).source_id == "fake"

    def test_evicts_oldest_entries(self, clock):
        inner = FakeProvider(default=make_table(DAY))
        memo = MemoizingRateProvider(inner, clock, max_entries=2)
        days = [DAY - timedelta(days=i) for i in range(3)]
        for day in days:
            memo.fetch(day)
        memo.fetch(days[0])  # was evicted -> fetched again
        assert inner.calls.count(days[0]) == 2
