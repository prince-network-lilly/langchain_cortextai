"""Demo: integrate ServiceNow's 3 APIs with CortexChain using only the @tool decorator.

This file shows the minimum surface area needed to plug an external REST API
into the framework. No subclassing, no boilerplate — three decorated functions
and one config block. Swap the URL / table names / fields and you've integrated
any other ServiceNow-style API.

Setup:
    export SNOW_INSTANCE_URL=https://<your-instance>.service-now.com
    export SNOW_USER=...
    export SNOW_PASS=...

Run:
    python examples/servicenow_tools_demo.py
"""

import json
import os

import requests
from requests.auth import HTTPBasicAuth

from cortexchain import CortexLLM, ReActAgent, AgentExecutor, tool
from dotenv import load_dotenv

load_dotenv()


# ---- 1. Config: the only thing that changes per ServiceNow table ------------

DEFAULT_ASSIGNMENT_GROUP = "GCCP-CMO-GLB"

SNOW_CONFIG = {
    "instance_url": os.getenv("SNOW_INSTANCE_URL", "").rstrip("/"),
    "user": os.getenv("SNOW_USER", ""),
    "password": os.getenv("SNOW_PASS", ""),
    "default_assignment_group": DEFAULT_ASSIGNMENT_GROUP,
    "tables": {
        "change_request": {
            "fields": ["number", "short_description", "state", "priority", "assigned_to"],
            "limit": 10,
        },
        "sc_req_item": {
            "fields": ["number", "short_description", "request_state", "requested_for", "priority"],
            "limit": 10,
        },
        "incident": {
            "fields": ["number", "short_description", "state", "priority", "caller_id", "sys_created_on"],
            "limit": 10,
        },
    },
}


# ---- 2. One shared call helper (the actual external integration) ------------

_ALLOWED_FIELDS = {
    "change_request": {
        "number", "short_description", "description", "state", "priority",
        "assigned_to", "assignment_group", "sys_created_on", "sys_updated_on",
        "start_date", "end_date", "type", "category", "risk", "impact",
    },
    "sc_req_item": {
        "number", "short_description", "description", "request_state",
        "requested_for", "priority", "assigned_to", "assignment_group",
        "sys_created_on", "sys_updated_on", "stage", "approval",
    },
    "incident": {
        "number", "short_description", "description", "state", "priority",
        "assigned_to", "assignment_group", "caller_id", "sys_created_on",
        "sys_updated_on", "category", "subcategory", "urgency", "impact",
        "resolved_at", "closed_at",
    },
}


def _parse_tool_input(table: str, tool_input: str) -> dict:
    """Accept either a plain string (treated as the query) or a JSON string
    with optional `query`, `limit`, `fields`, `order_by` keys."""
    cfg = SNOW_CONFIG["tables"][table]
    parsed = {
        "query": "",
        "limit": cfg["limit"],
        "fields": list(cfg["fields"]),
        "order_by": "sys_created_on",
        "order_dir": "DESC",
    }
    raw = (tool_input or "").strip()
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            parsed["query"] = str(data.get("query", "")).strip()
            if "limit" in data:
                parsed["limit"] = max(1, min(int(data["limit"]), 50))
            if "fields" in data and isinstance(data["fields"], list):
                allowed = _ALLOWED_FIELDS[table]
                requested = [f for f in data["fields"] if f in allowed]
                if requested:
                    parsed["fields"] = requested
            if "order_by" in data:
                ob = str(data["order_by"]).strip()
                if ob in _ALLOWED_FIELDS[table]:
                    parsed["order_by"] = ob
            if "order_dir" in data:
                od = str(data["order_dir"]).upper()
                if od in ("ASC", "DESC"):
                    parsed["order_dir"] = od
        except (ValueError, TypeError, KeyError):
            parsed["query"] = raw
    else:
        parsed["query"] = raw
    return parsed


def _snow_search(table: str, tool_input: str) -> str:
    p = _parse_tool_input(table, tool_input)
    url = f"{SNOW_CONFIG['instance_url']}/api/now/table/{table}"
    group_clause = f"assignment_group.name={SNOW_CONFIG['default_assignment_group']}"
    order_clause = f"ORDERBY{p['order_dir']}{p['order_by']}"
    print(f"DEBUG: _snow_search table={table} parsed={p}")
    params = {
        "sysparm_query": f"{group_clause}^{p['query']}^{order_clause}",
        "sysparm_limit": str(p["limit"]),
        "sysparm_fields": ",".join(p["fields"]),
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }
    try:
        resp = requests.get(
            url,
            params=params,
            auth=HTTPBasicAuth(SNOW_CONFIG["user"], SNOW_CONFIG["password"]),
            headers={"Accept": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        return json.dumps({"table": table, "results": resp.json().get("result", [])}, ensure_ascii=False)
    except requests.RequestException as e:
        return json.dumps({"table": table, "error": str(e)[:300]})


# ---- 3. Three tools — pure @tool decorator, one line of logic each ---------

_TOOL_CALLS = {"count": 0}


_CR_DESC = """\
Search ServiceNow Change Requests (CHG / change_request table).

Action Input MUST be a JSON object (string) with these keys:
  query     (str, required)  ServiceNow encoded-query fragment OR free text.
                             Example: "active=true^priority=1" or "VPN".
                             Use "" to skip text filtering.
  limit     (int, optional)  Max rows, 1-50. Default 10.
  fields    (list, optional) Which columns to return. Allowed:
                             number, short_description, description, state,
                             priority, assigned_to, assignment_group,
                             sys_created_on, sys_updated_on, start_date,
                             end_date, type, category, risk, impact.
  order_by  (str, optional)  Column to sort by. Default sys_created_on.
  order_dir (str, optional)  "ASC" or "DESC". Default DESC.

Example Action Input:
  {"query": "active=true^priority=1", "limit": 5,
   "fields": ["number","short_description","priority","assigned_to"]}
"""

_SR_DESC = """\
Search ServiceNow Service Requests (REQ/RITM / sc_req_item table).

Action Input MUST be a JSON object (string) with these keys:
  query     (str, required)  Encoded-query fragment OR free text. "" to skip.
  limit     (int, optional)  Max rows, 1-50. Default 10.
  fields    (list, optional) Allowed: number, short_description, description,
                             request_state, requested_for, priority,
                             assigned_to, assignment_group, sys_created_on,
                             sys_updated_on, stage, approval.
  order_by  (str, optional)  Default sys_created_on.
  order_dir (str, optional)  "ASC" or "DESC". Default DESC.

Example Action Input:
  {"query": "requested_for.name=Jaimin", "limit": 10,
   "fields": ["number","short_description","request_state","requested_for"]}
"""

_INC_DESC = """\
Search ServiceNow Incidents (INC / incident table).

Action Input MUST be a JSON object (string) with these keys:
  query     (str, required)  Encoded-query fragment OR free text. "" to skip.
  limit     (int, optional)  Max rows, 1-50. Default 10.
  fields    (list, optional) Allowed: number, short_description, description,
                             state, priority, assigned_to, assignment_group,
                             caller_id, sys_created_on, sys_updated_on,
                             category, subcategory, urgency, impact,
                             resolved_at, closed_at.
  order_by  (str, optional)  Default sys_created_on.
  order_dir (str, optional)  "ASC" or "DESC". Default DESC.

Example Action Input:
  {"query": "assigned_to.name=Jaimin^stateNOT IN6,7,8", "limit": 10,
   "fields": ["number","short_description","state","priority","assigned_to"]}
"""


@tool(name="search_change_requests", description=_CR_DESC)
def search_change_requests(query: str) -> str:
    _TOOL_CALLS["count"] += 1
    res = _snow_search("change_request", query)
    return res


@tool(name="search_service_requests", description=_SR_DESC)
def search_service_requests(query: str) -> str:
    _TOOL_CALLS["count"] += 1
    res = _snow_search("sc_req_item", query)
    return res


@tool(name="search_incidents", description=_INC_DESC)
def search_incidents(query: str) -> str:
    _TOOL_CALLS["count"] += 1
    res = _snow_search("incident", query)
    return res


# ---- 4. Wire the tools into a ReAct agent ----------------------------------


_RETRY_PREAMBLE = (
    "REMINDER: your previous attempt did not call any tool. You MUST emit:\n"
    "Action: <tool_name>\nAction Input: <query>\n"
    "before any Final Answer. Try again.\n\n"
)


def build_agent():
    llm = CortexLLM(agent_name="mydemo-prince-l103669")
    tools = [search_change_requests, search_service_requests, search_incidents]
    agent = ReActAgent(llm=llm, tools=tools)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)


def ask(executor: AgentExecutor, question: str, max_retries: int = 2) -> str:
    """Run the agent and force at least one tool call.

    If the model skipped tool use entirely (LLM hallucinated a Final Answer
    straight from the question), retry with a stronger reminder.
    """
    prompt = question
    for attempt in range(max_retries + 1):
        _TOOL_CALLS["count"] = 0
        result = executor.run(prompt)
        if _TOOL_CALLS["count"] > 0:
            return result
        print(f"[ask] No tool called on attempt {attempt + 1}; retrying with reminder.")
        prompt = _RETRY_PREAMBLE + question
    return (
        "Could not get the model to call a tool after multiple attempts. "
        f"Last raw output:\n{result}"
    )


# ---- 5. Demo run -----------------------------------------------------------

if __name__ == "__main__":
    executor = build_agent()

    questions = [
        "give me top 30 incidents and SRs assigned to hemal",
    ]
    for q in questions:
        print(f"\n=== {q} ===")
        print(ask(executor, q))