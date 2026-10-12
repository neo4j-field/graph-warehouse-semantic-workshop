# Creating a New Workshop From This Template

1. On GitHub choose **Use this template** (or clone and re-initialize git). Give the new repo its own name.
2. Rename the package in `pyproject.toml` and update `README.md`, `ARCHITECTURE.md` and `AGENTS.md`.
3. Decide what to keep. The generic scaffolding is `.session/`, `AGENTS.md`, `.github/`, `.env.example`, the docs
   structure and lab 00's pattern (read-only connectivity checks). The source-specific parts are the notebooks,
   `datasets/`, `workshop_agent/tools.py` and the Snowflake sections of the attendee guide.
4. Swap in your source and dataset (see [customizing_for_your_environment.md](customizing_for_your_environment.md#other-warehouses)).
5. Pin neocarta to a commit you have validated (ADR-0003) and run `uv lock`.
6. Run the clean-run test in [facilitator_guide.md](facilitator_guide.md) from a fresh clone.
7. Start a session file in `.session/` for the work, record decisions in the ledger, and promote durable ones to ADRs.
8. Remove anything that referred to the original workshop's accounts, data or hostnames before publishing.
