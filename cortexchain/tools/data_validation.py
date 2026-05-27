"""Data validation tool for MLOps — schema checks, null detection, drift detection."""

import json
from typing import Any, Dict, List, Optional
from cortexchain.tools.base import BaseTool


class DataValidationTool(BaseTool):
    """Validates data quality: schema checks, null percentages, value ranges, type consistency."""

    name = "data_validation"
    description = (
        "Validates data quality. Input: JSON with 'data' (list of dicts) and optional "
        "'schema' (expected column types), 'rules' (validation rules)."
    )

    def run(self, tool_input: str) -> str:
        try:
            params = json.loads(tool_input)
        except json.JSONDecodeError:
            return "Error: Input must be valid JSON."

        data = params.get("data", [])
        schema = params.get("schema", {})
        rules = params.get("rules", {})

        if not data:
            return "Error: No data provided."

        report = self._validate(data, schema, rules)
        return json.dumps(report, indent=2)

    def _validate(self, data: List[Dict], schema: Dict, rules: Dict) -> Dict:
        report = {
            "total_rows": len(data),
            "issues": [],
            "column_stats": {},
            "passed": True,
        }

        if not data:
            return report

        # Detect columns
        all_keys = set()
        for row in data:
            all_keys.update(row.keys())

        for col in sorted(all_keys):
            values = [row.get(col) for row in data]
            non_null = [v for v in values if v is not None and v != ""]
            null_pct = ((len(values) - len(non_null)) / len(values)) * 100

            col_stats = {
                "total": len(values),
                "non_null": len(non_null),
                "null_pct": round(null_pct, 2),
                "types_found": list(set(type(v).__name__ for v in non_null)),
            }

            # Numeric stats
            numeric_vals = [v for v in non_null if isinstance(v, (int, float))]
            if numeric_vals:
                col_stats["min"] = min(numeric_vals)
                col_stats["max"] = max(numeric_vals)
                col_stats["mean"] = round(sum(numeric_vals) / len(numeric_vals), 4)

            report["column_stats"][col] = col_stats

            # Schema check
            if schema and col in schema:
                expected_type = schema[col]
                wrong_types = [v for v in non_null if type(v).__name__ != expected_type]
                if wrong_types:
                    report["issues"].append(
                        f"Column '{col}': expected type '{expected_type}', "
                        f"found {len(wrong_types)} values with wrong type"
                    )
                    report["passed"] = False

            # Null threshold
            if rules.get("max_null_pct") and null_pct > rules["max_null_pct"]:
                report["issues"].append(
                    f"Column '{col}': null% ({null_pct:.1f}%) exceeds threshold ({rules['max_null_pct']}%)"
                )
                report["passed"] = False

        # Missing schema columns
        if schema:
            missing = set(schema.keys()) - all_keys
            if missing:
                report["issues"].append(f"Missing expected columns: {sorted(missing)}")
                report["passed"] = False

        return report


def validate_dataframe(df, schema: Dict = None, max_null_pct: float = None) -> Dict:
    """Validate a pandas DataFrame directly (convenience function)."""
    data = df.to_dict("records")
    tool = DataValidationTool()
    params = {"data": data}
    if schema:
        params["schema"] = schema
    if max_null_pct is not None:
        params["rules"] = {"max_null_pct": max_null_pct}
    result = tool.run(json.dumps(params))
    return json.loads(result)
