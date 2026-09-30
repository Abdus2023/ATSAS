#!/usr/bin/env python3
"""
validate_test_matrix.py — Validate that one or more Arena Assurance Test Matrix
Markdown files contain all 11 canonical columns, AAI-001..AAI-034 (RED-01..RED-34),
and P-001..P-008.
"""

from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_COLUMNS = (
    "TEST_ID",
    "TRIGGER",
    "PRECONDITION",
    "AUTHORIZED_SCOPE",
    "AGENT_ACTION",
    "EXPECTED_OBSERVATION",
    "EXPECTED_CLASSIFICATION",
    "REQUIRED_EVIDENCE",
    "FORBIDDEN_INFERENCE",
    "FAILURE_STATE",
    "TARGET_SKILL",
)


def main() -> int:
    targets = sys.argv[1:] or [
        ".claude/assurance/test-matrix.md",
        "ARENA_ASSURANCE_TEST_MATRIX.md",
    ]
    errors: list[str] = []

    for path_str in targets:
        p = Path(path_str).resolve()
        if not p.is_file():
            errors.append(f"Matrix file not found: {path_str}")
            continue
        text = p.read_text(encoding="utf-8")
        for col in REQUIRED_COLUMNS:
            if f"`{col}`" not in text:
                errors.append(f"{path_str}: missing column `{col}`")
        for i in range(1, 35):
            aai_id = f"AAI-{i:03d}"
            red_id = f"RED-{i:02d}"
            if f"| `{aai_id}` |" not in text:
                errors.append(f"{path_str}: missing behavioral test row `{aai_id}`")
            if red_id not in text:
                errors.append(f"{path_str}: missing `{red_id}` cross-reference")
        for i in range(1, 9):
            p_id = f"P-{i:03d}"
            if f"| `{p_id}` |" not in text:
                errors.append(f"{path_str}: missing pressure test row `{p_id}`")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(
        f"OK: Verified {len(targets)} matrix artifact(s) across 11 columns, 34 AAI/RED cases, and 8 P cases."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
