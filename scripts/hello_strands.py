"""Smoke test: validates credentials, provider config and model access in one
call. Uses the cheap tier, so it costs a fraction of a cent whoever is serving.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from strands import Agent          # noqa: E402
from quorum import models          # noqa: E402

print(models.describe())

agent = Agent(model=models.get_model(models.SPECIALIST),
              system_prompt="Answer in one short sentence.")
result = agent("What is a city council agenda packet?")

usage = result.metrics.accumulated_usage
print("\n--- usage ---")
print(usage)
print(f"cost: ${models.cost(models.SPECIALIST, usage):.5f}")
