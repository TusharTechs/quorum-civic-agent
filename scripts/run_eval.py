"""Tier 3: measure retrieval quality, and how much it varies between runs."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.evaluate import run          # noqa: E402
from quorum.household import load_profile  # noqa: E402

MEETING = "2026-06-30"
TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 5

items = json.loads(
    Path(f"data/cache/items_{MEETING}.json").read_text(encoding="utf-8"))
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
print(f"\ncost of this evaluation: "
      f"${(tot_in * 0.06 + tot_out * 0.24) / 1e6:.4f} "
      f"({tot_in:,} in / {tot_out:,} out, Nova Lite)")
