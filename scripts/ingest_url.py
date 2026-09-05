"""Ingest and segment a packet by full URL, for non-standard filenames."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.ingest import load_packet          # noqa: E402
from quorum.segment import segment, to_dicts   # noqa: E402

url, label = sys.argv[1], sys.argv[2]
packet = load_packet(url)
items = segment(packet)
out = Path(f"data/cache/items_{label}.json")
out.write_text(json.dumps(to_dicts(items), indent=2), encoding="utf-8")
print(f"{label}: {packet['n_pages']} pages, {packet['bytes']/1e6:.1f} MB, {len(items)} items")
