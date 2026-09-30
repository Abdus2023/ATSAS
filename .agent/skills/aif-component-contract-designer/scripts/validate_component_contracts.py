#!/usr/bin/env python3
"""
validate_component_contracts.py — Verify that all 8 component contracts (C-01..C-08),
all 13 phases (PHASE 0..PHASE 12), and all 15 failure codes are present.
"""

from __future__ import annotations

import sys
from pathlib import Path


COMPONENTS = (
    "arena-intake-and-authority",
    "agent-change-scope-audit",
    "dependency-supply-chain-audit",
    "ci-workflow-audit",
    "test-execution-and-evidence-audit",
    "evidence-receipt-generator",
    "arena-completion-gate",
    "skill-evaluation-harness",
)

FAILURE_CODES = (
    "AUTHORITY_MISSING",
    "SCOPE_UNDEFINED",
    "SCOPE_VIOLATION",
    "NOT_EXECUTED",
    "WRONG_HEAD",
    "STALE_EVIDENCE",
    "CI_NOT_CONFIGURED",
    "CI_NOT_EXECUTED",
    "TEST_NOT_EXECUTED",
    "TEST_FAILED",
    "SECRET_UNVERIFIED",
    "DEPENDENCY_UNRESOLVED",
    "EVIDENCE_INCOMPLETE",
    "ARTIFACT_MISMATCH",
    "RECEIPT_INVALID",
)


def main() -> int:
    repo_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    cc_path = repo_root / ".claude" / "assurance" / "component-contracts.md"
    w1_path = repo_root / "spec" / "06-wave1-skill-interfaces.md"

    errors: list[str] = []
    if not cc_path.is_file():
        errors.append("Missing .claude/assurance/component-contracts.md")
    if not w1_path.is_file():
        errors.append("Missing spec/06-wave1-skill-interfaces.md")
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    cc_text = cc_path.read_text(encoding="utf-8")
    w1_text = w1_path.read_text(encoding="utf-8")

    for i in range(1, 9):
        cid = f"C-{i:02d}"
        if f"`{cid}`" not in cc_text:
            errors.append(f"component-contracts.md missing `{cid}`")

    for comp in COMPONENTS:
        if f"`{comp}`" not in cc_text:
            errors.append(f"component-contracts.md missing `{comp}`")
        if f"`{comp}`" not in w1_text:
            errors.append(f"spec/06-wave1-skill-interfaces.md missing `{comp}`")

    for p in range(0, 13):
        if f"PHASE {p}" not in cc_text:
            errors.append(f"component-contracts.md missing `PHASE {p}`")

    for code in FAILURE_CODES:
        if f"`{code}`" not in w1_text:
            errors.append(f"spec/06-wave1-skill-interfaces.md missing failure code `{code}`")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(
        f"OK: Verified {len(COMPONENTS)} component contracts (C-01..C-08), PHASE 0..12, and {len(FAILURE_CODES)} failure taxonomy codes."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
