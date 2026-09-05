"""Measure whether QUORUM surfaces the items that actually matter.

Two questions, and the second is the one that nearly went unnoticed:

  1. On one run, what are precision and recall against a hand-labelled key?
  2. **How much do they move between runs on identical input?**

A single flattering run says almost nothing about a system whose first stage is
a language model. Recall on this agenda varied from 5 to 16 candidates across
runs of the same packet, so the harness runs the triage several times and
reports the spread, not just a mean.

The comparison that matters is model-only triage against model triage unioned
with the deterministic rate floor, because that is the change made in response
to the variance.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path

from . import cost as cost_mod
from . import stake as stake_mod
from .paths import REPO_ROOT


@dataclass
class Score:
    true_positives: set[int]
    false_positives: set[int]
    false_negatives: set[int]

    @property
    def precision(self) -> float:
        predicted = len(self.true_positives) + len(self.false_positives)
        return len(self.true_positives) / predicted if predicted else 0.0

    @property
    def recall(self) -> float:
        actual = len(self.true_positives) + len(self.false_negatives)
        return len(self.true_positives) / actual if actual else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


@dataclass
class Trial:
    model_only: Score
    with_rate_floor: Score
    usage: dict


@dataclass
class Evaluation:
    relevant: set[int]
    borderline: set[int]
    trials: list[Trial] = field(default_factory=list)

    def _series(self, arm: str, metric: str) -> list[float]:
        return [getattr(getattr(t, arm), metric) for t in self.trials]

    def summary(self, arm: str) -> dict:
        out = {}
        for metric in ("precision", "recall", "f1"):
            values = self._series(arm, metric)
            out[metric] = {
                "mean": statistics.fmean(values),
                "min": min(values),
                "max": max(values),
                "spread": max(values) - min(values),
            }
        return out


def load_labels(meeting: str) -> tuple[set[int], set[int]]:
    """Returns (relevant, borderline). Borderline items are excluded from
    scoring entirely: they count neither for nor against."""
    path = REPO_ROOT / "eval" / f"labels_{meeting}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return ({int(k) for k in data["relevant"]},
            {int(k) for k in data.get("borderline", {})})


def score(predicted: set[int], relevant: set[int], borderline: set[int],
          universe: set[int]) -> Score:
    """Borderline items are removed from both sides before scoring."""
    judged = universe - borderline
    predicted = predicted & judged
    actual = relevant & judged
    return Score(
        true_positives=predicted & actual,
        false_positives=predicted - actual,
        false_negatives=actual - predicted,
    )


def run(items: list[dict], profile: dict, meeting: str, trials: int = 5) -> Evaluation:
    """Run triage `trials` times and score both arms on each run."""
    relevant, borderline = load_labels(meeting)
    universe = {i["number"] for i in items}

    # The rate floor is deterministic, so it is computed once.
    floor = {r.item_number for r in cost_mod.compute(items, profile).included}

    evaluation = Evaluation(relevant=relevant, borderline=borderline)
    for _ in range(trials):
        verdicts, usage = stake_mod.triage(items, profile)
        model_hits = {v.item_number for v in verdicts.items if v.affects_household}
        evaluation.trials.append(Trial(
            model_only=score(model_hits, relevant, borderline, universe),
            with_rate_floor=score(model_hits | floor, relevant, borderline, universe),
            usage=usage,
        ))
    return evaluation
