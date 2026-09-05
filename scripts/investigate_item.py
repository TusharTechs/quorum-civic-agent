"""Tier 2: compose an investigation team from the item and run it."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quorum.household import describe, load_profile     # noqa: E402
from quorum.investigate import investigate              # noqa: E402

item_number = int(sys.argv[1]) if len(sys.argv) > 1 else 46
items = {i["number"]: i for i in
         json.loads(Path("data/cache/items_2026-06-30.json").read_text(encoding="utf-8"))}
item = items[item_number]

result = investigate(item, describe(load_profile()))
print(f"item {result.item_number}: {item['title'][:64]}")
print(f"classified as : {result.item_type}")
print(f"team summoned : {', '.join(result.team) or '(none)'}\n")
print(result.findings[:2600])
u = result.usage
cost = (u["inputTokens"] * 1.0 + u["outputTokens"] * 5.0) / 1_000_000
print(f"\ntokens: {u['inputTokens']:,} in / {u['outputTokens']:,} out  "
      f"~${cost:.4f} (Haiku)")
