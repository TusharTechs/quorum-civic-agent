"""QUORUM capabilities exposed to the deployed agent as tools.

The heavy lifting lives in the `quorum` package, which is installed as a
dependency rather than copied here. Each tool is a thin, well-described wrapper
so the model can choose between them; the reasoning that matters happens inside
the package, where it is deterministic and testable.

Nothing here can file anything. Submission is gated by Cedar in
`quorum.policy`, outside this code.
"""

from __future__ import annotations

import json
import os

# The package resolves its cache location at import time, so this must be set
# before any quorum module is imported. The runtime filesystem is read-only
# apart from /tmp.
os.environ.setdefault("QUORUM_CACHE_DIR", "/tmp/quorum-cache")

from strands import tool  # noqa: E402

from quorum.action import check_grounding, draft_comment, gate
from quorum.household import load_profile
from quorum.lineage import multi_meeting, resolve
from quorum.outcomes import load_outcomes
from quorum.pipeline import RunContext, build_graph
from quorum.segment import segment, to_dicts
from quorum.ingest import load_packet


@tool
def analyse_packet(packet_url: str, meeting_date: str) -> str:
    """Read a published agenda packet and surface only what affects this household.

    Runs the full lifecycle: fetch, parse, segment into agenda items, triage
    every item cheaply, then reason in depth over the few that survive. Returns
    the decisions worth this household's attention, each with a page citation,
    plus what the run cost.

    Args:
        packet_url: URL of the published agenda packet PDF.
        meeting_date: Human-readable meeting date, e.g. "Tuesday, 30 June 2026".
    """
    ctx = RunContext(packet_url=packet_url, meeting_date=meeting_date)
    build_graph(ctx)("Process the published packet for this household.")

    alerts = []
    if ctx.alerts:
        by_number = {i["number"]: i for i in ctx.items}
        for alert in ctx.alerts.alerts:
            pages = sorted({by_number[n]["page"] for n in alert.item_numbers
                            if n in by_number})
            alerts.append({
                "items": alert.item_numbers,
                "what": alert.what,
                "why_you": alert.why_you,
                "why_now": alert.why_now,
                "evidence": alert.evidence_quote,
                "cite": f"{packet_url}#page={pages[0]}" if pages else packet_url,
            })

    return json.dumps({
        "pages": ctx.packet["n_pages"] if ctx.packet else 0,
        "items": len(ctx.items),
        "candidates": len(ctx.candidates),
        "decisions": len(alerts),
        "alerts": alerts,
        "path": ctx.log,
        "usage": ctx.usage,
    }, default=str)


@tool
def track_decision(packet_urls: list[str], meeting_dates: list[str]) -> str:
    """Resolve the same decision across several meetings, despite renaming.

    Agenda items are renumbered, moved between calendars, and only acquire an
    ordinance number once they pass. This matches them on hard identifiers so a
    decision can be followed over months.

    Args:
        packet_urls: Packet URLs, oldest first.
        meeting_dates: Matching meeting dates in ISO form, e.g. "2026-03-10".
    """
    meetings = {}
    for url, date in zip(packet_urls, meeting_dates):
        meetings[date] = to_dicts(segment(load_packet(url)))

    tracked = []
    for lineage in multi_meeting(resolve(meetings)):
        tracked.append({
            "canonical_id": lineage.canonical_id,
            "confidence": lineage.confidence,
            "renumbered": lineage.renumbered,
            "gained_ordinance": lineage.gained_ordinance,
            "versions": [
                {"meeting": v.meeting_date, "item": v.item_number, "page": v.page,
                 "stage": v.calendar_hint, "ordinance": v.ordinance,
                 "title": v.title, "cite": v.citation}
                for v in lineage.versions
            ],
        })
    return json.dumps({"lineages": tracked}, default=str)


@tool
def verify_outcome(annotated_agenda_url: str, item_numbers: list[int]) -> str:
    """Report what the council actually decided, from the published record.

    Reads the Annotated Agenda, which records the action taken on every item,
    and returns the disposition for the items given.

    Args:
        annotated_agenda_url: URL of the Annotated Agenda PDF.
        item_numbers: Agenda item numbers to report on.
    """
    items = to_dicts(segment(load_packet(annotated_agenda_url)))
    outcomes = load_outcomes(items)
    wanted = set(item_numbers)
    return json.dumps({
        "outcomes": [
            {"item": o.item_number, "disposition": o.disposition,
             "headline": o.headline, "instrument": o.instrument,
             "speakers": o.speakers, "moved_by": o.movers,
             "continued_to": o.continued_to,
             "cite": f"{annotated_agenda_url}#page={o.page}"}
            for n, o in sorted(outcomes.items()) if n in wanted
        ]
    }, default=str)


@tool
def prepare_comment(packet_url: str, item_number: int, meeting_date: str,
                    has_standing: bool = False) -> str:
    """Draft a public comment, verify every claim, and ask the policy engine.

    Drafts the comment, checks in code that each factual assertion is traceable
    to a cited packet page, then asks Cedar whether it may be filed. A draft
    that passes every check is still refused when the configured identity has no
    standing in the jurisdiction. This tool never files anything.

    Args:
        packet_url: URL of the published agenda packet PDF.
        item_number: The agenda item to comment on.
        meeting_date: Human-readable meeting date.
        has_standing: Whether the configured identity is a verified stakeholder
            in this jurisdiction.
    """
    from quorum.stake import build_alerts

    items = {i["number"]: i for i in to_dicts(segment(load_packet(packet_url)))}
    item = items.get(item_number)
    if item is None:
        return json.dumps({"error": f"item {item_number} not on this agenda"})

    profile = load_profile()
    alerts, _ = build_alerts([item], profile, meeting_date)
    if not alerts.alerts:
        return json.dumps({"error": "no alert generated for this item"})

    draft = draft_comment(alerts.alerts[0], item, profile, meeting_date)
    source = f"{item['title']} {item['fields'].get('Recommendation:', '')}"
    grounding = check_grounding(draft, source)
    decision = gate(grounding, human_approved=True, approval_age_hours=0,
                    has_standing=has_standing)

    return json.dumps({
        "subject": draft.subject,
        "position": draft.position,
        "body": draft.body,
        "grounding": {
            "quotes_verified": f"{grounding.quotes_verified}/{grounding.quotes_checked}",
            "uncited_claims": grounding.uncited_sentences,
            "fabricated_quotes": grounding.unverified_quotes,
            "all_claims_cited": grounding.all_claims_cited,
        },
        "policy": {
            "allowed": decision.allowed,
            "headline": decision.headline,
            "reasons": decision.reasons,
        },
        "filed": False,
    }, default=str)


QUORUM_TOOLS = [analyse_packet, track_decision, verify_outcome, prepare_comment]
