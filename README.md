# Graph Warehouse Semantic Workshop

A hands-on workshop showing how to **add a semantic layer in Neo4j to the data warehouse you already have**,
so AI agents understand what your data is, what it means and how it joins. It uses
[neocarta](https://github.com/neo4j-labs/neocarta) to load warehouse metadata (Snowflake in this edition)
into a Neo4j graph, layers business meaning on top, and lets an agent write correct SQL from it.

This is a proof-of-value / "art of the possible" workshop. It is also a **GitHub template**: clone it for a
new warehouse (BigQuery, Databricks, ...) or a new dataset. See
[docs/creating_a_new_workshop.md](docs/creating_a_new_workshop.md).

## Who it is for

| You are | Start here |
|---|---|
| An attendee working through the labs | [docs/attendee_guide.md](docs/attendee_guide.md) |
| A presenter running the session | [docs/facilitator_guide.md](docs/facilitator_guide.md) |
| Adapting the labs to your own environment (with or without a coding agent) | [docs/customizing_for_your_environment.md](docs/customizing_for_your_environment.md) and [AGENTS.md](AGENTS.md) |
| Building a new workshop from this template | [docs/creating_a_new_workshop.md](docs/creating_a_new_workshop.md) |

## Quick Start

You need: Git, [`uv`](https://docs.astral.sh/uv/), a Snowflake account (a free trial works), a Neo4j database
(free Aura works) and optionally an embeddings API key. The attendee guide covers each one.

```sh
# Preferred
git clone https://github.com/neo4j-field/graph-warehouse-semantic-workshop.git
cd graph-warehouse-semantic-workshop
uv sync --extra dev
cp .env.example .env                      # then fill in values; never commit .env
uv run jupyter lab 00_prerequisites_and_connectivity.ipynb   # verify connectivity
UV_ENV_FILE=.env uv run neocarta snowflake schema --dry-run

# Fallback (traditional venv activated)
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
jupyter lab 00_prerequisites_and_connectivity.ipynb
```

neocarta is installed automatically at a pinned version; you do not need to clone it.

## Contents

| Path | Purpose |
|---|---|
| `docs/attendee_guide.md` | Zero-to-pipeline guide: accounts, credentials, ingest, verify, MCP, agent, troubleshooting |
| `docs/facilitator_guide.md` | Running the session: pre-work, timing, demo fallback, cleanup |
| `docs/customizing_for_your_environment.md` | Adapting to other warehouses, gateways, models and local neocarta changes |
| `docs/creating_a_new_workshop.md` | Using this repo as a template |
| `00_prerequisites_and_connectivity.ipynb` | Lab 00: read-only checks (runtime, config, Neo4j, Snowflake, dataset access) |
| `01_load_metadata_into_graph.ipynb` | Lab 01: ingest Snowflake metadata (physical layer), verify, semantic search |
| `02_load_semantic_layer.ipynb` | Lab 02: ingest an OSI semantic model; join paths, synonyms, metrics |
| `03_build_graph_stub_and_schema.ipynb` | Lab 03: supply chain graph seeded from TPC-H keys, schema registry, bridge to tables and columns |
| `datasets/tpch_semantic_model.yaml` | Hand-authored OSI semantic model for `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1` |
| `workshop_agent/` | Snowflake Text2SQL agent (`workshop-agent` CLI) |
| `docker/` | Optional local LLM (Ollama) compose files |
| `.env.example` | Environment template (copy to `.env`) |
| `AGENTS.md` | Contract for coding agents working in this repo |
| `.session/` | Session handoffs and architecture decision records (ADRs) |

## Development

```sh
uv run pytest
uv run ruff check .
uv run black --check .
```

## License

[MIT](LICENSE). neocarta is a separate project under its own license (Apache-2.0).
