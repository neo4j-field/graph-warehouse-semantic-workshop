---
tags: [neocarta, osi, semantic-layer, snowflake]
domain: "graph-warehouse-semantic-workshop"
scope: "workshop module 02 and any later semantic-layer ingest"
created: 2026-10-06
---
# ADR-0001: Use the OSI connector as the semantic-layer ingest path

Status: accepted
Deciders: Paul Drangeid, Claude

## Context

Workshop module 02 must ingest a business-facing semantic layer for the Snowflake sample data (`SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`) and map it onto the physical `Table`/`Column` nodes module 01 loads. Reading the neocarta clone showed it has no Snowflake semantic-view or Horizon catalog connector: `neocarta snowflake` offers only `schema` and `logs`. The only semantic-model ingest path is the OSI (Open Semantic Interchange) connector, `neocarta osi ingest --spec-source <yaml>`. Attendees use Snowflake trial accounts, where creating a semantic view cannot be assumed.

## Options Considered

1. Snowflake semantic view (Cortex Analyst) read back as YAML and converted to OSI — rejected because it depends on privileges and features that trial accounts may lack, and needs a converter we would own and keep in sync with a vendor format. Prefer a source that works without account-specific features.
2. Snowflake Horizon catalog content (object comments, tags) — rejected because neocarta has no connector for it; building one means editing the neocarta clone.
3. Hand-authored OSI YAML loaded with `neocarta osi ingest` — chosen, see Decision below.

## Decision

Source the workshop semantic layer from a hand-authored OSI 0.1.1 YAML under `datasets/` (`tpch_semantic_model.yaml`) and load it only with the `neocarta osi ingest` CLI. Every dataset `source` must be a 3-part `DATABASE.SCHEMA.TABLE` name using the real upper-case Snowflake identifiers, because neocarta derives node ids from it and that is what makes the semantic layer MERGE onto the existing physical nodes. Do not write a Snowflake semantic-view converter or a second ingest mechanism in this repo.

## Consequences

- Work this creates: the YAML must be maintained by hand if the sample data changes; owner unassigned.
- Attendees do not see a real Snowflake semantic view; the notebook presents the YAML as the semantic layer.
- OSI creates no Metric-to-Column edges, so metrics are explored through their `Expression` nodes.
- Enforced by the notebook's mapping checks in `02_load_semantic_layer.ipynb` (no duplicate Table/Column nodes, `OsiTable`/`OsiColumn` labels on the originals). Nothing enforces the 3-part, upper-case naming outside that notebook run.

## Revisit Triggers

- neocarta ships a Snowflake semantic-view or Horizon catalog connector.
- Workshop attendees' trial accounts reliably allow creating and exporting semantic views.
- The OSI spec version supported by neocarta moves past 0.1.1.
