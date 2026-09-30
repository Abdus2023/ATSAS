#!/usr/bin/env python3
"""
audit_test_execution.py — Deterministic Phase 7 Test Execution & Evidence Auditor for
.claude/skills/test-execution-and-evidence-audit (Component C-05, AIF-0.1.0).

Enforces Sections 7.1-7.18:
  PROCESS_SUCCESS != TEST_SUCCESS != TEST_COMPLETENESS != SEMANTIC_CORRECTNESS
  AIF-029 (Execution Evidence)
  AIF-030 (Discovery Completeness)
  AIF-031 (Test Snapshot Binding)
  AIF-032 (Test Scope Preservation)
  AIF-033 (Test Result Non-Transitivity)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def audit_test_execution(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate TestExecutionRecord[], TestDiscoveryEvidence, ChangeRecord[],
    required_tests / required_test_pattern, 9-criterion adequacy, and claim verification.
    """
    target_snapshot = payload.get("target_snapshot", "S1")
    package_scripts: Dict[str, str] = payload.get(
        "package_scripts",
        {"typecheck": "tsc --noEmit", "test": "tsx --test test/**/*.test.ts"},
    )
    required_tests: List[str] = payload.get("required_tests", [])
    required_test_pattern: Optional[str] = payload.get("required_test_pattern")
    acceptance: Optional[str] = payload.get("acceptance")
    required_set_establishable: bool = payload.get("required_set_establishable", True)
    selected_test_configuration: Optional[str] = payload.get("selected_test_configuration")
    required_test_categories: List[str] = payload.get("required_test_categories", [])
    claim_kind: str = payload.get("claim_kind", "FULL_SUITE")  # FULL_SUITE | SELECTED_SET | TYPECHECK | CORRECTNESS
    post_test_source_changed: bool = payload.get("post_test_source_changed", False)
    unauthorized_test_fix_loop: bool = payload.get("unauthorized_test_fix_loop", False)
    agent_prose_claim_only: bool = payload.get("agent_prose_claim_only", False)

    change_records: List[Dict[str, Any]] = payload.get("change_records", [])
    exec_records: List[Dict[str, Any]] = payload.get("test_execution_records", [])

    findings: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    verifications: List[Dict[str, Any]] = []
    limitations: List[str] = []

    def add_finding(code: str, category: str, proposition: str, invariant: str = "AIF-029") -> None:
        findings.append(
            {
                "finding_id": f"find-test-{len(findings) + 1:03d}",
                "code": code,
                "category": category,
                "invariant": invariant,
                "proposition": proposition,
                "remediation_authorized": False,
            }
        )

    # StreamForge procedure configuration states (Section 7.6)
    procedure_states: List[str] = []
    if "typecheck" in package_scripts:
        procedure_states.append("TYPECHECK_CONFIGURED")
    if "test" in package_scripts:
        procedure_states.append("TEST_CONFIGURED")

    # Section 7.10 & TEST-10, TEST-11, TEST-12, TEST-20: Inspect ChangeRecord[]
    for cr in change_records:
        path = cr.get("path", "")
        attr = cr.get("attribution", "AGENT_ATTRIBUTED")
        change_kind = cr.get("test_change_kind", "")

        if attr == "PREEXISTING":
            # TEST-12: Pre-existing dirty test files must not be attributed to the agent
            add_finding(
                "PREEXISTING_TEST_STATE",
                "TEST_ATTRIBUTION",
                f"Test file '{path}' was pre-existing dirty at S0; not attributed to agent (AIF-024).",
                "AIF-024",
            )
            continue

        if attr == "GENERATED" or cr.get("change_type") == "GENERATED":
            # TEST-20: Generated tests discovered -> preserve generated status
            add_finding(
                "GENERATED_TESTS_OBSERVED",
                "TEST_DISCOVERY",
                f"Generated test file '{path}' observed; generated provenance preserved.",
                "AIF-023",
            )

        if path.startswith("test/") or ".test." in path:
            add_finding(
                "TESTS_MODIFIED",
                "TEST_MUTATION",
                f"Test code '{path}' was modified ({attr}).",
                "AIF-006",
            )
            if change_kind == "ASSERTION" or cr.get("assertions_modified"):
                add_finding(
                    "TEST_ASSERTION_MODIFIED",
                    "TEST_MUTATION",
                    f"Assertions in '{path}' were modified before test execution.",
                    "AIF-006",
                )
        if change_kind == "CONFIG" or path in ("package.json", "tsconfig.json", "vitest.config.ts"):
            add_finding(
                "TEST_CONFIGURATION_MODIFIED",
                "TEST_MUTATION",
                f"Test configuration '{path}' was modified.",
                "AIF-032",
            )
        if change_kind == "DISCOVERY":
            add_finding(
                "TEST_DISCOVERY_MODIFIED",
                "TEST_MUTATION",
                f"Test discovery rules in '{path}' were modified.",
                "AIF-030",
            )

    # P-TEST-02: Unauthorized test-fixing loop (audit -> modify test -> rerun -> completion)
    if unauthorized_test_fix_loop:
        add_finding(
            "UNAUTHORIZED_TEST_FIX_LOOP",
            "TEST_GOVERNANCE",
            "Audit detected failing test and agent modified the test to pass without explicit authorization: STOP and REPORT (P-TEST-02, AIF-010).",
            "AIF-010",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "BLOCKED",
            "action_required": "STOP_AND_REPORT",
            "result": {
                "execution": "COMPLETED",
                "outcome": "UNKNOWN",
                "coverage": "PARTIAL",
                "snapshot": "MATCH",
            },
            "adequacy": "INSUFFICIENT",
            "verification": "NOT_VERIFIED",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # P-TEST-01 / Section 7.8: Agent reports "done" / "All tests passed" without execution record
    if agent_prose_claim_only and not exec_records:
        add_finding(
            "CLAIM_ONLY",
            "TEST_EVIDENCE",
            "Agent reported tests passed without preserving a TestExecutionRecord (CLAIM_ONLY -> NOT_VERIFIED, AIF-029).",
            "AIF-029",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "CLAIM_ONLY",
            "result": {
                "execution": "UNKNOWN",
                "outcome": "UNKNOWN",
                "coverage": "UNKNOWN",
                "snapshot": "UNKNOWN",
            },
            "adequacy": "INSUFFICIENT",
            "verification": "NOT_VERIFIED",
            "findings": findings,
            "evidence": [],
            "verifications": [],
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # Section 7.6: Only package.json configured, no execution observed
    if not exec_records:
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "CONFIGURED",
            "result": {
                "execution": "NOT_STARTED",
                "outcome": "UNKNOWN",
                "coverage": "UNKNOWN",
                "snapshot": "UNKNOWN",
            },
            "adequacy": "INSUFFICIENT",
            "verification": "NOT_VERIFIED",
            "findings": findings,
            "evidence": [],
            "verifications": [],
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # TEST-14: Contradictory reports across runs on same snapshot
    if len(exec_records) >= 2:
        outcomes = {r.get("outcome") or ("PASS" if r.get("exit_code") == 0 else "FAIL") for r in exec_records}
        if "PASS" in outcomes and "FAIL" in outcomes:
            for idx, r in enumerate(exec_records, 1):
                evidence.append(
                    {
                        "evidence_id": f"E-TEST-{idx:03d}",
                        "producer": "test-execution-and-evidence-audit",
                        "producer_version": "0.1.0",
                        "source_type": "COMMAND_OUTPUT",
                        "source_locator": r.get("test_execution_id", f"test-exec-{idx}"),
                        "subject_snapshot": r.get("subject_snapshot", target_snapshot),
                    }
                )
            add_finding(
                "TEST_REPORTS_CONTRADICTED",
                "TEST_EVIDENCE",
                "Contradictory test execution reports observed for the same snapshot (AIF-017).",
                "AIF-017",
            )
            return {
                "target_snapshot": target_snapshot,
                "procedure_states": procedure_states,
                "state": "CONTRADICTED",
                "result": {
                    "execution": "COMPLETED",
                    "outcome": "MIXED",
                    "coverage": "PARTIAL",
                    "snapshot": "MATCH",
                },
                "adequacy": "INSUFFICIENT",
                "verification": "CONTRADICTED",
                "findings": findings,
                "evidence": evidence,
                "verifications": verifications,
                "mutates_repository": False,
                "authority": False,
                "completion": False,
            }

    rec = exec_records[-1]
    tex_id = rec.get("test_execution_id", "tex-001")
    cmd = rec.get("command", "npm test")
    tool = rec.get("tool", "tsx")
    tool_version = rec.get("tool_version", "4.7.0")
    subj_snap = rec.get("subject_snapshot", target_snapshot)
    started_at = rec.get("started_at", "2026-09-29T10:00:00Z")
    ended_at = rec.get("ended_at", "2026-09-29T10:00:05Z")
    exit_code = rec.get("exit_code", 0)
    stdout_ref = rec.get("stdout_ref", "logs/stdout.log")
    stderr_ref = rec.get("stderr_ref", "logs/stderr.log")
    stdout_text = rec.get("stdout_text", "")
    exec_dim = rec.get("execution", "COMPLETED")

    disc = rec.get("discovery") or {}
    discovered = disc.get("discovered", 10)
    selected = disc.get("selected", discovered)
    executed = disc.get("executed", selected)
    skipped = disc.get("skipped", 0)
    filtered = disc.get("filtered", 0)
    failed = disc.get("failed", 0)

    disc_ev = rec.get("discovery_evidence") or {}
    discovered_tests: List[str] = disc_ev.get("discovered_tests", [])
    excluded_tests: List[str] = disc_ev.get("excluded_tests", [])
    filters: List[str] = disc_ev.get("filters", [])

    # TEST-04: Test command unavailable -> NOT_OBSERVABLE
    if exec_dim == "NOT_OBSERVABLE" or rec.get("command_unavailable"):
        add_finding(
            "TEST_COMMAND_NOT_OBSERVABLE",
            "TEST_OBSERVABILITY",
            f"Test command '{cmd}' is unavailable in environment (NOT_OBSERVABLE, AIF-008).",
            "AIF-008",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "NOT_OBSERVABLE",
            "result": {
                "execution": "NOT_STARTED",
                "outcome": "UNKNOWN",
                "coverage": "UNKNOWN",
                "snapshot": "UNKNOWN",
            },
            "adequacy": "NOT_OBSERVABLE",
            "verification": "NOT_OBSERVABLE",
            "findings": findings,
            "evidence": [],
            "verifications": [],
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # TEST-13: Test process killed -> INTERRUPTED, not pass
    if exec_dim == "INTERRUPTED" or rec.get("killed"):
        add_finding(
            "TEST_PROCESS_INTERRUPTED",
            "TEST_EXECUTION",
            f"Test process '{cmd}' was killed/interrupted before completion.",
            "AIF-029",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "INTERRUPTED",
            "result": {
                "execution": "INTERRUPTED",
                "outcome": "UNKNOWN",
                "coverage": "PARTIAL",
                "snapshot": "MATCH" if subj_snap == target_snapshot else "MISMATCH",
            },
            "adequacy": "PARTIAL",
            "verification": "NOT_VERIFIED",
            "findings": findings,
            "evidence": [],
            "verifications": [],
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # Record EvidenceRef for executed command
    if "tsc" in cmd:
        procedure_states.append("TYPECHECK_EXECUTED")
    else:
        procedure_states.append("TEST_EXECUTED")

    evidence.append(
        {
            "evidence_id": f"E-TEST-{tex_id}",
            "producer": "test-execution-and-evidence-audit",
            "producer_version": "0.1.0",
            "source_type": "COMMAND_OUTPUT",
            "source_locator": tex_id,
            "subject_snapshot": subj_snap,
            "scope": {
                "command": cmd,
                "tool": tool,
                "tool_version": tool_version,
                "discovery": disc,
            },
            "content_digest": f"sha256:test.{tex_id}",
            "provenance": [r for r in (stdout_ref, stderr_ref) if r],
        }
    )

    # TEST-05 / Section 7.13: Missing exit_code or missing 9-criterion fields -> partial evidence
    if exit_code is None or not stdout_ref or not tool or not started_at or not ended_at:
        limitations.append("Missing required 9-criterion execution metadata (e.g., exit_code or stdout_ref)")
        add_finding(
            "TEST_EVIDENCE_PARTIAL",
            "TEST_EVIDENCE",
            "One or more of the 9 required evidence criteria (such as exit_code) is missing -> PARTIAL.",
            "AIF-029",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "PARTIAL",
            "result": {
                "execution": "COMPLETED",
                "outcome": "UNKNOWN",
                "coverage": "PARTIAL",
                "snapshot": "MATCH" if subj_snap == target_snapshot else "MISMATCH",
            },
            "adequacy": "PARTIAL",
            "verification": "PARTIAL",
            "limitations": limitations,
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # TEST-16: stdout says pass but exit_code != 0 -> CONTRADICTED
    if exit_code != 0 and "all tests passed" in stdout_text.lower():
        add_finding(
            "TEST_STDOUT_EXIT_CONTRADICTION",
            "TEST_EVIDENCE",
            f"stdout claims 'All tests passed' but exit_code={exit_code} (CONTRADICTED).",
            "AIF-017",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "CONTRADICTED",
            "result": {
                "execution": "COMPLETED",
                "outcome": "FAIL",
                "coverage": "COMPLETE",
                "snapshot": "MATCH" if subj_snap == target_snapshot else "MISMATCH",
            },
            "adequacy": "INSUFFICIENT",
            "verification": "CONTRADICTED",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # TEST-17: exit_code == 0 but runner reports failures -> CONTRADICTED
    if exit_code == 0 and isinstance(failed, int) and failed > 0:
        add_finding(
            "TEST_EXIT_ZERO_WITH_FAILURES",
            "TEST_EVIDENCE",
            f"Process exited 0 but test runner reported failed={failed} (CONTRADICTED, AIF-029).",
            "AIF-029",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "CONTRADICTED",
            "result": {
                "execution": "COMPLETED",
                "outcome": "FAIL",
                "coverage": "COMPLETE",
                "snapshot": "MATCH" if subj_snap == target_snapshot else "MISMATCH",
            },
            "adequacy": "INSUFFICIENT",
            "verification": "CONTRADICTED",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # TEST-01 & P-TEST-03: exit_code == 0, discovered == 0 -> PROCESS_SUCCESS, TEST_VERIFICATION = INSUFFICIENT
    if exit_code == 0 and discovered == 0 and "tsc" not in cmd:
        add_finding(
            "ZERO_TESTS_DISCOVERED",
            "TEST_DISCOVERY",
            "Command exited 0 (PROCESS_SUCCESS) but discovered 0 tests (TEST_VERIFICATION = INSUFFICIENT, AIF-029, AIF-030).",
            "AIF-029",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "process_status": "PROCESS_SUCCESS",
            "state": "DISCOVERED",
            "result": {
                "execution": "COMPLETED",
                "outcome": "UNKNOWN",
                "coverage": "PARTIAL",
                "snapshot": "MATCH" if subj_snap == target_snapshot else "MISMATCH",
            },
            "adequacy": "INSUFFICIENT",
            "verification": "INSUFFICIENT",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # Section 7.14: discovery == "UNKNOWN" -> adequacy = PARTIAL
    if discovered == "UNKNOWN":
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "PARTIAL",
            "result": {
                "execution": "COMPLETED",
                "outcome": "PASS" if exit_code == 0 else "FAIL",
                "coverage": "UNKNOWN",
                "snapshot": "MATCH" if subj_snap == target_snapshot else "MISMATCH",
            },
            "adequacy": "PARTIAL",
            "verification": "PARTIAL",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # Section 7.5: If the required set cannot be established -> UNKNOWN rather than assuming observed set is complete
    if (acceptance == "CLAIM(all_required_tests_pass)" or required_test_pattern) and not required_set_establishable:
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "EXECUTED",
            "result": {
                "execution": "COMPLETED",
                "outcome": "PASS" if exit_code == 0 else "FAIL",
                "coverage": "UNKNOWN",
                "snapshot": "MATCH" if subj_snap == target_snapshot else "MISMATCH",
            },
            "adequacy": "PARTIAL",
            "verification": "UNKNOWN",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # Section 7.11: Test configuration narrowed (e.g. include = test/changed-feature.test.ts) -> PASS for selected test configuration
    if selected_test_configuration:
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "SELECTED",
            "result": {
                "execution": "COMPLETED",
                "outcome": "PASS",
                "coverage": "PARTIAL",
                "snapshot": "MATCH" if subj_snap == target_snapshot else "MISMATCH",
            },
            "adequacy": "PARTIAL",
            "verification": "PARTIAL",
            "verified_claim_scope": "PASS for selected test configuration",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # TEST-07: Tests ran against previous SHA -> MISMATCH
    if subj_snap != target_snapshot and not post_test_source_changed:
        add_finding(
            "TEST_SNAPSHOT_MISMATCH",
            "TEST_SNAPSHOT_BINDING",
            f"Tests executed against snapshot '{subj_snap}', which does not match target '{target_snapshot}' (MISMATCH, AIF-031).",
            "AIF-031",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "MISMATCH",
            "result": {
                "execution": "COMPLETED",
                "outcome": "PASS" if exit_code == 0 else "FAIL",
                "coverage": "COMPLETE",
                "snapshot": "MISMATCH",
            },
            "adequacy": "INSUFFICIENT",
            "verification": "MISMATCH",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # TEST-06 & P-TEST-04: Stale output (TEST(S0) = PASS, SOURCE(S0->S1) = changed -> STALE / UNVERIFIED)
    if post_test_source_changed:
        add_finding(
            "TEST_EVIDENCE_STALE",
            "TEST_SNAPSHOT_BINDING",
            f"Tests passed at '{subj_snap}', then production source changed to '{target_snapshot}' (STALE / UNVERIFIED, AIF-031).",
            "AIF-031",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "STALE",
            "result": {
                "execution": "COMPLETED",
                "outcome": "PASS",
                "coverage": "COMPLETE",
                "snapshot": "MISMATCH",
            },
            "adequacy": "INSUFFICIENT",
            "verification": "UNVERIFIED",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # TEST-18 / Section 7.6 / AIF-033: Only typecheck passes -> TYPECHECK_VERIFIED (not UNIT_TEST_PASS)
    if "tsc" in cmd and "--noEmit" in cmd:
        procedure_states.append("TYPECHECK_VERIFIED")
        if claim_kind == "TYPECHECK":
            return {
                "target_snapshot": target_snapshot,
                "procedure_states": procedure_states,
                "state": "PASSED",
                "result": {
                    "execution": "COMPLETED",
                    "outcome": "PASS",
                    "coverage": "COMPLETE",
                    "snapshot": "MATCH",
                },
                "adequacy": "SUFFICIENT",
                "verification": "VERIFIED",
                "verified_claim_scope": "TYPECHECK_PASS",
                "findings": findings,
                "evidence": evidence,
                "verifications": verifications,
                "mutates_repository": False,
                "authority": False,
                "completion": False,
            }
        add_finding(
            "TYPECHECK_NOT_UNIT_TESTS",
            "TEST_NON_TRANSITIVITY",
            "TYPECHECK_PASS != UNIT_TEST_PASS (AIF-033); typecheck-only execution cannot verify unit test claim.",
            "AIF-033",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "PARTIAL",
            "result": {
                "execution": "COMPLETED",
                "outcome": "PASS",
                "coverage": "PARTIAL",
                "snapshot": "MATCH",
            },
            "adequacy": "PARTIAL",
            "verification": "UNVERIFIED",
            "verified_claim_scope": "TYPECHECK_PASS",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # TEST-19: Integration tests unavailable when [typecheck, unit, integration] required -> PARTIAL
    if "integration" in required_test_categories and rec.get("integration_unavailable"):
        add_finding(
            "INTEGRATION_TESTS_UNAVAILABLE",
            "TEST_COVERAGE",
            "Unit tests passed, but required integration tests are unavailable (UNIT_TEST_PASS != INTEGRATION_TEST_PASS, AIF-033).",
            "AIF-033",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "PARTIAL",
            "result": {
                "execution": "COMPLETED",
                "outcome": "PASS",
                "coverage": "PARTIAL",
                "snapshot": "MATCH",
            },
            "adequacy": "PARTIAL",
            "verification": "PARTIAL",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # TEST-03 & TEST-08: Required test absent from discovered_tests or excluded by filter -> INCOMPLETE
    if required_tests:
        missing_req = [t for t in required_tests if t not in discovered_tests or t in excluded_tests]
        if missing_req:
            add_finding(
                "REQUIRED_TESTS_MISSING_OR_FILTERED",
                "TEST_DISCOVERY",
                f"Required tests {missing_req} were absent from discovery or excluded by filters {filters} (AIF-030, AIF-032).",
                "AIF-030",
            )
            return {
                "target_snapshot": target_snapshot,
                "procedure_states": procedure_states,
                "state": "PARTIAL",
                "result": {
                    "execution": "COMPLETED",
                    "outcome": "PASS",
                    "coverage": "PARTIAL",
                    "snapshot": "MATCH",
                },
                "adequacy": "PARTIAL",
                "verification": "INCOMPLETE",
                "findings": findings,
                "evidence": evidence,
                "verifications": verifications,
                "mutates_repository": False,
                "authority": False,
                "completion": False,
            }

    # TEST-02 & TEST-09: Subset executed (e.g. 10 discovered, 5 executed; or 100 discovered, 20 selected/executed)
    if isinstance(discovered, int) and isinstance(executed, int) and executed < discovered:
        result_dims = {
            "execution": "COMPLETED",
            "outcome": "PASS",
            "coverage": "PARTIAL",
            "snapshot": "MATCH",
        }
        if claim_kind == "SELECTED_SET":
            # TEST-09: All selected tests pass -> selected-set claim only
            return {
                "target_snapshot": target_snapshot,
                "procedure_states": procedure_states,
                "state": "SELECTED",
                "result": result_dims,
                "adequacy": "SUFFICIENT",
                "verification": "VERIFIED",
                "verified_claim_scope": f"{executed} selected tests executed and passed",
                "findings": findings,
                "evidence": evidence,
                "verifications": verifications,
                "mutates_repository": False,
                "authority": False,
                "completion": False,
            }
        add_finding(
            "PARTIAL_TEST_EXECUTION",
            "TEST_COVERAGE",
            f"Discovered {discovered} tests but executed only {executed} (AIF-030, AIF-032).",
            "AIF-032",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states,
            "state": "PARTIAL",
            "result": result_dims,
            "adequacy": "PARTIAL",
            "verification": "PARTIAL",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # Section 7.12 / AIF-033: TEST_PASS != IMPLEMENTATION_CORRECT
    if claim_kind == "CORRECTNESS":
        add_finding(
            "TEST_PASS_NOT_IMPLEMENTATION_CORRECT",
            "TEST_NON_TRANSITIVITY",
            "TEST_PASS != IMPLEMENTATION_CORRECT (AIF-006, AIF-033).",
            "AIF-033",
        )
        return {
            "target_snapshot": target_snapshot,
            "procedure_states": procedure_states + ["TEST_SUITE_VERIFIED"],
            "state": "PASSED",
            "result": {
                "execution": "COMPLETED",
                "outcome": "PASS",
                "coverage": "COMPLETE",
                "snapshot": "MATCH",
            },
            "adequacy": "INSUFFICIENT",
            "verification": "UNVERIFIED",
            "findings": findings,
            "evidence": evidence,
            "verifications": verifications,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # Full required test suite verified at snapshot S
    procedure_states.append("TEST_SUITE_VERIFIED")
    verifications.append(
        {
            "verification_id": f"ver-test-{tex_id}",
            "claim_id": f"TEST_SUITE_PASS({target_snapshot})",
            "result": "VERIFIED",
            "adequacy": "SUFFICIENT",
            "coverage": {
                "subject_match": True,
                "snapshot_match": True,
                "scope_match": True,
                "method_match": True,
                "adequacy": "SUFFICIENT",
            },
        }
    )
    return {
        "target_snapshot": target_snapshot,
        "procedure_states": procedure_states,
        "state": "PASSED",
        "result": {
            "execution": "COMPLETED",
            "outcome": "PASS",
            "coverage": "COMPLETE",
            "snapshot": "MATCH",
        },
        "adequacy": "SUFFICIENT",
        "verification": "VERIFIED",
        "verified_claim_scope": f"The executed tests ({executed}/{discovered}) passed for snapshot {target_snapshot}.",
        "findings": findings,
        "evidence": evidence,
        "verifications": verifications,
        "mutates_repository": False,
        "authority": False,
        "completion": False,
    }


def run_self_tests() -> int:
    """Execute all 20 RED tests (TEST-01..TEST-20), 4 Pressure tests (P-TEST-01..P-TEST-04), and StreamForge check."""
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

    base_rec = {
        "test_execution_id": "tex-1",
        "command": "npm test",
        "tool": "tsx",
        "tool_version": "4.7.0",
        "subject_snapshot": "S1",
        "started_at": "2026-09-29T10:00:00Z",
        "ended_at": "2026-09-29T10:00:04Z",
        "exit_code": 0,
        "discovery": {"discovered": 10, "selected": 10, "executed": 10, "skipped": 0, "filtered": 0, "failed": 0},
        "discovery_evidence": {
            "test_runner": "tsx",
            "command": "tsx --test test/**/*.test.ts",
            "discovery_rules": "test/**/*.test.ts",
            "discovered_tests": [
                "test/auth.test.ts",
                "test/resolver.test.ts",
                "test/ranking.test.ts",
                "test/security.test.ts",
            ],
            "excluded_tests": [],
            "filters": [],
            "subject_snapshot": "S1",
        },
        "stdout_ref": "logs/stdout.log",
        "stderr_ref": "logs/stderr.log",
    }

    # TEST-01: command exits 0, no tests discovered -> not full pass
    r01 = audit_test_execution(
        {"test_execution_records": [dict(base_rec, discovery={"discovered": 0, "selected": 0, "executed": 0})]}
    )
    check(
        "TEST-01 (command exits 0, no tests discovered -> not full pass / INSUFFICIENT)",
        r01["process_status"] == "PROCESS_SUCCESS" and r01["verification"] == "INSUFFICIENT",
        str(r01),
    )

    # TEST-02: 10 tests discovered, 5 executed -> PARTIAL
    r02 = audit_test_execution(
        {"test_execution_records": [dict(base_rec, discovery={"discovered": 10, "selected": 5, "executed": 5})]}
    )
    check(
        "TEST-02 (10 tests discovered, 5 executed -> PARTIAL)",
        r02["state"] == "PARTIAL" and r02["verification"] == "PARTIAL",
        str(r02),
    )

    # TEST-03: required test absent -> INCOMPLETE
    r03 = audit_test_execution(
        {
            "required_tests": ["test/auth.test.ts", "test/missing.test.ts"],
            "test_execution_records": [base_rec],
        }
    )
    check(
        "TEST-03 (required test absent -> INCOMPLETE)",
        r03["verification"] == "INCOMPLETE",
        str(r03),
    )

    # TEST-04: test command unavailable -> NOT_OBSERVABLE
    r04 = audit_test_execution({"test_execution_records": [dict(base_rec, command_unavailable=True)]})
    check(
        "TEST-04 (test command unavailable -> NOT_OBSERVABLE)",
        r04["state"] == "NOT_OBSERVABLE" and r04["verification"] == "NOT_OBSERVABLE",
        str(r04),
    )

    # TEST-05: exit code missing -> partial evidence
    r05 = audit_test_execution({"test_execution_records": [dict(base_rec, exit_code=None)]})
    check(
        "TEST-05 (exit code missing -> partial evidence / PARTIAL)",
        r05["adequacy"] == "PARTIAL" and r05["verification"] == "PARTIAL",
        str(r05),
    )

    # TEST-06: stale output -> STALE
    r06 = audit_test_execution(
        {"target_snapshot": "S1", "post_test_source_changed": True, "test_execution_records": [dict(base_rec, subject_snapshot="S0")]}
    )
    check(
        "TEST-06 (stale output -> STALE)",
        r06["state"] == "STALE" and r06["verification"] == "UNVERIFIED",
        str(r06),
    )

    # TEST-07: tests ran against previous SHA -> MISMATCH
    r07 = audit_test_execution(
        {"target_snapshot": "S1", "test_execution_records": [dict(base_rec, subject_snapshot="S0")]}
    )
    check(
        "TEST-07 (tests ran against previous SHA -> MISMATCH)",
        r07["state"] == "MISMATCH" and r07["result"]["snapshot"] == "MISMATCH",
        str(r07),
    )

    # TEST-08: test filter excludes required tests -> incomplete
    r08_rec = dict(base_rec)
    r08_rec["discovery_evidence"] = dict(
        base_rec["discovery_evidence"],
        excluded_tests=["test/security.test.ts"],
        filters=["--test-name-pattern=resolver"],
    )
    r08 = audit_test_execution(
        {"required_tests": ["test/resolver.test.ts", "test/security.test.ts"], "test_execution_records": [r08_rec]}
    )
    check(
        "TEST-08 (test filter excludes required tests -> INCOMPLETE)",
        r08["verification"] == "INCOMPLETE",
        str(r08),
    )

    # TEST-09: all selected tests pass -> selected-set claim only (COMPLETED + PASS + PARTIAL + MATCH)
    r09 = audit_test_execution(
        {
            "claim_kind": "SELECTED_SET",
            "test_execution_records": [dict(base_rec, discovery={"discovered": 100, "selected": 20, "executed": 20})],
        }
    )
    check(
        "TEST-09 (all selected tests pass -> COMPLETED + PASS + PARTIAL + MATCH & selected-set claim only)",
        r09["result"] == {"execution": "COMPLETED", "outcome": "PASS", "coverage": "PARTIAL", "snapshot": "MATCH"}
        and r09["verification"] == "VERIFIED"
        and "20 selected tests executed" in r09["verified_claim_scope"],
        str(r09),
    )

    # TEST-10: test configuration changed -> finding
    r10 = audit_test_execution(
        {
            "change_records": [{"path": "package.json", "test_change_kind": "CONFIG", "attribution": "AGENT_ATTRIBUTED"}],
            "test_execution_records": [base_rec],
        }
    )
    check(
        "TEST-10 (test configuration changed -> TEST_CONFIGURATION_MODIFIED finding)",
        any(f["code"] == "TEST_CONFIGURATION_MODIFIED" for f in r10["findings"]),
        str(r10),
    )

    # TEST-11: assertions modified before execution -> finding + evidence
    r11 = audit_test_execution(
        {
            "change_records": [
                {"path": "test/resolver.test.ts", "assertions_modified": True, "attribution": "AGENT_ATTRIBUTED"}
            ],
            "test_execution_records": [base_rec],
        }
    )
    check(
        "TEST-11 (assertions modified before execution -> TEST_ASSERTION_MODIFIED finding + evidence retained)",
        any(f["code"] == "TEST_ASSERTION_MODIFIED" for f in r11["findings"]) and len(r11["evidence"]) == 1,
        str(r11),
    )

    # TEST-12: test files pre-existed dirty -> do not attribute to agent
    r12 = audit_test_execution(
        {
            "change_records": [{"path": "test/auth.test.ts", "attribution": "PREEXISTING"}],
            "test_execution_records": [base_rec],
        }
    )
    check(
        "TEST-12 (test files pre-existed dirty -> PREEXISTING_TEST_STATE, not TESTS_MODIFIED)",
        any(f["code"] == "PREEXISTING_TEST_STATE" for f in r12["findings"])
        and not any(f["code"] == "TESTS_MODIFIED" for f in r12["findings"]),
        str(r12),
    )

    # TEST-13: test process killed -> interrupted, not pass
    r13 = audit_test_execution({"test_execution_records": [dict(base_rec, execution="INTERRUPTED", killed=True)]})
    check(
        "TEST-13 (test process killed -> INTERRUPTED, not pass)",
        r13["state"] == "INTERRUPTED" and r13["result"]["execution"] == "INTERRUPTED" and r13["verification"] == "NOT_VERIFIED",
        str(r13),
    )

    # TEST-14: contradictory reports -> CONTRADICTED
    r14 = audit_test_execution(
        {
            "test_execution_records": [
                dict(base_rec, test_execution_id="tex-pass", exit_code=0, outcome="PASS"),
                dict(base_rec, test_execution_id="tex-fail", exit_code=1, outcome="FAIL"),
            ]
        }
    )
    check(
        "TEST-14 (contradictory reports -> CONTRADICTED)",
        r14["state"] == "CONTRADICTED" and r14["verification"] == "CONTRADICTED",
        str(r14),
    )

    # TEST-15: same receipt regenerated -> deterministic result
    r15_a = audit_test_execution({"test_execution_records": [base_rec]})
    r15_b = audit_test_execution({"test_execution_records": [base_rec]})
    check(
        "TEST-15 (same receipt regenerated -> deterministic result)",
        json.dumps(r15_a, sort_keys=True) == json.dumps(r15_b, sort_keys=True),
        "Non-deterministic output",
    )

    # TEST-16: stdout says pass but exit code fails -> contradiction
    r16 = audit_test_execution(
        {"test_execution_records": [dict(base_rec, exit_code=1, stdout_text="All tests passed")]}
    )
    check(
        "TEST-16 (stdout says pass but exit code fails -> CONTRADICTED)",
        r16["state"] == "CONTRADICTED" and r16["verification"] == "CONTRADICTED",
        str(r16),
    )

    # TEST-17: exit 0 but runner reports failures -> contradiction
    r17 = audit_test_execution(
        {
            "test_execution_records": [
                dict(base_rec, exit_code=0, discovery={"discovered": 10, "selected": 10, "executed": 10, "failed": 2})
            ]
        }
    )
    check(
        "TEST-17 (exit 0 but runner reports failures -> CONTRADICTED)",
        r17["state"] == "CONTRADICTED" and r17["verification"] == "CONTRADICTED",
        str(r17),
    )

    # TEST-18: only typecheck passes -> typecheck claim only
    r18_tc = audit_test_execution(
        {"claim_kind": "TYPECHECK", "test_execution_records": [dict(base_rec, command="tsc --noEmit")]}
    )
    r18_unit = audit_test_execution(
        {"claim_kind": "FULL_SUITE", "test_execution_records": [dict(base_rec, command="tsc --noEmit")]}
    )
    check(
        "TEST-18 / AIF-033 (only typecheck passes -> TYPECHECK_VERIFIED for typecheck claim, UNVERIFIED for unit tests)",
        r18_tc["verification"] == "VERIFIED"
        and r18_tc["verified_claim_scope"] == "TYPECHECK_PASS"
        and r18_unit["verification"] == "UNVERIFIED",
        str((r18_tc, r18_unit)),
    )

    # TEST-19: integration tests unavailable -> partial
    r19 = audit_test_execution(
        {
            "required_test_categories": ["typecheck", "unit", "integration"],
            "test_execution_records": [dict(base_rec, integration_unavailable=True)],
        }
    )
    check(
        "TEST-19 (integration tests unavailable -> PARTIAL)",
        r19["state"] == "PARTIAL" and r19["verification"] == "PARTIAL",
        str(r19),
    )

    # TEST-20: generated tests discovered -> generated status preserved
    r20 = audit_test_execution(
        {
            "change_records": [{"path": "test/generated-api.test.ts", "attribution": "GENERATED", "change_type": "GENERATED"}],
            "test_execution_records": [base_rec],
        }
    )
    check(
        "TEST-20 (generated tests discovered -> GENERATED_TESTS_OBSERVED preserved)",
        any(f["code"] == "GENERATED_TESTS_OBSERVED" for f in r20["findings"]),
        str(r20),
    )

    # P-TEST-01: "Just run npm test" -> agent reports done without execution evidence -> NOT_VERIFIED
    p01 = audit_test_execution({"agent_prose_claim_only": True, "test_execution_records": []})
    check(
        "P-TEST-01 ('Just run npm test' -> done without preserving execution evidence -> NOT_VERIFIED)",
        p01["state"] == "CLAIM_ONLY" and p01["verification"] == "NOT_VERIFIED",
        str(p01),
    )

    # P-TEST-02: Test-fixing loop -> failing test -> modifies test until it passes without authorization -> STOP & REPORT
    p02 = audit_test_execution({"unauthorized_test_fix_loop": True, "test_execution_records": [base_rec]})
    check(
        "P-TEST-02 (unauthorized test-fixing loop -> STOP_AND_REPORT)",
        p02["action_required"] == "STOP_AND_REPORT" and p02["verification"] == "NOT_VERIFIED",
        str(p02),
    )

    # P-TEST-03: Empty test suite -> exit 0 with tests discovered = 0 -> PROCESS_SUCCESS + TEST_VERIFICATION = INSUFFICIENT
    p03 = audit_test_execution(
        {"test_execution_records": [dict(base_rec, discovery={"discovered": 0, "selected": 0, "executed": 0})]}
    )
    check(
        "P-TEST-03 (empty test suite -> PROCESS_SUCCESS + TEST_VERIFICATION = INSUFFICIENT)",
        p03["process_status"] == "PROCESS_SUCCESS" and p03["verification"] == "INSUFFICIENT",
        str(p03),
    )

    # P-TEST-04: Current source changed after test -> TEST(S0)=PASS + SOURCE(S0->S1)=changed -> TEST(S1)=UNVERIFIED
    p04 = audit_test_execution(
        {"target_snapshot": "S1", "post_test_source_changed": True, "test_execution_records": [dict(base_rec, subject_snapshot="S0")]}
    )
    check(
        "P-TEST-04 (TEST(S0)=PASS + SOURCE(S0->S1)=changed -> TEST(S1)=UNVERIFIED)",
        p04["verification"] == "UNVERIFIED" and p04["state"] == "STALE",
        str(p04),
    )

    # Section 7.6 StreamForge package.json local procedure check
    sf = audit_test_execution({"test_execution_records": []})
    check(
        "Section 7.6 StreamForge (package.json -> TYPECHECK_CONFIGURED & TEST_CONFIGURED, not EXECUTED or VERIFIED)",
        sf["procedure_states"] == ["TYPECHECK_CONFIGURED", "TEST_CONFIGURED"]
        and sf["state"] == "CONFIGURED"
        and sf["verification"] == "NOT_VERIFIED",
        str(sf),
    )

    # Section 7.5 unestablishable required test set -> UNKNOWN
    s75 = audit_test_execution(
        {
            "acceptance": "CLAIM(all_required_tests_pass)",
            "required_set_establishable": False,
            "test_execution_records": [base_rec],
        }
    )
    check(
        "Section 7.5 (required test set cannot be established -> coverage=UNKNOWN & verification=UNKNOWN)",
        s75["result"]["coverage"] == "UNKNOWN" and s75["verification"] == "UNKNOWN",
        str(s75),
    )

    # Section 7.11 & 7.14 narrowed test configuration + discovery=UNKNOWN
    s711 = audit_test_execution(
        {
            "selected_test_configuration": "include = test/changed-feature.test.ts",
            "test_execution_records": [base_rec],
        }
    )
    s714 = audit_test_execution(
        {
            "test_execution_records": [dict(base_rec, discovery={"discovered": "UNKNOWN", "selected": "UNKNOWN", "executed": "UNKNOWN"})],
        }
    )
    check(
        "Section 7.11 & 7.14 (narrowed test config -> 'PASS for selected test configuration'; discovery=UNKNOWN -> adequacy=PARTIAL)",
        s711["verified_claim_scope"] == "PASS for selected test configuration"
        and s714["adequacy"] == "PARTIAL",
        str((s711, s714)),
    )

    print(f"\ntest-execution-and-evidence-audit Self-Test Summary: {passed} passed, {failed} failed")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit test configuration, discovery, execution, 4D result states, and claim verification under AIF-0.1.0."
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to JSON file containing test execution audit input.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the 25-case Phase 7 test execution & evidence suite (TEST-01..20 + P-TEST-01..04 + StreamForge check).",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_tests()

    if not args.input_path:
        parser.error("Provide an input JSON path or --self-test")

    payload = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
    result = audit_test_execution(payload)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
