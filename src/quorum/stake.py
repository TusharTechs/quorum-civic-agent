"""Stake matching: which of ~50 agenda items actually touch this household.

Two stages, routed by cost (brief §9):
  triage  — Nova Lite over every item's title + recommendation. Structural,
            high volume, invisible quality. ~$0.001 for a whole packet.
  brief   — Claude Sonnet on the handful that survive. This is what the judge
            reads, so this is where the money goes.

Every alert must carry a page citation, because an uncitable claim is worthless
(brief §14: provenance on every extracted claim).
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from strands import Agent
from strands.models import BedrockModel

from .household import describe

REGION = "us-west-2"
TRIAGE_MODEL = "us.amazon.nova-lite-v1:0"
DEEP_MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

# Truncate each item for triage; the full text is only read for survivors.
TRIAGE_CHARS = 600


class TriagedItem(BaseModel):
    item_number: int = Field(description="The agenda item number")
    affects_household: bool = Field(
        description="True only if this item plausibly changes something for THIS household"
    )
    stake: str = Field(
        description="Which specific part of the household profile it touches, or 'none'"
    )


class TriageResult(BaseModel):
    items: list[TriagedItem]


class Alert(BaseModel):
    item_numbers: list[int] = Field(
        description="Every agenda item this one decision spans. Group items that "
                    "are the same decision rather than alerting on each separately."
    )
    what: str = Field(description="One sentence: what the council is deciding")
    why_you: str = Field(description="One sentence tying it to THIS household's specifics")
    why_now: str = Field(description="The deadline or timing that makes this urgent")
    evidence_quote: str = Field(
        description="A short verbatim quote from the item text supporting the claim"
    )


class AlertSet(BaseModel):
    alerts: list[Alert]


def _model(model_id: str) -> BedrockModel:
    return BedrockModel(model_id=model_id, region_name=REGION)


def triage(items: list[dict], profile: dict) -> tuple[TriageResult, dict]:
    """Cheap pass over every item. Returns (result, token usage)."""
    listing = "\n".join(
        f"{item['number']}. {item['title']}\n   "
        f"{item['fields'].get('Recommendation:', '')[:TRIAGE_CHARS]}"
        for item in items
    )
    agent = Agent(
        model=_model(TRIAGE_MODEL),
        system_prompt=(
            "You triage city council agenda items for one household. Be strict: "
            "most items affect nobody in particular. Mark affects_household true "
            "only when the item changes something concrete for this household "
            "given their address, tenure, commute, school, parking or taxes."
        ),
    )
    prompt = (
        f"HOUSEHOLD PROFILE\n{describe(profile)}\n\n"
        f"AGENDA ITEMS\n{listing}\n\n"
        "Return a verdict for every item number listed."
    )
    result = agent(prompt, structured_output_model=TriageResult)
    return result.structured_output, result.metrics.accumulated_usage


def build_alerts(
    candidates: list[dict], profile: dict, meeting_date: str
) -> tuple[AlertSet, dict]:
    """Expensive pass over survivors only. Produces the four-question alert."""
    detail = "\n\n".join(
        f"ITEM {item['number']} (agenda page {item['page']})\n"
        f"TITLE: {item['title']}\n"
        f"RECOMMENDATION: {item['fields'].get('Recommendation:', '')}\n"
        f"FINANCIAL IMPLICATIONS: {item['fields'].get('Financial Implications:', '')}"
        for item in candidates
    )
    agent = Agent(
        model=_model(DEEP_MODEL),
        system_prompt=(
            "You write the alert a resident reads. Four questions, in order: "
            "WHAT the council is deciding, WHY IT AFFECTS THIS HOUSEHOLD "
            "specifically, WHY NOW, and the EVIDENCE. "
            "Never assert a fact that is not present in the item text you were "
            "given. Quote verbatim for evidence. Be concrete and plain; no "
            "hedging, no 'may potentially'. Never call this an AI summary."
        ),
    )
    prompt = (
        f"HOUSEHOLD PROFILE\n{describe(profile)}\n\n"
        f"MEETING DATE: {meeting_date}\n\n"
        f"CANDIDATE ITEMS\n{detail}\n\n"
        "Write one alert per DECISION, not per agenda item. Where several "
        "items are the same decision split across the agenda (for example a "
        "set of annual tax rates), consolidate them into a single alert and "
        "state the combined effect on this household. Omit anything that does "
        "not genuinely warrant their attention."
    )
    result = agent(prompt, structured_output_model=AlertSet)
    return result.structured_output, result.metrics.accumulated_usage
