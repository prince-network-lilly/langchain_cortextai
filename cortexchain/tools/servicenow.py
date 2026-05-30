"""ServiceNow Table API search tools (CR / SR / INC).

Each tool takes a natural-language query, translates it into a ServiceNow
encoded query (`sysparm_query`), calls the Table API, and returns the top
results as a JSON string. The agent reads the JSON back and reasons over it.
"""

import json
import os
import re
from typing import Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

from cortexchain.tools.base import BaseTool


_DEFAULT_FIELDS = [
    "number",
    "short_description",
    "state",
    "priority",
    "sys_created_on",
    "assigned_to",
]

_STATE_KEYWORDS = {
    "open": "stateNOT IN6,7,8",
    "active": "active=true",
    "closed": "state=7",
    "resolved": "state=6",
    "cancelled": "state=8",
    "new": "state=1",
    "in progress": "state=2",
    "on hold": "state=3",
}

_PRIORITY_KEYWORDS = {
    "critical": "priority=1",
    "high": "priority=2",
    "moderate": "priority=3",
    "medium": "priority=3",
    "low": "priority=4",
    "planning": "priority=5",
}

_NUMBER_RE = re.compile(r"\b(CHG|REQ|INC|RITM|CR|SR)\d{4,}\b", re.IGNORECASE)


def _nl_to_sysparm(query: str, table: str) -> str:
    """Best-effort NL -> ServiceNow encoded query.

    Strategy: pick up explicit ticket numbers, state/priority keywords, and
    fall back to a 123TEXTQUERY41 full-text search on the rest.
    """
    clauses: List[str] = []
    q = query.strip()

    num_match = _NUMBER_RE.search(q)
    if num_match:
        clauses.append(f"number={num_match.group(0).upper()}")
        q = q.replace(num_match.group(0), "").strip()

    lowered = q.lower()
    for kw, clause in _STATE_KEYWORDS.items():
        if kw in lowered:
            clauses.append(clause)
            lowered = lowered.replace(kw, "")
    for kw, clause in _PRIORITY_KEYWORDS.items():
        if re.search(rf"\b{kw}\s+priority\b", lowered) or re.search(rf"\bpriority\s+{kw}\b", lowered):
            clauses.append(clause)
            lowered = lowered.replace(kw, "")

    residual = re.sub(r"\s+", " ", lowered).strip(" ?.,;:")
    if residual:
        clauses.append(f"123TEXTQUERY41={residual}")

    return "^".join(clauses) if clauses else f"123TEXTQUERY41={query.strip()}"


class _ServiceNowSearchTool(BaseTool):
    """Shared implementation. The three exported tools differ only by table."""

    table: str = ""
    record_kind: str = ""

    def __init__(
        self,
        instance_url: Optional[str] = None,
        user_env: str = "SNOW_USER",
        pass_env: str = "SNOW_PASS",
        fields: Optional[List[str]] = None,
        limit: int = 5,
        timeout: int = 15,
    ):
        self.instance_url = (instance_url or os.getenv("SNOW_INSTANCE_URL", "")).rstrip("/")
        self.user_env = user_env
        self.pass_env = pass_env
        self.fields = fields or _DEFAULT_FIELDS
        self.limit = limit
        self.timeout = timeout

    def _auth(self) -> HTTPBasicAuth:
        user = os.getenv(self.user_env)
        password = os.getenv(self.pass_env)
        if not user or not password:
            raise RuntimeError(
                f"ServiceNow credentials missing: set {self.user_env} and {self.pass_env}."
            )
        return HTTPBasicAuth(user, password)

    def _endpoint(self) -> str:
        if not self.instance_url:
            raise RuntimeError("SNOW_INSTANCE_URL is not set.")
        return f"{self.instance_url}/api/now/table/{self.table}"

    def run(self, tool_input: str) -> str:
        if not tool_input or not tool_input.strip():
            return json.dumps({"error": "empty query", "table": self.table})

        sysparm_query = _nl_to_sysparm(tool_input, self.table)
        params: Dict[str, str] = {
            "sysparm_query": sysparm_query,
            "sysparm_limit": str(self.limit),
            "sysparm_fields": ",".join(self.fields),
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
        }

        try:
            resp = requests.get(
                self._endpoint(),
                params=params,
                auth=self._auth(),
                headers={"Accept": "application/json"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
        except requests.HTTPError as e:
            return json.dumps({
                "error": "http_error",
                "status": e.response.status_code if e.response else None,
                "table": self.table,
                "sysparm_query": sysparm_query,
                "detail": (e.response.text[:300] if e.response else str(e)),
            })
        except requests.RequestException as e:
            return json.dumps({
                "error": "request_failed",
                "table": self.table,
                "sysparm_query": sysparm_query,
                "detail": str(e)[:300],
            })

        results = payload.get("result", [])
        return json.dumps({
            "kind": self.record_kind,
            "table": self.table,
            "sysparm_query": sysparm_query,
            "count": len(results),
            "results": results,
        }, ensure_ascii=False)


class ChangeRequestSearchTool(_ServiceNowSearchTool):
    name = "search_change_requests"
    description = (
        "Search ServiceNow Change Requests (CHG / change_request table). "
        "Input: a natural-language query describing the change records you want "
        "(e.g. 'open critical changes about database migration this week'). "
        "Returns JSON with the top matching CHG records."
    )
    table = "change_request"
    record_kind = "change_request"


class ServiceRequestSearchTool(_ServiceNowSearchTool):
    name = "search_service_requests"
    description = (
        "Search ServiceNow Service Requests (REQ/RITM / sc_request table). "
        "Input: a natural-language query (e.g. 'pending laptop access requests "
        "for finance team'). Returns JSON with the top matching service requests."
    )
    table = "sc_request"
    record_kind = "service_request"


class IncidentSearchTool(_ServiceNowSearchTool):
    name = "search_incidents"
    description = (
        "Search ServiceNow Incidents (INC / incident table). "
        "Input: a natural-language query (e.g. 'high priority incidents about "
        "VPN outage in the last 24 hours'). Returns JSON with the top matching incidents."
    )
    table = "incident"
    record_kind = "incident"
