"""Rate selection: weekends, unpublished dates, offline handling and the saved copy (FR-011..FR-015)."""

from datetime import date, datetime

import pytest

from currency_converter.application.lookup import NoticeKind, RatesUnavailableError, SourceKind
from currency_converter.application.rate_service import RateService
from currency_converter.domain.calendar import (
    business_day_on_or_before, is_weekend, previous_business_day,
)
from currency_converter.domain.errors import (
    MalformedResponseError, NoSavedCopyError, RatesNotFoundError, SourceUnavailableError,
)
from currency_converter.domain.models import SavedCopy
from tests.conftest import FakeClock, FakeProvider, InMemoryCache, make_table

WED = date(2026, 11, 18)
THU = date(2026, 11, 19)
FRI = date(2026, 11, 13)
SAT = date(2026, 11, 14)
SUN = date(2026, 11, 15)
MON = date(2026, 11, 16)
TUE = date(2026, 11, 17)


def service(provider, cache=None, clock=None, **kwargs) -> RateService:
    return RateService(provider, cache or InMemoryCache(), clock or FakeClock(), **kwargs)


class TestCalendar:
    def test_weekend_detection(self):
        assert [is_weekend(d) for d in (FRI, SAT, SUN, MON)] == [False, True, True, False]

    def test_previous_business_day_skips_weekend(self):
        assert previous_business_day(MON) == FRI
        assert previous_business_day(TUE) == MON

    def test_business_day_on_or_before(self):
        assert business_day_on_or_before(SUN) == FRI
        assert business_day_on_or_before(WED) == WED


class TestLiveLookup:
    def test_published_date_is_used_without_notices(self):
        lookup = service(FakeProvider({WED: make_table(WED)})).lookup(WED)
        assert lookup.used_date == WED
        assert lookup.source is SourceKind.LIVE
        assert lookup.notices == ()

    @pytest.mark.parametrize("weekend_day", [SAT, SUN])
    def test_weekend_uses_previous_friday_and_says_so(self, weekend_day):
        provider = FakeProvider({FRI: make_table(FRI)})
        lookup = service(provider).lookup(weekend_day)
        assert provider.calls == [FRI]  # the weekend date itself is never requested
        assert lookup.used_date == FRI
        assert [(n.kind, n.requested_date, n.used_date) for n in lookup.notices] == [
            (NoticeKind.WEEKEND, weekend_day, FRI)
        ]

    def test_unpublished_holiday_falls_back_to_previous_business_day(self):
        provider = FakeProvider({FRI: make_table(FRI)})  # Monday has nothing (holiday)
        lookup = service(provider).lookup(MON)
        assert provider.calls == [MON, FRI]
        assert lookup.used_date == FRI
        assert lookup.notices[0].kind is NoticeKind.NOT_PUBLISHED

    def test_tomorrow_not_yet_published_uses_today(self):
        provider = FakeProvider({WED: make_table(WED)})
        lookup = service(provider, clock=FakeClock(datetime(2026, 11, 18, 10, 0))).lookup(THU)
        assert lookup.used_date == WED
        assert lookup.notices[0].kind is NoticeKind.NOT_YET_PUBLISHED

    def test_gives_up_after_the_fallback_window(self):
        provider = FakeProvider()  # nothing is ever published
        with pytest.raises(RatesNotFoundError) as error:
            service(provider, max_fallback_days=10).lookup(WED)
        assert error.value.requested_date == WED
        assert error.value.earliest_tried == date(2026, 11, 8)
        assert all(not is_weekend(day) for day in provider.calls)
        assert min(provider.calls) >= date(2026, 11, 8)

    def test_successful_answer_refreshes_saved_copy(self, clock):
        cache = InMemoryCache()
        service(FakeProvider({WED: make_table(WED)}), cache, clock).lookup(WED)
        assert cache.copy.table.rate_date == WED
        assert cache.copy.saved_at == clock.now()
        assert cache.copy.source_id == "fake"

    def test_failure_to_save_does_not_break_the_lookup(self):
        lookup = service(FakeProvider({WED: make_table(WED)}), InMemoryCache(fail_on_save=True)).lookup(WED)
        assert lookup.used_date == WED


class TestOffline:
    saved = SavedCopy(make_table(TUE), datetime(2026, 11, 17, 9, 30), "fake")

    @pytest.mark.parametrize("failure", [
        SourceUnavailableError("timed out"),
        MalformedResponseError("broken XML"),
    ])
    def test_source_failure_offers_saved_copy(self, failure):
        provider = FakeProvider({WED: failure})
        with pytest.raises(RatesUnavailableError) as error:
            service(provider, InMemoryCache(self.saved)).lookup(WED)
        assert error.value.cause is failure
        assert error.value.saved.rate_date == TUE
        assert error.value.saved.saved_at == datetime(2026, 11, 17, 9, 30)

    def test_source_failure_without_saved_copy(self):
        with pytest.raises(RatesUnavailableError) as error:
            service(FakeProvider({WED: SourceUnavailableError("offline")})).lookup(WED)
        assert error.value.saved is None

    def test_failure_does_not_overwrite_saved_copy(self):
        cache = InMemoryCache(self.saved)
        with pytest.raises(RatesUnavailableError):
            service(FakeProvider({WED: SourceUnavailableError("offline")}), cache).lookup(WED)
        assert cache.copy is self.saved
        assert cache.saves == 0

    def test_saved_mode_uses_saved_copy_and_says_so(self):
        provider = FakeProvider()
        lookup = service(provider, InMemoryCache(self.saved)).lookup(WED, use_saved=True)
        assert provider.calls == []  # no network in saved mode
        assert lookup.source is SourceKind.SAVED
        assert lookup.used_date == TUE
        assert lookup.saved_at == self.saved.saved_at
        assert lookup.notices[0].kind is NoticeKind.SAVED_COPY

    def test_saved_mode_without_saved_copy(self):
        with pytest.raises(NoSavedCopyError):
            service(FakeProvider()).lookup(WED, use_saved=True)
