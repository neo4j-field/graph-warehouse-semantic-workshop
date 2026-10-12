"""Snowflake Text2SQL agent factory (workshop copy of neocarta's agent/agent.py)."""

from __future__ import annotations

from langchain.agents import create_agent
from langchain.tools import BaseTool
from langchain_litellm import ChatLiteLLM
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

from .config import Settings

SYSTEM_PROMPT = """You are a Text2SQL agent answering questions about data in Snowflake.

Use the metadata graph tools to find relevant tables, columns and relationships
before writing SQL, then run the query with execute_sql.

Workflow: (1) call get_full_metadata_schema or list_schemas / list_tables_by_schema
to see what exists, (2) write SQL using only tables and columns the graph returned,
(3) run it with execute_sql. Questions about what data exists can be answered from
the graph alone, without running SQL.

Rules:
* Always qualify tables as DATABASE.SCHEMA.TABLE (Snowflake names are upper case)
* Always get the schema from the metadata graph before writing a query
* Only read-only SQL is allowed; keep results small (aggregate or LIMIT)
* If a query errors, read the error, fix the SQL and retry
* Return results to the user in a readable format"""


def create_text2sql_agent(
    tools: list[BaseTool], settings: Settings
) -> CompiledStateGraph:
    """Create the LangGraph agent; custom gateway headers go via ``model_kwargs``."""
    model = ChatLiteLLM(
        model=settings.agent_model, model_kwargs=settings.litellm_kwargs
    )
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )
