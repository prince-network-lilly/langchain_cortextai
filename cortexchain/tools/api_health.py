"""API health check tool — batch-check multiple endpoints for uptime/latency."""

import json
import time
from typing import Dict, List, Optional
from cortexchain.tools.base import BaseTool

try:
    import requests
except ImportError:
    requests = None


class APIHealthCheckTool(BaseTool):
    """Checks health of API endpoints. Input: JSON list of URLs or a single URL string."""

    name = "api_health_check"
    description = (
        "Checks health/availability of API endpoints. "
        "Input: a URL string, or JSON list of URLs, or JSON with 'endpoints' key."
    )

    def __init__(self, timeout: int = 10, expected_status: int = 200):
        self.timeout = timeout
        self.expected_status = expected_status

    def run(self, tool_input: str) -> str:
        if requests is None:
            return "Error: 'requests' package not installed."

        try:
            data = json.loads(tool_input)
            if isinstance(data, list):
                urls = data
            elif isinstance(data, dict):
                urls = data.get("endpoints", data.get("urls", []))
            else:
                urls = [str(data)]
        except json.JSONDecodeError:
            urls = [tool_input.strip()]

        results = []
        for url in urls:
            results.append(self._check(url))

        healthy = sum(1 for r in results if r["healthy"])
        summary = f"\nSummary: {healthy}/{len(results)} endpoints healthy"
        lines = [self._format_result(r) for r in results]
        lines.append(summary)
        return "\n".join(lines)

    def _check(self, url: str) -> Dict:
        try:
            start = time.time()
            resp = requests.get(url, timeout=self.timeout)
            latency_ms = (time.time() - start) * 1000
            healthy = resp.status_code == self.expected_status
            return {
                "url": url,
                "status_code": resp.status_code,
                "latency_ms": round(latency_ms, 1),
                "healthy": healthy,
                "error": None,
            }
        except requests.exceptions.Timeout:
            return {"url": url, "status_code": None, "latency_ms": None, "healthy": False, "error": "Timeout"}
        except requests.exceptions.ConnectionError:
            return {
                "url": url,
                "status_code": None,
                "latency_ms": None,
                "healthy": False,
                "error": "Connection refused",
            }
        except Exception as e:
            return {"url": url, "status_code": None, "latency_ms": None, "healthy": False, "error": str(e)}

    def _format_result(self, result: Dict) -> str:
        icon = "OK" if result["healthy"] else "FAIL"
        if result["error"]:
            return f"[{icon}] {result['url']} — {result['error']}"
        return f"[{icon}] {result['url']} — HTTP {result['status_code']} ({result['latency_ms']}ms)"
