"""The model that backs the hosted agent itself.

Routed through the same provider layer as the pipeline's own tiers, so the
deployed agent and the code it calls agree on who is serving them. Set
QUORUM_PROVIDER in the runtime environment to change it; Bedrock is the default.

The scaffold shipped a hardcoded BedrockModel here. That is fine until the
account loses Bedrock access, at which point the tools keep working and the
agent hosting them does not.
"""

from quorum.models import DEEP, get_model


def load_model():
    """The reasoning model for the hosted agent."""
    return get_model(DEEP)
