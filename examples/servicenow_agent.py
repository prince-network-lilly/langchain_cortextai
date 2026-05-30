"""ServiceNow search agent — picks the right tool (CR/SR/INC) for the user's
question, builds a query, and returns a synthesized answer.

Env required:
    SNOW_INSTANCE_URL   e.g. https://lillyprod.service-now.com
    SNOW_USER
    SNOW_PASS
"""

from cortexchain import CortexLLM, ReActAgent, AgentExecutor
from cortexchain.tools.servicenow import (
    ChangeRequestSearchTool,
    ServiceRequestSearchTool,
    IncidentSearchTool,
)


def main():
    llm = CortexLLM(agent_name="servicenow-search-agent")

    tools = [
        ChangeRequestSearchTool(),
        ServiceRequestSearchTool(),
        IncidentSearchTool(),
    ]

    agent = ReActAgent(llm=llm, tools=tools)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)

    questions = [
        "Show me the open critical incidents related to VPN from this week.",
        "Any pending service requests for laptop access in finance?",
        "List recent change requests about database migration.",
    ]
    for q in questions:
        print("\n=== Q:", q)
        print(executor.run(q))


if __name__ == "__main__":
    main()
