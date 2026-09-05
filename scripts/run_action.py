"""Day 5 gate: draft -> grounding -> interrupt -> approval -> Cedar -> outcome."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from strands import Agent, tool                                  # noqa: E402
from strands.models import BedrockModel                          # noqa: E402
from strands.session import FileSessionManager                   # noqa: E402
from strands.types.tools import ToolContext                      # noqa: E402

from quorum.action import check_grounding, draft_comment, gate   # noqa: E402
from quorum.household import load_profile                        # noqa: E402
from quorum.stake import build_alerts                            # noqa: E402

MEETING = "Tuesday, 30 June 2026"
ITEM_NUMBER = 1                       # goBerkeley parking meters
HAS_STANDING = False                  # the operator is in India (brief §5)

items = {i["number"]: i for i in
         json.loads(Path("data/cache/items_2026-06-30.json").read_text(encoding="utf-8"))}
item = items[ITEM_NUMBER]
profile = load_profile()

alerts, _ = build_alerts([item], profile, MEETING)
alert = alerts.alerts[0]
print(f"ALERT  {alert.what[:110]}\n")

draft = draft_comment(alert, item, profile, MEETING)
print("=" * 72)
print(f"DRAFT — {draft.subject}   [{draft.position}]")
print("=" * 72)
print(draft.body[:900])

source = f"{item['title']} {item['fields'].get('Recommendation:', '')}"
g = check_grounding(draft, source)
print(f"\nGROUNDING: quotes {g.quotes_verified}/{g.quotes_checked} verified, "
      f"{len(g.uncited_sentences)} uncited sentence(s) -> "
      f"all_claims_cited={g.all_claims_cited}")
for q in g.unverified_quotes:
    print(f"   UNVERIFIED QUOTE: {q}")
for s in g.uncited_sentences:
    print(f"   UNCITED: {s}")


@tool(context=True)
def submit_public_comment(meeting: str, tool_context: ToolContext) -> str:
    """Submit the prepared public comment. Requires human approval."""
    approval = tool_context.interrupt(
        name="approve_submission",
        reason={"meeting": meeting, "subject": draft.subject,
                "question": "Approve filing this comment into the public record?"},
    )
    decision = gate(g, human_approved=bool(approval), approval_age_hours=0,
                    has_standing=HAS_STANDING)
    return json.dumps({"allowed": decision.allowed, "headline": decision.headline,
                       "reasons": decision.reasons})


def steward():
    return Agent(
        model=BedrockModel(model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
                           region_name="us-west-2"),
        tools=[submit_public_comment],
        system_prompt="Use submit_public_comment to file the prepared comment. "
                      "Report the policy decision exactly as returned.",
        session_manager=FileSessionManager(session_id="quorum-action",
                                           storage_dir="data/sessions"),
    )


print("\n" + "=" * 72)
r = steward()(f"File the prepared public comment for the {MEETING} meeting.")
print(f"INTERRUPT RAISED — stop_reason={r.stop_reason}")
for i in r.interrupts or []:
    print(f"   asks: {i.reason['question']}")
    print(f"   re  : {i.reason['subject']}")

iid = r.interrupts[0].id
r2 = steward()([{"interruptResponse": {"interruptId": iid, "response": "approved"}}])
print("\nHUMAN APPROVED -> resumed, policy gate consulted")
print("=" * 72)
decision = gate(g, human_approved=True, approval_age_hours=0, has_standing=HAS_STANDING)
if decision.allowed:
    print("  Comment FILED to council@berkeleyca.gov")
else:
    print(f"  ⛔ {decision.headline}")
    for reason in decision.reasons:
        print(f"     {reason}")
    print("\n  Comment prepared, not filed.")
    print("  The LLM can recommend an action. It cannot grant itself")
    print("  permission to take it — including when the operator is us.")
