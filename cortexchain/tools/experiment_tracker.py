"""Experiment tracking tool for MLOps — log metrics, compare runs, manage experiments."""
import json
import os
import time
from typing import Any, Dict, List, Optional
from cortexchain.tools.base import BaseTool


class ExperimentTrackerTool(BaseTool):
    """Tracks ML experiments: logs metrics, parameters, and allows comparison across runs."""

    name = "experiment_tracker"
    description = (
        "Tracks ML experiments. Actions: "
        '"log" (log metrics/params for a run), '
        '"compare" (compare multiple runs), '
        '"list" (list all runs), '
        '"best" (get best run by metric). '
        'Input: JSON with "action" and relevant fields.'
    )

    def __init__(self, storage_dir: str = ".experiments"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _experiments_file(self) -> str:
        return os.path.join(self.storage_dir, "experiments.json")

    def _load_experiments(self) -> List[Dict]:
        path = self._experiments_file()
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_experiments(self, experiments: List[Dict]) -> None:
        with open(self._experiments_file(), "w", encoding="utf-8") as f:
            json.dump(experiments, f, indent=2, default=str)

    def run(self, tool_input: str) -> str:
        try:
            params = json.loads(tool_input)
        except json.JSONDecodeError:
            return 'Error: Input must be JSON with "action" key.'

        action = params.get("action", "")
        if action == "log":
            return self._log_run(params)
        elif action == "compare":
            return self._compare_runs(params)
        elif action == "list":
            return self._list_runs(params)
        elif action == "best":
            return self._best_run(params)
        else:
            return f"Error: Unknown action '{action}'. Use: log, compare, list, best."

    def _log_run(self, params: Dict) -> str:
        experiments = self._load_experiments()
        run = {
            "run_id": params.get("run_id", f"run_{len(experiments) + 1}"),
            "name": params.get("name", "unnamed"),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metrics": params.get("metrics", {}),
            "params": params.get("params", {}),
            "tags": params.get("tags", []),
            "notes": params.get("notes", ""),
        }
        experiments.append(run)
        self._save_experiments(experiments)
        return f"Logged run '{run['run_id']}' with metrics: {run['metrics']}"

    def _compare_runs(self, params: Dict) -> str:
        experiments = self._load_experiments()
        run_ids = params.get("run_ids", [])
        if run_ids:
            runs = [r for r in experiments if r["run_id"] in run_ids]
        else:
            runs = experiments[-5:]  # Last 5 by default

        if not runs:
            return "No runs found to compare."

        # Build comparison table
        all_metrics = set()
        for r in runs:
            all_metrics.update(r.get("metrics", {}).keys())

        lines = ["Run ID | " + " | ".join(sorted(all_metrics))]
        lines.append("-" * len(lines[0]))
        for r in runs:
            vals = [str(r.get("metrics", {}).get(m, "-")) for m in sorted(all_metrics)]
            lines.append(f"{r['run_id']} | " + " | ".join(vals))

        return "\n".join(lines)

    def _list_runs(self, params: Dict) -> str:
        experiments = self._load_experiments()
        if not experiments:
            return "No experiments logged yet."
        limit = params.get("limit", 10)
        lines = []
        for run in experiments[-limit:]:
            metrics_str = ", ".join(f"{k}={v}" for k, v in run.get("metrics", {}).items())
            lines.append(f"[{run['timestamp']}] {run['run_id']} ({run['name']}): {metrics_str}")
        return "\n".join(lines)

    def _best_run(self, params: Dict) -> str:
        experiments = self._load_experiments()
        metric = params.get("metric", "")
        maximize = params.get("maximize", True)

        if not metric:
            return "Error: Must specify 'metric' to find best run."

        valid_runs = [r for r in experiments if metric in r.get("metrics", {})]
        if not valid_runs:
            return f"No runs found with metric '{metric}'."

        best = max(valid_runs, key=lambda r: r["metrics"][metric]) if maximize \
            else min(valid_runs, key=lambda r: r["metrics"][metric])

        return json.dumps(best, indent=2)


def log_experiment(name: str, metrics: Dict, params: Dict = None, storage_dir: str = ".experiments") -> str:
    """Convenience function to log an experiment run."""
    tool = ExperimentTrackerTool(storage_dir=storage_dir)
    payload = {"action": "log", "name": name, "metrics": metrics, "params": params or {}}
    return tool.run(json.dumps(payload))
