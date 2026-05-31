"""ServiceNow Table API search tools (CR / SR / INC).

Each tool accepts a JSON `Action Input` describing the search and returns
the matching rows as a JSON string. The agent reads the JSON back and
reasons over it.

Action Input schema (passed to `run()` as a JSON string):
    {
      "query":     "<encoded-query fragment OR free text>",   # required
      "limit":     <int 1..50>,                               # optional
      "fields":    [<column>, ...],                           # optional, allow-listed
      "order_by":  "<column>",                                # optional, allow-listed
      "order_dir": "ASC" | "DESC"                             # optional
    }

Plain strings are still accepted (treated as the `query`) for backward
compatibility with the original NL-only interface.

Credentials & instance URL:
    Pass them as constructor arguments (preferred):
        IncidentSearchTool(
            instance_url="https://acme.service-now.com",
            user="svc_account",
            password="...",
            default_assignment_group="GCCP-CMO-GLB",
        )

    Or fall back to environment variables:
        SNOW_INSTANCE_URL  e.g. https://<instance>.service-now.com
        SNOW_USER
        SNOW_PASS
        SNOW_DEFAULT_ASSIGNMENT_GROUP   (optional)
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Set

import requests
from requests.auth import HTTPBasicAuth

from cortexchain.tools.base import BaseTool


# ---- Defaults & allow-lists ------------------------------------------------

_DEFAULT_FIELDS: Dict[str, List[str]] = {
    "change_request": [
        "number", "short_description", "state", "priority", "assigned_to",
    ],
    "sc_req_item": [
        "number", "short_description", "state", "request", "requested_for", "priority",
    ],
    "incident": [
        "number", "short_description", "state", "priority",
        "caller_id", "sys_created_on",
    ],
}

_ALLOWED_FIELDS: Dict[str, Set[str]] = {
    "change_request": {
        "number", "short_description", "description", "state", "priority",
        "assigned_to", "assignment_group", "sys_created_on", "sys_updated_on",
        "start_date", "end_date", "type", "category", "risk", "impact",
    },
    "sc_req_item": {
        "number", "short_description", "description", "state",
        "request", "requested_for", "priority", "assigned_to", "assignment_group",
        "sys_created_on", "sys_updated_on", "stage", "approval",
        "cat_item", "opened_by", "opened_at", "due_date",
    },
    "incident": {
        "number", "short_description", "description", "state", "priority",
        "assigned_to", "assignment_group", "caller_id", "sys_created_on",
        "sys_updated_on", "category", "subcategory", "urgency", "impact",
        "resolved_at", "closed_at",
    },
}

_DEFAULT_LIMIT = 10
_MAX_LIMIT = 50

# NL-fallback hints when the LLM passes free text instead of a JSON object.
# State codes differ per table — keep these table-scoped.
_STATE_KEYWORDS_BY_TABLE: Dict[str, Dict[str, str]] = {
    "incident": {
        "open": "stateNOT IN6,7,8",
        "active": "active=true",
        "closed": "state=7",
        "resolved": "state=6",
        "cancelled": "state=8",
        "new": "state=1",
        "in progress": "state=2",
        "on hold": "state=3",
    },
    "change_request": {
        "open": "stateNOT IN3,4",
        "active": "active=true",
        "closed": "state=3",
        "cancelled": "state=4",
        "new": "state=-5",
        "scheduled": "state=-2",
        "implement": "state=-1",
        "review": "state=0",
    },
    "sc_req_item": {
        "open": "stateIN1,2,3",
        "pending": "state=1",
        "work in progress": "state=3",
        "in progress": "state=3",
        "closed": "stateIN4,7",
        "closed complete": "state=4",
        "closed skipped": "state=7",
    },
}

_PRIORITY_KEYWORDS = {
    "critical": "priority=1",
    "high": "priority=2",
    "moderate": "priority=3",
    "medium": "priority=3",
    "low": "priority=4",
    "planning": "priority=5",
}

_NUMBER_RE = re.compile(r"\b(CHG|REQ|INC|RITM)\d{4,}\b", re.IGNORECASE)


def _nl_to_query(text: str, table: str) -> str:
    """Best-effort NL -> ServiceNow encoded-query fragment for a given table.

    Used only when the agent passes a plain string (not a JSON object).
    Picks up explicit ticket numbers, table-specific state keywords, and
    treats the residue as text-search input.
    """
    clauses: List[str] = []
    q = text.strip()

    num_match = _NUMBER_RE.search(q)
    if num_match:
        clauses.append(f"number={num_match.group(0).upper()}")
        q = q.replace(num_match.group(0), "").strip()

    lowered = q.lower()
    state_map = _STATE_KEYWORDS_BY_TABLE.get(table, {})
    # Match longer phrases first (e.g. "in progress" before "in").
    for kw in sorted(state_map, key=len, reverse=True):
        if kw in lowered:
            clauses.append(state_map[kw])
            lowered = lowered.replace(kw, "")
    for kw, clause in _PRIORITY_KEYWORDS.items():
        if re.search(rf"\b{kw}\s+priority\b", lowered) or re.search(rf"\bpriority\s+{kw}\b", lowered):
            clauses.append(clause)
            lowered = lowered.replace(kw, "")

    residual = re.sub(r"\s+", " ", lowered).strip(" ?.,;:")
    if residual:
        clauses.append(f"123TEXTQUERY41={residual}")

    return "^".join(clauses)


# ---- Shared tool implementation -------------------------------------------

class _ServiceNowSearchTool(BaseTool):
    """Shared implementation. The three exported tools differ only by table."""

    table: str = ""
    record_kind: str = ""

    def __init__(
        self,
        instance_url: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        user_env: str = "SNOW_USER",
        pass_env: str = "SNOW_PASS",
        instance_url_env: str = "SNOW_INSTANCE_URL",
        fields: Optional[List[str]] = None,
        limit: int = _DEFAULT_LIMIT,
        timeout: int = 15,
        default_assignment_group: Optional[str] = None,
        default_order_by: str = "sys_created_on",
        default_order_dir: str = "DESC",
    ):
        """Caller-supplied credentials take priority; env vars are a fallback.

        Args:
            instance_url: Full ServiceNow base URL (e.g. https://acme.service-now.com).
                Falls back to ``$SNOW_INSTANCE_URL`` (or ``instance_url_env``).
            user: ServiceNow username for basic auth. Falls back to ``$SNOW_USER``.
            password: ServiceNow password for basic auth. Falls back to ``$SNOW_PASS``.
            user_env / pass_env / instance_url_env: env-var names to look up
                when the corresponding argument is not passed.
            default_assignment_group: scopes every search to this group via
                ``assignment_group.name=<value>``. Empty string disables it.
                Falls back to ``$SNOW_DEFAULT_ASSIGNMENT_GROUP``.
        """
        resolved_url = instance_url or os.getenv(instance_url_env, "")
        self.instance_url = resolved_url.rstrip("/")
        self._user = user if user is not None else os.getenv(user_env)
        self._password = password if password is not None else os.getenv(pass_env)
        self.fields = fields or list(_DEFAULT_FIELDS.get(self.table, []))
        self.limit = limit
        self.timeout = timeout
        self.default_assignment_group = (
            default_assignment_group
            if default_assignment_group is not None
            else os.getenv("SNOW_DEFAULT_ASSIGNMENT_GROUP", "")
        )
        self.default_order_by = default_order_by
        self.default_order_dir = default_order_dir.upper()

    # -- helpers ----------------------------------------------------------

    def _auth(self) -> HTTPBasicAuth:
        if not self._user or not self._password:
            raise RuntimeError(
                "ServiceNow credentials missing: pass user/password to the "
                "tool constructor or set SNOW_USER / SNOW_PASS in the environment."
            )
        return HTTPBasicAuth(self._user, self._password)

    def _endpoint(self) -> str:
        if not self.instance_url:
            raise RuntimeError(
                "ServiceNow instance_url is missing: pass it to the tool "
                "constructor or set SNOW_INSTANCE_URL in the environment."
            )
        return f"{self.instance_url}/api/now/table/{self.table}"

    def _parse_input(self, tool_input: str) -> Dict[str, Any]:
        """Parse the agent's `Action Input` into a normalized search spec."""
        allowed = _ALLOWED_FIELDS[self.table]
        spec: Dict[str, Any] = {
            "query": "",
            "limit": self.limit,
            "fields": list(self.fields),
            "order_by": self.default_order_by,
            "order_dir": self.default_order_dir,
        }
        raw = (tool_input or "").strip()
        if not raw:
            return spec

        if raw.startswith("{"):
            try:
                data = json.loads(raw)
            except (ValueError, TypeError):
                spec["query"] = _nl_to_query(raw, self.table)
                return spec

            spec["query"] = str(data.get("query", "")).strip()
            if "limit" in data:
                try:
                    spec["limit"] = max(1, min(int(data["limit"]), _MAX_LIMIT))
                except (TypeError, ValueError):
                    pass
            if isinstance(data.get("fields"), list):
                requested = [f for f in data["fields"] if f in allowed]
                if requested:
                    spec["fields"] = requested
            if "order_by" in data:
                ob = str(data["order_by"]).strip()
                if ob in allowed:
                    spec["order_by"] = ob
            if "order_dir" in data:
                od = str(data["order_dir"]).upper()
                if od in ("ASC", "DESC"):
                    spec["order_dir"] = od
        else:
            spec["query"] = _nl_to_query(raw, self.table)

        return spec

    def _build_sysparm_query(self, spec: Dict[str, Any]) -> str:
        clauses: List[str] = []
        if self.default_assignment_group:
            clauses.append(f"assignment_group.name={self.default_assignment_group}")
        if spec["query"]:
            clauses.append(spec["query"])
        clauses.append(f"ORDERBY{spec['order_dir']}{spec['order_by']}")
        return "^".join(clauses)

    # -- public API -------------------------------------------------------

    def run(self, tool_input: str) -> str:
        spec = self._parse_input(tool_input)
        sysparm_query = self._build_sysparm_query(spec)

        params: Dict[str, str] = {
            "sysparm_query": sysparm_query,
            "sysparm_limit": str(spec["limit"]),
            "sysparm_fields": ",".join(spec["fields"]),
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
            "limit": spec["limit"],
            "fields": spec["fields"],
            "count": len(results),
            "results": results,
        }, ensure_ascii=False)


# ---- Tool descriptions (teach the LLM the JSON schema) --------------------

# Per-table state legends. The LLM reads these to translate words in the
# USER'S prompt ("open", "closed", "in progress") into the right numeric
# code FOR THAT TABLE. Codes differ between tables — do not share.
_STATE_LEGEND: Dict[str, str] = {
    "incident": (
        "1=New, 2=In Progress, 3=On Hold, 6=Resolved, 7=Closed, 8=Cancelled.\n"
        '                             "open" means stateNOT IN6,7,8.'
    ),
    "change_request": (
        "-5=New, -4=Assess, -3=Authorize, -2=Scheduled, -1=Implement, "
        "0=Review, 3=Closed, 4=Cancelled.\n"
        '                             "open" means stateNOT IN3,4.'
    ),
    "sc_req_item": (
        "1=Pending, 2=Open, 3=Work In Progress, 4=Closed Complete, "
        "7=Closed Skipped.\n"
        '                             "open" means stateIN1,2,3.'
    ),
}

# Per-table priority legend (consistent across these tables).
_PRIORITY_LEGEND = (
    "1=Critical, 2=High, 3=Moderate, 4=Low, 5=Planning."
)


def _describe(table_label: str, table_name: str, allowed_fields: Set[str]) -> str:
    fields_str = ", ".join(sorted(allowed_fields))
    return (
        f"Search ServiceNow {table_label} ({table_name} table).\n\n"
        "HOW TO BUILD `query`: read the USER'S PROMPT, identify the filters\n"
        "they mentioned (state, priority, assignee, requester, text, dates, "
        "ticket number),\n"
        "and translate ONLY those into a ServiceNow encoded-query fragment.\n"
        "Do NOT add filters the user did not ask for. If the user asked for\n"
        "no filter, pass query=\"\".\n\n"
        f"State codes for this table:\n"
        f"  {_STATE_LEGEND[table_name]}\n"
        f"Priority codes (all tables): {_PRIORITY_LEGEND}\n\n"
        "Common encoded-query patterns (substitute values from the prompt):\n"
        '  state                  -> "state=<code>"  or  "stateIN<a>,<b>"\n'
        '  priority               -> "priority=<code>"\n'
        '  assignee               -> "assigned_to.nameLIKE<name from prompt>"\n'
        '  requester (RITM only)  -> "requested_for.nameLIKE<name from prompt>"\n'
        '  ticket number          -> "number=<INC/CHG/RITM number from prompt>"\n'
        '  free-text search       -> "123TEXTQUERY41=<keywords from prompt>"\n'
        "  combine with `^` (AND).\n\n"
        "Action Input MUST be a JSON object (string) with these keys:\n"
        '  query     (str, required)  Encoded query built from filters\n'
        '                             the USER actually mentioned. "" if none.\n'
        f"  limit     (int, optional)  Max rows 1-{_MAX_LIMIT}. Default {_DEFAULT_LIMIT}.\n"
        "                             Override only when the user names a count.\n"
        "  fields    (list, optional) Columns to return. Allowed:\n"
        f"                             {fields_str}.\n"
        "                             Narrow only when user asks for specific columns.\n"
        "  order_by  (str, optional)  Default sys_created_on.\n"
        '  order_dir (str, optional)  "ASC" or "DESC". Default DESC.\n\n'
        "Returns JSON: {table, sysparm_query, count, results: [...]}"
    )


# ---- Concrete tools --------------------------------------------------------

class ChangeRequestSearchTool(_ServiceNowSearchTool):
    name = "search_change_requests"
    table = "change_request"
    record_kind = "change_request"
    description = _describe(
        "Change Requests (CHG records)",
        "change_request",
        _ALLOWED_FIELDS["change_request"],
    )


class ServiceRequestSearchTool(_ServiceNowSearchTool):
    name = "search_service_requests"
    table = "sc_req_item"
    record_kind = "service_request"
    description = _describe(
        "Service Requests / Requested Items (RITM records)",
        "sc_req_item",
        _ALLOWED_FIELDS["sc_req_item"],
    )


class IncidentSearchTool(_ServiceNowSearchTool):
    name = "search_incidents"
    table = "incident"
    record_kind = "incident"
    description = _describe(
        "Incidents (INC records)",
        "incident",
        _ALLOWED_FIELDS["incident"],
    )
