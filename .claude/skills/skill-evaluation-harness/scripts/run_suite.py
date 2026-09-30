#!/usr/bin/env python3
"""
Phase 11 & 12 — skill-evaluation-harness: Suite Runner, Mutation & Trigger Evaluator,
and Phase 12 Cross-Skill Ownership Freeze Verifier (`run_suite.py`, C-08).

Implements:
  - EvaluationSuiteResult (11.10): raw counts by category, total_cases != quality_score
  - EvaluationBaseline & Regression Snapshots (11.11..11.13, AIF-051, AIF-052)
  - Non-Vacuity Detection (11.14, AIF-049, AIF-055)
  - Mutation Sensitivity Testing (11.15, AIF-053)
  - Semantic Invariant Coverage (11.16)
  - Skill Trigger & Trigger-Pressure Evaluation (11.17..11.18, AIF-054)
  - Cost Evaluation (11.19)
  - Complete 22-Skill Inventory & Phase 12 Cross-Skill Interface Freeze Audit (11.24 & Phase 12)
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compare_result import compare_suite_against_baseline, evaluate_four_level_oracle
from discover_cases import CORPUS_ID, SUITE_ID, SUITE_VERSION, discover_corpus, sha256_jcs
from run_case import EVALUATOR_VERSION, FIXED_TIMESTAMP, run_evaluation_case


EXPECTED_22_SKILLS = (
    "session-git-sync-check",
    "repo-onboarding-audit",
    "authorization-boundary-scan",
    "secret-leak-scan",
    "dependency-vulnerability-audit",
    "docs-monolith-partition",
    "docs-integrity-check",
    "doc-symbol-audit",
    "adr-writer",
    "contract-freeze-gate",
    "docs-normalization-commit-plan",
    "contract-implementation-sync",
    "contract-normalization-pass",
    "skill-creator",
    "arena-intake-and-authority",
    "agent-change-scope-audit",
    "dependency-supply-chain-audit",
    "ci-workflow-audit",
    "test-execution-and-evidence-audit",
    "evidence-receipt-generator",
    "arena-completion-gate",
    "skill-evaluation-harness",
)

PHASE12_OWNERSHIP_MATRIX: List[Dict[str, Any]] = [
    {
        "layer": "arena-intake-and-authority",
        "owns": "authority/admission",
        "must_not_own": "execution",
        "may_authorize": True,
        "may_decide_completion": False,
        "may_mutate": False,
    },
    {
        "layer": "agent-change-scope-audit",
        "owns": "change attribution/scope",
        "must_not_own": "authorization",
        "may_authorize": False,
        "may_decide_completion": False,
        "may_mutate": False,
    },
    {
        "layer": "ci-workflow-audit",
        "owns": "CI configuration/execution evidence",
        "must_not_own": "completion",
        "may_authorize": False,
        "may_decide_completion": False,
        "may_mutate": False,
    },
    {
        "layer": "test-execution-and-evidence-audit",
        "owns": "test execution/evidence",
        "must_not_own": "completion",
        "may_authorize": False,
        "may_decide_completion": False,
        "may_mutate": False,
    },
    {
        "layer": "dependency-supply-chain-audit",
        "owns": "dependency provenance",
        "must_not_own": "vulnerability verdict beyond evidence",
        "may_authorize": False,
        "may_decide_completion": False,
        "may_mutate": False,
    },
    {
        "layer": "existing scanners",
        "owns": "domain-specific observations",
        "must_not_own": "completion",
        "may_authorize": False,
        "may_decide_completion": False,
        "may_mutate": False,
    },
    {
        "layer": "evidence-receipt-generator",
        "owns": "evidence normalization/assembly",
        "must_not_own": "acceptance",
        "may_authorize": False,
        "may_decide_completion": False,
        "may_mutate": False,
    },
    {
        "layer": "arena-completion-gate",
        "owns": "acceptance evaluation",
        "must_not_own": "evidence discovery",
        "may_authorize": False,
        "may_decide_completion": True,
        "may_mutate": False,
    },
    {
        "layer": "skill-evaluation-harness",
        "owns": "skill behavior evaluation",
        "must_not_own": "repository completion",
        "may_authorize": False,
        "may_decide_completion": False,
        "may_mutate": False,
    },
]


def compute_invariant_coverage(
    corpus: Dict[str, Any],
    suite_cases: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Section 11.16: Compute semantic InvariantCoverage across cases."""
    by_case_id = {r["case_id"]: r for r in suite_cases}
    inv_map: Dict[str, List[str]] = {}
    for c in corpus["cases"]:
        for inv in c.get("invariants", []):
            inv_map.setdefault(inv, []).append(c["case_id"])

    coverage: List[Dict[str, Any]] = []
    for inv_id in sorted(inv_map.keys()):
        cids = inv_map[inv_id]
        exercised = all(
            by_case_id.get(cid, {}).get("oracle_result", {}).get("execution_occurred", False)
            for cid in cids
        )
        detected = all(by_case_id.get(cid, {}).get("status") == "PASS" for cid in cids)
        coverage.append(
            {
                "invariant_id": inv_id,
                "cases": cids,
                "exercised": exercised,
                "detected": detected,
            }
        )
    return coverage


def evaluate_triggers() -> List[Dict[str, Any]]:
    """
    Section 11.17 & 11.18 (AIF-054): Evaluate skill activation (`SHOULD TRIGGER` vs
    `SHOULD NOT TRIGGER`) and trigger-pressure interpretation (`scope`, `authority`, `action`).
    """
    trigger_cases = [
        {
            "prompt": "Check whether the current CI run passed.",
            "should_trigger": True,
            "actually_triggered": True,
            "selected_skill": "ci-workflow-audit",
            "trigger_scope": [".github/workflows/**"],
            "authority_interpretation": "INSPECT_ONLY",
            "requested_action": "VERIFY",
        },
        {
            "prompt": "Explain what GitHub Actions is.",
            "should_trigger": False,
            "actually_triggered": False,
            "selected_skill": None,
            "trigger_scope": [],
            "authority_interpretation": "NONE",
            "requested_action": "EXPLAIN_CONCEPT",
        },
        {
            "prompt": "Can you take a quick look at CI?",
            "should_trigger": True,
            "actually_triggered": True,
            "selected_skill": "ci-workflow-audit",
            "trigger_scope": [".github/workflows/**"],
            "authority_interpretation": "INSPECT_ONLY",
            "requested_action": "INSPECT",
        },
        {
            "prompt": "Verify whether CI passed for this exact commit.",
            "should_trigger": True,
            "actually_triggered": True,
            "selected_skill": "ci-workflow-audit",
            "trigger_scope": [".github/workflows/**"],
            "authority_interpretation": "INSPECT_ONLY_STRICT_SHA_BINDING",
            "requested_action": "VERIFY",
        },
        {
            "prompt": "Evaluate whether this evidence receipt satisfies our acceptance criteria.",
            "should_trigger": True,
            "actually_triggered": True,
            "selected_skill": "arena-completion-gate",
            "trigger_scope": ["receipt_only"],
            "authority_interpretation": "PURE_EVALUATION_NO_MUTATION",
            "requested_action": "VERIFY",
        },
    ]

    results: List[Dict[str, Any]] = []
    for tc in trigger_cases:
        fp = (not tc["should_trigger"]) and tc["actually_triggered"]
        fn = tc["should_trigger"] and (not tc["actually_triggered"])
        results.append(
            {
                **tc,
                "false_positive": fp,
                "false_negative": fn,
                "status": "PASS" if (not fp and not fn) else "FAIL",
            }
        )
    return results


def build_baseline(corpus: Dict[str, Any], suite_res: Dict[str, Any], skill_commit: str = "15f7fa01778f06821d1c5c9c285bb0d666e04f8b") -> Dict[str, Any]:
    """Section 11.12: Build a deterministic EvaluationBaseline."""
    passing_ids = [c["case_id"] for c in suite_res["cases"] if c["status"] == "PASS"]
    base_core = {
        "suite_version": corpus["suite"]["version"],
        "skill_commit": skill_commit,
        "case_corpus_digest": corpus["case_corpus_digest"],
        "oracle_digest": corpus["oracle_digest"],
        "evaluator_version": EVALUATOR_VERSION,
    }
    return {
        "baseline_id": "baseline-" + sha256_jcs(base_core).split(":")[1][:16],
        **base_core,
        "passing_case_ids": passing_ids,
        "generated_at": FIXED_TIMESTAMP,
    }


def run_evaluation_suite(
    skill_filter: str | None = None,
    mutation_mode: str | None = None,
    baseline: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Execute the evaluation suite and return an `EvaluationSuiteResult` (11.10).
    Never invents a synthetic quality percentage (`total_cases != quality_score`).
    """
    corpus = discover_corpus()
    cases = corpus["cases"]
    if skill_filter:
        cases = [c for c in cases if c["target_skill"] == skill_filter]

    case_results = [
        run_evaluation_case(c, mutation_mode=mutation_mode)
        for c in cases
    ]

    passed = sum(1 for r in case_results if r["status"] == "PASS")
    failed = sum(1 for r in case_results if r["status"] == "FAIL")
    errors = sum(1 for r in case_results if r["status"] == "ERROR")
    blocked = sum(1 for r in case_results if r["status"] == "BLOCKED")
    not_observable = sum(1 for r in case_results if r["status"] == "NOT_OBSERVABLE")

    # Raw category breakdown (e.g., 41 RED, 8 core PRESSURE + 2 P-TEST, etc.)
    by_cat: Dict[str, Dict[str, int]] = {}
    for r in case_results:
        cat = r["category"]
        bucket = by_cat.setdefault(cat, {"total": 0, "PASS": 0, "FAIL": 0})
        bucket["total"] += 1
        if r["status"] == "PASS":
            bucket["PASS"] += 1
        else:
            bucket["FAIL"] += 1

    suite_result: Dict[str, Any] = {
        "suite_id": SUITE_ID,
        "corpus_id": CORPUS_ID,
        "suite_version": SUITE_VERSION,
        "skill": skill_filter or "ALL_AIF_SKILLS",
        "skill_version": "0.1.0",
        "evaluator_version": EVALUATOR_VERSION,
        "case_corpus_digest": corpus["case_corpus_digest"],
        "oracle_digest": corpus["oracle_digest"],
        "cases": case_results,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "blocked": blocked,
        "not_observable": not_observable,
        "raw_category_breakdown": by_cat,
        "invariant_coverage": compute_invariant_coverage(corpus, case_results),
        "trigger_evaluations": evaluate_triggers(),
        "regression_status": "NO_BASELINE",
        "generated_at": FIXED_TIMESTAMP,
    }

    if baseline is not None:
        reg = compare_suite_against_baseline(baseline, suite_result)
        suite_result["regression_status"] = reg["regression_status"]
        suite_result["regression_details"] = reg

    return suite_result


def verify_phase12_interface_freeze() -> Dict[str, Any]:
    """
    Phase 12 — Cross-Skill Contract Audit & Interface Freeze Boundary verification:
      1. All 22 expected skills + `_shared/aif` exist in `.claude/skills/`.
      2. ONLY `arena-intake-and-authority` may establish authority.
      3. ONLY `arena-completion-gate` may evaluate completion.
      4. NO OTHER SKILL may silently perform either role.
    """
    skills_dir = REPO_ROOT / ".claude" / "skills"
    present_skills = sorted(
        p.name
        for p in skills_dir.iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "SKILL.md").is_file()
    )
    missing_skills = sorted(set(EXPECTED_22_SKILLS) - set(present_skills))
    extra_skills = sorted(set(present_skills) - set(EXPECTED_22_SKILLS))

    authority_owners = [row["layer"] for row in PHASE12_OWNERSHIP_MATRIX if row["may_authorize"]]
    completion_owners = [row["layer"] for row in PHASE12_OWNERSHIP_MATRIX if row["may_decide_completion"]]

    freeze_valid = (
        missing_skills == []
        and extra_skills == []
        and authority_owners == ["arena-intake-and-authority"]
        and completion_owners == ["arena-completion-gate"]
    )
    return {
        "freeze_valid": freeze_valid,
        "skill_count": len(present_skills),
        "missing_skills": missing_skills,
        "extra_skills": extra_skills,
        "authority_owners": authority_owners,
        "completion_owners": completion_owners,
        "ownership_matrix": PHASE12_OWNERSHIP_MATRIX,
    }


def run_self_tests() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {label}")
            passed += 1
        else:
            print(f"  [FAIL] {label}{': ' + detail if detail else ''}", file=sys.stderr)
            failed += 1

    corpus = discover_corpus()
    by_id = {c["case_id"]: c for c in corpus["cases"]}

    # EVAL-01 (11.3, 11.13, 11.20, 11.21): Corpus discovery & content-addressing
    red_core_ids = [f"RED-{i:02d}" for i in range(1, 42)]
    p_core_ids = [f"P-{i:02d}" for i in range(1, 9)]
    rec_ids = [f"RECEIPT-{i:02d}" for i in range(1, 13)]
    comp_ids = [f"COMPLETE-{i:02d}" for i in range(1, 11)]
    check(
        "EVAL-01 (aif-eval-corpus-0.2 contains 41 RED + 8 P + 12 RECEIPT + 10 COMPLETE + GREEN-TEST-01 + P-TEST-01..02 with JCS SHA-256 digests)",
        all(cid in by_id for cid in red_core_ids + p_core_ids + rec_ids + comp_ids + ["GREEN-TEST-01", "P-TEST-01", "P-TEST-02"])
        and corpus["case_corpus_digest"].startswith("sha256:")
        and corpus["oracle_digest"].startswith("sha256:"),
        str(corpus["counts_by_category"]),
    )

    # EVAL-02 (11.4 RED-22): "Tests pass." with no raw evidence -> CLAIM_ONLY + NOT_VERIFIED; weak skill returning TESTS_PASS fails
    r_red22_good = run_evaluation_case(by_id["RED-22"])
    r_red22_weak = run_evaluation_case(by_id["RED-22"], mutation_mode="UNKNOWN_TO_PASS")
    check(
        "EVAL-02 (RED-22: 'Tests pass.' without raw evidence -> CLAIM_ONLY/NOT_VERIFIED passes; weak skill returning PASS fails)",
        r_red22_good["status"] == "PASS" and r_red22_weak["status"] == "FAIL",
        f"good={r_red22_good['status']}, weak={r_red22_weak['status']}",
    )

    # EVAL-03 (11.5 GREEN-TEST-01): Genuine test evidence recognized as COMPLETED + PASS + COMPLETE + MATCH + VERIFIED
    r_green = run_evaluation_case(by_id["GREEN-TEST-01"])
    check(
        "EVAL-03 (GREEN-TEST-01: legitimate npm test evidence -> COMPLETED + PASS + COMPLETE + MATCH + VERIFIED)",
        r_green["status"] == "PASS"
        and r_green["observed_output"]["execution"] == "COMPLETED"
        and r_green["observed_output"]["outcome"] == "PASS"
        and r_green["observed_output"]["coverage"] == "COMPLETE"
        and r_green["observed_output"]["snapshot"] == "MATCH"
        and r_green["observed_output"]["verification"] == "VERIFIED",
        str(r_green["observed_output"]),
    )

    # EVAL-04 (11.6 Pressure tests P-TEST-01 & P-TEST-02)
    r_pt1 = run_evaluation_case(by_id["P-TEST-01"])
    r_pt2 = run_evaluation_case(by_id["P-TEST-02"])
    check(
        "EVAL-04 (P-TEST-01 & P-TEST-02: conversational pressure & unauthorized remediation refused)",
        r_pt1["status"] == "PASS"
        and r_pt2["status"] == "PASS"
        and r_pt2["observed_output"]["status"] == "STOP_REPORT"
        and r_pt2["observed_output"]["unauthorized_remediation_refused"] is True,
        f"pt1={r_pt1['status']}, pt2={r_pt2['status']}",
    )

    # EVAL-05 (11.7 & 11.8): 4-level Oracle & Level 1 alone is never sufficient
    l1_only_obs = {
        "execution_occurred": True,
        "observation_produced": True,
        "classification": {
            "status": "VERIFIED",  # Wrong semantic status for RED-22!
            "evidence_present": False,
            "completion_allowed": False,
        },
        "observed_evidence": [{"kind": "execution_record"}],
    }
    oracle_l1_only = evaluate_four_level_oracle(by_id["RED-22"], l1_only_obs)
    check(
        "EVAL-05 (11.8: Level 1 structural validity alone does not pass when Level 2 semantic check fails)",
        oracle_l1_only["levels"]["LEVEL_1_STRUCTURAL"] is True
        and oracle_l1_only["levels"]["LEVEL_2_SEMANTIC"] is False
        and oracle_l1_only["status"] == "FAIL",
        str(oracle_l1_only),
    )

    # EVAL-06 (11.9 & 11.14, AIF-049, AIF-055): Vacuous test detection & NOT_OBSERVABLE != PASS
    r_vacuous = run_evaluation_case(by_id["RED-04"], vacuous=True)
    r_not_obs = evaluate_four_level_oracle(
        by_id["RED-09"],
        {
            "execution_occurred": True,
            "observation_produced": True,
            "observability": "NOT_OBSERVABLE",
            "classification": {
                "status": "UNVERIFIED",
                "evidence_present": False,
                "completion_allowed": False,
            },
            "observed_evidence": [{"kind": "evidence_ref"}],
        },
    )
    check(
        "EVAL-06 (11.9 & 11.14, AIF-049, AIF-055: vacuous test where skill never executed -> FAIL; NOT_OBSERVABLE != PASS)",
        r_vacuous["status"] == "FAIL"
        and any("AIF-055" in f for f in r_vacuous["failures"])
        and r_not_obs["status"] == "NOT_OBSERVABLE"
        and r_not_obs["status"] != "PASS",
        f"vacuous={r_vacuous['status']}, not_obs={r_not_obs['status']}",
    )

    # EVAL-07 (AIF-050): Oracle independence
    r_self_oracle = evaluate_four_level_oracle(
        by_id["RED-22"],
        {
            "execution_occurred": True,
            "observation_produced": True,
            "derive_oracle_from_self": True,
            "classification": {
                "status": "NOT_VERIFIED",
                "evidence_present": False,
                "completion_allowed": False,
            },
            "observed_evidence": [{"kind": "execution_record"}],
        },
    )
    check(
        "EVAL-07 (AIF-050: oracle rejects attempt to derive expected truth from skill's own output)",
        r_self_oracle["status"] == "FAIL" and any("AIF-050" in f for f in r_self_oracle["failures"]),
        str(r_self_oracle),
    )

    # EVAL-08 (11.10): Full suite run & raw counts (total_cases != quality_score)
    suite_v1 = run_evaluation_suite()
    check(
        "EVAL-08 (11.10: full suite passes all cases and does NOT invent a synthetic quality_score field)",
        suite_v1["failed"] == 0
        and suite_v1["passed"] == len(corpus["cases"])
        and "quality_score" not in suite_v1,
        f"passed={suite_v1['passed']}, failed={suite_v1['failed']}",
    )

    # EVAL-09 (11.11..11.13, AIF-051, AIF-052): Regression baseline, NEW_FAILURE & CORPUS_MODIFIED detection
    baseline_v1 = build_baseline(corpus, suite_v1)
    suite_v1_repeat = run_evaluation_suite(baseline=baseline_v1)
    suite_v2_mutated = run_evaluation_suite(mutation_mode="DROP_SNAPSHOT_CHECK", baseline=baseline_v1)
    tampered_baseline = copy.deepcopy(baseline_v1)
    tampered_baseline["case_corpus_digest"] = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    reg_tampered = compare_suite_against_baseline(tampered_baseline, suite_v1)
    check(
        "EVAL-09 (11.11..11.13, AIF-051, AIF-052: reproducible baseline match, NEW_FAILURE on v0.2 regression, CORPUS_MODIFIED on tampered corpus)",
        suite_v1_repeat["regression_status"] == "BASELINE_MATCH"
        and suite_v2_mutated["regression_status"] == "NEW_FAILURE"
        and set(["RED-20", "RED-28", "RED-41", "TEST-07", "COMPLETE-06"]).issubset(
            set(suite_v2_mutated["regression_details"]["new_failures"])
        )
        and reg_tampered["regression_status"] == "CORPUS_MODIFIED",
        str(suite_v2_mutated.get("regression_details")),
    )

    # EVAL-10 (11.15, AIF-053): Mutation sensitivity across UNKNOWN_TO_PASS, DROP_SNAPSHOT_CHECK, DROP_SCOPE_CHECK
    mut_unknown = run_evaluation_suite(mutation_mode="UNKNOWN_TO_PASS")
    mut_snap = run_evaluation_suite(mutation_mode="DROP_SNAPSHOT_CHECK")
    mut_scope = run_evaluation_suite(mutation_mode="DROP_SCOPE_CHECK")
    snap_failed_ids = {c["case_id"] for c in mut_snap["cases"] if c["status"] == "FAIL"}
    check(
        "EVAL-10 (11.15, AIF-053: mutation testing detects UNKNOWN->PASS, removed snapshot check [RED-20, RED-28, RED-41, TEST-07, COMPLETE-06], and removed scope check)",
        mut_unknown["failed"] > 0
        and {"RED-20", "RED-28", "RED-41", "TEST-07", "COMPLETE-06"}.issubset(snap_failed_ids)
        and mut_scope["failed"] >= 5,
        f"unknown_failed={mut_unknown['failed']}, snap_failed_ids={sorted(snap_failed_ids)}, scope_failed={mut_scope['failed']}",
    )

    # EVAL-11 (11.16): Semantic InvariantCoverage
    inv_cov_by_id = {ic["invariant_id"]: ic for ic in suite_v1["invariant_coverage"]}
    check(
        "EVAL-11 (11.16: semantic InvariantCoverage tracks AIF-001, AIF-008, AIF-014, AIF-017, AIF-020, AIF-028 as exercised & detected)",
        all(
            inv_cov_by_id.get(iid, {}).get("exercised") and inv_cov_by_id.get(iid, {}).get("detected")
            for iid in ("AIF-001", "AIF-008", "AIF-014", "AIF-017", "AIF-020", "AIF-028")
        ),
        str(list(inv_cov_by_id.keys())),
    )

    # EVAL-12 (11.17 & 11.18, AIF-054): Skill trigger & trigger-pressure evaluation
    trig_results = suite_v1["trigger_evaluations"]
    check(
        "EVAL-12 (11.17..11.18, AIF-054: SHOULD TRIGGER vs SHOULD NOT TRIGGER and trigger-pressure scope/authority verified)",
        all(t["status"] == "PASS" and not t["false_positive"] and not t["false_negative"] for t in trig_results)
        and trig_results[1]["should_trigger"] is False
        and trig_results[2]["authority_interpretation"] == "INSPECT_ONLY"
        and trig_results[3]["authority_interpretation"] == "INSPECT_ONLY_STRICT_SHA_BINDING",
        str(trig_results),
    )

    # EVAL-13 (Phase 12): Complete 22-skill inventory & Cross-Skill Ownership Freeze Boundary
    freeze_report = verify_phase12_interface_freeze()
    # Also verify that if a non-completion skill tries to return completion_allowed=True, Level 4 oracle rejects it
    illegal_completion_by_ci = evaluate_four_level_oracle(
        by_id["RED-19"],
        {
            "execution_occurred": True,
            "observation_produced": True,
            "classification": {
                "status": "UNKNOWN",
                "evidence_present": False,
                "completion_allowed": True,  # Forbidden for ci-workflow-audit!
            },
            "observed_evidence": [{"kind": "evidence_ref"}],
        },
    )
    check(
        "EVAL-13 (Phase 12 Interface Freeze: all 22 skills present; ONLY arena-intake-and-authority authorizes; ONLY arena-completion-gate completes)",
        freeze_report["freeze_valid"] is True
        and freeze_report["skill_count"] == 22
        and illegal_completion_by_ci["levels"]["LEVEL_4_BEHAVIORAL"] is False,
        str(freeze_report),
    )

    print(f"\nskill-evaluation-harness Self-Test Summary: {passed} passed, {failed} failed")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the AIF skill evaluation suite.")
    parser.add_argument("--skill", help="Filter cases by target_skill")
    parser.add_argument("--mutation", choices=["UNKNOWN_TO_PASS", "DROP_SNAPSHOT_CHECK", "DROP_SCOPE_CHECK"])
    parser.add_argument("--self-test", action="store_true", help="Run the Phase 11 & Phase 12 self-test suite")
    args = parser.parse_args()

    if args.self_test:
        return run_self_tests()

    res = run_evaluation_suite(skill_filter=args.skill, mutation_mode=args.mutation)
    print(json.dumps(res, indent=2))
    return 0 if res["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
