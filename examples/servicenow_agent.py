import os
from cortexchain import CortexLLM
from cortexchain.agents import ServiceNowAgent

llm = CortexLLM(agent_name="mydemo-prince-l103669")

snow = ServiceNowAgent(
    llm=llm,
    instance_url = os.getenv("SNOW_INSTANCE_URL", ""),
    user = os.getenv("SNOW_USER", ""),
    password = os.getenv("SNOW_PASS", ""),
    assignment_group = os.getenv("SNOW_DEFAULT_ASSIGNMENT_GROUP", "GCCP-CMO-GLB")
)

QUESTIONS = [
    # Exercises: incident routing + custom limit + custom field set.
    "Give me the top 3 open incidents — only show number, description and priority.",
    # Exercises: change-request routing + ordering by a non-default column.
    "List 5 most recently updated change requests, sorted by latest.",
    # Exercises: service-request routing + filter by requested_for.
    "Show me service requests which are assign to Jaimin, limit 5.",
]

for q in QUESTIONS:
    print(f"\n=== Q: {q}")
    print(snow.ask(q))

# print(snow.ask("top 5 open incidents assigned to Jaimin"))
# print(snow.ask("recent change requests this week"))