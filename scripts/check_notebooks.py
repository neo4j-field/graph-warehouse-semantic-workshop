"""Fail if any notebook has stored outputs, execution counts or invalid structure."""

from __future__ import annotations

import sys
from pathlib import Path

import nbformat


def main() -> int:
    """Validate every notebook at the repo root; return a process exit code."""
    problems: list[str] = []
    for path in sorted(Path(".").glob("[0-9][0-9]_*.ipynb")):
        nb = nbformat.read(path, as_version=4)
        try:
            nbformat.validate(nb)
        except nbformat.ValidationError as e:
            problems.append(f"{path}: invalid notebook: {e}")
        for i, cell in enumerate(nb.cells):
            if cell.cell_type != "code":
                continue
            if cell.get("outputs"):
                problems.append(f"{path}: cell {i} has stored outputs")
            if cell.get("execution_count") is not None:
                problems.append(f"{path}: cell {i} has an execution count")
    for line in problems:
        sys.stderr.write(line + "\n")
    sys.stdout.write(f"notebooks checked, problems={len(problems)}\n")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
