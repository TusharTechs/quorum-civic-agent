"""Compose an investigation team to match the item, then let it work.

Running four specialists over every agenda item is both wasteful and worse: a
fiscal analyst has nothing useful to say about a ceremonial resolution, and a
civil-liberties reviewer has nothing to say about a playground contract. The
team is therefore composed from the item itself.

Classification is deterministic — a keyword and structure match over the item's
own text — because which specialists to summon is not a judgement call worth
paying a model for, and a wrong team should be explainable.

Cost note: specialists run on Haiku. The Swarm exists to produce depth on one
contested item, not to re-read the packet, so its context is a single item.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from strands import Agent
from strands.models import BedrockModel
from strands.multiagent import Swarm

REGION = "us-west-2"
SPECIALIST_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# Ordered: the first pattern that matches wins, most specific first.
ITEM_TYPES: list[tuple[str, re.Pattern]] = [
    ("surveillance", re.compile(
        r"surveillance|police|camera|automated licen[cs]e|investigative software", re.I)),
    ("zoning", re.compile(
        r"\bzoning\b|BMC Title 23|lot coverage|floor area ratio|density|"
        r"use permit|general plan", re.I)),
    ("rate", re.compile(
        r"tax rate|per square foot|fee schedule|assessment|rate schedule|"
        r"special tax", re.I)),
    ("ballot", re.compile(r"ballot|initiative ordinance|measure on the", re.I)),
    ("parking", re.compile(r"parking|meter|goBerkeley|traffic", re.I)),
    ("contract", re.compile(r"^contract|contract no\.|amendment:|purchase order", re.I)),
    ("ceremonial", re.compile(
        r"proclamation|commendation|in recognition|adjourn in memory|"
        r"relinquishment of council office budget", re.I)),
]

SPECIALISTS: dict[str, tuple[str, str]] = {
    "precedent": (
        "Precedent",
        "You find what this council has already done on this subject. Look for "
        "prior readings, earlier versions, referrals to committee, and anything "
        "indicating the item has been here before. Say plainly when the text "
        "gives you no history to work from."),
    "parcel": (
        "Parcel Impact",
        "You reason about geography. Given a household address and an item, work "
        "out whether it touches this parcel, this block, this district, or the "
        "whole city, and say which. Never guess a distance you cannot support."),
    "procedure": (
        "Procedure",
        "You establish what stage this is at and what a resident can still do. "
        "First or second reading, consent or action calendar, public hearing, "
        "and what the deadline to comment actually is. Procedure decides whether "
        "attention is useful or too late."),
    "fiscal": (
        "Fiscal",
        "You handle money. Identify who pays, how much, on what basis, and over "
        "what period. State the basis of any rate explicitly. If arithmetic has "
        "already been computed and given to you, use it and do not recompute."),
    "household": (
        "Household Impact",
        "You translate a decision into what changes for one specific household. "
        "Concrete and second-order effects only; no generalities about residents "
        "at large."),
    "liberties": (
        "Civil Liberties",
        "You review for rights and oversight: who can access data, under what "
        "authority, with what retention, what audit exists, and what is left "
        "unspecified. What a policy does NOT say is often the finding."),
}

TEAMS: dict[str, list[str]] = {
    "surveillance": ["liberties", "precedent", "procedure"],
    "zoning": ["precedent", "parcel", "procedure"],
    "rate": ["fiscal", "household", "procedure"],
    "ballot": ["fiscal", "household", "procedure"],
    "parking": ["parcel", "household", "procedure"],
    "contract": ["fiscal", "procedure"],
    "ceremonial": [],          # deliberately empty: archive, do not investigate
    "other": ["household", "procedure"],
}


@dataclass
class Investigation:
    item_number: int
    item_type: str
    team: list[str]
    findings: str
    usage: dict


def classify(item: dict) -> str:
    """Which kind of decision is this? Deterministic and explainable."""
    blob = f"{item['title']} {item['fields'].get('Recommendation:', '')}"
    for name, pattern in ITEM_TYPES:
        if pattern.search(blob):
            return name
    return "other"


def team_for(item_type: str) -> list[str]:
    return TEAMS.get(item_type, TEAMS["other"])


def _agent(key: str) -> Agent:
    name, brief = SPECIALISTS[key]
    return Agent(
        name=name,
        model=BedrockModel(model_id=SPECIALIST_MODEL, region_name=REGION),
        system_prompt=(
            f"You are the {name} specialist on a team reading one city council "
            f"agenda item.\n\n{brief}\n\n"
            "Rules, without exception:\n"
            "- At most four sentences.\n"
            "- State no number, count, date or deadline that is not written in "
            "the item text you were given. If the text gives no deadline, say "
            "that the text gives none.\n"
            "- Do not negotiate scope with colleagues or ask who owns a "
            "question. Answer your part and stop.\n"
            "- Hand off at most once, and only to add something you cannot "
            "provide yourself."
        ),
    )


def investigate(item: dict, profile_description: str,
                extra_context: str = "") -> Investigation:
    """Run a team sized to the item. A ceremonial item gets no team at all."""
    item_type = classify(item)
    team_keys = team_for(item_type)

    if not team_keys:
        return Investigation(
            item_number=item["number"], item_type=item_type, team=[],
            findings="No investigation: ceremonial item with no decision "
                     "affecting this household.",
            usage={"inputTokens": 0, "outputTokens": 0, "totalTokens": 0})

    swarm = Swarm(
        [_agent(k) for k in team_keys],
        max_handoffs=3,
        max_iterations=4,
        # Two specialists arguing over whose question it is burns tokens and
        # produces nothing; cut the conversation when it starts circling.
        repetitive_handoff_detection_window=3,
        repetitive_handoff_min_unique_agents=2,
        node_timeout=120.0,
        execution_timeout=420.0,
    )
    task = (
        f"HOUSEHOLD\n{profile_description}\n\n"
        f"AGENDA ITEM {item['number']} (packet page {item['page']})\n"
        f"TITLE: {item['title']}\n"
        f"RECOMMENDATION: {item['fields'].get('Recommendation:', '')}\n"
        f"POLICY COMMITTEE: {item['fields'].get('Policy Committee Recommendation:', '')}\n"
        f"{extra_context}\n\n"
        "Between you, establish what this changes, for whom, at what stage, and "
        "what is unresolved."
    )
    result = swarm(task)

    parts = []
    for node_id, node_result in result.results.items():
        for agent_result in node_result.get_agent_results():
            message = getattr(agent_result, "message", None) or {}
            content = message.get("content", []) if isinstance(message, dict) else []
            text = " ".join(
                block["text"] for block in content
                if isinstance(block, dict) and block.get("text")
            ).strip()
            if text:
                parts.append(f"[{SPECIALISTS.get(node_id, (node_id,))[0]}] {text}")

    return Investigation(
        item_number=item["number"], item_type=item_type, team=team_keys,
        findings="\n\n".join(parts),
        usage=result.accumulated_usage,
    )
