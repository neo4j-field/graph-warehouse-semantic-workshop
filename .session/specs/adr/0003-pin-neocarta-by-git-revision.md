---
tags: [neocarta, dependencies, reproducibility]
domain: "graph-warehouse-semantic-workshop"
scope: "how this repo depends on neocarta"
created: 2026-10-12
---
# ADR-0003: Pin neocarta to a git revision, not a sibling clone

Status: accepted
Deciders: Paul Drangeid, Claude

## Context

The labs were developed against a sibling clone of neocarta installed editable. A public repo cannot assume attendees have that layout, and neocarta releases on PyPI may lag the features the labs use (OSI ingest, Snowflake PAT and key-pair auth). The labs were validated on neocarta commit `ba6bf79` (`neocarta-v0.8.0`, 45 commits later). neocarta is not bundled or copied into this repo.

## Options Considered

1. Editable sibling clone — rejected because it adds setup steps for every attendee, and the clone drifts from what the labs were tested on.
2. PyPI release — rejected for now because a release containing every feature the labs use was not confirmed; revisit when one is.
3. Pinned git revision in `[tool.uv.sources]` — chosen, see Decision below.

## Decision

Declare neocarta in `pyproject.toml` with a `[tool.uv.sources]` git entry pinned to a full commit SHA, and commit `uv.lock`. Bump the pin only after re-running labs 00-03 against the new revision. Do not vendor neocarta source into this repo. Anyone who needs to change neocarta (for example a gateway header patch) works from a separate local clone, as described in `docs/customizing_for_your_environment.md`, and does not commit that change here.

## Consequences

- Attendees need no second clone; `uv sync` fetches neocarta from GitHub, which needs access to github.com.
- Links to neocarta source and examples in the docs should point at the pinned commit.
- Someone must bump and re-validate the pin periodically; the facilitator checklist covers this.
- Enforced by `uv.lock` and the CI install check; nothing prevents a pin bump without re-validation.

## Revisit Triggers

- A PyPI neocarta release includes every feature the labs use.
- A lab breaks against a newer neocarta and the pin must move.
