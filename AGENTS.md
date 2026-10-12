# AGENTS.md: graph-warehouse-semantic-workshop

Contract for coding agents (Claude Code, Copilot CLI, Cursor, etc.) and humans working in this repo.
Read it at the start of every session. `CLAUDE.md` only imports this file.

## What this repo is

A hands-on workshop, and a GitHub template, for adding a Neo4j semantic layer to an existing data warehouse
with [neocarta](https://github.com/neo4j-labs/neocarta). Labs 00-03 are Jupyter notebooks at the repo root;
`workshop_agent/` is a Snowflake Text2SQL agent; `datasets/` holds the OSI semantic model. See
[ARCHITECTURE.md](ARCHITECTURE.md) for data flow and components.

neocarta is a dependency pinned by git revision (ADR-0003), not part of this repo. Do not copy its source here.

## Adapting this repo to a user's environment

A common task is "make the labs work with my warehouse, gateway or model." Start with
[docs/customizing_for_your_environment.md](docs/customizing_for_your_environment.md). Rules:

- Configuration lives in `.env` (gitignored). `.env.example` documents every key. Add new keys there.
- Never hardcode URIs, accounts, tokens, hostnames or personal paths in notebooks, code or docs.
- Never print, log or commit secret values. When showing config, mask secrets.
- Prefer changing configuration over changing code; prefer changing this repo over patching neocarta.
- If neocarta itself must change (for example custom HTTP headers for an LLM gateway), work in a separate
  local clone as described in the customization guide, and do not commit the patch to this repo.
- A notebook cell that writes to Neo4j must be idempotent (`MERGE`, never bare `CREATE` for entities that may exist).
- Keep notebooks free of stored outputs and execution counts before committing.
- After a change that alters setup steps, update `docs/attendee_guide.md` and, if needed, the facilitator guide.

## Conventions

### Python
- Python >= 3.11, `pyproject.toml` only. Formatter `black` (88), linter `ruff` (E, F, W, I, UP, B), tests `pytest`.
- `uv` first, always: `uv sync --extra dev`, `uv run pytest`. Document the plain `pip` fallback second.
- CLI via `typer`, console output via `rich`. No bare `print()` in package code (notebooks may print).
- Logging: `logging.getLogger(__name__)`; `--debug` sets DEBUG. Use `logger.warning` for skipped or non-fatal
  issues and `logger.error(f"Failed to process {item}: {e}")` with context for failures.
- One bad record must not crash a run: catch, log, continue, and surface skipped items at the end.
- Configuration is read once, in `workshop_agent/config.py` (the only module that reads `.env`), and passed down.
- Inline docstrings on public functions.

### Cypher and Neo4j
- Idempotent writes: `MERGE` on a reduced, stable key set; set nullable or optional fields with `SET` afterwards.
- Separate immutable and updatable fields with `ON CREATE SET` / `ON MATCH SET`.
- Parameterize values (`$param`); never f-string user data into Cypher.
- Create a constraint or index only with `IF NOT EXISTS`.
- Use `IS NULL` / `IS NOT NULL`, not `exists(n.prop)`.
- Carry variables through every `WITH`; use `WITH` between `MERGE` and `MATCH`.
- Do not store maps as node properties; encode as JSON strings.
- Ad-hoc exploration is read-only. Graph writes come from the labs and neocarta CLI, not hand-run Cypher.
- Do not invent labels or relationship types ad hoc: add them to the registry below first.

### Documentation
- `README.md` and `ARCHITECTURE.md` are live artifacts; keep them matching the code. Update `docs/` when
  flags, config keys, lab steps or outputs change.

## Graph model registry

Node labels and relationship types written by this repo (neocarta's own are documented in its README).

Added by lab 03: instance labels `FinishedGood`, `Assembly`, `Part`, `Supplier` (keys `sku` / `partKey` /
`supplierKey`, Snowflake TPC-H keys as strings); schema registry labels `GraphDatabase`, `GraphNodeSchema`,
`GraphRelSchema` (`id` = `<graph>.<label|type>`).

| Relationship | Meaning |
|---|---|
| `REQUIRES` | finished good or assembly requires a part or assembly (`quantity`) |
| `SOURCED_FROM` | part sourced from a supplier (`isPrimary`, `unitCost`) |
| `CONTAINS_NODE_SCHEMA`, `CONTAINS_REL_SCHEMA` | graph registry contains a node or relationship schema |
| `CORRELATES_TO`, `ENRICHED_BY` | schema node to `Table` / `Column` (a `target` property says which; `graphKey`, `relationalKey`, `joinType` / `metric`, `lookupTable`, `valueColumn`) |
| `STANDARDIZES` | `BusinessTerm` to `GraphNodeSchema` |

Instances are never linked to `Table` / `Column` nodes (the bridge is class-level only).

## Decisions and sessions

- Durable decisions are ADRs in `.session/specs/adr/` (one per file, numbered, never renumbered; supersede by
  changing Status). Check `index.md` before deciding something that may already be decided.
- Work in a session file `.session/YYYY-MM-DD-topic.md` copied from `.session/_template.md`
  (YAML frontmatter plus one `## Ledger` block with runs, decisions, questions, findings, checks, debt, blockers,
  produced). Record decisions in the ledger as they are made; close it with an outcome.
- Commit on a feature branch; include a `Session: <session-file-stem>` trailer when a session file exists.
  Merging to `main` is a human action.

### Starting a session
1. Read this file. 2. Check `.session/` for a `draft` or `active` session file and read it.
3. Skim `.session/specs/adr/index.md`; open only relevant ADRs. 4. Confirm the goal and constraints.

### Closing a session
Close the ledger (`summary`, `commits`, check results, `outcome`), promote durable decisions to ADRs,
add a Review Log entry and refresh Next Steps and Technical Debt below, and commit.

## Notes

### Next Steps
- Run the full clean-environment test of labs 00-03 and fix any drift (see `docs/facilitator_guide.md`).
- Point `workshop-agent` at the semantic layer: ask for "net revenue by region" and confirm it uses the
  `net_revenue` metric and the `REFERENCES` join path.
- Consider a larger or hosted default model; a 7B local model skips graph tools and can hallucinate results.
- Possible future modules for other warehouses (BigQuery, Databricks).

### Technical Debt
- Notebook and guide commands are only partly validated live; Snowsight menu names and PAT bypass wording are
  from knowledge, not verified in the UI.
- neocarta's `examples/snowflake_schema.py` supports password auth only; the CLI supports PAT and key-pair.
- neocarta's OSI ingest never overwrites existing Table/Column properties and has no CLI flag for it, so YAML
  descriptions only land on a graph with no physical nodes yet (ADR-0002).
- Lab 02's business-term search demo needs the table vector index (embeddings); the no-embeddings path is untested.
- neocarta CLI and MCP expose no `api_base` setting; they depend on LiteLLM env vars (`OPENAI_BASE_URL`, `OLLAMA_API_BASE`).
- Notebooks live at the repo root because they read `.env` and `datasets/` relative to the working directory.

### Review Log
**2026-10-12 — Initial public import**
Extracted from the private development workspace: labs 00-03, the OSI TPC-H semantic model, the Snowflake
Text2SQL agent, Ollama compose files, attendee guide, ADR-0001/0002 and a pinned neocarta dependency (ADR-0003).
Rewrote AGENTS.md for public use and added facilitator, customization and new-workshop guides. Notebook
installation no longer needs a sibling neocarta clone. Session: 2026-10-12-public-repo-initial-import.
