"""Tier 2: what this meeting's tax items cost this household, with provenance."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.cost import compute            # noqa: E402
from quorum.household import load_profile  # noqa: E402

PACKET_URL = ("https://berkeleyca.gov/sites/default/files/city-council-meetings/"
              "2026-06-30%20Agenda%20Packet%20-%20Council%20-%20WEB.pdf")

items = json.loads(Path("data/cache/items_2026-06-30.json").read_text(encoding="utf-8"))
profile = load_profile()
cost = compute(items, profile)

print(f"household: {profile['dwelling_sqft']:,} sq ft, "
      f"assessed ${profile['assessed_value_usd']:,}\n")

print("PER SQUARE FOOT OF DWELLING")
for r in sorted((x for x in cost.rates if x.basis == "per_sqft_dwelling"),
                key=lambda x: x.item_number):
    print(f"  item {r.item_number:>2}  p{r.page:<3} ${r.value:.5f}/sqft  "
          f"{(r.ordinance or '-'):<12} ${r.value * cost.dwelling_sqft:>8,.2f}")
print(f"  {'':>26}total ${cost.sqft_rate_total:.5f}/sqft  "
      f"{'':<12} ${cost.sqft_cost:>8,.2f}")

print("\nPERCENT OF ASSESSED VALUE")
for r in sorted((x for x in cost.rates if x.basis == "assessed_value"),
                key=lambda x: x.item_number):
    print(f"  item {r.item_number:>2}  p{r.page:<3} {r.value:.4f}%"
          f"{'':<14}{(r.ordinance or '-'):<12} "
          f"${r.value * cost.assessed_value_usd / 100:>8,.2f}")
print(f"  {'':>26}total {cost.assessed_percent_total:.4f}%"
      f"{'':<13} ${cost.assessed_cost:>8,.2f}")

print("\nEXCLUDED — looks like a household rate, is not")
for r in cost.excluded:
    print(f"  item {r.item_number:>2}  p{r.page:<3} {r.value:.5f}  {r.excluded_reason}")
    print(f"            \"{r.quote[:88]}\"")

print("\n" + "=" * 66)
print(f"  ANNUAL TOTAL FOR THIS HOUSEHOLD   ${cost.annual_total:>10,.2f}")
print(f"  across {len(cost.item_numbers)} separate agenda items: {cost.item_numbers}")
print("=" * 66)
overstated = cost.naive_total - cost.annual_total
print(f"\nA naive sum of every 'per square foot' rate gives "
      f"${cost.naive_total:,.2f} — overstating by ${overstated:,.2f}/year.")
print(f"Source: {PACKET_URL}")
