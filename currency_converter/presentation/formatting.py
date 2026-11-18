"""Display formatting in Russian conventions: '1 234,56', '18.11.2026' (research R5, FR-019)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

GROUP_SEPARATOR = " "  # no-break space, keeps a number on one line
DECIMAL_SEPARATOR = ","
AMOUNT_PLACES = 2
RATE_PLACES = 4
SMALL_VALUE_SIGNIFICANT_DIGITS = 2


def quantize(value: Decimal, places: int) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def _places_for(value: Decimal, places: int) -> int:
    """Enough places to keep a tiny non-zero value visible (2 significant digits)."""
    threshold = Decimal(1).scaleb(-places)
    if value != 0 and abs(value) < threshold:
        return -value.adjusted() + SMALL_VALUE_SIGNIFICANT_DIGITS - 1
    return places


def plain_decimal(value: Decimal, places: int) -> str:
    """Machine-readable string with a dot: '1000.50'."""
    return f"{quantize(value, _places_for(value, places)):f}"


def format_decimal(value: Decimal, places: int) -> str:
    rounded = quantize(value, _places_for(value, places))
    sign = "-" if rounded < 0 else ""
    integer, _, fraction = f"{abs(rounded):f}".partition(".")
    groups = []
    while len(integer) > 3:
        groups.insert(0, integer[-3:])
        integer = integer[:-3]
    groups.insert(0, integer)
    text = GROUP_SEPARATOR.join(groups)
    return f"{sign}{text}{DECIMAL_SEPARATOR}{fraction}" if fraction else f"{sign}{text}"


def format_amount(value: Decimal) -> str:
    return format_decimal(value, AMOUNT_PLACES)


def format_rate(value: Decimal) -> str:
    return format_decimal(value, RATE_PLACES)


def format_date(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def format_datetime(value: datetime) -> str:
    return value.strftime("%d.%m.%Y %H:%M")
