---
schema_version: 1
id: 2026-10-12-public-repo-initial-import
title: Initial import of the workshop into this public template repo
status: active
status_reason: null
created: 2026-10-12
repos:
  - {name: graph-warehouse-semantic-workshop, role: primary}
branch: feature/initial-import
links:
  depends_on: []
  supersedes: []
  split_from: null
  references:
    - https://github.com/neo4j-labs/neocarta
---
# Initial import of the workshop

## Goal

Land the sanitized workshop assets (labs 00-03, OSI dataset, Snowflake agent, docs, ADRs, CI) on `main` through a
pull request, then validate the attendee guide with a clean-environment run. Judged by checks C1-C6.

## Context & Constraints

Assets were extracted from a private development workspace with fresh history (D1). neocarta is a pinned git
dependency, not vendored (D2). The repo is a template for future workshops (D3). The maintainer makes the repo
public and marks it as a template; agents never push to `main`.

## Instructions

1. Review and merge the `feature/initial-import` pull request.
2. Run the clean-environment test (fresh clone, new Snowflake trial, Aura Free, public LLM key) following only
   `docs/attendee_guide.md`; record each undocumented step as a finding and fix it.
3. When C1-C6 pass, close this session, tag `v0.1.0` and make the repo public.

## Ledger

```yaml session-ledger
runs:
  - date: 2026-10-12
    surface: claude-code-cli@unknown
    summary: Created the repo contents from the private workspace, replaced the sibling-clone dependency with a pinned git revision, rewrote AGENTS.md for public use, added guides, ADR-0003, CI and a notebook hygiene check.
    commits: []
outcome: null
decisions:
  - {id: D1, status: accepted, origin: user, text: "Fresh single history; do not carry over the private development session files."}
  - {id: D2, status: accepted, origin: user, adr: ADR-0003, text: "Depend on neocarta via a git revision pin (ba6bf79), not a sibling clone or vendored copy."}
  - {id: D3, status: accepted, origin: user, text: "Structure the repo as a GitHub template with attendee, facilitator, customization and new-workshop guides."}
  - {id: D4, status: accepted, origin: agent, text: "Keep notebooks at the repo root instead of a labs/ folder because they read .env and datasets/ relative to the working directory; revisit with a path helper."}
  - {id: D5, status: accepted, origin: agent, text: "Notebooks read only .env (the .env.workshop precedence was removed) and the single env template is .env.example."}
  - {id: D6, status: accepted, origin: agent, text: "Exclude notebooks from ruff and check them with scripts/check_notebooks.py (valid structure, no stored outputs)."}
questions:
  - {id: Q1, status: open, text: "Should the notebooks move to a labs/ folder with a helper that resolves the repo root?"}
  - {id: Q2, status: open, text: "Which license header or CODEOWNERS and branch protection should the neo4j-field repo use before it goes public?"}
findings: []
checks:
  - {id: C1, result: pass, text: "Fresh uv sync --extra dev from the lockfile succeeds with the pinned neocarta and no sibling clone; neocarta --help runs."}
  - {id: C2, result: pass, text: "ruff, black --check and pytest (13 tests) pass."}
  - {id: C3, result: pass, text: "Notebook hygiene check passes (valid, no outputs); path and secret grep is clean."}
  - {id: C4, result: pending, text: "Maintainer clean-environment run of labs 00-03 following only the attendee guide, with no undocumented steps."}
  - {id: C5, result: pending, text: "CI workflow passes on the pull request."}
  - {id: C6, result: pending, text: "Guide statements about live behaviour (Snowsight menus, PAT bypass wording) verified in the UI during the clean run."}
debt:
  - {id: T1, scope: this_repo, text: "Snowsight menu names and PAT bypass wording are not verified in the UI."}
  - {id: T2, scope: this_repo, text: "The no-embeddings path of lab 02's business-term search is untested."}
blockers: []
produced: []
```
