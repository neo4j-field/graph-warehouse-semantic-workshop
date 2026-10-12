# Customizing for Your Environment

The labs target a Snowflake trial, Neo4j Aura and a public LLM API. Most real environments differ. This
guide lists the common adaptations, in order of preference: **change configuration, then this repo, then (rarely) a
local copy of neocarta.** You can do these yourself or hand them to a coding agent; `AGENTS.md` tells the agent the rules.

## Using a coding agent

Start your agent (Claude Code, Copilot CLI, Cursor, ...) in the repo root and describe the environment, for example:

```text
Read AGENTS.md and docs/customizing_for_your_environment.md. My warehouse is <X>, my Neo4j is <Y>,
and my LLM is reached through <gateway>. Adapt the labs and .env.example for this and tell me what you changed.
Do not print or commit any secrets.
```

Review what it changes. Keep secrets only in `.env`.

## Common adaptations

| Situation | Change |
|---|---|
| Different Snowflake database or schema | Set `SNOWFLAKE_DATABASE` / `SNOWFLAKE_SCHEMA` in `.env`. Lab 02 and lab 03 are TPC-H specific; copy the YAML and notebook cells for your tables (see below) |
| Key-pair or SSO authentication | Set the Snowflake auth variables in `.env.example`'s options; lab 00 reports which method it will use |
| Local Neo4j instead of Aura | Use `neo4j://localhost:7687` or `bolt://...` in `NEO4J_URI` |
| TLS-inspecting corporate proxy | Use the `neo4j+ssc://` URI scheme |
| Blocked or no public LLM | Use the Ollama option (`docker/`) or an OpenAI-compatible gateway; see the LLM section of the attendee guide |
| Gateway needs custom HTTP headers | Needs a local neocarta change for embeddings; see below |
| Your own semantic layer | Copy `datasets/tpch_semantic_model.yaml`, describe your tables in OSI format, load with `neocarta osi ingest` |
| BigQuery, Databricks or another source | See "Other warehouses" below and `docs/creating_a_new_workshop.md` |

## Working from a local neocarta clone

By default neocarta is installed from a pinned git revision. If you need to change it (for example to add gateway
headers), use a separate clone and install it editable over the pinned copy:

```sh
git clone https://github.com/neo4j-labs/neocarta.git ../neocarta
git -C ../neocarta checkout ba6bf7945bf9c60640c664a03ccc26d0013996bf    # the pinned revision
uv sync --extra dev
uv pip install -e "../neocarta[cli,snowflake,mcp]"
export UV_NO_SYNC=1      # PowerShell: $env:UV_NO_SYNC=1; stops `uv run` from reinstalling the pinned copy
```

Re-run `uv sync` (without `UV_NO_SYNC`) to return to the pinned version. Do not commit your neocarta patch to this repo.

Where gateway headers would be applied in neocarta: `neocarta/_mcp/embeddings.py`, `neocarta/_cli/commands/_common.py`
and, for chat in neocarta's own agent, `agent/agent.py`. The workshop agent in this repo already reads
`CORPORATE_GATEWAY_HEADERS` and needs no patch.

## Other warehouses

neocarta has connectors for other sources (BigQuery, Databricks, JDBC, CSV). To adapt a lab:

1. Replace the connectivity checks in lab 00 with the source's client and credentials, and add its keys to `.env.example`.
2. In lab 01, swap the `neocarta snowflake schema` command for the connector's command.
3. Rewrite the `source` names in the OSI YAML to the new identifier format. Node ids derive from them, which is
   what lets the semantic layer merge onto the physical nodes (ADR-0001).
4. Replace the Snowflake `execute_sql` tool in `workshop_agent/tools.py` with one for your engine, keeping it read-only.
5. Update `docs/attendee_guide.md` for account setup, and run the clean-run test in the facilitator guide.
