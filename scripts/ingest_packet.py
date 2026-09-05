"""Day 1: ingest one real packet and report what we got."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.ingest import load_packet  # noqa: E402

PACKET_URL = (
    "https://berkeleyca.gov/sites/default/files/city-council-meetings/"
    "2026-06-30%20Agenda%20Packet%20-%20Council%20-%20WEB.pdf"
)

packet = load_packet(PACKET_URL)

pages = packet["pages"]
total_chars = sum(p["chars"] for p in pages)
empty = [p["page"] for p in pages if p["chars"] < 50]

print(f"source      : {packet['source_url']}")
print(f"retrieved   : {packet['retrieved_at']}")
print(f"sha256      : {packet['sha256'][:16]}...")
print(f"size        : {packet['bytes'] / 1_048_576:.1f} MB")
print(f"pages       : {packet['n_pages']}")
print(f"characters  : {total_chars:,}")
print(f"est. tokens : ~{total_chars // 4:,}")
print(f"image-only  : {len(empty)} pages with <50 chars (OCR fallback candidates)")
if empty[:15]:
    print(f"              first few: {empty[:15]}")
