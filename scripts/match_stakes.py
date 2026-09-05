"""Day 2 gate: surface the items that actually touch one household."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.household import load_profile           # noqa: E402
from quorum.stake import triage, build_alerts       # noqa: E402

MEETING_DATE = "Tuesday, 30 June 2026"
PACKET_URL = (
    "https://berkeleyca.gov/sites/default/files/city-council-meetings/"
    "2026-06-30%20Agenda%20Packet%20-%20Council%20-%20WEB.pdf"
)

items = json.loads(Path("data/cache/items_2026-06-30.json").read_text(encoding="utf-8"))
profile = load_profile()

verdicts, triage_usage = triage(items, profile)
hits = [v for v in verdicts.items if v.affects_household]
print(f"triage: {len(items)} items -> {len(hits)} candidates")

by_number = {i["number"]: i for i in items}
candidates = [by_number[v.item_number] for v in hits if v.item_number in by_number]

alerts, deep_usage = build_alerts(candidates, profile, MEETING_DATE)

print("\n" + "=" * 72)
print("Why QUORUM interrupted you")
print("=" * 72)
for alert in alerts.alerts:
    nums = alert.item_numbers
    pages = sorted({by_number[n]["page"] for n in nums if n in by_number})
    label = f"ITEM {nums[0]}" if len(nums) == 1 else f"ITEMS {', '.join(map(str, nums))}"
    plural = "s" if len(pages) > 1 else ""
    print(f"\n{label}  (agenda page{plural} {', '.join(map(str, pages))})")
    print(f"  WHAT     {alert.what}")
    print(f"  WHY YOU  {alert.why_you}")
    print(f"  WHY NOW  {alert.why_now}")
    print(f'  EVIDENCE "{alert.evidence_quote[:140]}"')
    print(f"           {PACKET_URL}#page={pages[0]}")

t_in, t_out = triage_usage["inputTokens"], triage_usage["outputTokens"]
d_in, d_out = deep_usage["inputTokens"], deep_usage["outputTokens"]
cost = (t_in * 0.06 + t_out * 0.24 + d_in * 3.0 + d_out * 15.0) / 1_000_000

print("\n--- attention efficiency ---")
print(f"  1,790 pages -> {len(items)} items -> {len(hits)} candidates "
      f"-> {len(alerts.alerts)} decision(s)")
print("--- tokens ---")
print(f"  triage (Nova Lite) : {t_in:,} in / {t_out:,} out")
print(f"  deep   (Sonnet 4.5): {d_in:,} in / {d_out:,} out")
print(f"  estimated cost this run: ${cost:.4f}")
