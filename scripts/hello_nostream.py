from strands import Agent
from strands.models import BedrockModel

model = BedrockModel(
    model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="us-west-2",
    streaming=False,
)
agent = Agent(model=model, system_prompt="Answer in one short sentence.")
result = agent("What is a city council agenda packet?")
print("\n--- usage ---")
print(result.metrics.accumulated_usage)
