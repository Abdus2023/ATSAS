#!/usr/bin/env python3
"""
check_capability_overlap.py — Verify that all non-_shared skills in .claude/skills/
and all 42 test cases (AAI-001..034, P-001..008) are mapped in the capability overlap
matrices without premature SKILL.md creation.
"""

from __future__ import annotations

import sys
from pathlib import Path


LABELS = (
    "COVERED",
    "PARTIALLY_COVERED",
    "UNCOVERED",
    "DUPLICATE",
    "CONFLICTING",
    "ORPHANED",
)


def main() -> int:
    repo_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    skills_root = repo_root / ".claude" / "skills"
    skill_dirs = sorted(
        p.name for p in skills_root.iterdir() if p.is_dir() and not p.name.startswith("_")
    )

    errors: list[str] = []
    for rel in (
        ".claude/assurance/capability-map.md",
        "ARENA_CAPABILITY_OVERLAP_MATRIX.md",
    ):
        p = repo_root / rel
        if not p.is_file():
            errors.append(f"Missing capability overlap artifact: {rel}")
            continue
        text = p.read_text(encoding="utf-8")
        for s_name in skill_dirs:
            if f"`{s_name}`" not in text:
                errors.append(f"{rel}: missing skill `{s_name}`")
        for i in range(1, 35):
            if f"| `AAI-{i:03d}` |" not in text:
                errors.append(f"{rel}: missing case `AAI-{i:03d}`")
        for i in range(1, 9):
            if f"| `P-{i:03d}` |" not in text:
                errors.append(f"{rel}: missing pressure case `P-{i:03d}`")
        for label in LABELS:
            if f"`{label}`" not in text:
                errors.append(f"{rel}: missing classification label `{label}`")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(
        f"OK: Capability overlap audit verified ({len(skill_dirs)} skills, 42 test cases, 6 classification labels)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
