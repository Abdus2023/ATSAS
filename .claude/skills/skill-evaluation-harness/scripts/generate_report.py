#!/usr/bin/env python3
"""
Phase 11 & 12 — skill-evaluation-harness: Report Generator (`generate_report.py`, C-08).

Generates a human-readable or JSON evaluation report from `run_evaluation_suite()`.
Enforces Section 11.10 (`total_cases != quality_score`: raw counts by category
and layer rather than a synthetic percentage) and includes the Phase 12
Cross-Skill Ownership & Interface Freeze summary.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from discover_cases import discover_corpus
from run_suite import (
    build_baseline,
    run_evaluation_suite,
    run_evaluator_attack_corpus,
    verify_phase12_interface_freeze,
)


def format_markdown_report(
    suite_res: Dict[str, Any],
    freeze_res: Dict[str, Any],
    baseline: Dict[str, Any],
    attack_res: Dict[str, Any],
) -> str:
    cat = suite_res.get("raw_category_breakdown", {})
    red_c = cat.get("RED", {"total": 0, "PASS": 0, "FAIL": 0})
    pres_c = cat.get("PRESSURE", {"total": 0, "PASS": 0, "FAIL": 0})
    green_c = cat.get("GREEN", {"total": 0, "PASS": 0, "FAIL": 0})
    detected_attacks = sum(1 for f in attack_res["fixtures"] if f["detected"])

    lines = [
        "AIF SKILL EVALUATION HARNESS REPORT",
        "",
        f"Suite      : {suite_res['suite_id']} v{suite_res['suite_version']} ({suite_res['corpus_id']})",
        f"Evaluator  : skill-evaluation-harness v{suite_res['evaluator_version']}",
        f"Corpus SHA : {suite_res['case_corpus_digest']}",
        f"Oracle SHA : {suite_res['oracle_digest']}",
        f"Baseline   : {baseline['baseline_id']}",
        "",
        "Raw Category Results (total_cases != quality_score):",
        f"  {red_c['total']:2d} RED:      {red_c['PASS']:2d} PASS  {red_c['FAIL']:2d} FAIL",
        f"  {pres_c['total']:2d} PRESSURE: {pres_c['PASS']:2d} PASS  {pres_c['FAIL']:2d} FAIL",
        f"  {green_c['total']:2d} GREEN:    {green_c['PASS']:2d} PASS  {green_c['FAIL']:2d} FAIL",
        f"  Total Cases: {suite_res['passed']} PASS, {suite_res['failed']} FAIL, {suite_res['not_observable']} NOT_OBSERVABLE",
        "",
        f"Phase 15.1 Evaluator Attack Corpus ({attack_res['corpus_id']}):",
        f"  Adversarial Fixtures (EVAL-A049..A055): {detected_attacks}/{attack_res['total_attack_fixtures']} DETECTED",
        "",
        "Phase 12 Interface Freeze Boundary:",
        f"  Skills Verified (22)  : {'PASS' if freeze_res['freeze_valid'] else 'FAIL'} ({freeze_res['skill_count']}/22)",
        f"  Authority Owner       : {', '.join(freeze_res['authority_owners'])}",
        f"  Completion Gate Owner : {', '.join(freeze_res['completion_owners'])}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate AIF skill evaluation report.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    corpus = discover_corpus()
    suite_res = run_evaluation_suite()
    baseline = build_baseline(corpus, suite_res)
    freeze_res = verify_phase12_interface_freeze()
    attack_res = run_evaluator_attack_corpus()

    if args.json:
        print(
            json.dumps(
                {
                    "suite_result": suite_res,
                    "baseline": baseline,
                    "phase12_interface_freeze": freeze_res,
                    "phase15_evaluator_attack_corpus": attack_res,
                },
                indent=2,
            )
        )
    else:
        print(format_markdown_report(suite_res, freeze_res, baseline, attack_res))
    return 0 if (suite_res["failed"] == 0 and freeze_res["freeze_valid"] and attack_res["all_detected"]) else 1


if __name__ == "__main__":
    sys.exit(main())
