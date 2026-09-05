"""Draft -> grounding check -> interrupt -> policy gate -> act.

The ordering matters and is not decorative. The model drafts. Code checks that
every factual claim is traceable to a packet page. A human approves. Only then
does Cedar decide - and Cedar can still say no.

"The LLM can recommend an action. It cannot grant itself permission to take
it." (§5)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from pydantic import BaseModel, Field
from strands import Agent
from strands.models import BedrockModel

from .policy import ActionContext, Decision, evaluate

REGION = "us-west-2"
DRAFT_MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

# A quote counts as grounded if this much of it appears verbatim in the source.
QUOTE_MIN_CHARS = 25


class CommentDraft(BaseModel):
    subject: str = Field(description="Email subject line for the public comment")
    body: str = Field(
        description="The comment itself. Every factual assertion must be followed "
                    "by a citation in the form (packet p.NNN). Quote the packet "
                    "verbatim inside double quotes when asserting what it says."
    )
    position: str = Field(description="support, oppose, or request clarification")


@dataclass
class Grounding:
    quotes_checked: int = 0
    quotes_verified: int = 0
    uncited_sentences: list[str] = field(default_factory=list)
    unverified_quotes: list[str] = field(default_factory=list)

    @property
    def all_claims_cited(self) -> bool:
        return not self.uncited_sentences and not self.unverified_quotes


CITATION = re.compile(r"\(\s*(?:packet\s*)?p+\.?\s*\d+\s*\)", re.I)
QUOTED = re.compile(r"[\"“]([^\"”]{%d,})[\"”]" % QUOTE_MIN_CHARS)

# Sentence splitting must not break on abbreviations. "8 p.m." and "(packet
# p.3)" are not sentence ends, and treating them as such manufactures
# uncited fragments out of properly cited sentences.
ABBREVIATIONS = r"(?<!\bp\.m)(?<!\ba\.m)(?<!\bNo)(?<!\bp)(?<!\bpp)(?<!\bSt)(?<!\bInc)(?<!\bvs)"
SENTENCE_END = re.compile(ABBREVIATIONS + r'(?<=[.!?])\s+(?=[A-Z"“])')

# A public comment legitimately contains the resident's own circumstances and
# their opinion. Only claims about what the PACKET says require a citation:
# cite the document, not your own life and not your own argument.
PACKET_CLAIM = re.compile(
    r"\b(ordinance|resolution|the item|agenda|packet|staff report|"
    r"the propos\w+|the polic\w+|council (is|will|would|voted)|"
    r"per square foot|the rate|the fee)\b", re.I)

NORMATIVE = re.compile(
    r"\b(should|must|urge|i ask|i request|please|i oppose|i support|"
    r"call on|recommend that)\b", re.I)

FIRST_PERSON = re.compile(r"^\s*(i|my|our|we)\b", re.I)


def _needs_citation(sentence: str) -> bool:
    """Does this sentence assert something about the packet?"""
    if QUOTED.search(sentence):
        return True                      # quoting the packet always needs a cite
    if not PACKET_CLAIM.search(sentence):
        return False                     # says nothing about the document
    if NORMATIVE.search(sentence):
        return False                     # an argument, not a factual claim
    if FIRST_PERSON.match(sentence) and not PACKET_CLAIM.search(sentence):
        return False                     # the resident's own circumstances
    return True


def check_grounding(draft: CommentDraft, source_text: str) -> Grounding:
    """Verify the draft against the packet. Deterministic - no model involved."""
    result = Grounding()
    normalised = " ".join(source_text.split()).lower()

    for quote in QUOTED.findall(draft.body):
        result.quotes_checked += 1
        needle = " ".join(quote.split()).lower()
        if needle in normalised:
            result.quotes_verified += 1
        else:
            result.unverified_quotes.append(quote[:90])

    for sentence in SENTENCE_END.split(draft.body):
        text = " ".join(sentence.split())
        if len(text) < 40 or not _needs_citation(text):
            continue
        if not CITATION.search(text):
            result.uncited_sentences.append(text[:90])
    return result


def draft_comment(alert, item: dict, profile: dict, meeting_date: str) -> CommentDraft:
    """Write the comment. Citations are mandatory and are checked afterwards."""
    agent = Agent(
        model=BedrockModel(model_id=DRAFT_MODEL, region_name=REGION),
        system_prompt=(
            "You draft public comments a resident submits to their city council. "
            "Rules, without exception: every factual assertion about the item must "
            "end with a citation in the form (packet p.NNN). When you state what "
            "the packet says, quote it verbatim in double quotes. Assert nothing "
            "you were not given. Be brief, specific and civil. No AI disclaimers, "
            "no filler, no invented statistics."
        ),
    )
    prompt = (
        f"MEETING: {meeting_date}\n"
        f"AGENDA ITEM {item['number']} (packet p.{item['page']}): {item['title']}\n"
        f"RECOMMENDATION: {item['fields'].get('Recommendation:', '')}\n\n"
        f"WHY IT MATTERS TO THIS HOUSEHOLD: {alert.why_you}\n\n"
        "Draft a short public comment from this resident."
    )
    return agent(prompt, structured_output_model=CommentDraft).structured_output


def gate(grounding: Grounding, *, human_approved: bool, approval_age_hours: int,
         has_standing: bool, comments_filed_for_meeting: int = 0) -> Decision:
    """Ask Cedar whether this may actually be filed."""
    return evaluate(
        "submit",
        ActionContext(
            human_approved=human_approved,
            approval_age_hours=approval_age_hours,
            has_standing=has_standing,
            all_claims_cited=grounding.all_claims_cited,
            comments_filed_for_meeting=comments_filed_for_meeting,
        ),
    )
