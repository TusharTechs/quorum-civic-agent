"""Day 4 gate: the whole lifecycle runs end to end as a Strands Graph."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.pipeline import RunContext, build_graph   # noqa: E402

PACKET_URL = (
    "https://berkeleyca.gov/sites/default/files/city-council-meetings/"
    "2026-06-30%20Agenda%20Packet%20-%20Council%20-%20WEB.pdf"
)

ctx = RunContext(packet_url=PACKET_URL, meeting_date="Tuesday, 30 June 2026")
graph = build_graph(ctx)
result = graph("Process the published packet for this household.")

print(f"\nstatus        : {result.status}")
print(f"nodes executed: {result.execution_count}")
print(f"time          : {result.execution_time} ms")
print("\npath:")
for line in ctx.log:
    print(f"  {line}")

if ctx.alerts:
    print("\nWhy QUORUM interrupted you")
    for a in ctx.alerts.alerts:
        print(f"  items {a.item_numbers}: {a.what[:100]}")

tokens = {k: (v["inputTokens"], v["outputTokens"]) for k, v in ctx.usage.items()}
cost = sum(
    (v["inputTokens"] * (0.06 if k == "triage" else 3.0)
     + v["outputTokens"] * (0.24 if k == "triage" else 15.0)) / 1e6
    for k, v in ctx.usage.items()
)
print(f"\ntokens: {tokens}")
print(f"estimated cost: ${cost:.4f}")
