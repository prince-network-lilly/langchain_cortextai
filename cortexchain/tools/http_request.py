"""Make HTTP requests to external APIs."""
import json
from typing import Dict, Optional
from cortexchain.tools.base import BaseTool

try:
    import requests
except ImportError:
    requests = None


class HTTPRequestTool(BaseTool):
    """Makes HTTP requests (GET/POST). Input: JSON with 'url', optional 'method', 'headers', 'body'."""

    name = "http_request"
    description = (
        "Makes HTTP requests to APIs. Input should be JSON: "
        '{"url": "...", "method": "GET|POST", "headers": {...}, "body": {...}}'
    )

    def __init__(self, timeout: int = 30, allowed_domains: Optional[list] = None):
        self.timeout = timeout
        self.allowed_domains = allowed_domains

    def run(self, tool_input: str) -> str:
        if requests is None:
            return "Error: 'requests' package not installed. Run: pip install requests"

        try:
            params = json.loads(tool_input)
        except json.JSONDecodeError:
            # Treat as a raw URL for GET request
            params = {"url": tool_input.strip(), "method": "GET"}

        url = params.get("url", "")
        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        body = params.get("body")

        if self.allowed_domains:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            if not any(d in domain for d in self.allowed_domains):
                return f"Error: Domain {domain!r} not in allowed list: {self.allowed_domains}"

        try:
            if method == "GET":
                resp = requests.get(url, headers=headers, timeout=self.timeout)
            elif method == "POST":
                resp = requests.post(url, headers=headers, json=body, timeout=self.timeout)
            elif method == "PUT":
                resp = requests.put(url, headers=headers, json=body, timeout=self.timeout)
            elif method == "DELETE":
                resp = requests.delete(url, headers=headers, timeout=self.timeout)
            else:
                return f"Error: Unsupported method: {method}"

            try:
                content = json.dumps(resp.json(), indent=2)
            except (json.JSONDecodeError, ValueError):
                content = resp.text[:2000]

            return f"Status: {resp.status_code}\n{content}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
