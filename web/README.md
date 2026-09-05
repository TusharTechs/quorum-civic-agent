# Static site output

`index.html` is a generated snapshot of a real QUORUM run against Berkeley's
30 June 2026 packet. It is a single self-contained file: no scripts, no external
requests, no secrets, nothing to build.

Regenerate it with `python scripts/build_report.py` from the repository root.

This directory is what gets deployed. The Python pipeline is NOT deployed here —
it runs on Amazon Bedrock AgentCore, because it needs AWS credentials, Bedrock
access and minutes of runtime to parse a 65 MB PDF. None of that belongs on a
static host.
