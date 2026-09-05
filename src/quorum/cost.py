"""What a meeting's tax items actually cost one household.

The hard part is not arithmetic, it is classification. A single agenda uses
three different rate bases and phrases them almost identically:

    "$0.06297 (6.297 cents) per square foot for dwelling units"
    "$0.02339 (2.339 cents) per square foot of improvements"
    "$0.9168 (91.68 cents) per square foot of improvements"   <- non-profits only
    "at 0.0075%"                                              <- of assessed value
    "65.1005 cents ... for each prearranged trip"              <- not property at all

Summing everything that says "per square foot" overstates a 1,450 sq ft
household by $1,329 a year, because the largest such rate on the page applies
only to large non-profits. Every rate therefore carries the basis it was
classified as and the page it came from, so a wrong answer is traceable rather
than merely wrong.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# "$0.06297 (6.297 cents) per square foot ..." or "$0.17842 per square foot ..."
PER_SQFT = re.compile(
    r"\$?(?P<rate>\d\.\d{3,6})\s*(?:\([\d.]+\s*cents?\)\s*)?"
    r"per square foot(?P<qualifier>[^.;]*)",
    re.I,
)
AD_VALOREM = re.compile(r"\bat\s+(?P<rate>\d+\.\d+)\s*%", re.I)
PER_TRIP = re.compile(r"per|for each\s+.{0,30}trip", re.I)

# Rates that are phrased like a dwelling rate but are not one.
NON_DWELLING = re.compile(r"non-?profit", re.I)

ORDINANCE = re.compile(r"Ordinance\s+(?:No\.\s*)?([\d,]+)\s*[-–]\s*N\.?\s*S\.?", re.I)


@dataclass
class Rate:
    item_number: int
    page: int
    title: str
    basis: str                 # per_sqft_dwelling | assessed_value | excluded
    value: float               # $/sq ft, or percent of assessed value
    quote: str                 # the verbatim phrase it was read from
    ordinance: str | None = None
    excluded_reason: str | None = None


@dataclass
class HouseholdCost:
    dwelling_sqft: int
    assessed_value_usd: int
    rates: list[Rate] = field(default_factory=list)

    @property
    def included(self) -> list[Rate]:
        return [r for r in self.rates if r.basis != "excluded"]

    @property
    def excluded(self) -> list[Rate]:
        return [r for r in self.rates if r.basis == "excluded"]

    @property
    def sqft_rate_total(self) -> float:
        return sum(r.value for r in self.rates if r.basis == "per_sqft_dwelling")

    @property
    def assessed_percent_total(self) -> float:
        return sum(r.value for r in self.rates if r.basis == "assessed_value")

    @property
    def sqft_cost(self) -> float:
        return self.dwelling_sqft * self.sqft_rate_total

    @property
    def assessed_cost(self) -> float:
        return self.assessed_value_usd * self.assessed_percent_total / 100

    @property
    def annual_total(self) -> float:
        return self.sqft_cost + self.assessed_cost

    @property
    def naive_total(self) -> float:
        """What a summariser gets by adding every 'per square foot' rate."""
        every = sum(r.value for r in self.rates
                    if r.basis == "per_sqft_dwelling"
                    or (r.basis == "excluded" and r.quote and "square foot" in r.quote))
        return self.dwelling_sqft * every + self.assessed_cost

    @property
    def item_numbers(self) -> list[int]:
        return sorted({r.item_number for r in self.included})


def classify(item: dict) -> Rate | None:
    """Read one agenda item's rate, and say which basis it is on."""
    recommendation = " ".join(item["fields"].get("Recommendation:", "").split())
    if not recommendation:
        return None

    ordinance_match = ORDINANCE.search(recommendation)
    ordinance = f"{ordinance_match.group(1)}-N.S." if ordinance_match else None

    common = dict(item_number=item["number"], page=item["page"],
                  title=item["title"], ordinance=ordinance)

    sqft = PER_SQFT.search(recommendation)
    if sqft:
        quote = " ".join(sqft.group(0).split())
        # Order matters: a non-profit rate is phrased like a dwelling rate.
        if NON_DWELLING.search(recommendation):
            return Rate(basis="excluded", value=float(sqft.group("rate")),
                        quote=quote,
                        excluded_reason="applies to large non-profits, not dwellings",
                        **common)
        return Rate(basis="per_sqft_dwelling", value=float(sqft.group("rate")),
                    quote=quote, **common)

    advalorem = AD_VALOREM.search(recommendation)
    if advalorem:
        quote = " ".join(advalorem.group(0).split())
        return Rate(basis="assessed_value", value=float(advalorem.group("rate")),
                    quote=quote, **common)

    if "trip" in recommendation.lower() and "tax rate" in recommendation.lower():
        return Rate(basis="excluded", value=0.0,
                    quote="per prearranged trip",
                    excluded_reason="charged per ride, not on property", **common)

    return None


def compute(items: list[dict], profile: dict) -> HouseholdCost:
    """Total what this meeting's rate items cost this household in a year."""
    rates = [r for r in (classify(item) for item in items) if r is not None]
    return HouseholdCost(
        dwelling_sqft=profile["dwelling_sqft"],
        assessed_value_usd=profile["assessed_value_usd"],
        rates=rates,
    )
