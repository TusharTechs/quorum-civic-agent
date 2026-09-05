"""Render one real run as a self-contained HTML page."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.action import check_grounding, draft_comment, gate   # noqa: E402
from quorum.outcomes import load_outcomes                        # noqa: E402
from quorum.pipeline import RunContext, build_graph              # noqa: E402
from quorum.report import write                                  # noqa: E402

PACKET_URL = ("https://berkeleyca.gov/sites/default/files/city-council-meetings/"
              "2026-06-30%20Agenda%20Packet%20-%20Council%20-%20WEB.pdf")
ANNOTATED_URL = ("https://berkeleyca.gov/sites/default/files/city-council-meetings/"
                 "2026-06-30%20Annotated%20Agenda%20-%20Council.pdf")

ctx = RunContext(packet_url=PACKET_URL, meeting_date="Tuesday, 30 June 2026")
build_graph(ctx)("Process the published packet for this household.")
print(f"run: {len(ctx.items)} items -> {len(ctx.candidates)} candidates -> "
      f"{len(ctx.alerts.alerts) if ctx.alerts else 0} decisions")

# The prepared-but-refused comment, on the parking ordinance.
items = {i["number"]: i for i in ctx.items}
alert = next((a for a in ctx.alerts.alerts if 1 in a.item_numbers), None)
decision = grounding = None
if alert:
    draft = draft_comment(alert, items[1], ctx.profile, ctx.meeting_date)
    source = f"{items[1]['title']} {items[1]['fields'].get('Recommendation:', '')}"
    grounding = check_grounding(draft, source)
    decision = gate(grounding, human_approved=True, approval_age_hours=0,
                    has_standing=False)
    print(f"policy: {decision.headline}")

annotated = json.loads(
    Path("data/cache/items_2026-06-30-ANNOTATED.json").read_text(encoding="utf-8"))
flagged = {n for a in ctx.alerts.alerts for n in a.item_numbers} if ctx.alerts else set()
outcomes = {n: o for n, o in load_outcomes(annotated).items() if n in flagged}

out = write(ctx, Path("data/report.html"), decision=decision, grounding=grounding,
            outcomes=outcomes, annotated_url=ANNOTATED_URL)
print(f"wrote {out} ({out.stat().st_size:,} bytes, self-contained)")
