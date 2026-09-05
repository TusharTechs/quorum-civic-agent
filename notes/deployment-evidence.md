# AgentCore deployment — verified 5 September 2026

Deployed, invoked against a real document, and torn down in one session.

## Resources created
| Resource | Identifier |
|---|---|
| CloudFormation stack | `AgentCore-quorum-default` |
| Runtime | `quorum_quorumAgent-iJRQvtAgVJ` (READY) |
| Memory | `quorum_quorumAgentMemory-k5LruM4AFy` |
| Memory strategies | SEMANTIC, USER_PREFERENCE, SUMMARIZATION, EPISODIC |
| Region | us-west-2 |

Runtime ARN
`arn:aws:bedrock-agentcore:us-west-2:756590016817:runtime/quorum_quorumAgent-iJRQvtAgVJ`

Memory ARN
`arn:aws:bedrock-agentcore:us-west-2:756590016817:memory/quorum_quorumAgentMemory-k5LruM4AFy`

Seven CloudFormation resources: two IAM execution roles, an IAM policy, the
Memory, the Runtime, its endpoint and CDK metadata. Memory took ~2m25s to
create; the whole deploy completed in about five minutes.

## Proof it works, not just that it started

Invoked the deployed agent with a plain-language question about a real Berkeley
document it had never seen locally:

> "Using the Annotated Agenda at <url>, what did the Berkeley council actually
> decide on agenda items 1, 2 and 46? Give the disposition and the page
> citation for each."

The agent chose the `verify_outcome` tool, fetched the 27-page PDF from
berkeleyca.gov, parsed it, and returned:

| Item | Disposition | Instrument | Page |
|---|---|---|---|
| 1 | Adopted | Ordinance 8,012-N.S. | 3 |
| 2 | Adopted | Ordinance 8,013-N.S. | 3 |
| 46 | Adopted | Resolution 72,369-N.S., 17 speakers, moved Blackaby/Humbert | 19 |

**Identical to the local run.** The deployed agent reaches the real world,
parses hostile documents, and cites pages — in AWS, not on a laptop.

Session id `df66f106-4feb-48f9-8222-863efb694dc6`, resumable via
`agentcore invoke --session-id ...`.

## Pre-flight that made the deploy work first time

- The package resolves and builds from the public repository on **Python 3.14.7**,
  the runtime's version. `pymupdf` and `cedarpy` both have working 3.14 wheels —
  this was the most likely failure mode and was ruled out before deploying.
- The Cedar policy ships inside the wheel and refuses correctly from an
  installed copy with no repository checkout present.
- `QUORUM_CACHE_DIR` is set to `/tmp/quorum-cache` before any package import,
  because the cache location is bound at import time and the runtime filesystem
  is read-only elsewhere.

## Teardown

The resources are **CDK-managed**, so deleting them individually would leave the
CloudFormation stack drifted. Teardown is therefore a stack delete:

    aws cloudformation delete-stack --stack-name AgentCore-quorum-default --region us-west-2
    aws cloudformation wait stack-delete-complete --stack-name AgentCore-quorum-default --region us-west-2

Confirmed: the stack no longer exists, and an independent sweep with
`scripts/teardown.py` reports `Nothing is running. Nothing is billing.`

Note that the current AgentCore CLI has **no `destroy` command** — that belonged
to the deprecated Python starter toolkit. `agentcore remove` edits project
config, not AWS. `scripts/teardown.py` remains the safety net for resources
created outside CDK (browser and code-interpreter sessions), which is exactly
the category that bills quietly.

Total exposure for deploy + invoke + teardown: well under $1.
