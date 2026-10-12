# Facilitator Guide

For the person running the session. Attendees use [attendee_guide.md](attendee_guide.md).

## Before the session

Send attendees this pre-work at least a week ahead. Account setup is where most of the time goes.

1. Install Git and `uv`; clone this repo; run `uv sync --extra dev` (attendee guide sections 1.1-1.3).
2. Create a Snowflake trial and a free Neo4j Aura instance (sections 3 and 4). Save the Aura password: it is shown once.
3. Create `.env` and run lab 00. Every check should show ✅. Ask attendees to send you a screenshot or the failing
   check text if not (never the `.env` contents).
4. Optional: an embeddings key (section 5), or the Ollama path for blocked networks.

Your own checklist:

- [ ] Run labs 00-04 yourself on the day before, on a fresh Aura instance, with the same dependency pin.
- [ ] Confirm `SNOWFLAKE_SAMPLE_DATA` exists in the trial accounts you recommend.
- [ ] Prepare a **pre-run Neo4j database** with labs 01-03 loaded (lab 04 runs live against it) (see "No source database available" below).
- [ ] Decide how attendees get an LLM key (their own, a shared workshop key, or Ollama) and who revokes shared keys.

## Suggested agenda (adjust after your own test run)

| Block | Content | Notes |
|---|---|---|
| Intro | Why a semantic layer for agents; the physical vs semantic layer | Slides are not included in this repo |
| Lab 00 | Prerequisites and connectivity | Mostly done as pre-work; use the time to unblock stragglers |
| Lab 01 | Load warehouse metadata into Neo4j | Show the graph in Neo4j Browser; optional embeddings |
| Lab 02 | Semantic layer (OSI): joins, synonyms, metrics | Key insight: TPC-H has no FKs, the YAML supplies join paths |
| Lab 03 | Supply chain graph and schema bridge | Graph plus warehouse: traverse the graph, then run SQL built from the bridge |
| Lab 04 | An agent walks the golden thread | Show the 🌿 tool calls: it reads the `ENRICHED_BY` bridge before writing SQL; the notebook's C1-C3 checks prove it. Needs a capable tool-calling model; small local models may fail C2 |
| Agent demo | `workshop-agent` answering a business question | Smaller local models are unreliable; use a hosted tool-calling model for demos |
| Wrap-up | Adapting to your own warehouse | Point at the customization guide |

## No source database available

Not everyone has Snowflake access. Present from a pre-run Neo4j database instead: load labs 01-03 into a
dedicated instance, open Neo4j Browser, and walk through the schema and the queries in the lab markdown cells.
Attendees watch rather than run. Keep this instance read-only for the audience (share a read-only user, or screen-share).

## Troubleshooting

See attendee guide section 9. Frequent causes: Aura URI scheme, Snowflake PAT without a network policy,
wrong account identifier format, `UV_ENV_FILE` not set for the `neocarta` CLI.

## Cleanup

- Attendees: remove the Snowflake token and wipe a throwaway Neo4j database (attendee guide section 10).
- You: revoke shared API keys, delete workshop Aura instances, and delete any pre-run database you no longer need.

## Maintaining this repo

- **neocarta pin:** `pyproject.toml` pins neocarta to a commit (ADR-0003). To bump it, change the `rev`,
  run `uv lock`, rerun labs 00-04 on a clean database, then update the links in `docs/` that mention the
  old commit and add a `CHANGELOG.md` entry.
- **Clean-run test:** use a fresh clone, a new venv, and a fresh Snowflake trial and Aura Free instance, following
  only the attendee guide. Log every undocumented step as an issue and fix the guide.
