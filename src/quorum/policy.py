"""The Civic Integrity Policy gate.

Enforcement is by the Cedar engine, not by prompt instructions and not by a
hand-rolled if-statement pretending to be a policy engine. The policy text in
`policy/quorum.cedar` is the artefact; this module only assembles the request.

The point of §5 is that a policy engine which refuses its own author is more
credible than any successful filing.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path

import cedarpy

from .paths import policy_file


@dataclass
class ActionContext:
    """The facts the policy decides on. Every field is checkable evidence."""

    human_approved: bool
    approval_age_hours: int
    has_standing: bool
    all_claims_cited: bool
    comments_filed_for_meeting: int


@dataclass
class Decision:
    allowed: bool
    action: str
    reasons: list[str]
    context: dict

    @property
    def headline(self) -> str:
        if self.allowed:
            return f"Permitted: {self.action}"
        return "Blocked by Civic Integrity Policy"


def _policies() -> str:
    return policy_file().read_text(encoding="utf-8")


def _explain(context: ActionContext) -> list[str]:
    """Which conditions failed, in the words a resident would want."""
    checks = [
        (context.human_approved, "a human has not approved this comment"),
        (context.approval_age_hours <= 24,
         f"approval is {context.approval_age_hours}h old; the limit is 24h"),
        (context.has_standing,
         "the configured identity has no verified standing in this jurisdiction"),
        (context.all_claims_cited,
         "the draft contains an assertion not cited to a packet page"),
        (context.comments_filed_for_meeting == 0,
         "a comment has already been filed for this meeting"),
    ]
    return [reason for ok, reason in checks if not ok]


def evaluate(action: str, context: ActionContext, *, principal: str = "quorum") -> Decision:
    """Ask Cedar. The answer is the answer."""
    request = {
        "principal": f'Agent::"{principal}"',
        "action": f'Action::"{action}"',
        "resource": 'Comment::"public-comment"',
        "context": asdict(context),
    }
    result = cedarpy.is_authorized(request, _policies(), [])
    allowed = result.decision == cedarpy.Decision.Allow
    return Decision(
        allowed=allowed,
        action=action,
        reasons=[] if allowed else _explain(context),
        context=asdict(context),
    )
