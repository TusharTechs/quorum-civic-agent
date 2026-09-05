"""Packet ingest: fetch a published agenda packet once, cache it, extract text.

Two rules from the brief drive this module:
  §9  Never pay an LLM for extraction, and parse each packet exactly once, ever.
  §14 Provenance on every extracted claim: source URL, page, retrieved-at.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import httpx

from .paths import cache_dir

CACHE_DIR = cache_dir()

# Berkeley's WAF returns 403 to HEAD requests and to unadorned clients, but
# serves GET normally. Probe with a ranged GET, never HEAD.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _slug(url: str) -> str:
    """Stable, filesystem-safe id for a source URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def fetch_pdf(url: str, *, refresh: bool = False) -> tuple[Path, dict]:
    """Download a packet PDF to the disk cache. Returns (path, provenance).

    A cached packet is never re-fetched unless refresh=True.
    """
    pdf_dir = CACHE_DIR / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{_slug(url)}.pdf"
    meta_path = pdf_path.with_suffix(".meta.json")

    if pdf_path.exists() and meta_path.exists() and not refresh:
        return pdf_path, json.loads(meta_path.read_text())

    with httpx.stream(
        "GET", url, headers=HEADERS, follow_redirects=True, timeout=120.0
    ) as response:
        response.raise_for_status()
        with pdf_path.open("wb") as handle:
            for chunk in response.iter_bytes(chunk_size=1 << 16):
                handle.write(chunk)

    provenance = {
        "source_url": url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
        "bytes": pdf_path.stat().st_size,
    }
    meta_path.write_text(json.dumps(provenance, indent=2))
    return pdf_path, provenance


def extract_pages(pdf_path: Path, provenance: dict, *, refresh: bool = False) -> dict:
    """Extract per-page text. Cached, so a packet is parsed exactly once.

    Pages are 1-indexed to match how a human cites a packet ("page 287").
    """
    text_dir = CACHE_DIR / "text"
    text_dir.mkdir(parents=True, exist_ok=True)
    out_path = text_dir / f"{pdf_path.stem}.json"

    if out_path.exists() and not refresh:
        return json.loads(out_path.read_text())

    with pymupdf.open(pdf_path) as document:
        pages = [
            {
                "page": index + 1,
                "text": page.get_text(),
                "chars": len(page.get_text()),
            }
            for index, page in enumerate(document)
        ]
        document_meta = {"n_pages": document.page_count}

    record = {**provenance, **document_meta, "pages": pages}
    out_path.write_text(json.dumps(record, indent=2))
    return record


def load_packet(url: str, *, refresh: bool = False) -> dict:
    """Fetch + extract in one call, both cached."""
    pdf_path, provenance = fetch_pdf(url, refresh=refresh)
    return extract_pages(pdf_path, provenance, refresh=refresh)
