"""Sweep AgentCore resources so nothing bills overnight.

Idle compute is the expensive failure mode, not active compute: a runtime or
browser session left alive costs money continuously while doing nothing, where
a full pipeline run costs about two cents.

Dry run by default. Pass --yes to actually delete.

    python scripts/teardown.py            # report what exists
    python scripts/teardown.py --yes      # delete it
"""

from __future__ import annotations

import argparse
import sys

import boto3
from botocore.exceptions import ClientError

REGION = "us-west-2"

# (label, list operation, response key, id field, delete operation, delete arg)
SWEEPS = [
    ("agent runtime",    "list_agent_runtimes",  "agentRuntimes",
     "agentRuntimeId",   "delete_agent_runtime", "agentRuntimeId"),
    ("browser",          "list_browsers",        "browserSummaries",
     "browserId",        "delete_browser",       "browserId"),
    ("code interpreter", "list_code_interpreters", "codeInterpreterSummaries",
     "codeInterpreterId", "delete_code_interpreter", "codeInterpreterId"),
    ("memory",           "list_memories",        "memories",
     "id",               "delete_memory",        "memoryId"),
    ("gateway",          "list_gateways",        "items",
     "gatewayId",        "delete_gateway",       "gatewayIdentifier"),
]

# Browsers and code interpreters include AWS-managed defaults that cannot be
# deleted and cost nothing. Skip them rather than reporting spurious failures.
SYSTEM_PREFIXES = ("aws.browser", "aws.codeinterpreter")


def _identifier(item: dict, field: str) -> str | None:
    return item.get(field) or item.get("id") or item.get("name")


def sweep(client, *, apply: bool) -> tuple[int, int]:
    found = removed = 0
    for label, list_op, key, id_field, delete_op, delete_arg in SWEEPS:
        try:
            items = getattr(client, list_op)().get(key, [])
        except ClientError as exc:
            print(f"  {label:17} could not list ({exc.response['Error']['Code']})")
            continue
        except AttributeError:
            print(f"  {label:17} not available in this boto3 version")
            continue

        live = []
        for item in items:
            ident = _identifier(item, id_field)
            if ident and not ident.startswith(SYSTEM_PREFIXES):
                live.append(ident)

        if not live:
            print(f"  {label:17} none")
            continue

        found += len(live)
        for ident in live:
            if not apply:
                print(f"  {label:17} WOULD DELETE  {ident}")
                continue
            try:
                getattr(client, delete_op)(**{delete_arg: ident})
                removed += 1
                print(f"  {label:17} deleted       {ident}")
            except ClientError as exc:
                print(f"  {label:17} FAILED        {ident} "
                      f"({exc.response['Error']['Code']})")
    return found, removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true",
                        help="actually delete; without this the script only reports")
    parser.add_argument("--region", default=REGION)
    args = parser.parse_args()

    client = boto3.client("bedrock-agentcore-control", region_name=args.region)
    mode = "DELETING" if args.yes else "dry run"
    print(f"AgentCore teardown ({mode}) in {args.region}\n")

    found, removed = sweep(client, apply=args.yes)

    print()
    if not found:
        print("Nothing is running. Nothing is billing.")
        return 0
    if args.yes:
        print(f"Removed {removed} of {found} resource(s).")
        return 0 if removed == found else 1
    print(f"{found} resource(s) would be deleted. Re-run with --yes to remove them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
