"""Pipeline monitoring tool for MLOps — check pipeline health, logs, and alerts."""

import json
import time
from typing import Dict, List, Optional
from cortexchain.tools.base import BaseTool

try:
    import requests
except ImportError:
    requests = None


class PipelineMonitorTool(BaseTool):
    """Monitors ML pipeline health: checks status, latency, error rates, and recent runs."""

    name = "pipeline_monitor"
    description = (
        "Monitors ML pipeline health. Actions: "
        '"status" (check pipeline status), '
        '"health_check" (run health check on endpoints), '
        '"recent_runs" (get recent pipeline run info), '
        '"alert" (check for alerts/anomalies). '
        'Input: JSON with "action" and relevant fields.'
    )

    def __init__(self, pipelines: Optional[Dict[str, str]] = None):
        self.pipelines = pipelines or {}
        self._run_history: List[Dict] = []

    def register_pipeline(self, name: str, endpoint: str) -> None:
        self.pipelines[name] = endpoint

    def run(self, tool_input: str) -> str:
        try:
            params = json.loads(tool_input)
        except json.JSONDecodeError:
            return 'Error: Input must be JSON with "action" key.'

        action = params.get("action", "")
        if action == "status":
            return self._check_status(params)
        elif action == "health_check":
            return self._health_check(params)
        elif action == "recent_runs":
            return self._recent_runs(params)
        elif action == "log_run":
            return self._log_run(params)
        elif action == "alert":
            return self._check_alerts(params)
        else:
            return f"Error: Unknown action '{action}'. Use: status, health_check, recent_runs, log_run, alert."

    def _check_status(self, params: Dict) -> str:
        pipeline_name = params.get("pipeline", "")
        if pipeline_name and pipeline_name in self.pipelines:
            endpoint = self.pipelines[pipeline_name]
            return self._ping_endpoint(pipeline_name, endpoint)

        # Check all registered pipelines
        if not self.pipelines:
            return "No pipelines registered. Use register_pipeline() to add endpoints."

        results = []
        for name, endpoint in self.pipelines.items():
            results.append(self._ping_endpoint(name, endpoint))
        return "\n".join(results)

    def _ping_endpoint(self, name: str, endpoint: str) -> str:
        if requests is None:
            return f"[{name}] Cannot check — 'requests' not installed"
        try:
            start = time.time()
            resp = requests.get(endpoint, timeout=10)
            latency = (time.time() - start) * 1000
            status = "HEALTHY" if resp.status_code < 400 else "UNHEALTHY"
            return f"[{name}] {status} | HTTP {resp.status_code} | {latency:.0f}ms | {endpoint}"
        except Exception as e:
            return f"[{name}] DOWN | Error: {e} | {endpoint}"

    def _health_check(self, params: Dict) -> str:
        endpoints = params.get("endpoints", [])
        if not endpoints:
            endpoints = [{"name": k, "url": v} for k, v in self.pipelines.items()]
        if not endpoints:
            return "No endpoints to check."

        results = []
        for ep in endpoints:
            name = ep.get("name", ep.get("url", "unknown"))
            url = ep.get("url", "")
            results.append(self._ping_endpoint(name, url))
        return "\n".join(results)

    def _log_run(self, params: Dict) -> str:
        run_info = {
            "pipeline": params.get("pipeline", "unknown"),
            "status": params.get("status", "completed"),
            "duration_sec": params.get("duration_sec", 0),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metrics": params.get("metrics", {}),
            "error": params.get("error", ""),
        }
        self._run_history.append(run_info)
        return f"Logged run for pipeline '{run_info['pipeline']}': {run_info['status']}"

    def _recent_runs(self, params: Dict) -> str:
        limit = params.get("limit", 10)
        pipeline = params.get("pipeline", "")
        runs = self._run_history
        if pipeline:
            runs = [r for r in runs if r["pipeline"] == pipeline]
        recent = runs[-limit:]
        if not recent:
            return "No pipeline runs recorded."
        lines = []
        for r in recent:
            lines.append(f"[{r['timestamp']}] {r['pipeline']}: {r['status']} ({r['duration_sec']}s)")
        return "\n".join(lines)

    def _check_alerts(self, params: Dict) -> str:
        threshold_latency = params.get("max_latency_ms", 5000)
        threshold_error_rate = params.get("max_error_rate", 0.1)

        alerts = []
        recent = self._run_history[-20:]
        if recent:
            errors = [r for r in recent if r.get("status") == "failed"]
            error_rate = len(errors) / len(recent)
            if error_rate > threshold_error_rate:
                alerts.append(f"HIGH ERROR RATE: {error_rate:.1%} of last {len(recent)} runs failed")

            slow_runs = [r for r in recent if r.get("duration_sec", 0) > threshold_latency / 1000]
            if slow_runs:
                alerts.append(f"SLOW RUNS: {len(slow_runs)} runs exceeded {threshold_latency}ms")

        if not alerts:
            return "No alerts. All systems nominal."
        return "ALERTS:\n" + "\n".join(f"  - {a}" for a in alerts)
