import os

from dotenv import load_dotenv

from cortexchain import AgentExecutor, CortexLLM, ReActAgent
from cortexchain.tools.servicenow import (
    ChangeRequestSearchTool,
    IncidentSearchTool,
    ServiceRequestSearchTool,
)

load_dotenv()


# ---- Build the agent -------------------------------------------------------

def build_executor() -> AgentExecutor:
    """Construct the three tools with explicit creds + instance URL.

    Replace `os.getenv(...)` calls with literals if you prefer to hard-code
    them for a quick test (NOT recommended for committed code).
    """
    instance_url = os.getenv("SNOW_INSTANCE_URL", "")
    user = os.getenv("SNOW_USER", "")
    password = os.getenv("SNOW_PASS", "")
    group = os.getenv("SNOW_DEFAULT_ASSIGNMENT_GROUP", "GCCP-CMO-GLB")

    common = dict(
        instance_url=instance_url,
        user=user,
        password=password,
        default_assignment_group=group,
    )

    tools = [
        ChangeRequestSearchTool(**common),
        ServiceRequestSearchTool(**common),
        IncidentSearchTool(**common),
    ]

    llm = CortexLLM(agent_name="mydemo-prince-l103669")
    agent = ReActAgent(llm=llm, tools=tools)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=5)


# ---- Smoke questions covering the new features ----------------------------

QUESTIONS = [
    # Exercises: incident routing + custom limit + custom field set.
    "Give me the top 3 open incidents — only show number, short_description and priority.",
    # Exercises: change-request routing + ordering by a non-default column.
    "List 5 most recently updated change requests, sorted by sys_updated_on desc.",
    # Exercises: service-request routing + filter by requested_for.
    "Show me service requests where requested_for is Jaimin, limit 5.",
]


def main() -> None:
    executor = build_executor()
    for q in QUESTIONS:
        print(f"\n=== Q: {q}")
        print(executor.run(q))


if __name__ == "__main__":
    main()