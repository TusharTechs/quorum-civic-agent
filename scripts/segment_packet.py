"""Day 1 gate: segment one real packet into agenda items."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.ingest import load_packet          # noqa: E402
from quorum.segment import segment, to_dicts   # noqa: E402

PACKET_URL = (
    "https://berkeleyca.gov/sites/default/files/city-council-meetings/"
    "2026-06-30%20Agenda%20Packet%20-%20Council%20-%20WEB.pdf"
)

packet = load_packet(PACKET_URL)
items = segment(packet)

out = Path("data/cache/items_2026-06-30.json")
out.write_text(json.dumps(to_dicts(items), indent=2), encoding="utf-8")

print(f"packet   : {packet['n_pages']} pages")
print(f"items    : {len(items)}")
print(f"written  : {out}\n")
for item in items:
    flag = "$" if "per square foot" in item.recommendation else " "
    print(f"{flag} {item.number:>2}. p{item.page:<3} {item.title[:78]}")
