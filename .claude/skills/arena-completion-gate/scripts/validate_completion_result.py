#!/usr/bin/env python3
"""
validate_completion_result.py — Structural & Semantic Validator for CompletionResult
(.claude/skills/arena-completion-gate, Component C-07, AIF-0.1.0).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_FIELDS = (
    "request_id",
    "acceptance_expression",
    "status",
    "evaluated_claims",
    "satisfied_requirements",
    "unmet_requirements",
    "blockers",
    "unknowns",
    "contradictions",
    "evidence_refs",
    "evaluated_snapshot",
    "generated_at",
    "evaluator",
    "evaluator_version",
)

ALLOWED_STATUSES = {
    "COMPLETABLE",
    "INCOMPLETE",
    "BLOCKED",
    "CONTRADICTED",
    "INVALID",
    "ACCEPTANCE_UNSPECIFIED",
    "REJECTED",
    "UNVERIFIED",
}


def validate_completion_result(res: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    for f in REQUIRED_FIELDS:
        if f not in res:
            errors.append(f"Missing required field '{f}'")

    status = res.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"Invalid status '{status}' (note: COMPLETED is forbidden; use COMPLETABLE)")

    if status == "COMPLETABLE":
        if res.get("unmet_requirements"):
            errors.append("status=COMPLETABLE cannot have non-empty unmet_requirements")
        if res.get("contradictions"):
            errors.append("status=COMPLETABLE cannot have non-empty contradictions")
        if res.get("blockers"):
            errors.append("status=COMPLETABLE cannot have non-empty blockers")

    if status == "CONTRADICTED" and not res.get("contradictions"):
        errors.append("status=CONTRADICTED must record at least one contradicted claim in contradictions[]")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a CompletionResult JSON object.")
    parser.add_argument("input_path", help="Path to CompletionResult JSON file.")
    args = parser.parse_args()

    obj = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
    out = validate_completion_result(obj)
    print(json.dumps(out, indent=2))
    return 0 if out["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
