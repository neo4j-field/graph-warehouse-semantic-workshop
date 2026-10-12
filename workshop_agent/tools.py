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
from neo4j import GraphDatabase

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


_CYPHER_WRITE = re.compile(
    r"\b(create|merge|delete|detach|set|remove|drop|load\s+csv|foreach)\b"
    r"|\bcall\s+(apoc\.(create|merge|refactor|periodic|trigger)|dbms|db\.(create|drop))",
    re.I,
)


def check_read_only_cypher(cypher: str) -> str | None:
    """Return an error message if ``cypher`` looks like it writes to the graph."""
    stripped = re.sub(r"//[^\n]*|/\*.*?\*/", " ", cypher, flags=re.S)
    stripped = re.sub(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"", "''", stripped)
    if (m := _CYPHER_WRITE.search(stripped)) is not None:
        return f"Only read-only Cypher is allowed; found '{m.group(0)}'."
    return None


_UNBOUND_HINT = (
    "\nHint: name every relationship you reference, e.g. (a)-[r:TYPE]->(b), "
    "then use r.property. Call describe_graph_schema if unsure of the model."
)

_SCHEMA_QUERIES = (
    (
        "NODE",
        "MATCH (n) WITH labels(n)[0] AS item, keys(n) AS props "
        "RETURN item, collect(props) AS props ORDER BY item",
    ),
    (
        "REL",
        "MATCH (a)-[r]->(b) WITH labels(a)[0] + ' -[' + type(r) + ']-> ' + "
        "labels(b)[0] AS item, keys(r) AS props "
        "RETURN item, collect(props) AS props ORDER BY item",
    ),
)


def _read_cypher(
    state: dict[str, Any], neo4j_kwargs: dict[str, Any], query: str, row_limit: int
) -> tuple[list[str], list[list[Any]]]:
    """Run ``query`` in a server-enforced read transaction on a lazy driver."""
    if state["driver"] is None:
        state["driver"] = GraphDatabase.driver(
            neo4j_kwargs["uri"], auth=neo4j_kwargs["auth"]
        )

    def work(tx: Any) -> tuple[list[str], list[list[Any]]]:
        result = tx.run(query)
        keys = list(result.keys())
        return keys, [[r[k] for k in keys] for r in result.fetch(row_limit + 1)]

    with state["driver"].session(database=neo4j_kwargs["database"]) as session:
        return session.execute_read(work)


def make_graph_tools(neo4j_kwargs: dict[str, Any], row_limit: int) -> list[BaseTool]:
    """Build the read-only graph tools (``execute_cypher``, ``describe_graph_schema``).

    Safety is layered: a keyword screen, plus a server-enforced read transaction
    (``execute_read``), so a write that slips past the screen is still rejected.
    """
    state: dict[str, Any] = {"driver": None}

    @tool
    def describe_graph_schema() -> str:
        """List node labels, their properties and the relationship patterns.

        Call this first to learn the model (supply chain instances, GraphNodeSchema
        registry, ENRICHED_BY bridges) before writing Cypher.
        """
        lines: list[str] = []
        try:
            for kind, query in _SCHEMA_QUERIES:
                _, rows = _read_cypher(state, neo4j_kwargs, query, 1000)
                for item, prop_lists in rows:
                    props = sorted({p for plist in prop_lists for p in plist})
                    lines.append(
                        f"{kind} {item}" + (f" {{{', '.join(props)}}}" if props else "")
                    )
        except Exception as e:
            logger.error(f"Failed to describe graph schema: {e}")
            return f"Error: {e}"
        return "\n".join(lines)

    @tool
    def execute_cypher(query: str) -> str:
        """Run one read-only Cypher query on the Neo4j graph (supply chain, bridge).

        Use it to traverse instances (Supplier, Part, Assembly, FinishedGood) and the
        schema registry (GraphNodeSchema, ENRICHED_BY, CORRELATES_TO) to Table/Column.
        """
        if (err := check_read_only_cypher(query)) is not None:
            return f"Error: {err}"
        try:
            columns, rows = _read_cypher(state, neo4j_kwargs, query, row_limit)
        except Exception as e:  # surface to the model so it can correct its Cypher
            logger.error(f"Failed to execute Cypher {query!r}: {e}")
            hint = _UNBOUND_HINT if "not defined" in str(e) else ""
            return f"Error: {e}{hint}"
        return format_rows(
            columns, [tuple(r) for r in rows[:row_limit]], len(rows) > row_limit
        )

    return [execute_cypher, describe_graph_schema]
