"""Segment a packet into agenda items.

Berkeley's front matter is rigidly structured, so segmentation is pure Python
and costs nothing (brief §9: never pay an LLM for extraction). An LLM is only
needed where structure runs out.

Listing format, one block per item:

    N.
    <title, one or more lines>
    From: <originating body>
    Recommendation: <text, often containing the actual rates and dollar amounts>
    Financial Implications: <text>
    Contact: <name, department, phone>
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Iterator

FIELD_LABELS = (
    "From:",
    "Recommendation:",
    "Financial Implications:",
    "Policy Committee Recommendation:",
    "Contact:",
    "Vote:",
    "First Reading Vote:",
    # Annotated agendas carry what the Council actually did.
    "Action:",
    "Recommendation Adopted:",
)

# An item begins with its number alone on a line.
ITEM_START = re.compile(r"^[ \t]*(\d{1,3})\.[ \t]*$", re.M)

# The agenda listing ends here. Without this the final item absorbs the
# boilerplate that follows it (legal notices, adjournment, minutes text).
LISTING_END = re.compile(
    r"^[ 	]*(Public Comment\s*[-–]\s*Items Not Listed|Adjournment|"
    r"NOTICE CONCERNING YOUR LEGAL RIGHTS)",
    re.M,
)


@dataclass
class AgendaItem:
    number: int
    title: str
    page: int                      # page of the agenda listing where it appears
    fields: dict[str, str] = field(default_factory=dict)
    source_url: str = ""
    retrieved_at: str = ""

    @property
    def recommendation(self) -> str:
        return self.fields.get("Recommendation:", "")


def _page_index(pages: list[dict]) -> tuple[str, list[tuple[int, int]]]:
    """Concatenate page text and record (offset, page_number) for each page."""
    parts: list[str] = []
    offsets: list[tuple[int, int]] = []
    cursor = 0
    for page in pages:
        offsets.append((cursor, page["page"]))
        text = page["text"]
        parts.append(text)
        cursor += len(text)
    return "".join(parts), offsets


def _page_for(offset: int, offsets: list[tuple[int, int]]) -> int:
    page = offsets[0][1]
    for start, number in offsets:
        if start > offset:
            break
        page = number
    return page


def _split_fields(block: str) -> tuple[str, dict[str, str]]:
    """Split an item block into its title and its labelled fields."""
    label_pattern = "|".join(re.escape(label) for label in FIELD_LABELS)
    matches = list(re.finditer(rf"^[ \t]*({label_pattern})", block, re.M))

    if not matches:
        return " ".join(block.split()), {}

    title = " ".join(block[: matches[0].start()].split())
    fields: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        label = match.group(1)
        value = block[match.end() : end]
        fields[label] = " ".join(value.split())
    return title, fields


def segment(packet: dict, *, listing_pages: int = 30) -> list[AgendaItem]:
    """Extract the canonical agenda item list from a packet's front matter.

    Item numbers must run consecutively from 1; a numbered line that isn't the
    next expected number is a sub-item inside a recommendation, not a new item.
    """
    pages = [p for p in packet["pages"] if p["page"] <= listing_pages]
    text, offsets = _page_index(pages)

    starts: list[tuple[int, int, int]] = []  # (offset, end_of_marker, number)
    expected = 1
    for match in ITEM_START.finditer(text):
        number = int(match.group(1))
        if number == expected:
            starts.append((match.start(), match.end(), number))
            expected += 1

    tail = LISTING_END.search(text, starts[-1][1]) if starts else None
    listing_end = tail.start() if tail else len(text)

    items: list[AgendaItem] = []
    for index, (start, marker_end, number) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else listing_end
        title, fields = _split_fields(text[marker_end:end])
        items.append(
            AgendaItem(
                number=number,
                title=title,
                page=_page_for(start, offsets),
                fields=fields,
                source_url=packet["source_url"],
                retrieved_at=packet["retrieved_at"],
            )
        )
    return items


def to_dicts(items: list[AgendaItem]) -> list[dict]:
    return [asdict(item) for item in items]
