"""Ingest and segment several packets by meeting date."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.ingest import load_packet          # noqa: E402
from quorum.segment import segment, to_dicts   # noqa: E402

BASE = "https://berkeleyca.gov/sites/default/files/city-council-meetings/"

for date in sys.argv[1:]:
    url = f"{BASE}{date}%20Agenda%20Packet%20-%20Council%20-%20WEB.pdf"
    try:
        packet = load_packet(url)
    except Exception as exc:                     # noqa: BLE001
        print(f"{date}: FAILED {type(exc).__name__}: {str(exc)[:90]}")
        continue
    items = segment(packet)
    out = Path(f"data/cache/items_{date}.json")
    out.write_text(json.dumps(to_dicts(items), indent=2), encoding="utf-8")
    print(f"{date}: {packet['n_pages']:>5} pages, {packet['bytes']/1e6:>5.1f} MB, "
          f"{len(items):>2} items -> {out.name}")
