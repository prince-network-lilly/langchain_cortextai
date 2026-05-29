"""SQL database query tool with safe read-only mode."""
import json
from typing import Optional
from cortexchain.tools.base import BaseTool


class SQLDatabaseTool(BaseTool):
    """Executes SQL queries against a database. Input: SQL query string or JSON with 'query' key."""

    name = "sql_database"
    description = (
        "Executes SQL queries against a database and returns results. "
        "Input: a SQL query string. Use SELECT for read operations."
    )

    def __init__(
        self,
        connection_string: str = None,
        connection=None,
        read_only: bool = True,
        max_rows: int = 50,
    ):
        self.connection_string = connection_string
        self._connection = connection
        self.read_only = read_only
        self.max_rows = max_rows

    def _get_connection(self):
        if self._connection:
            return self._connection
        if not self.connection_string:
            raise ValueError("No connection_string or connection provided.")

        import sqlite3
        self._connection = sqlite3.connect(self.connection_string)
        return self._connection

    def run(self, tool_input: str) -> str:
        try:
            params = json.loads(tool_input)
            query = params.get("query", tool_input)
        except (json.JSONDecodeError, AttributeError):
            query = tool_input.strip()

        if self.read_only:
            normalized = query.strip().upper()
            if not normalized.startswith("SELECT") and not normalized.startswith("PRAGMA"):
                return "Error: Read-only mode. Only SELECT and PRAGMA queries are allowed."

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query)

            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchmany(self.max_rows)
                result_lines = [" | ".join(columns)]
                result_lines.append("-" * len(result_lines[0]))
                for row in rows:
                    result_lines.append(" | ".join(str(v) for v in row))
                total = cursor.rowcount if cursor.rowcount >= 0 else len(rows)
                result_lines.append(f"\n({total} rows)")
                return "\n".join(result_lines)
            else:
                conn.commit()
                return f"Query executed. Rows affected: {cursor.rowcount}"
        except Exception as e:
            return f"SQL Error: {e}"
