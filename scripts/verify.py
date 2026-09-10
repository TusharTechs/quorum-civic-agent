"""One command that reproduces every claim this project makes without a model.

    python scripts/verify.py

Downloads four public PDFs (~274 MB, 5-10 minutes the first time, cached
afterwards), runs the deterministic half of the pipeline, and checks the
result against the figures quoted in the README and the demo video. No AWS
account, no API key, nothing billed: none of these paths call a model.

Exits 0 if every claim holds, 1 if any fails.
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

BASE = "https://berkeleyca.gov/sites/default/files/city-council-meetings/"
JUNE = f"{BASE}2026-06-30%20Agenda%20Packet%20-%20Council%20-%20WEB.pdf"
MAY = f"{BASE}2026-05-07%20Revised%20Special%20Agenda%20Packet%20-%20Council%20-%20WEB.pdf"
ANNOTATED = f"{BASE}2026-06-30%20Annotated%20Agenda%20-%20Council.pdf"
DATES = ["2026-03-10", "2026-03-24", "2026-06-30"]
SENTENCE = "repositioned to capture an area"

results: list[tuple[bool, str, str]] = []


def check(ok: bool, claim: str, found: str) -> bool:
    results.append((ok, claim, found))
    print(f"  {'PASS' if ok else 'FAIL'}  {claim}\n        {found}")
    return ok


def step(n: int, title: str) -> None:
    print(f"\n[{n}/6] {title}\n" + "-" * 72)


def main() -> int:
    if sys.version_info < (3, 10):
        print(f"Python 3.10+ required; this is {sys.version.split()[0]}")
        return 1
    try:
        import pymupdf                                    # noqa: F401
        from quorum.cost import compute
        from quorum.household import load_profile
        from quorum.ingest import fetch_pdf, load_packet
        from quorum.lineage import multi_meeting, resolve
        from quorum.outcomes import load_outcomes
        from quorum.segment import segment, to_dicts
    except ImportError as exc:
        print(f"Dependencies missing ({exc.name}). Activate the virtualenv first:\n"
              "    python -m venv .venv\n"
              "    source .venv/bin/activate    # Windows: .venv\\Scripts\\activate\n"
              "    pip install -r requirements.txt")
        return 1

    started = time.time()
    print("QUORUM - reproducing the published claims, no model calls\n"
          "First run downloads ~274 MB of public PDFs; afterwards it is cached.")
    cache = ROOT / "data" / "cache"
    cache.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- 1
    step(1, "Ingest and segment the 30 June 2026 packet")
    packet = load_packet(JUNE)
    items = segment(packet)
    (cache / "items_2026-06-30.json").write_text(
        json.dumps(to_dicts(items), indent=2), encoding="utf-8")
    check(packet["n_pages"] == 1790, "The packet is 1,790 pages",
          f"n_pages = {packet['n_pages']}")
    check(len(items) == 51, "It segments into 51 agenda items, with no model",
          f"{len(items)} items -> data/cache/items_2026-06-30.json")
    chars = sum(len(pg["text"]) for pg in packet["pages"])
    dollars = (chars / 4) * 3.0 / 1e6          # ~4 chars/token, Sonnet 4.5 input
    check(chars > 7_000_000,
          "Reading it whole would cost far more than routing it",
          f"{chars:,} chars ~ {chars/4:,.0f} tokens ~ ${dollars:,.2f} for one "
          f"frontier pass, against $0.02 routed")

    # ---------------------------------------------------------------- 2
    step(2, "The sentence that changed between two meetings")
    import pymupdf
    may_pdf, _ = fetch_pdf(MAY)
    jun_pdf, _ = fetch_pdf(JUNE)
    with pymupdf.open(may_pdf) as doc:
        may_pages = doc.page_count
        may_hits = [p + 1 for p in range(doc.page_count) if doc[p].search_for(SENTENCE)]
    with pymupdf.open(jun_pdf) as doc:
        jun_hits = [p + 1 for p in range(doc.page_count) if doc[p].search_for(SENTENCE)]
        p1394 = doc[1393].get_text()
    check(may_pages == 176 and not may_hits,
          f"Absent from the 7 May packet: '{SENTENCE}'",
          f"{may_pages} pages, {len(may_hits)} matches")
    check(jun_hits == [1395, 1402, 1413, 1415],
          "Present four times in the 30 June packet",
          f"pages {jun_hits}")
    check("feasibility of notifying camera owners" in p1394
          and "not a minimum requirement" in p1394,
          "Page 1394 demotes the committee's request",
          "'...describe the feasibility of notifying camera owners...' / "
          "'...not a minimum requirement for vendor selection.'")

    # ---------------------------------------------------------------- 3
    step(3, "The same decision across three meetings")
    meetings = {}
    for date in DATES:
        path = cache / f"items_{date}.json"
        if not path.exists():
            url = f"{BASE}{date}%20Agenda%20Packet%20-%20Council%20-%20WEB.pdf"
            p = load_packet(url)
            path.write_text(json.dumps(to_dicts(segment(p)), indent=2), encoding="utf-8")
            print(f"        {date}: {p['n_pages']} pages -> {path.name}")
        meetings[date] = json.loads(path.read_text(encoding="utf-8"))
    tracked = multi_meeting(resolve(meetings))
    zoning = next((l for l in tracked if l.canonical_id == "23.324.050"), None)
    if zoning is None:
        check(False, "BMC 23.324.050 is tracked across meetings", "lineage not found")
    else:
        v = {x.meeting_date: x for x in zoning.versions}
        a, b = v.get("2026-03-10"), v.get("2026-03-24")
        check(bool(a and b) and a.item_number == 14 and not a.ordinance
              and b.item_number == 1 and b.ordinance == "8,003-N.S.",
              "One ordinance, renumbered between meetings",
              f"10 Mar: item {a.item_number} ord={a.ordinance or '-'}  ->  "
              f"24 Mar: item {b.item_number} ord={b.ordinance}")

    # ---------------------------------------------------------------- 4
    step(4, "What this household pays, computed in code")
    cost = compute(meetings["2026-06-30"], load_profile())
    check(round(cost.annual_total, 2) == 2199.92,
          "Thirteen items tax this household: $2,199.92 a year",
          f"${cost.annual_total:,.2f} across {len(cost.item_numbers)} items")
    over = cost.naive_total - cost.annual_total
    check(round(cost.naive_total, 2) == 3529.28 and round(over, 2) == 1329.36,
          "Summing every 'per square foot' rate overstates it",
          f"naive ${cost.naive_total:,.2f}, overstated by ${over:,.2f}")
    item4 = next((r for r in cost.excluded if r.item_number == 4), None)
    check(item4 is not None and "non-profit" in (item4.excluded_reason or ""),
          "The biggest rate on the page is correctly excluded",
          f"item 4 excluded - {item4.excluded_reason if item4 else 'not excluded'}")

    # ---------------------------------------------------------------- 5
    step(5, "What the council actually decided")
    ann_path = cache / "items_2026-06-30-ANNOTATED.json"
    if not ann_path.exists():
        ann = load_packet(ANNOTATED)
        ann_path.write_text(json.dumps(to_dicts(segment(ann)), indent=2), encoding="utf-8")
    outcomes = load_outcomes(json.loads(ann_path.read_text(encoding="utf-8")))
    check(len(outcomes) == len(meetings["2026-06-30"]),
          "Every item's outcome is read from the published record",
          f"{len(outcomes)}/{len(meetings['2026-06-30'])} items")
    one = outcomes.get(1)
    check(one is not None and one.instrument == "Ordinance 8,012-N.S.",
          "Item 1 was adopted as Ordinance 8,012-N.S.",
          f"item 1 -> {one.headline if one else 'missing'}")

    # ---------------------------------------------------------------- 6
    step(6, "Summary")
    failed = [c for ok, c, _ in results if not ok]
    print(f"  {len(results) - len(failed)}/{len(results)} claims reproduced "
          f"in {time.time() - started:.0f}s, without calling a model.")
    if failed:
        print("\n  FAILED:")
        for c in failed:
            print(f"    - {c}")
        return 1
    print("\n  Next, with model credentials:\n"
          "    python scripts/run_action.py   draft -> grounding -> interrupt -> refusal\n"
          "    python scripts/run_eval.py 5 --quiet   precision, recall, variance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
