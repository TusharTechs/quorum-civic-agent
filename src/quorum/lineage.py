"""Cross-meeting entity resolution and version diff.

This is the part a database cannot do (brief §2, defence 2). The same decision
reappears across meetings under a different item number, a different calendar,
and eventually an ordinance number it did not have the first time. There is no
shared key. Identity has to be *resolved*.

Resolution is deterministic where the documents give us something hard (a BMC
section, an ordinance number) and falls back to title similarity. An LLM is
used only to explain a diff, never to establish identity - identity must be
auditable.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

# Hard identifiers, in order of trustworthiness.
ORDINANCE = re.compile(r"Ordinance\s+(?:No\.\s*)?([\d,]+-N\.S\.)", re.I)
BMC_SECTION = re.compile(r"BMC\s+(?:Title\s+\d+\s+)?(?:Section|Chapter)\s+([\d]+\.[\d.]+)", re.I)
RESOLUTION = re.compile(r"Resolution\s+No\.\s*([\d,]+-N\.S\.)", re.I)

TITLE_MATCH_THRESHOLD = 0.86


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).split() and " ".join(
        re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()
    ) or ""


@dataclass
class Version:
    meeting_date: str
    item_number: int
    title: str
    page: int
    doc_ref: str          # source packet URL
    text_hash: str
    recommendation: str
    calendar_hint: str    # e.g. "first reading" / "second reading"
    ordinance: str | None
    bmc_section: str | None

    @property
    def citation(self) -> str:
        return f"{self.doc_ref}#page={self.page}"


@dataclass
class Lineage:
    canonical_id: str
    versions: list[Version] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    outcome: dict | None = None

    @property
    def confidence(self) -> str:
        """Strong when a hard identifier ties the versions together.

        Title similarity alone is not identity: "Minutes for Approval" appears
        at nearly every meeting and is a standing fixture, not one decision
        travelling across meetings.
        """
        reasons = (self.outcome or {}).get("match_reasons", [])
        hard = any(r.startswith(("same BMC", "same ordinance")) for r in reasons)
        return "strong" if hard else "weak"

    @property
    def renumbered(self) -> bool:
        return len({v.item_number for v in self.versions}) > 1

    @property
    def gained_ordinance(self) -> bool:
        seen = [v.ordinance for v in self.versions]
        return any(o is None for o in seen) and any(o for o in seen)


def _calendar_hint(recommendation: str) -> str:
    low = recommendation.lower()
    for phrase in ("second reading", "first reading", "public hearing"):
        if phrase in low:
            return phrase
    return ""


def to_version(item: dict, meeting_date: str) -> Version:
    rec = item["fields"].get("Recommendation:", "")
    blob = f"{item['title']}\n{rec}"
    ordn = ORDINANCE.search(rec)
    bmc = BMC_SECTION.search(rec) or BMC_SECTION.search(item["title"])
    return Version(
        meeting_date=meeting_date,
        item_number=item["number"],
        title=item["title"],
        page=item["page"],
        doc_ref=item["source_url"],
        text_hash=hashlib.sha256(blob.encode()).hexdigest()[:12],
        recommendation=rec,
        calendar_hint=_calendar_hint(rec),
        ordinance=ordn.group(1) if ordn else None,
        bmc_section=bmc.group(1) if bmc else None,
    )


def _same_decision(a: Version, b: Version) -> tuple[bool, str]:
    """Is this the same underlying decision? Returns (verdict, reason)."""
    if a.bmc_section and a.bmc_section == b.bmc_section:
        return True, f"same BMC section {a.bmc_section}"
    if a.ordinance and a.ordinance == b.ordinance:
        return True, f"same ordinance {a.ordinance}"
    ratio = SequenceMatcher(None, _norm(a.title), _norm(b.title)).ratio()
    if ratio >= TITLE_MATCH_THRESHOLD:
        return True, f"title similarity {ratio:.2f}"
    return False, ""


def resolve(meetings: dict[str, list[dict]]) -> list[Lineage]:
    """Group items across meetings into lineages. Deterministic and auditable."""
    versions: list[Version] = []
    for meeting_date in sorted(meetings):
        for item in meetings[meeting_date]:
            versions.append(to_version(item, meeting_date))

    lineages: list[Lineage] = []
    reasons: dict[int, list[str]] = {}
    for version in versions:
        placed = False
        for index, lineage in enumerate(lineages):
            match, reason = _same_decision(lineage.versions[-1], version)
            if match:
                lineage.versions.append(version)
                if version.title not in lineage.aliases:
                    lineage.aliases.append(version.title)
                reasons[index].append(reason)
                placed = True
                break
        if not placed:
            lineages.append(
                Lineage(
                    canonical_id=(version.bmc_section or version.ordinance
                                  or version.text_hash),
                    versions=[version],
                    aliases=[version.title],
                )
            )
            reasons[len(lineages) - 1] = []

    for index, lineage in enumerate(lineages):
        lineage.outcome = {"match_reasons": reasons.get(index, [])}
    return lineages


def multi_meeting(lineages: list[Lineage], *, strong_only: bool = True) -> list[Lineage]:
    """Lineages that actually span meetings.

    strong_only drops title-similarity-only matches, which are recurring
    fixtures rather than a single decision being tracked.
    """
    spanning = [l for l in lineages if len({v.meeting_date for v in l.versions}) > 1]
    return [l for l in spanning if l.confidence == "strong"] if strong_only else spanning


def diff_versions(earlier: Version, later: Version) -> dict:
    """Textual delta between two versions of the same decision."""
    import difflib

    a = earlier.recommendation.split()
    b = later.recommendation.split()
    added, removed = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag in ("replace", "delete"):
            removed.append(" ".join(a[i1:i2]))
        if tag in ("replace", "insert"):
            added.append(" ".join(b[j1:j2]))
    similarity = difflib.SequenceMatcher(None, earlier.recommendation,
                                         later.recommendation).ratio()
    return {
        "identifier_drift": {
            "item_number": [earlier.item_number, later.item_number],
            "ordinance": [earlier.ordinance, later.ordinance],
            "stage": [earlier.calendar_hint, later.calendar_hint],
            "title_changed": earlier.title != later.title,
        },
        "text_similarity": round(similarity, 4),
        "removed": [t for t in removed if t.strip()],
        "added": [t for t in added if t.strip()],
        "provenance": {
            "from": {"meeting": earlier.meeting_date, "cite": earlier.citation},
            "to": {"meeting": later.meeting_date, "cite": later.citation},
        },
    }


# --- Enacting text -----------------------------------------------------------
# The Recommendation line is only a summary. A substantive amendment between
# readings shows up in the ordinance body, so the diff that matters compares
# enacting text. In a first-reading packet the draft ordinance is embedded in a
# staff report with no closing heading, so the body is bounded by content, not
# by page count.

ENACTING_START = "BE IT ORDAINED"

TERMINATOR = re.compile(
    r"(At a regular meeting|AT A REGULAR MEETING|STAFF REPORT|"
    r"Office of the City Manager|Planning and Development Department|"
    r"Land Use Planning Division)"
)

VOTE = re.compile(
    r"Ayes:\s*(?P<ayes>[^.]*)\.\s*Noes:\s*(?P<noes>[^.]*)\.\s*Absent:\s*(?P<absent>[^.]*)\.",
    re.I,
)


def enacting_text(pages: list[dict], start_page: int, span: int = 6) -> str:
    """The operative text of an ordinance, normalised for comparison."""
    blob = "\n".join(p["text"] for p in pages[start_page - 1 : start_page - 1 + span])
    start = blob.find(ENACTING_START)
    if start < 0:
        return ""
    rest = blob[start:]
    end = TERMINATOR.search(rest, 200)
    return " ".join(rest[: end.start() if end else len(rest)].split())


FURNITURE_WORDS = {"", "of", "page", "ordinance", "no", "n", "s", "ns", "nos"}


def _is_cosmetic(before: str, after: str) -> bool:
    """Whitespace, hyphenation and page furniture are not amendments.

    Packet pages carry running headers ("Page 6 of 11", "Ordinance No.
    8,003-N.S.") that differ between a draft embedded in a staff report and the
    standalone enacted ordinance. Those differences are noise. A block is
    cosmetic when both sides collapse to the same letters, or when every word
    left after removing digits is page furniture.
    """
    squash = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())  # noqa: E731
    if squash(before) == squash(after):
        return True

    def words(text: str) -> set[str]:
        stripped = re.sub(r"[\d]", " ", text.lower())
        return {w for w in re.split(r"[^a-z]+", stripped) if w}

    return (words(before) | words(after)) <= FURNITURE_WORDS


def diff_enacting(draft: str, enacted: str) -> dict:
    """Compare two versions of enacting text, separating substance from noise."""
    from difflib import SequenceMatcher

    a, b = draft.split(), enacted.split()
    substantive, cosmetic = [], []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, a, b).get_opcodes():
        if tag == "equal":
            continue
        before, after = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        (cosmetic if _is_cosmetic(before, after) else substantive).append(
            {"op": tag, "before": before, "after": after}
        )
    return {
        "similarity": round(SequenceMatcher(None, draft, enacted).ratio(), 4),
        "substantive_changes": substantive,
        "cosmetic_changes": len(cosmetic),
        "amended_between_readings": bool(substantive),
    }


def extract_vote(pages: list[dict], start_page: int, span: int = 4) -> dict | None:
    """The recorded vote, which the second-reading packet carries verbatim.

    This fills the `outcome` field of the Civic Change Graph (brief §3) without
    needing the minutes.
    """
    blob = " ".join(p["text"] for p in pages[start_page - 1 : start_page - 1 + span])
    match = VOTE.search(" ".join(blob.split()))
    if not match:
        return None
    split = lambda s: [n.strip() for n in re.split(r",| and ", s) if n.strip()]  # noqa: E731
    ayes, noes, absent = (split(match.group(k)) for k in ("ayes", "noes", "absent"))
    drop_none = lambda xs: [] if xs == ["None"] else xs  # noqa: E731
    return {
        "ayes": ayes,
        "noes": drop_none(noes),
        "absent": drop_none(absent),
        "tally": f"{len(ayes)}-{len(drop_none(noes))}",
        "source_page": start_page,
    }
