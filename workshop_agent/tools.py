"""Snowflake execution tool for the workshop agent.

A workshop convenience: a small read-only ``execute_sql`` tool. In production,
prefer a Snowflake-managed MCP server for robust Snowflake support.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import snowflake.connector
from langchain.tools import BaseTool, tool

logger = logging.getLogger(__name__)

_ALLOWED_STATEMENTS = {"select", "with", "show", "describe", "desc", "explain"}


def check_read_only(sql: str) -> str | None:
    """Return an error message if ``sql`` is not a single read-only statement."""
    stripped = re.sub(r"--[^\n]*|/\*.*?\*/", " ", sql, flags=re.S).strip().rstrip(";")
    if not stripped:
        return "Empty SQL statement."
    if ";" in re.sub(r"'(?:[^']|'')*'", "''", stripped):
        return "Only a single statement is allowed."
    first = stripped.split(None, 1)[0].lower()
    if first not in _ALLOWED_STATEMENTS:
        allowed = ", ".join(sorted(_ALLOWED_STATEMENTS))
        return f"Only read-only statements are allowed ({allowed}); got '{first}'."
    return None


def format_rows(
    columns: list[str], rows: list[tuple[Any, ...]], truncated: bool
) -> str:
    """Render a result set as a markdown table."""
    if not rows:
        return "Query returned no rows."
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in rows]
    if truncated:
        lines.append(f"\n(Results truncated to {len(rows)} rows.)")
    return "\n".join(lines)


def make_execute_sql_tool(connect_kwargs: dict[str, Any], row_limit: int) -> BaseTool:
    """Build the ``execute_sql`` tool bound to one lazily created connection."""
    state: dict[str, Any] = {"conn": None}

    @tool
    def execute_sql(query: str) -> str:
        """Run one read-only SQL query (SELECT/WITH/SHOW/DESCRIBE) on Snowflake.

        Always use fully qualified names: DATABASE.SCHEMA.TABLE.
        """
        if (err := check_read_only(query)) is not None:
            return f"Error: {err}"
        try:
            if state["conn"] is None:
                state["conn"] = snowflake.connector.connect(**connect_kwargs)
            cur = state["conn"].cursor()
            try:
                cur.execute(query)
                columns = [d[0] for d in cur.description or []]
                rows = cur.fetchmany(row_limit + 1)
            finally:
                cur.close()
        except Exception as e:  # surface to the model so it can correct its SQL
            logger.error(f"Failed to execute SQL {query!r}: {e}")
            return f"Error: {e}"
        return format_rows(columns, rows[:row_limit], len(rows) > row_limit)

    return execute_sql
