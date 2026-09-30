#!/usr/bin/env python3
"""
verify_semantic_kernel.py — Verify that _shared/aif/ protocol directories contain
all required markdown specs and 13 modular JSON Schemas, and execute the Phase 0/1
28-case RED invariant test suite.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REQUIRED_DOCS = (
    "VERSION",
    "README.md",
    "invariants.md",
    "states.md",
    "snapshots.md",
    "evidence.md",
    "evidence-rules.md",
    "compatibility.md",
)

REQUIRED_SCHEMAS = (
    "request.schema.json",
    "authority-event.schema.json",
    "admission.schema.json",
    "admission-record.schema.json",
    "snapshot.schema.json",
    "snapshot-ref.schema.json",
    "execution-record.schema.json",
    "change-record.schema.json",
    "claim.schema.json",
    "evidence-ref.schema.json",
    "evidence-coverage.schema.json",
    "verification-record.schema.json",
    "finding.schema.json",
    "acceptance-expression.schema.json",
    "completion-result.schema.json",
    "evidence-receipt.schema.json",
)


def main() -> int:
    repo_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []

    for shared_rel in (
        ".claude/skills/_shared/aif",
        ".agent/skills/_shared/aif",
    ):
        base = repo_root / shared_rel
        if not base.is_dir():
            errors.append(f"Missing shared AIF kernel directory: {shared_rel}")
            continue
        for doc in REQUIRED_DOCS:
            if not (base / doc).is_file():
                errors.append(f"Missing {shared_rel}/{doc}")
        for sch in REQUIRED_SCHEMAS:
            if not (base / "schema" / sch).is_file():
                errors.append(f"Missing {shared_rel}/schema/{sch}")

    proc = subprocess.run(
        [sys.executable, str(repo_root / "tests" / "aif-v01-red-suite.py")],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        errors.append(f"aif-v01-red-suite.py failed:\n{proc.stdout}\n{proc.stderr}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(
        "OK: AIF-0.1 Semantic Kernel verified across .claude/skills/_shared/aif/, .agent/skills/_shared/aif/, 13 modular schemas, and 28 RED invariant tests."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
