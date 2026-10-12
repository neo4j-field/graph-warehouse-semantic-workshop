# Architecture

## Philosophy

This repo holds teaching assets only. All ingestion logic lives in the
[neocarta](https://github.com/neo4j-labs/neocarta) library, installed as a dependency pinned to a git
revision (ADR-0003). Everything here must be reproducible by an attendee from scratch, so every step is
documented in `docs/attendee_guide.md` and every credential comes from `.env`. The repo is also a GitHub
template: the warehouse-specific parts are kept separate from the generic scaffolding so a new workshop can
swap them (see `docs/creating_a_new_workshop.md`).

## Data Flow

```
Snowflake INFORMATION_SCHEMA --(neocarta snowflake schema)--> Neo4j semantic graph
        optional: LiteLLM embeddings --> vector indexes
datasets/tpch_semantic_model.yaml (OSI) --(neocarta osi ingest)--> same Neo4j graph
        (merges onto the existing Table/Column nodes, adds Metric/Join/BusinessTerm nodes)
lab 03 seeds a supply chain graph from Snowflake keys and bridges its schema to Table/Column/BusinessTerm
Neo4j graph --(neocarta-mcp)--> agent (workshop-agent) --(execute_sql)--> Snowflake
```

Only metadata crosses into Neo4j; the semantic layer comes from a local YAML file, not Snowflake. Lab 00
performs read-only checks along this path and never ingests.

## Components

| Component | Responsibility | Key Logic |
|---|---|---|
| `docs/attendee_guide.md` | End-to-end attendee guide | Where to find each Snowflake/Neo4j value; PAT creation with temporary network-policy bypass; LLM options |
| `docs/facilitator_guide.md` | Presenter runbook | Pre-work, timing, demo fallback, cleanup, pin bump |
| `docs/customizing_for_your_environment.md` | Adaptation guide | Config-first changes, local neocarta checkout, other warehouses |
| `00_prerequisites_and_connectivity.ipynb` | Pre-workshop verification | Mirrors neocarta auth precedence (key-pair > authenticator > password); URI scheme sanity; checks metadata vs SELECT access; constructs `SnowflakeSchemaConnector` only |
| `01_load_metadata_into_graph.ipynb` | Guided ingest | Checks the embedding model, dry run, runs the `neocarta snowflake schema` CLI with the loaded `.env` values, verifies nodes/indexes in Neo4j, demos vector search; writes to Neo4j, idempotent |
| `02_load_semantic_layer.ipynb` | Guided semantic-layer ingest | Requires lab 01's nodes (stops otherwise); dry run, `neocarta osi ingest` CLI; verifies no duplicate Table/Column nodes, `OsiTable`/`OsiColumn` labels, physical names unchanged; shows join paths, synonyms, metrics; idempotent re-run |
| `03_build_graph_stub_and_schema.ipynb` | Domain graph plus schema bridge | Seeds parts/suppliers from Snowflake `PART`/`PARTSUPP`/`SUPPLIER`; MERGE-only writes; `GraphDatabase`/`GraphNodeSchema`/`GraphRelSchema` registry; `CORRELATES_TO`/`ENRICHED_BY` link schema nodes (never instances) to `Table`/`Column`, `STANDARDIZES` to `BusinessTerm`; ends with a traversal that builds Snowflake SQL from the bridge |
| `04_agentic_workflow.ipynb` | Autonomous golden thread | Builds the agent toolbox (Neocarta MCP catalog, `describe_graph_schema` / `execute_cypher`, `execute_sql`); computes the expected answer with plain Cypher/SQL as a control; runs the agent via LiteLLM; checks the transcript (C1 affected goods from a graph result, C2 a successful `ENRICHED_BY` query before any SQL, C3 valid SQL and expected total). Read-only |
| `datasets/tpch_semantic_model.yaml` | Business semantic layer for TPCH_SF1 | OSI 0.1.1; 3-part `source` makes each dataset MERGE onto the physical `Table` node; UPPER-CASE names match Snowflake; relationships supply the FK/`REFERENCES` edges TPCH lacks; one SQL formula per metric |
| `.env.example` | Config template | Neo4j, Snowflake, LLM provider options, optional MCP vars |
| `workshop_agent/` | Snowflake Text2SQL agent (typer CLI `workshop-agent`) | Adapted from neocarta's BigQuery agent; `config.py` is the only `.env` reader; read-only `execute_sql` tool and read-only graph tools (`execute_cypher`, `describe_graph_schema`: keyword screen plus a server-enforced read transaction; the Neocarta MCP server is catalog-only); `CORPORATE_GATEWAY_HEADERS` to LiteLLM `extra_headers`; spawns `neocarta-mcp` over stdio |
| `docker/docker-compose.ollama*.yml` | Local LLM for offline or blocked-network setups | Ollama plus one-shot model pull (qwen2.5:7b, nomic-embed-text); GPU overlay |
| `pyproject.toml`, `uv.lock` | Dependencies | neocarta pinned to a git revision; agent, notebook and dev extras |
| `.mcp.json`, `.claude/settings.json` | Optional coding-agent access to the graph | Official `neo4j-mcp-server`, write tool denied |
| `.github/workflows/ci.yml` | Quality gate | Install from lockfile, ruff, black, pytest, notebook hygiene check |
| `.session/` | Decisions and session handoffs | ADRs 0001-0003; session template |
| `neocarta` (external, pinned) | Connectors, CLI, MCP server | Embeddings via LiteLLM; endpoint selected by env vars |
