"""Model selection, decoupled from any one provider.

The pipeline reasons in three tiers and does not care who serves them:

    triage      high volume, low visibility - every item on the agenda
    deep        what a person actually reads - the surviving few
    specialist  investigation team members

Bedrock is the default and nothing about it changes. Set QUORUM_PROVIDER to
move the whole pipeline elsewhere:

    QUORUM_PROVIDER=bedrock     (default) Amazon Bedrock, AWS credentials
    QUORUM_PROVIDER=anthropic   Anthropic API, ANTHROPIC_API_KEY
    QUORUM_PROVIDER=ollama      local models, no key, no network

This exists because provider access is not guaranteed. Bedrock access to this
account was withdrawn without notice on 9 September 2026, mid-build, and a
pipeline with one hard dependency on one vendor's decision is a pipeline that
can stop working for reasons that have nothing to do with its code.
"""

from __future__ import annotations

import os

TRIAGE = "triage"
DEEP = "deep"
SPECIALIST = "specialist"

DEFAULT_PROVIDER = "bedrock"
DEFAULT_REGION = "us-west-2"

# Model per provider per tier. Tiers are the contract; ids are an implementation
# detail that changes with whoever is serving them.
CATALOGUE: dict[str, dict[str, str]] = {
    "bedrock": {
        TRIAGE: "us.amazon.nova-lite-v1:0",
        DEEP: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        SPECIALIST: "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    },
    "anthropic": {
        TRIAGE: "claude-haiku-4-5",
        DEEP: "claude-sonnet-5",
        SPECIALIST: "claude-haiku-4-5",
    },
    "ollama": {
        TRIAGE: "llama3.2",
        DEEP: "llama3.1:8b",
        SPECIALIST: "llama3.2",
    },
}

# USD per million tokens (input, output), so the run cost printed at the end of
# a run stays honest when the provider changes.
PRICING: dict[str, dict[str, tuple[float, float]]] = {
    "bedrock": {
        TRIAGE: (0.06, 0.24),
        DEEP: (3.00, 15.00),
        SPECIALIST: (1.00, 5.00),
    },
    "anthropic": {
        TRIAGE: (1.00, 5.00),
        DEEP: (2.00, 10.00),
        SPECIALIST: (1.00, 5.00),
    },
    "ollama": {TRIAGE: (0.0, 0.0), DEEP: (0.0, 0.0), SPECIALIST: (0.0, 0.0)},
}


def provider() -> str:
    name = os.environ.get("QUORUM_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    if name not in CATALOGUE:
        raise ValueError(
            f"Unknown QUORUM_PROVIDER {name!r}. "
            f"Choose one of: {', '.join(sorted(CATALOGUE))}"
        )
    return name


def model_id(tier: str, name: str | None = None) -> str:
    return CATALOGUE[name or provider()][tier]


def price(tier: str, name: str | None = None) -> tuple[float, float]:
    """(input, output) USD per million tokens for this tier."""
    return PRICING[name or provider()][tier]


def cost(tier: str, usage: dict, name: str | None = None) -> float:
    """Dollar cost of one call, from a Strands accumulated_usage dict."""
    dollars_in, dollars_out = price(tier, name)
    return (usage.get("inputTokens", 0) * dollars_in
            + usage.get("outputTokens", 0) * dollars_out) / 1_000_000


def get_model(tier: str, *, max_tokens: int = 4096):
    """A Strands model for this tier, from whichever provider is configured.

    Imports are deferred: each provider adapter needs its own SDK installed, and
    requiring all of them to use one of them would defeat the point.
    """
    name = provider()
    identifier = model_id(tier, name)

    if name == "bedrock":
        from strands.models import BedrockModel

        return BedrockModel(
            model_id=identifier,
            region_name=os.environ.get("AWS_REGION", DEFAULT_REGION),
        )

    if name == "anthropic":
        from strands.models.anthropic import AnthropicModel

        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "QUORUM_PROVIDER=anthropic requires ANTHROPIC_API_KEY to be set."
            )
        return AnthropicModel(
            client_args={"api_key": key},
            model_id=identifier,
            max_tokens=max_tokens,
        )

    if name == "ollama":
        from strands.models.ollama import OllamaModel

        return OllamaModel(
            host=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            model_id=identifier,
        )

    raise ValueError(f"No adapter wired for provider {name!r}")


def describe() -> str:
    """One line naming the provider and what it will use, for run output."""
    name = provider()
    tiers = CATALOGUE[name]
    return (f"provider={name}  triage={tiers[TRIAGE]}  "
            f"deep={tiers[DEEP]}  specialist={tiers[SPECIALIST]}")
