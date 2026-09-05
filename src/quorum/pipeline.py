"""The QUORUM lifecycle, expressed as a Strands Graph.

The Graph *is* the coordinator (brief §3) - there is no supervisor agent layered
on top of it, because that would be redundant orchestration.

Node types are chosen on principle:
  * Deterministic work (fetching, parsing, segmenting, diffing) is a
    MultiAgentBase node. It costs nothing and its behaviour is auditable.
    Paying a model to do structural work would be both slower and wrong (§9).
  * Reasoning work (triage, stake matching, drafting) runs through Strands
    Agents on the model tier that matches the job.

Edges carry the branching: a candidate path, a low-impact archive path, and a
genuine error edge for packets that will not parse.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from strands.agent.agent_result import AgentResult
from strands.multiagent import GraphBuilder
from strands.multiagent.base import MultiAgentBase, MultiAgentResult, NodeResult, Status
from strands.telemetry.metrics import EventLoopMetrics

from . import ingest as ingest_mod
from . import segment as segment_mod
from . import cost as cost_mod
from . import stake as stake_mod
from .household import load_profile

# A packet with this share of pages carrying no extractable text is treated as
# unparseable and routed down the error edge to OCR.
OCR_THRESHOLD = 0.25


@dataclass
class RunContext:
    """Everything the run accumulates. Nodes write here; edges read from here."""

    packet_url: str
    meeting_date: str
    profile: dict = field(default_factory=load_profile)
    packet: dict | None = None
    items: list[dict] = field(default_factory=list)
    candidates: list[dict] = field(default_factory=list)
    alerts: Any = None
    unparseable_ratio: float = 0.0
    archived: list[int] = field(default_factory=list)
    cost: Any = None
    usage: dict[str, dict] = field(default_factory=dict)
    log: list[str] = field(default_factory=list)

    def note(self, message: str) -> None:
        self.log.append(message)


class Step(MultiAgentBase):
    """A deterministic graph node: real work, no model call, auditable."""

    def __init__(self, name: str, fn: Callable[[RunContext], str], ctx: RunContext):
        super().__init__()
        self.name = name
        self._fn = fn
        self._ctx = ctx

    async def invoke_async(self, task=None, invocation_state=None, **kwargs) -> MultiAgentResult:
        started = time.time()
        failure: Exception | None = None
        try:
            summary = self._fn(self._ctx)
            status = Status.COMPLETED
        except Exception as exc:                      # noqa: BLE001
            failure, summary, status = exc, f"{type(exc).__name__}: {exc}", Status.FAILED
        elapsed = int((time.time() - started) * 1000)
        self._ctx.note(f"[{self.name}] {summary}")

        # Downstream nodes read prior output as an AgentResult, so a
        # deterministic step reports itself in the same shape an agent would.
        payload = failure or AgentResult(
            stop_reason="end_turn",
            message={"role": "assistant", "content": [{"text": f"{self.name}: {summary}"}]},
            metrics=EventLoopMetrics(),
            state={},
        )
        return MultiAgentResult(
            status=status,
            results={self.name: NodeResult(result=payload, status=status,
                                           execution_time=elapsed,
                                           execution_count=1)},
            execution_time=elapsed,
            execution_count=1,
        )


def _cost_summary(cost) -> str:
    """The household figures, stated as computed fact for the drafting model."""
    if cost is None or not cost.included:
        return ""
    lines = [
        f"This household: {cost.dwelling_sqft:,} sq ft, "
        f"assessed ${cost.assessed_value_usd:,}.",
        f"Per-square-foot dwelling taxes total ${cost.sqft_rate_total:.5f}/sq ft "
        f"= ${cost.sqft_cost:,.2f}/year (items "
        f"{[r.item_number for r in cost.rates if r.basis == 'per_sqft_dwelling']}).",
        f"Assessed-value taxes total {cost.assessed_percent_total:.4f}% "
        f"= ${cost.assessed_cost:,.2f}/year (items "
        f"{[r.item_number for r in cost.rates if r.basis == 'assessed_value']}).",
        f"COMBINED ANNUAL TOTAL: ${cost.annual_total:,.2f} across "
        f"{len(cost.item_numbers)} agenda items.",
    ]
    for r in cost.excluded:
        lines.append(f"EXCLUDED item {r.item_number}: {r.excluded_reason}. "
                     f"Do not include it in the household total.")
    return "\n".join(lines)


# --- node bodies -------------------------------------------------------------

def _watch(ctx: RunContext) -> str:
    return f"target packet {ctx.packet_url.rsplit('/', 1)[-1][:48]}"


def _ingest(ctx: RunContext) -> str:
    ctx.packet = ingest_mod.load_packet(ctx.packet_url)
    pages = ctx.packet["pages"]
    blank = sum(1 for p in pages if p["chars"] < 50)
    ctx.unparseable_ratio = blank / max(len(pages), 1)
    return (f"{ctx.packet['n_pages']} pages, "
            f"{blank} image-only ({ctx.unparseable_ratio:.1%})")


def _segment(ctx: RunContext) -> str:
    items = segment_mod.segment(ctx.packet)
    ctx.items = segment_mod.to_dicts(items)
    return f"{len(ctx.items)} agenda items"


def _triage(ctx: RunContext) -> str:
    """Cheap model pass, unioned with a deterministic floor.

    Model triage recall varies between runs on identical input. A tax levied on
    this household's dwelling affects it whether or not a model notices, so
    rate-bearing items bypass triage entirely. The model decides the judgement
    calls; it does not get a vote on arithmetic that is already established.
    """
    verdicts, usage = stake_mod.triage(ctx.items, ctx.profile)
    ctx.usage["triage"] = usage
    by_number = {i["number"]: i for i in ctx.items}

    hits = {v.item_number for v in verdicts.items if v.affects_household}

    ctx.cost = cost_mod.compute(ctx.items, ctx.profile)
    always = {r.item_number for r in ctx.cost.included}
    missed = sorted(always - hits)

    selected = sorted(hits | always)
    ctx.candidates = [by_number[n] for n in selected if n in by_number]
    ctx.archived = [i["number"] for i in ctx.items if i["number"] not in set(selected)]

    note = f", {len(missed)} added by rate filter {missed}" if missed else ""
    return f"{len(ctx.candidates)} candidates, {len(ctx.archived)} archived{note}"


def _ocr_fallback(ctx: RunContext) -> str:
    # Deliberately not implemented as OCR yet; the edge and the honest refusal
    # to proceed on unverified text are what matter (brief §5).
    return ("packet is largely image-only; evidence incomplete, "
            "escalating rather than guessing")


def _archive(ctx: RunContext) -> str:
    return f"no action recommended; {len(ctx.archived)} items archived"


def _deep_read(ctx: RunContext) -> str:
    # Arithmetic is done in code and handed to the model as fact. Letting a
    # model multiply the number the whole alert rests on is a hallucination
    # surface for no benefit.
    alerts, usage = stake_mod.build_alerts(
        ctx.candidates, ctx.profile, ctx.meeting_date,
        cost_summary=_cost_summary(ctx.cost),
    )
    ctx.usage["deep"] = usage
    ctx.alerts = alerts
    return f"{len(alerts.alerts)} decision-level alert(s)"


# --- edge conditions ---------------------------------------------------------

def _unparseable(ctx: RunContext):
    return lambda state: ctx.unparseable_ratio >= OCR_THRESHOLD


def _parseable(ctx: RunContext):
    return lambda state: ctx.unparseable_ratio < OCR_THRESHOLD


def _has_candidates(ctx: RunContext):
    return lambda state: bool(ctx.candidates)


def _no_candidates(ctx: RunContext):
    return lambda state: not ctx.candidates


def build_graph(ctx: RunContext):
    """Wire the lifecycle. Branching lives on the edges, not inside the nodes."""
    b = GraphBuilder()
    b.add_node(Step("watch", _watch, ctx), "watch")
    b.add_node(Step("ingest", _ingest, ctx), "ingest")
    b.add_node(Step("segment", _segment, ctx), "segment")
    b.add_node(Step("triage", _triage, ctx), "triage")
    b.add_node(Step("ocr_fallback", _ocr_fallback, ctx), "ocr_fallback")
    b.add_node(Step("archive", _archive, ctx), "archive")
    b.add_node(Step("deep_read", _deep_read, ctx), "deep_read")

    b.add_edge("watch", "ingest")
    # error edge: a packet we cannot read does not proceed on guesswork
    b.add_edge("ingest", "ocr_fallback", condition=_unparseable(ctx))
    b.add_edge("ingest", "segment", condition=_parseable(ctx))
    b.add_edge("segment", "triage")
    b.add_edge("triage", "archive", condition=_no_candidates(ctx))
    b.add_edge("triage", "deep_read", condition=_has_candidates(ctx))

    b.set_entry_point("watch")
    # The lifecycle revisits nodes when tracking an item across meetings, so the
    # graph permits cycles - and therefore needs an explicit ceiling.
    b.set_max_node_executions(24)
    b.set_execution_timeout(900)
    return b.build()
