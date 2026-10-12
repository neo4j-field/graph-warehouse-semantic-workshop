---
tags: [neocarta, osi, semantic-layer, enrichment]
domain: "graph-warehouse-semantic-workshop"
scope: "how semantic metadata relates to physical metadata in the graph"
created: 2026-10-06
---
# ADR-0002: Accept the OSI loader's no-overwrite behaviour; enrich with new nodes, not property overwrites

Status: accepted
Deciders: Paul Drangeid, Claude

## Context

The plan assumed the OSI ingest would overwrite physical `Table`/`Column` descriptions with business definitions, and that this would serve as a visible "enrichment" step (D5). A real ingest against the live graph disproved it (finding F3): the 8 `Table` and 61 `Column` nodes kept their names and descriptions. In neocarta, `neocarta/ingest/utils.py` builds `ON CREATE SET` for properties and `ON MATCH SET` for labels only unless `overwrite_existing=True`, and `OsiConnector.ingest` never passes that flag; the CLI exposes no option for it. Overwriting would need either a library call with `overwrite_existing=True` or a local neocarta patch.

## Options Considered

1. Call neocarta's OSI extractor, transformer and loader from the notebook with `overwrite_existing=True` — rejected because it bypasses the documented CLI that attendees would use in practice and makes the workshop show behaviour the CLI does not have.
2. Patch the neocarta clone to add an `--overwrite` flag — rejected because the labs run unmodified neocarta so attendees can reproduce them from the pinned release (ADR-0003) and a patch would drift from upstream on `git pull`.
3. Use the plain `neocarta osi ingest` CLI and present enrichment as new linked nodes — chosen, see Decision below.

## Decision

Run `neocarta osi ingest` unchanged and let it preserve existing physical `name` and `description`. Show the semantic layer as new nodes attached to the preserved physical nodes (`OsiSemanticModel`, `Metric`, `Expression`, `Join`, `BusinessTerm`, `REFERENCES` edges, and the `OsiTable`/`OsiColumn` labels). Do not call the loader with `overwrite_existing=True` and do not add an overwrite patch to the neocarta clone to make the workshop narrative work. Workshop text must not say the YAML descriptions replace the physical ones.

## Consequences

- YAML table and column descriptions only reach the graph on a database with no existing physical nodes; on the normal 00 → 01 → 02 path they are not visible on `Table`/`Column`. Descriptions in the YAML remain useful as documentation and for the `Metric` nodes, which are new.
- Notebook 02 asserts the preservation (checks that names and descriptions are unchanged), so a future neocarta that starts overwriting will fail the notebook's "preserved" checks.
- Recorded as Technical Debt in `AGENTS.md`.
- Not enforced beyond that notebook run.

## Revisit Triggers

- neocarta exposes an overwrite option on `neocarta osi ingest` (or changes the default).
- The notebook's "Table names and descriptions preserved" check starts failing after a neocarta update.
- Attendee feedback shows the missing description enrichment makes the module unconvincing.
