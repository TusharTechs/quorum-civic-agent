"""Tier 3: measure retrieval quality, and how much it varies between runs."""

import contextlib
import io
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.evaluate import run          # noqa: E402
from quorum.household import load_profile  # noqa: E402
from quorum.models import TRIAGE, cost, model_id  # noqa: E402

MEETING = "2026-06-30"

# --quiet swallows the streamed model reasoning, the way scripts/scene.py does
# for filming: on screen it buries the numbers the evaluation is about. It also
# silences asyncio's report of the provider's async client closing after its
# loop has gone, which is teardown noise rather than a failure.
QUIET = "--quiet" in sys.argv
_args = [a for a in sys.argv[1:] if a != "--quiet"]
if QUIET:
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)

TRIALS = int(_args[0]) if _args else 5

items = json.loads(
    Path(f"data/cache/items_{MEETING}.json").read_text(encoding="utf-8"))
if QUIET:
    print(f"\n  evaluating the {MEETING} packet over {TRIALS} trials ...\n")
    with contextlib.redirect_stdout(io.StringIO()):
        ev = run(items, load_profile(), MEETING, trials=TRIALS)
else:
    ev = run(items, load_profile(), MEETING, trials=TRIALS)

print(f"meeting {MEETING} | {len(items)} items | {TRIALS} trials")
print(f"labelled relevant: {len(ev.relevant)}   "
      f"borderline (excluded from scoring): {len(ev.borderline)}\n")

for arm, label in (("model_only", "model triage alone"),
                   ("with_rate_floor", "model triage + rate floor")):
    s = ev.summary(arm)
    print(f"{label}")
    for metric in ("precision", "recall", "f1"):
        m = s[metric]
        print(f"  {metric:<10} mean {m['mean']:.3f}   "
              f"range {m['min']:.3f}-{m['max']:.3f}   spread {m['spread']:.3f}")
    print()

print("per-trial recall")
for i, t in enumerate(ev.trials, 1):
    missed = sorted(t.model_only.false_negatives)
    print(f"  trial {i}: model {t.model_only.recall:.3f} -> "
          f"with floor {t.with_rate_floor.recall:.3f}"
          f"   model missed {missed if missed else 'nothing'}")

tot_in = sum(t.usage["inputTokens"] for t in ev.trials)
tot_out = sum(t.usage["outputTokens"] for t in ev.trials)
usage = {"inputTokens": tot_in, "outputTokens": tot_out}
print(f"\ncost of this evaluation: ${cost(TRIAGE, usage):.4f} "
      f"({tot_in:,} in / {tot_out:,} out, {model_id(TRIAGE)})")
