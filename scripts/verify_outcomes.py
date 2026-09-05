"""Close the loop: what happened to the items QUORUM flagged."""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.outcomes import load_outcomes   # noqa: E402

ANNOTATED_URL = ("https://berkeleyca.gov/sites/default/files/city-council-meetings/"
                 "2026-06-30%20Annotated%20Agenda%20-%20Council.pdf")

annotated = json.loads(
    Path("data/cache/items_2026-06-30-ANNOTATED.json").read_text(encoding="utf-8"))
packet = {i["number"]: i for i in json.loads(
    Path("data/cache/items_2026-06-30.json").read_text(encoding="utf-8"))}

outcomes = load_outcomes(annotated)
print(f"outcomes recorded: {len(outcomes)}/{len(packet)} items\n")

print("disposition breakdown")
for disp, n in Counter(o.disposition for o in outcomes.values()).most_common():
    print(f"  {disp:12} {n}")

# The items this household was alerted about, plus the tracked policy item.
FLAGGED = [1, 2, 3, 12, 14, 46]
print("\nitems QUORUM flagged for this household")
print("=" * 74)
for n in FLAGGED:
    o = outcomes.get(n)
    if not o:
        continue
    title = packet[n]["title"][:66]
    print(f"\nITEM {n} — {title}")
    print(f"  OUTCOME  {o.headline}")
    if o.speakers:
        print(f"  SPEAKERS {o.speakers}")
    if o.movers:
        print(f"  MOVED BY {o.movers}")
    print(f"  SOURCE   {ANNOTATED_URL}#page={o.page}")

print("\ncontinued items (a lineage that is not finished)")
for n, o in sorted(outcomes.items()):
    if o.disposition == "continued":
        print(f"  item {n:>2}: {o.headline} — {packet[n]['title'][:60]}")
