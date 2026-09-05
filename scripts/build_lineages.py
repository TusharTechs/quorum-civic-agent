"""Day 3 gate: resolve item lineages across meetings and show the drift."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.lineage import resolve, multi_meeting   # noqa: E402

DATES = ["2026-03-10", "2026-03-24", "2026-06-30"]

meetings = {
    d: json.loads(Path(f"data/cache/items_{d}.json").read_text(encoding="utf-8"))
    for d in DATES
}
print("meetings: " + ", ".join(f"{d} ({len(v)} items)" for d, v in meetings.items()))

lineages = resolve(meetings)
tracked = multi_meeting(lineages)
print(f"lineages: {len(lineages)} total, {len(tracked)} spanning >1 meeting\n")

for lineage in tracked:
    print("=" * 74)
    print(f"canonical_id: {lineage.canonical_id}")
    print(f"renumbered={lineage.renumbered}  gained_ordinance={lineage.gained_ordinance}")
    print(f"match reasons: {lineage.outcome['match_reasons']}")
    for v in lineage.versions:
        ordn = v.ordinance or "—"
        print(f"  {v.meeting_date}  item {v.item_number:>2}  p{v.page:<3} "
              f"[{v.calendar_hint or 'n/a':^14}] ord={ordn}")
        print(f"      {v.title[:88]}")
    if len(lineage.aliases) > 1:
        print(f"  aliases: {len(lineage.aliases)} distinct titles")
