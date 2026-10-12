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

The graph also holds a supply chain and a schema registry bridged to the warehouse:
* Instances: (:Supplier {supplierKey, name})<-[:SOURCED_FROM]-(:Part {partKey, name})
  <-[:REQUIRES*1..2]-(:FinishedGood {sku, name}); keys are TPC-H keys as strings
* Registry: (:GraphNodeSchema {label})-[:ENRICHED_BY {metric, target, graphKey,
  relationalKey}]->(:Table|:Column). target='table' points at the Table, target='column'
  at the value Column. Table and Column nodes carry id and name.
For supply chain questions call describe_graph_schema once to learn the model, then
use execute_cypher. To find where a fact (e.g. a metric such
as 'On-Hand Inventory') lives, you MUST query the ENRICHED_BY edges of the matching
GraphNodeSchema and use the table, key column and value column it returns; never guess
table or column names that the bridge can tell you. Say plainly which results came
from the bridge, and only claim a bridge result when the query succeeded. Bridge query
shape (name the relationship variable):
  MATCH (:GraphNodeSchema {label: 'Part'})-[e:ENRICHED_BY {metric: '<metric>'}]->(x)
  RETURN e.target, e.graphKey, e.relationalKey, x.id, x.name

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
