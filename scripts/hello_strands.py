"""Smoke test: validates AWS credentials, region and Bedrock model access
through Strands in a single call. Uses Haiku to keep the cost negligible."""

from strands import Agent
from strands.models import BedrockModel

MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

model = BedrockModel(model_id=MODEL_ID, region_name="us-west-2")
agent = Agent(model=model, system_prompt="Answer in one short sentence.")

result = agent("What is a city council agenda packet?")
print("\n--- usage ---")
print(result.metrics.accumulated_usage)
