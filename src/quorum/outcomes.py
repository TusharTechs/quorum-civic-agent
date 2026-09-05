"""Verification: what the council actually did.

Berkeley publishes an Annotated Agenda after each meeting recording the action
taken on every item. It parses with the same segmenter as the agenda packet —
the only difference is two extra field labels — so outcomes join to items by
number without any new machinery.

This is the step that turns an alert into a record: the household was told an
item mattered, and afterwards it can be told what happened to it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# "M/S/C (Blackaby/Humbert) to adopt Resolution No. 72,369-N.S."
MOTION = re.compile(r"M/S/C\s*\(([^)]+)\)", re.I)
SPEAKERS = re.compile(r"(\d+)\s+speakers?", re.I)
ORDINANCE = re.compile(r"Ordinance No\.\s*([\d,]+)\s*[-–]\s*N\.\s*S\.", re.I)
RESOLUTION = re.compile(r"Resolution No\.\s*([\d,]+)\s*[-–]\s*N\.\s*S\.", re.I)
CONTINUED = re.compile(
    r"to continue (?:Item )?\d*\s*to the ([A-Z][a-z]+ \d{1,2}, \d{4})", re.I)


@dataclass
class Outcome:
    item_number: int
    page: int
    disposition: str          # adopted | continued | referred | other
    text: str
    speakers: int | None = None
    movers: str | None = None
    instrument: str | None = None      # ordinance or resolution number
    continued_to: str | None = None

    @property
    def headline(self) -> str:
        if self.disposition == "continued":
            return f"Continued to {self.continued_to}"
        if self.instrument:
            return f"{self.disposition.title()} — {self.instrument}"
        return self.disposition.title()


def _classify(text: str) -> str:
    low = text.lower()
    if "to continue" in low:
        return "continued"
    if "adopted" in low or "to adopt" in low or "approved" in low:
        return "adopted"
    if "refer" in low:
        return "referred"
    if "withdraw" in low:
        return "withdrawn"
    return "other"


def parse_outcome(item: dict) -> Outcome | None:
    """Build an Outcome from one segmented annotated-agenda item."""
    text = " ".join(item["fields"].get("Action:", "").split())
    if not text:
        return None

    ordinance = ORDINANCE.search(text)
    resolution = RESOLUTION.search(text)
    speakers = SPEAKERS.search(text)
    movers = MOTION.search(text)
    continued = CONTINUED.search(text)

    instrument = None
    if ordinance:
        instrument = f"Ordinance {ordinance.group(1)}-N.S."
    elif resolution:
        instrument = f"Resolution {resolution.group(1)}-N.S."

    return Outcome(
        item_number=item["number"],
        page=item["page"],
        disposition=_classify(text),
        text=text,
        speakers=int(speakers.group(1)) if speakers else None,
        movers=movers.group(1) if movers else None,
        instrument=instrument,
        continued_to=continued.group(1) if continued else None,
    )


def load_outcomes(annotated_items: list[dict]) -> dict[int, Outcome]:
    """Map item number -> Outcome for every item with a recorded action."""
    parsed = (parse_outcome(item) for item in annotated_items)
    return {o.item_number: o for o in parsed if o is not None}
