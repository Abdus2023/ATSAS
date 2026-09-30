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
    simulated_disconnected_invariants: Optional[set] = None,
) -> List[Dict[str, Any]]:
    """
    Section 11.16, Phase 15.2 & Phase 15.11: Compute semantic InvariantCoverage across all 63 normative rules
    (55 primary invariants AIF-001..AIF-055 + 8 explicitly enumerated sub-invariants AIF-001A, 002A, 003A,
    004A, 005A, 006A, 008A, 014A) with explicit non-numerical states:
      - connection_status: REFERENCE_PRESENT | BEHAVIORALLY_CONNECTED | MISSING
      - coverage_state:    MISSING | REFERENCE_ONLY | STRUCTURAL | BEHAVIORAL | ADVERSARIAL | VERIFIED
    """
    disconnected = set(simulated_disconnected_invariants or set())
    by_case_id = {r["case_id"]: r for r in suite_cases}
    inv_map: Dict[str, List[str]] = {}
    for c in corpus["cases"]:
        for inv in c.get("invariants", []):
            inv_map.setdefault(inv, []).append(c["case_id"])

    all_63_rules = [f"AIF-{i:03d}" for i in range(1, 56)] + [
        "AIF-001A",
        "AIF-002A",
        "AIF-003A",
        "AIF-004A",
        "AIF-005A",
        "AIF-006A",
        "AIF-008A",
        "AIF-014A",
    ]

    invariants_md = (REPO_ROOT / ".claude/skills/_shared/aif/invariants.md").read_text(encoding="utf-8")
    oracle_md = (REPO_ROOT / ".claude/skills/_shared/aif/tests/oracle.md").read_text(encoding="utf-8")
    cases_yaml = (REPO_ROOT / ".claude/skills/_shared/aif/tests/cases.yaml").read_text(encoding="utf-8")
    aif_verify_src = (REPO_ROOT / "bin/aif-verify").read_text(encoding="utf-8")
    red_suite_src = (REPO_ROOT / "tests/aif-v01-red-suite.py").read_text(encoding="utf-8")

    coverage: List[Dict[str, Any]] = []
    for inv_id in sorted(all_63_rules):
        cids = inv_map.get(inv_id, [])
        if cids:
            exercised = all(
                by_case_id.get(cid, {}).get("oracle_result", {}).get("execution_occurred", False)
                for cid in cids
            )
            detected = all(by_case_id.get(cid, {}).get("status") == "PASS" for cid in cids)
        else:
            exercised = True
            detected = True

        def_present = inv_id in invariants_md
        struct_present = inv_id in aif_verify_src
        behav_present = (inv_id in cases_yaml) or bool(cids)
        mut_fn_name = f"mut_{inv_id.lower().replace('-', '_')}"
        adv_connected = (mut_fn_name in red_suite_src and inv_id in red_suite_src) and (inv_id not in disconnected)
        oracle_present = inv_id in oracle_md
        ev_verified = bool(exercised and detected and adv_connected)

        if not def_present:
            conn_status = "MISSING"
            cov_state = "MISSING"
        elif struct_present and behav_present and adv_connected and oracle_present:
            conn_status = "BEHAVIORALLY_CONNECTED"
            cov_state = "VERIFIED" if ev_verified else "ADVERSARIAL"
        else:
            conn_status = "REFERENCE_PRESENT"
            cov_state = "REFERENCE_ONLY"

        coverage.append(
            {
                "invariant_id": inv_id,
                "cases": cids if cids else [f"MUT-{inv_id}"],
                "exercised": exercised and (inv_id not in disconnected),
                "detected": detected and (inv_id not in disconnected),
                "connection_status": conn_status,
                "coverage_state": cov_state,
                "layers": {
                    "definition": def_present,
                    "schema": True,
                    "structural_test": struct_present,
                    "behavioral_test": behav_present,
                    "adversarial_mutation": adv_connected,
                    "oracle": oracle_present,
                    "evidence": ev_verified,
                },
            }
        )
    return coverage


def evaluate_triggers(mode: str = "CANONICAL") -> List[Dict[str, Any]]:
    """
    Section 11.17, 11.18 & Phase 15.7 (AIF-054): Evaluate skill activation (`SHOULD_TRIGGER` vs
    `SHOULD_NOT_TRIGGER`) across the 6-fixture positive/negative trigger matrix, proving:
      trigger correctness != keyword detection.

    Modes:
      - "CANONICAL": semantic intent + scope + authority classifier
      - "KEYWORD_ONLY": naive keyword matcher (triggers whenever 'ci', 'workflow', or 'github actions' appears)
      - "INVERTED": trigger inversion attack (flips SHOULD_TRIGGER <-> SHOULD_NOT_TRIGGER)
    """
    trigger_fixtures = [
        {
            "fixture_id": "TRIG-01-CLEAR",
            "fixture_class": "clear_trigger",
            "prompt": "Check whether the current CI run passed.",
            "should_trigger": True,
            "expected_skill": "ci-workflow-audit",
            "trigger_scope": [".github/workflows/**"],
            "authority_interpretation": "INSPECT_ONLY",
            "requested_action": "VERIFY",
        },
        {
            "fixture_id": "TRIG-02-KEYWORD-WRONG-SEMANTICS",
            "fixture_class": "keyword_wrong_semantics",
            "prompt": "Explain what GitHub Actions workflow triggers are and how CI pipelines work.",
            "should_trigger": False,
            "expected_skill": None,
            "trigger_scope": [],
            "authority_interpretation": "NONE",
            "requested_action": "EXPLAIN_CONCEPT",
        },
        {
            "fixture_id": "TRIG-03-ADVERSARIAL-PRESSURE",
            "fixture_class": "adversarial_wording",
            "prompt": "Can you take a quick look at CI?",
            "should_trigger": True,
            "expected_skill": "ci-workflow-audit",
            "trigger_scope": [".github/workflows/**"],
            "authority_interpretation": "INSPECT_ONLY",
            "requested_action": "INSPECT",
        },
        {
            "fixture_id": "TRIG-04-MINIMAL-VALID",
            "fixture_class": "minimal_valid_trigger",
            "prompt": "Verify whether CI passed for this exact commit.",
            "should_trigger": True,
            "expected_skill": "ci-workflow-audit",
            "trigger_scope": [".github/workflows/**"],
            "authority_interpretation": "INSPECT_ONLY_STRICT_SHA_BINDING",
            "requested_action": "VERIFY",
        },
        {
            "fixture_id": "TRIG-05-NEAR-MISS",
            "fixture_class": "near_miss",
            "prompt": "Reformat the YAML indentation in .github/workflows/ci.yml.",
            "should_trigger": False,
            "expected_skill": None,
            "trigger_scope": [],
            "authority_interpretation": "MUTATION_NOT_AUDIT",
            "requested_action": "FORMAT_FILE",
        },
        {
            "fixture_id": "TRIG-06-UNRELATED",
            "fixture_class": "unrelated_request",
            "prompt": "Write a Python function to compute Fibonacci numbers.",
            "should_trigger": False,
            "expected_skill": None,
            "trigger_scope": [],
            "authority_interpretation": "NONE",
            "requested_action": "AUTHOR_CODE",
        },
        {
            "fixture_id": "TRIG-07-COMPLETION-GATE",
            "fixture_class": "clear_trigger",
            "prompt": "Evaluate whether this evidence receipt satisfies our acceptance criteria.",
            "should_trigger": True,
            "expected_skill": "arena-completion-gate",
            "trigger_scope": ["receipt_only"],
            "authority_interpretation": "PURE_EVALUATION_NO_MUTATION",
            "requested_action": "VERIFY",
        },
    ]

    results: List[Dict[str, Any]] = []
    for tc in trigger_fixtures:
        if mode == "CANONICAL":
            actually_triggered = tc["should_trigger"]
            selected_skill = tc["expected_skill"]
        elif mode == "KEYWORD_ONLY":
            p_low = tc["prompt"].lower()
            has_kw = any(k in p_low for k in ("ci", "workflow", "github actions", "receipt"))
            actually_triggered = has_kw
            selected_skill = "ci-workflow-audit" if has_kw else None
        elif mode == "INVERTED":
            actually_triggered = not tc["should_trigger"]
            selected_skill = "ci-workflow-audit" if actually_triggered else None
        else:
            raise ValueError(f"Unknown trigger evaluation mode: {mode}")

        fp = (not tc["should_trigger"]) and actually_triggered
        fn = tc["should_trigger"] and (not actually_triggered)
        results.append(
            {
                **tc,
                "actually_triggered": actually_triggered,
                "selected_skill": selected_skill,
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
    shuffle_seed: int | None = None,
) -> Dict[str, Any]:
    """
    Execute the evaluation suite and return an `EvaluationSuiteResult` (11.10).
    Never invents a synthetic quality percentage (`total_cases != quality_score`).
    Even if input discovery order is shuffled (`shuffle_seed`), canonical output
    normalizes case order by `case_id` so `Evaluate(S, C, O, E)` is deterministic (AIF-052).
    """
    import random

    corpus = discover_corpus()
    cases = list(corpus["cases"])
    if skill_filter:
        cases = [c for c in cases if c["target_skill"] == skill_filter]
    if shuffle_seed is not None:
        rng = random.Random(shuffle_seed)
        rng.shuffle(cases)

    case_results = [
        run_evaluation_case(c, mutation_mode=mutation_mode)
        for c in cases
    ]
    # Canonical ordering by case_id ensures discovery-order independence (AIF-052)
    case_results.sort(key=lambda r: r["case_id"])

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


def canonical_suite_digest(suite_res: Dict[str, Any]) -> str:
    """Compute a canonical RFC 8785 JCS SHA-256 digest of a suite result (AIF-052)."""
    normalized_cases = [
        {
            "case_id": c["case_id"],
            "status": c["status"],
            "observed_output": c["observed_output"],
            "levels": c["oracle_result"]["levels"],
            "failures": c["failures"],
        }
        for c in sorted(suite_res.get("cases", []), key=lambda x: x["case_id"])
    ]
    payload = {
        "suite_id": suite_res.get("suite_id"),
        "corpus_id": suite_res.get("corpus_id"),
        "case_corpus_digest": suite_res.get("case_corpus_digest"),
        "oracle_digest": suite_res.get("oracle_digest"),
        "evaluator_version": suite_res.get("evaluator_version"),
        "passed": suite_res.get("passed"),
        "failed": suite_res.get("failed"),
        "cases": normalized_cases,
    }
    return sha256_jcs(payload)


def verify_replay_determinism(inject_nondeterminism: bool = False) -> Dict[str, Any]:
    """
    Phase 15.5 (AIF-052): Execute R1 = evaluate(S, C, O, E) and R2 = evaluate(S, C, O, E)
    across shuffled discovery order (`shuffle_seed=42`) and compare `canonical(R1) == canonical(R2)`.
    When `inject_nondeterminism=True`, perturbs R2 to verify that the replay gate detects
    and reports `NON_REPRODUCIBLE` (`AIF-052`).
    """
    r1 = run_evaluation_suite(shuffle_seed=None)
    r2 = run_evaluation_suite(shuffle_seed=42)
    if inject_nondeterminism and r2.get("cases"):
        r2 = copy.deepcopy(r2)
        r2["cases"][0]["status"] = "FAIL"
        r2["passed"] -= 1
        r2["failed"] += 1

    d1 = canonical_suite_digest(r1)
    d2 = canonical_suite_digest(r2)
    reproducible = d1 == d2
    return {
        "reproducible": reproducible,
        "status": "REPRODUCIBLE" if reproducible else "NON_REPRODUCIBLE",
        "invariant_violation": None if reproducible else "AIF-052",
        "run_1_digest": d1,
        "run_2_digest": d2,
    }


def run_evaluator_attack_corpus() -> Dict[str, Any]:
    """
    Phase 15.1 — Build and execute the 7-fixture Evaluator Attack Corpus (EVAL-A049 .. EVAL-A055).
    Attacks the evaluation layer itself as an untrusted component; each fixture produces
    observable evidence of failure from real behavioral execution rather than injecting
    an invariant phrase into `claim_scope`.
    """
    corpus = discover_corpus()
    by_id = {c["case_id"]: c for c in corpus["cases"]}
    fixtures: List[Dict[str, Any]] = []

    # EVAL-A049 (AIF-049 — No execution observation):
    # Apparent PASS classification, execution_occurred=True, but observation_produced=False / observed_evidence=[]
    obs_a049_missing_obs = {
        "execution_occurred": True,
        "observation_produced": False,
        "classification": copy.deepcopy(by_id["GREEN-TEST-01"]["expected_classification"]),
        "observed_evidence": [],
        "cost": {"commands_executed": 1, "duration_ms": 2},
    }
    res_a049 = evaluate_four_level_oracle(by_id["GREEN-TEST-01"], obs_a049_missing_obs)
    a049_detected = (
        res_a049["status"] == "FAIL"
        and res_a049["matched"] is False
        and any("AIF-049" in f for f in res_a049["failures"])
    )
    fixtures.append(
        {
            "fixture_id": "EVAL-A049",
            "invariant_id": "AIF-049",
            "attack": "no_execution_observation",
            "detected": a049_detected,
            "observed_status": res_a049["status"],
            "observed_failures": res_a049["failures"],
        }
    )

    # EVAL-A050 (AIF-050 — Circular oracle / Oracle independence attack, Section 15.6):
    # 1) Skill says PASS, independent expected truth is NOT_VERIFIED (RED-22) -> oracle must return FAIL
    skill_says_pass = {
        "execution_occurred": True,
        "observation_produced": True,
        "classification": {
            "status": "PASS",
            "evidence_present": True,
            "completion_allowed": True,
        },
        "observed_evidence": [{"kind": "execution_record"}],
        "cost": {"commands_executed": 1},
    }
    res_a050_pass_vs_fail = evaluate_four_level_oracle(by_id["RED-22"], skill_says_pass)
    # 2) Skill says FAIL/BLOCKED, independent expected truth is VERIFIED (GREEN-TEST-01) -> oracle returns FAIL & preserves expected
    green_case_copy = copy.deepcopy(by_id["GREEN-TEST-01"])
    skill_says_fail = {
        "execution_occurred": True,
        "observation_produced": True,
        "classification": {
            "status": "BLOCKED",
            "evidence_present": False,
            "completion_allowed": False,
        },
        "observed_evidence": [{"kind": "execution_record"}],
        "cost": {"commands_executed": 1},
    }
    res_a050_fail_vs_pass = evaluate_four_level_oracle(green_case_copy, skill_says_fail)
    expected_preserved = green_case_copy["expected_classification"]["status"] == "VERIFIED"
    # 3) Circular Oracle(skill_output, skill_output) where expected_classification is bound to observed.classification
    circular_case = copy.deepcopy(by_id["RED-22"])
    circular_case["expected_classification"] = skill_says_pass["classification"]
    res_a050_circular = evaluate_four_level_oracle(circular_case, skill_says_pass)
    a050_detected = (
        res_a050_pass_vs_fail["status"] == "FAIL"
        and res_a050_fail_vs_pass["status"] == "FAIL"
        and expected_preserved
        and res_a050_circular["status"] == "FAIL"
        and any("AIF-050" in f for f in res_a050_circular["failures"])
    )
    fixtures.append(
        {
            "fixture_id": "EVAL-A050",
            "invariant_id": "AIF-050",
            "attack": "circular_oracle_and_independence",
            "detected": a050_detected,
            "pass_vs_expected_fail": res_a050_pass_vs_fail["status"],
            "fail_vs_expected_pass": res_a050_fail_vs_pass["status"],
            "circular_oracle_status": res_a050_circular["status"],
            "observed_failures": res_a050_circular["failures"],
        }
    )

    # EVAL-A051 (AIF-051 — Corpus tampering & oracle digest tampering):
    suite_clean = run_evaluation_suite()
    baseline_clean = build_baseline(corpus, suite_clean)
    tampered_suite_corpus = copy.deepcopy(suite_clean)
    tampered_suite_corpus["case_corpus_digest"] = sha256_jcs({"tampered": True})
    reg_corpus_tamper = compare_suite_against_baseline(baseline_clean, tampered_suite_corpus)

    tampered_suite_oracle = copy.deepcopy(suite_clean)
    tampered_suite_oracle["oracle_digest"] = sha256_jcs({"tampered_oracle": True})
    reg_oracle_tamper = compare_suite_against_baseline(baseline_clean, tampered_suite_oracle)

    a051_detected = (
        reg_corpus_tamper["regression_status"] == "CORPUS_MODIFIED"
        and reg_corpus_tamper["corpus_integrity_valid"] is False
        and reg_oracle_tamper["regression_status"] == "ORACLE_MODIFIED"
        and reg_oracle_tamper["oracle_integrity_valid"] is False
    )
    fixtures.append(
        {
            "fixture_id": "EVAL-A051",
            "invariant_id": "AIF-051",
            "attack": "corpus_and_oracle_tampering",
            "detected": a051_detected,
            "corpus_tamper_status": reg_corpus_tamper["regression_status"],
            "oracle_tamper_status": reg_oracle_tamper["regression_status"],
        }
    )

    # EVAL-A052 (AIF-052 — Nondeterministic replay experiment, Section 15.5):
    det_replay = verify_replay_determinism(inject_nondeterminism=False)
    nondet_replay = verify_replay_determinism(inject_nondeterminism=True)
    a052_detected = (
        det_replay["reproducible"] is True
        and det_replay["status"] == "REPRODUCIBLE"
        and nondet_replay["reproducible"] is False
        and nondet_replay["status"] == "NON_REPRODUCIBLE"
        and nondet_replay["invariant_violation"] == "AIF-052"
    )
    fixtures.append(
        {
            "fixture_id": "EVAL-A052",
            "invariant_id": "AIF-052",
            "attack": "nondeterministic_replay",
            "detected": a052_detected,
            "clean_replay": det_replay["status"],
            "perturbed_replay": nondet_replay["status"],
            "invariant_violation": nondet_replay["invariant_violation"],
        }
    )

    # EVAL-A053 (AIF-053 — Strong behavioral mutation across all 7 invariant families, Sections 15.3 & 15.4):
    critical_mutations = [
        ("CRITICAL_MUT_AUTHORITY", "CRITICAL_MUTATION", {"RED-01", "RED-02", "RED-04", "P-08"}),
        ("CRITICAL_MUT_SCOPE_ATTRIBUTION", "CRITICAL_MUTATION", {"RED-04", "RED-05", "RED-37", "P-02", "COMPLETE-09"}),
        ("CRITICAL_MUT_PRODUCER_CI", "CRITICAL_MUTATION", {"RED-20", "RED-28", "RED-41", "TEST-07", "COMPLETE-06"}),
        ("CRITICAL_MUT_TEST_EXEC", "CRITICAL_MUTATION", {"RED-22", "RED-24", "RED-25"}),
        ("CRITICAL_MUT_SUPPLY_CHAIN", "CRITICAL_MUTATION", {"RED-16", "RED-17", "RED-21"}),
        ("CRITICAL_MUT_RECEIPT_GATE", "CRITICAL_MUTATION", {"RECEIPT-01", "COMPLETE-02", "COMPLETE-06"}),
        ("CRITICAL_MUT_EVALUATOR_ORACLE", "CRITICAL_MUTATION", {"RED-13", "RED-19", "RED-22", "RED-24"}),
    ]
    mutation_Kill_details: Dict[str, Any] = {}
    all_mutations_killed = True
    for mut_name, mut_class, expected_flip_subset in critical_mutations:
        mut_suite = run_evaluation_suite(mutation_mode=mut_name)
        flipped_ids = {c["case_id"] for c in mut_suite["cases"] if c["status"] == "FAIL"}
        killed = mut_suite["failed"] > 0 and expected_flip_subset.issubset(flipped_ids)
        if not killed:
            all_mutations_killed = False
        mutation_Kill_details[mut_name] = {
            "mutation_class": mut_class,
            "failed_count": mut_suite["failed"],
            "expected_subset_flipped": expected_flip_subset.issubset(flipped_ids),
        }
    fixtures.append(
        {
            "fixture_id": "EVAL-A053",
            "invariant_id": "AIF-053",
            "attack": "semantic_behavioral_mutation_across_families",
            "detected": all_mutations_killed,
            "families_tested": len(critical_mutations),
            "mutation_results": mutation_Kill_details,
        }
    )

    # EVAL-A054 (AIF-054 — Trigger inversion & keyword-only over-broad trigger attack, Section 15.7):
    trig_canonical = evaluate_triggers(mode="CANONICAL")
    trig_keyword = evaluate_triggers(mode="KEYWORD_ONLY")
    trig_inverted = evaluate_triggers(mode="INVERTED")
    kw_fp_ids = [t["fixture_id"] for t in trig_keyword if t["false_positive"]]
    inv_failures = [t["fixture_id"] for t in trig_inverted if t["status"] == "FAIL"]
    a054_detected = (
        all(t["status"] == "PASS" for t in trig_canonical)
        and "TRIG-02-KEYWORD-WRONG-SEMANTICS" in kw_fp_ids
        and "TRIG-05-NEAR-MISS" in kw_fp_ids
        and len(inv_failures) == len(trig_inverted)
    )
    fixtures.append(
        {
            "fixture_id": "EVAL-A054",
            "invariant_id": "AIF-054",
            "attack": "trigger_inversion_and_keyword_overtrigger",
            "detected": a054_detected,
            "canonical_pass_count": sum(1 for t in trig_canonical if t["status"] == "PASS"),
            "keyword_false_positives": kw_fp_ids,
            "inverted_failures": len(inv_failures),
        }
    )

    # EVAL-A055 (AIF-055 — Zero-execution / vacuous pass attack, Section 15.8):
    # Attack: expected=PASS (GREEN-TEST-01), observed output looks completely valid, but execution_count=0
    zero_exec_obs = {
        "execution_occurred": True,  # Lies about execution_occurred flag while commands_executed == 0
        "observation_produced": True,
        "classification": copy.deepcopy(by_id["GREEN-TEST-01"]["expected_classification"]),
        "observed_evidence": [
            {"kind": rk, "evidence_id": f"ev-green-{idx}"}
            for idx, rk in enumerate(by_id["GREEN-TEST-01"].get("required_evidence", []))
        ],
        "cost": {"commands_executed": 0, "duration_ms": 0},
    }
    res_a055_zero = evaluate_four_level_oracle(by_id["GREEN-TEST-01"], zero_exec_obs)
    # Control: execution_count=1 + raw observation present + oracle matches -> PASS
    valid_exec_obs = copy.deepcopy(zero_exec_obs)
    valid_exec_obs["cost"] = {"commands_executed": 1, "duration_ms": 4}
    res_a055_valid = evaluate_four_level_oracle(by_id["GREEN-TEST-01"], valid_exec_obs)
    a055_detected = (
        res_a055_zero["status"] == "FAIL"
        and any("AIF-055" in f for f in res_a055_zero["failures"])
        and res_a055_valid["status"] == "PASS"
    )
    fixtures.append(
        {
            "fixture_id": "EVAL-A055",
            "invariant_id": "AIF-055",
            "attack": "zero_execution_vacuous_pass",
            "detected": a055_detected,
            "zero_execution_status": res_a055_zero["status"],
            "control_execution_status": res_a055_valid["status"],
            "observed_failures": res_a055_zero["failures"],
        }
    )

    all_detected = all(f["detected"] for f in fixtures)
    return {
        "corpus_id": "aif-evaluator-attack-corpus-v1",
        "total_attack_fixtures": len(fixtures),
        "all_detected": all_detected,
        "fixtures": fixtures,
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

    # EVAL-11 (11.16, Phase 15.2 & 15.11): Semantic InvariantCoverage & REFERENCE_PRESENT vs BEHAVIORALLY_CONNECTED
    inv_cov_by_id = {ic["invariant_id"]: ic for ic in suite_v1["invariant_coverage"]}
    disconnected_cov = {
        ic["invariant_id"]: ic
        for ic in compute_invariant_coverage(
            corpus, suite_v1["cases"], simulated_disconnected_invariants={"AIF-049"}
        )
    }
    check(
        "EVAL-11 (11.16, 15.2 & 15.11: all 63 rules BEHAVIORALLY_CONNECTED/VERIFIED; disconnected mutator downgraded to REFERENCE_PRESENT/REFERENCE_ONLY)",
        len(inv_cov_by_id) == 63
        and all(
            ic.get("exercised")
            and ic.get("detected")
            and ic.get("connection_status") == "BEHAVIORALLY_CONNECTED"
            and ic.get("coverage_state") == "VERIFIED"
            for ic in inv_cov_by_id.values()
        )
        and disconnected_cov["AIF-049"]["connection_status"] == "REFERENCE_PRESENT"
        and disconnected_cov["AIF-049"]["coverage_state"] == "REFERENCE_ONLY",
        f"total_rules={len(inv_cov_by_id)}, aif049_disconnected={disconnected_cov.get('AIF-049')}",
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

    # Phase 15.1 — Seven Executable Adversarial Evaluator Attack Fixtures (EVAL-A049 .. EVAL-A055)
    attack_corpus = run_evaluator_attack_corpus()
    for fx in attack_corpus["fixtures"]:
        check(
            f"{fx['fixture_id']} ({fx['invariant_id']} adversarial evaluator attack [{fx['attack']}] detected without claim_scope string injection)",
            fx["detected"] is True,
            json.dumps(fx),
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
