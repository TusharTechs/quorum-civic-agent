// QUORUM Civic Integrity Policy
//
// These rules are enforced OUTSIDE agent code (brief §5). The model can
// recommend an action; it cannot grant itself permission to take one.
// This is the same policy text intended for AgentCore Policy - it is
// evaluated here by the Cedar engine itself, not by a lookalike.
//
// Cedar is deny-by-default: an action with no matching permit is refused.

// 1. Drafting is always allowed. Reading and preparing a comment is safe,
//    reversible, and private until a human acts on it.
permit (
  principal,
  action == Action::"draft",
  resource
);

// 2. Submission is permitted only when every integrity condition holds.
permit (
  principal,
  action == Action::"submit",
  resource
) when {
  context.human_approved             == true &&   // a person said yes
  context.approval_age_hours         <= 24   &&   // and said it recently
  context.has_standing               == true &&   // in THIS jurisdiction
  context.all_claims_cited           == true &&   // no ungrounded assertions
  context.comments_filed_for_meeting == 0         // one comment per meeting
};

// 3. Defence in depth. Even if a permit were mistakenly broadened, an
//    operator without standing in the jurisdiction can never file.
//    This is the rule that refuses QUORUM's own author (§5).
forbid (
  principal,
  action == Action::"submit",
  resource
) unless {
  context.has_standing == true
};

// 4. A comment containing an assertion not traceable to a packet page is
//    never submittable, regardless of approval.
forbid (
  principal,
  action == Action::"submit",
  resource
) unless {
  context.all_claims_cited == true
};
