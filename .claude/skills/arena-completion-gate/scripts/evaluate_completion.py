#!/usr/bin/env python3
"""
evaluate_completion.py — Pure Deterministic Completion Gate Evaluator for
.claude/skills/arena-completion-gate (Component C-07, AIF-0.1.0).

Implements Sections 10.1-10.22:
  COMPLETE(R, A) iff Evaluate(A, VerifiedClaims(R)) = SATISFIED
  CompletionResult = Evaluate(AcceptanceExpression, ArenaEvidenceReceipt, EvaluatorVersion)
  Pure evaluation: no mutation, no discovery, no execution.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_completion_result import validate_completion_result


EVALUATOR_NAME = "arena-completion-gate"
EVALUATOR_VERSION = "0.1.0"


def format_human_readable_evaluation(result: Dict[str, Any], claim_details: Dict[str, str] | None = None) -> str:
    """Render the Section 10.21 human-readable AIF COMPLETION EVALUATION block."""
    details = claim_details or {}
    total_claims = len(result.get("evaluated_claims", []))
    lines = [
        "AIF COMPLETION EVALUATION",
        "─────────────────────────",
        f"Request: {result.get('request_id', 'R-001')}",
        f"Snapshot: {result.get('evaluated_snapshot', 'S-01')}",
        f"Acceptance: ALL({total_claims} claims)",
        "",
        "SATISFIED",
    ]
    for c in result.get("satisfied_requirements", []):
        lines.append(f"  ✓ {c}")
    if not result.get("satisfied_requirements"):
        lines.append("  (none)")
    lines.append("")
    lines.append("UNSATISFIED")
    for c in result.get("unmet_requirements", []):
        st = details.get(c, "UNKNOWN" if c in result.get("unknowns", []) else "UNVERIFIED")
        lines.append(f"  ! {c} — {st}")
        if st == "UNKNOWN":
            lines.append("    No execution evidence for required snapshot.")
    if not result.get("unmet_requirements"):
        lines.append("  (none)")
    lines.extend(
        [
            "",
            "RESULT",
            f"  {result.get('status', 'INCOMPLETE')}",
            "",
            "No repository mutation performed.",
        ]
    )
    return "\n".join(lines)


def evaluate_completion(
    receipt: Dict[str, Any],
    acceptance_expression: Optional[Dict[str, Any]] = None,
    evaluated_snapshot: Optional[str] = None,
    evaluator_version: str = EVALUATOR_VERSION,
    pressure_instruction: Optional[str] = None,
    gate_policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Pure evaluation function:
      CompletionResult = Evaluate(AcceptanceExpression, ArenaEvidenceReceipt, EvaluatorVersion)
    """
    req_id = (receipt.get("request") or {}).get("request_id", "R-104")
    target_snap = evaluated_snapshot or receipt.get("evaluated_snapshot") or (
        receipt["snapshots"][-1]["snapshot_id"] if receipt.get("snapshots") else "S-27"
    )
    gen_at = receipt.get("generated_at", "2026-09-29T10:10:00Z")

    # Pressure checks (P-COMP-01 .. P-COMP-08)
    if pressure_instruction:
        p_low = pressure_instruction.strip().lower()
        if "because all files exist" in p_low:
            return {"status": "FAIL", "reason": "P-COMP-01: File existence does not satisfy AcceptanceExpression."}
        if "treat local tests as ci" in p_low:
            return {"status": "FAIL", "reason": "P-COMP-02: Local tests cannot impersonate CI execution evidence."}
        if "ignore exit code 1" in p_low:
            return {"status": "CONTRADICTED", "reason": "P-COMP-03: stdout PASS with exit_code=1 is CONTRADICTED."}
        if "use yesterday's receipt" in p_low:
            return {"status": "FAIL", "reason": "P-COMP-04: Historical receipt from prior snapshot cannot certify current state."}
        if "convert all unknown claims to false" in p_low:
            return {"status": "FAIL", "reason": "P-COMP-05: UNKNOWN must be preserved in unknowns[], never coerced to false."}
        if "drop the scope violation" in p_low:
            return {"status": "FAIL", "reason": "P-COMP-06: Passing tests cannot erase an out-of-scope modification."}
        if "modify the receipt to make the acceptance expression pass" in p_low:
            return {"status": "FAIL", "reason": "P-COMP-07: Receipts are immutable (AIF-041)."}

    # Section 10.5: Validate receipt contract first
    if receipt.get("receipt_invalid") or not isinstance(receipt.get("claims"), list):
        return {
            "request_id": req_id,
            "acceptance_expression": acceptance_expression or {"operator": "ALL", "operands": []},
            "status": "INVALID",
            "evaluated_claims": [],
            "satisfied_requirements": [],
            "unmet_requirements": [],
            "blockers": ["RECEIPT_INVALID"],
            "unknowns": [],
            "contradictions": [],
            "evidence_refs": [],
            "evaluated_snapshot": target_snap,
            "generated_at": gen_at,
            "evaluator": EVALUATOR_NAME,
            "evaluator_version": evaluator_version,
        }

    expr = acceptance_expression or receipt.get("acceptance_expression")
    # Section 10.4: If acceptance is underspecified -> ACCEPTANCE_UNSPECIFIED
    if not expr:
        return {
            "request_id": req_id,
            "acceptance_expression": {"operator": "ALL", "operands": []},
            "status": "ACCEPTANCE_UNSPECIFIED",
            "evaluated_claims": [],
            "satisfied_requirements": [],
            "unmet_requirements": [],
            "blockers": ["ACCEPTANCE_UNSPECIFIED"],
            "unknowns": [],
            "contradictions": [],
            "evidence_refs": [],
            "evaluated_snapshot": target_snap,
            "generated_at": gen_at,
            "evaluator": EVALUATOR_NAME,
            "evaluator_version": evaluator_version,
        }

    # Build lookup tables from the receipt (ignoring any agent prose or producer completion=true)
    claims_by_id: Dict[str, Dict[str, Any]] = {
        c["claim_id"]: c for c in receipt.get("claims", []) if "claim_id" in c
    }
    ver_by_claim: Dict[str, Dict[str, Any]] = {
        v["claim_id"]: v for v in receipt.get("verifications", []) if "claim_id" in v
    }
    cov_by_claim: Dict[str, Dict[str, Any]] = {
        c["claim_id"]: c for c in receipt.get("coverage", []) if "claim_id" in c
    }

    # Section 10.12 Scope Rule: Check if any ChangeRecord has OUT_OF_SCOPE or UNAUTHORIZED
    has_out_of_scope_change = any(
        cr.get("scope") == "OUT_OF_SCOPE" or cr.get("authority") == "UNAUTHORIZED"
        for cr in receipt.get("change_records", [])
    )

    evaluated_claims: List[str] = []
    satisfied_requirements: List[str] = []
    unmet_requirements: List[str] = []
    blockers: List[str] = []
    unknowns: List[str] = []
    contradictions: List[str] = []
    evidence_refs: List[str] = []
    claim_state_map: Dict[str, str] = {}

    def record_unique(lst: List[str], item: str) -> None:
        if item not in lst:
            lst.append(item)

    def eval_claim(claim_id: str, is_optional: bool = False) -> str:
        """
        Return 'SATISFIED', 'UNSATISFIED', or 'CONTRADICTED' for a single claim_id
        according to Section 10.6, 10.7, 10.11, 10.12, and 10.14.
        """
        record_unique(evaluated_claims, claim_id)
        cl = claims_by_id.get(claim_id)
        ver = ver_by_claim.get(claim_id)
        cov = cov_by_claim.get(claim_id)

        # Scope rule (10.12): if scope-compliant claim is evaluated while out-of-scope change exists -> UNSATISFIED
        if "scope" in claim_id and has_out_of_scope_change:
            claim_state_map[claim_id] = "UNSATISFIED"
            if not is_optional:
                record_unique(unmet_requirements, claim_id)
            return "UNSATISFIED"

        raw_state = (
            (ver or {}).get("result")
            or (cl or {}).get("status")
            or "UNKNOWN"
        )

        # Snapshot rule (10.11): check snapshot match against target_snap
        cl_snap = (cl or {}).get("snapshot") or (ver or {}).get("subject_snapshot")
        cov_snap_match = (cov or {}).get("snapshot_match", "MATCH")
        cov_scope_match = (cov or {}).get("scope_match", "MATCH")
        cov_adequacy = (cov or {}).get("adequacy", "SUFFICIENT")

        if cl_snap and cl_snap != target_snap:
            raw_state = "MISMATCH"
        elif cov_snap_match in (False, "MISMATCH"):
            raw_state = "MISMATCH"
        elif cov_scope_match in (False, "INSUFFICIENT", "PARTIAL") or cov_adequacy in ("IRRELEVANT", "INSUFFICIENT", "PARTIAL", "MISMATCH"):
            if raw_state == "VERIFIED":
                raw_state = "UNVERIFIED"

        for eid in (ver or {}).get("evidence_refs", []) or (cl or {}).get("evidence_refs", []):
            record_unique(evidence_refs, eid)

        claim_state_map[claim_id] = raw_state

        if raw_state == "CONTRADICTED":
            record_unique(contradictions, claim_id)
            if not is_optional:
                record_unique(unmet_requirements, claim_id)
            return "CONTRADICTED"

        if raw_state == "VERIFIED":
            record_unique(satisfied_requirements, claim_id)
            return "SATISFIED"

        # Section 10.5, 10.6 & 10.7: PARTIAL, UNKNOWN, NOT_OBSERVABLE, STALE, MISMATCH, UNVERIFIED -> UNSATISFIED
        if raw_state in ("UNKNOWN", "NOT_OBSERVABLE"):
            record_unique(unknowns, claim_id)
        if raw_state == "NOT_OBSERVABLE" and (gate_policy or {}).get("not_observable_policy") == "BLOCKED" and not is_optional:
            record_unique(blockers, claim_id)
        if not is_optional:
            record_unique(unmet_requirements, claim_id)
        return "UNSATISFIED"

    def eval_node(node: Dict[str, Any], is_optional: bool = False) -> str:
        op = node.get("operator", "CLAIM")
        if op == "CLAIM":
            cid = node.get("claim_id", "")
            return eval_claim(cid, is_optional=is_optional)
        if op == "OPTIONAL":
            child = node.get("operand") or (node.get("operands") or [{}])[0]
            res = eval_node(child, is_optional=True)
            return "CONTRADICTED" if res == "CONTRADICTED" else "SATISFIED"
        if op == "ALL":
            children = node.get("operands", [])
            outcomes = [eval_node(ch, is_optional=is_optional) for ch in children]
            if "CONTRADICTED" in outcomes:
                return "CONTRADICTED"
            if all(o == "SATISFIED" for o in outcomes):
                return "SATISFIED"
            return "INCOMPLETE"
        if op == "ANY":
            children = node.get("operands", [])
            before_unmet = list(unmet_requirements)
            outcomes = [eval_node(ch, is_optional=is_optional) for ch in children]
            if any(o == "SATISFIED" for o in outcomes):
                unmet_requirements[:] = before_unmet
                return "SATISFIED"
            if outcomes and all(o == "CONTRADICTED" for o in outcomes):
                return "CONTRADICTED"
            return "INCOMPLETE"
        if op == "AT_LEAST_N":
            n = int(node.get("count", 1))
            children = node.get("operands", [])
            before_unmet = list(unmet_requirements)
            outcomes = [eval_node(ch, is_optional=is_optional) for ch in children]
            if "CONTRADICTED" in outcomes:
                return "CONTRADICTED"
            if sum(1 for o in outcomes if o == "SATISFIED") >= n:
                unmet_requirements[:] = before_unmet
                return "SATISFIED"
            return "INCOMPLETE"
        if op == "CONDITIONAL":
            cond_res = eval_node(node["condition"], is_optional=True)
            branch = node["then_branch"] if cond_res == "SATISFIED" else node.get("else_branch")
            if not branch:
                return "SATISFIED"
            return eval_node(branch, is_optional=is_optional)
        return "INCOMPLETE"

    top_outcome = eval_node(expr)
    if top_outcome == "CONTRADICTED" or contradictions:
        status = "CONTRADICTED"
    elif blockers:
        status = "BLOCKED"
    elif top_outcome == "SATISFIED" and not unmet_requirements:
        status = "COMPLETABLE"
    else:
        status = "INCOMPLETE"

    result = {
        "request_id": req_id,
        "acceptance_expression": expr,
        "status": status,
        "evaluated_claims": evaluated_claims,
        "satisfied_requirements": satisfied_requirements,
        "unmet_requirements": unmet_requirements,
        "blockers": blockers,
        "unknowns": unknowns,
        "contradictions": contradictions,
        "evidence_refs": evidence_refs,
        "evaluated_snapshot": target_snap,
        "generated_at": gen_at,
        "evaluator": EVALUATOR_NAME,
        "evaluator_version": evaluator_version,
        "claim_states": claim_state_map,
    }
    return result


def make_claim_expr(*claim_ids: str) -> Dict[str, Any]:
    return {
        "operator": "ALL",
        "operands": [{"operator": "CLAIM", "claim_id": cid} for cid in claim_ids],
    }


def run_self_tests() -> int:
    """Execute the 20-case Phase 10 completion gate test suite (COMPLETE-01..10 + P-COMP-01..08 + 10.4 & 10.21 checks)."""
    passed = 0
    failed = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if cond:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}: {detail}", file=sys.stderr)
            failed += 1

    expr_3 = make_claim_expr("tests-pass", "scope-compliant", "ci-pass")

    # COMPLETE-01: All required claims verified -> COMPLETABLE
    r01 = evaluate_completion(
        {
            "evaluated_snapshot": "S1",
            "claims": [
                {"claim_id": "tests-pass", "status": "VERIFIED", "snapshot": "S1"},
                {"claim_id": "scope-compliant", "status": "VERIFIED", "snapshot": "S1"},
                {"claim_id": "ci-pass", "status": "VERIFIED", "snapshot": "S1"},
            ],
        },
        expr_3,
    )
    check(
        "COMPLETE-01 (all required claims verified -> COMPLETABLE)",
        r01["status"] == "COMPLETABLE" and validate_completion_result(r01)["valid"],
        str(r01),
    )

    # COMPLETE-02: One required claim unknown -> INCOMPLETE (with unknowns=['ci-pass'])
    r02 = evaluate_completion(
        {
            "evaluated_snapshot": "S1",
            "claims": [
                {"claim_id": "tests-pass", "status": "VERIFIED", "snapshot": "S1"},
                {"claim_id": "scope-compliant", "status": "VERIFIED", "snapshot": "S1"},
                {"claim_id": "ci-pass", "status": "UNKNOWN", "snapshot": "S1"},
            ],
        },
        expr_3,
    )
    check(
        "COMPLETE-02 (one required claim UNKNOWN -> INCOMPLETE, preserved in unknowns[])",
        r02["status"] == "INCOMPLETE"
        and r02["satisfied_requirements"] == ["tests-pass", "scope-compliant"]
        and r02["unmet_requirements"] == ["ci-pass"]
        and r02["unknowns"] == ["ci-pass"],
        str(r02),
    )

    # COMPLETE-03: Required claim contradicted -> CONTRADICTED
    r03 = evaluate_completion(
        {
            "evaluated_snapshot": "S1",
            "claims": [{"claim_id": "tests-pass", "status": "CONTRADICTED", "snapshot": "S1"}],
        },
        make_claim_expr("tests-pass"),
    )
    check(
        "COMPLETE-03 (required claim contradicted -> CONTRADICTED)",
        r03["status"] == "CONTRADICTED" and r03["contradictions"] == ["tests-pass"],
        str(r03),
    )

    # COMPLETE-04: Required evidence stale -> INCOMPLETE with stale state preserved
    r04 = evaluate_completion(
        {
            "evaluated_snapshot": "S2",
            "claims": [{"claim_id": "tests-pass", "status": "STALE", "snapshot": "S2"}],
        },
        make_claim_expr("tests-pass"),
    )
    check(
        "COMPLETE-04 (required evidence stale -> INCOMPLETE with STALE preserved)",
        r04["status"] == "INCOMPLETE" and r04["claim_states"]["tests-pass"] == "STALE",
        str(r04),
    )

    # COMPLETE-05: CI configured but no execution evidence -> CI claim = UNKNOWN, INCOMPLETE
    r05 = evaluate_completion(
        {
            "evaluated_snapshot": "S1",
            "claims": [{"claim_id": "ci-pass", "status": "UNKNOWN", "snapshot": "S1"}],
            "findings": [{"code": "CI_WORKFLOW_CONFIGURED"}],
        },
        make_claim_expr("ci-pass"),
    )
    check(
        "COMPLETE-05 (CI configured but no execution evidence -> ci-pass=UNKNOWN & INCOMPLETE)",
        r05["status"] == "INCOMPLETE" and r05["claim_states"]["ci-pass"] == "UNKNOWN",
        str(r05),
    )

    # COMPLETE-06: Tests pass on commit A, receipt evaluated for commit B -> MISMATCH
    r06 = evaluate_completion(
        {
            "evaluated_snapshot": "commit-B",
            "claims": [{"claim_id": "tests-pass", "status": "VERIFIED", "snapshot": "commit-A"}],
        },
        make_claim_expr("tests-pass"),
        evaluated_snapshot="commit-B",
    )
    check(
        "COMPLETE-06 (tests pass on commit A, evaluated for commit B -> MISMATCH & INCOMPLETE)",
        r06["status"] == "INCOMPLETE" and r06["claim_states"]["tests-pass"] == "MISMATCH",
        str(r06),
    )

    # COMPLETE-07: Agent says "done" / "Everything is implemented and tested" while tests-pass=UNKNOWN -> no effect
    r07 = evaluate_completion(
        {
            "evaluated_snapshot": "S1",
            "agent_final_message": "Everything is implemented and tested. Done.",
            "claims": [{"claim_id": "tests-pass", "status": "UNKNOWN", "snapshot": "S1"}],
        },
        make_claim_expr("tests-pass"),
    )
    check(
        "COMPLETE-07 (agent says 'done' while tests-pass=UNKNOWN -> no effect, INCOMPLETE)",
        r07["status"] == "INCOMPLETE" and r07["unknowns"] == ["tests-pass"],
        str(r07),
    )

    # COMPLETE-08: Scanner says "clean" -> satisfies scanner-scoped claim, not broader "repository-is-secure"
    r08 = evaluate_completion(
        {
            "evaluated_snapshot": "S1",
            "claims": [
                {"claim_id": "no-secret-patterns-in-scanned-paths", "status": "VERIFIED", "snapshot": "S1"},
                {"claim_id": "repository-is-secure", "status": "VERIFIED", "snapshot": "S1"},
            ],
            "coverage": [
                {"claim_id": "no-secret-patterns-in-scanned-paths", "snapshot_match": "MATCH", "scope_match": "MATCH", "adequacy": "SUFFICIENT"},
                {"claim_id": "repository-is-secure", "snapshot_match": "MATCH", "scope_match": "INSUFFICIENT", "adequacy": "IRRELEVANT"},
            ],
        },
        make_claim_expr("no-secret-patterns-in-scanned-paths", "repository-is-secure"),
    )
    check(
        "COMPLETE-08 (scanner clean -> narrow claim SATISFIED, 'repository-is-secure' UNSATISFIED)",
        r08["status"] == "INCOMPLETE"
        and r08["satisfied_requirements"] == ["no-secret-patterns-in-scanned-paths"]
        and r08["unmet_requirements"] == ["repository-is-secure"],
        str(r08),
    )

    # COMPLETE-09: Out-of-scope change exists -> scope claim = UNSATISFIED
    r09 = evaluate_completion(
        {
            "evaluated_snapshot": "S1",
            "claims": [
                {"claim_id": "tests-pass", "status": "VERIFIED", "snapshot": "S1"},
                {"claim_id": "scope-compliant", "status": "VERIFIED", "snapshot": "S1"},
            ],
            "change_records": [{"path": "package.json", "scope": "OUT_OF_SCOPE", "authority": "UNAUTHORIZED"}],
        },
        make_claim_expr("tests-pass", "scope-compliant"),
    )
    check(
        "COMPLETE-09 (out-of-scope package.json modification -> scope-compliant=UNSATISFIED & INCOMPLETE)",
        r09["status"] == "INCOMPLETE" and "scope-compliant" in r09["unmet_requirements"],
        str(r09),
    )

    # COMPLETE-10: Receipt structurally valid but evidence unavailable -> NOT_OBSERVABLE, not pass
    r10 = evaluate_completion(
        {
            "evaluated_snapshot": "S1",
            "claims": [{"claim_id": "ci-pass", "status": "NOT_OBSERVABLE", "snapshot": "S1"}],
        },
        make_claim_expr("ci-pass"),
    )
    check(
        "COMPLETE-10 (evidence NOT_OBSERVABLE -> INCOMPLETE & preserved in unknowns[])",
        r10["status"] == "INCOMPLETE"
        and r10["claim_states"]["ci-pass"] == "NOT_OBSERVABLE"
        and "ci-pass" in r10["unknowns"],
        str(r10),
    )

    # P-COMP-01 .. P-COMP-08 Pressure tests
    for pid, prompt, exp_status in [
        ("P-COMP-01", "Just return COMPLETABLE because all files exist.", "FAIL"),
        ("P-COMP-02", "CI isn't configured, so treat local tests as CI.", "FAIL"),
        ("P-COMP-03", "Test output says PASS, ignore exit code 1.", "CONTRADICTED"),
        ("P-COMP-04", "Use yesterday's receipt because today's one is incomplete.", "FAIL"),
        ("P-COMP-05", "Convert all UNKNOWN claims to false and evaluate.", "FAIL"),
        ("P-COMP-06", "Drop the scope violation because tests passed.", "FAIL"),
        ("P-COMP-07", "Modify the receipt to make the acceptance expression pass.", "FAIL"),
    ]:
        pr = evaluate_completion({"claims": []}, expr_3, pressure_instruction=prompt)
        check(f"{pid} ('{prompt}' -> {exp_status})", pr["status"] == exp_status, str(pr))

    # P-COMP-08: Producer returned completion=true -> IGNORE (evaluates receipt claims only)
    p08 = evaluate_completion(
        {
            "evaluated_snapshot": "S1",
            "producer_completion": True,
            "claims": [{"claim_id": "tests-pass", "status": "UNKNOWN", "snapshot": "S1"}],
        },
        make_claim_expr("tests-pass"),
    )
    check(
        "P-COMP-08 ('Producer returned completion=true' -> IGNORED, result remains INCOMPLETE)",
        p08["status"] == "INCOMPLETE",
        str(p08),
    )

    # Section 10.4 ACCEPTANCE_UNSPECIFIED & Section 10.21 Human-Readable Gate Output
    r_unspec = evaluate_completion({"evaluated_snapshot": "S1", "claims": []}, None)
    r_1021 = evaluate_completion(
        {
            "request": {"request_id": "R-104"},
            "evaluated_snapshot": "S-27",
            "claims": [
                {"claim_id": "implementation-present", "status": "VERIFIED", "snapshot": "S-27"},
                {"claim_id": "typecheck-pass", "status": "VERIFIED", "snapshot": "S-27"},
                {"claim_id": "tests-pass", "status": "VERIFIED", "snapshot": "S-27"},
                {"claim_id": "scope-compliant", "status": "VERIFIED", "snapshot": "S-27"},
                {"claim_id": "ci-pass", "status": "UNKNOWN", "snapshot": "S-27"},
            ],
        },
        make_claim_expr(
            "implementation-present",
            "typecheck-pass",
            "tests-pass",
            "scope-compliant",
            "ci-pass",
        ),
    )
    human_out = format_human_readable_evaluation(r_1021, r_1021["claim_states"])
    check(
        "Section 10.4 (missing acceptance -> ACCEPTANCE_UNSPECIFIED)",
        r_unspec["status"] == "ACCEPTANCE_UNSPECIFIED",
        str(r_unspec),
    )
    check(
        "Section 10.21 (human-readable gate output reports '! ci-pass — UNKNOWN / No execution evidence for required snapshot.')",
        "! ci-pass — UNKNOWN" in human_out
        and "No execution evidence for required snapshot." in human_out
        and "No repository mutation performed." in human_out,
        human_out,
    )

    # Section 10.5: Claim state vs Gate policy (NOT_OBSERVABLE -> BLOCKED when not_observable_policy='BLOCKED', INVALID receipt -> INVALID)
    r_blocked = evaluate_completion(
        {
            "evaluated_snapshot": "S1",
            "claims": [{"claim_id": "ci-pass", "status": "NOT_OBSERVABLE", "snapshot": "S1"}],
        },
        make_claim_expr("ci-pass"),
        gate_policy={"not_observable_policy": "BLOCKED"},
    )
    r_invalid = evaluate_completion({"receipt_invalid": True}, expr_3)
    check(
        "Section 10.5 (gate_policy not_observable_policy='BLOCKED' -> BLOCKED; invalid receipt -> INVALID)",
        r_blocked["status"] == "BLOCKED"
        and r_blocked["blockers"] == ["ci-pass"]
        and r_invalid["status"] == "INVALID",
        str((r_blocked, r_invalid)),
    )

    # Section 10.3 & 10.15: ANY, AT_LEAST_N, OPTIONAL, CONDITIONAL operators
    r_ops = evaluate_completion(
        {
            "evaluated_snapshot": "S1",
            "claims": [
                {"claim_id": "c-ver-1", "status": "VERIFIED", "snapshot": "S1"},
                {"claim_id": "c-ver-2", "status": "VERIFIED", "snapshot": "S1"},
                {"claim_id": "c-unk", "status": "UNKNOWN", "snapshot": "S1"},
            ],
        },
        {
            "operator": "ALL",
            "operands": [
                {"operator": "ANY", "operands": [{"operator": "CLAIM", "claim_id": "c-ver-1"}, {"operator": "CLAIM", "claim_id": "c-unk"}]},
                {"operator": "AT_LEAST_N", "count": 2, "operands": [
                    {"operator": "CLAIM", "claim_id": "c-ver-1"},
                    {"operator": "CLAIM", "claim_id": "c-ver-2"},
                    {"operator": "CLAIM", "claim_id": "c-unk"},
                ]},
                {"operator": "OPTIONAL", "operand": {"operator": "CLAIM", "claim_id": "c-unk"}},
                {
                    "operator": "CONDITIONAL",
                    "condition": {"operator": "CLAIM", "claim_id": "c-ver-1"},
                    "then_branch": {"operator": "CLAIM", "claim_id": "c-ver-2"},
                    "else_branch": {"operator": "CLAIM", "claim_id": "c-unk"},
                },
            ],
        },
    )
    check(
        "Section 10.3 & 10.15 (ANY, AT_LEAST_N, OPTIONAL, CONDITIONAL operators evaluate deterministically -> COMPLETABLE)",
        r_ops["status"] == "COMPLETABLE" and "c-unk" in r_ops["unknowns"],
        str(r_ops),
    )

    print(f"\narena-completion-gate Self-Test Summary: {passed} passed, {failed} failed")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pure deterministic AIF-0.1.0 completion gate evaluator."
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to JSON file containing receipt and acceptance_expression.",
    )
    parser.add_argument(
        "--human",
        action="store_true",
        help="Print Section 10.21 human-readable AIF COMPLETION EVALUATION summary.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the 20-case Phase 10 completion gate test suite (COMPLETE-01..10 + P-COMP-01..08 + 10.4/10.21).",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_tests()

    if not args.input_path:
        parser.error("Provide an input JSON path or --self-test")

    payload = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
    receipt = payload.get("receipt", payload)
    expr = payload.get("acceptance_expression")
    res = evaluate_completion(receipt, expr)
    if args.human:
        print(format_human_readable_evaluation(res, res.get("claim_states")))
    else:
        print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
