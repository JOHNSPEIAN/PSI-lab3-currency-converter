"""Currency conversion through the base currency MDL, exact Decimal arithmetic."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from currency_converter.domain.models import Currency, RateTable

ONE = Decimal(1)


@dataclass(frozen=True)
class Conversion:
    amount: Decimal
    source: Currency
    target: Currency
    result: Decimal
    rate: Decimal
    """1 source = ``rate`` target."""
    inverse_rate: Decimal
    """1 target = ``inverse_rate`` source."""


class CurrencyConverter:
    def convert(self, amount: Decimal, source_code: str, target_code: str,
                table: RateTable) -> Conversion:
        source = table.find(source_code)
        target = table.find(target_code)
        if source.code == target.code:
            rate = inverse = ONE
        else:
            rate = table.per_unit(source.code) / table.per_unit(target.code)
            inverse = table.per_unit(target.code) / table.per_unit(source.code)
        return Conversion(amount, source, target, amount * rate, rate, inverse)
