#!/usr/bin/env python3
"""
audit_ci_workflow.py — Deterministic Phase 6 CI Workflow & Execution Auditor for
.claude/skills/ci-workflow-audit (Component C-04, AIF-0.1.0).

Answers Q1..Q6 without collapsing into a single CI_PASS boolean and enforces
AIF-028 (CI Subject Binding: VERIFY(C, CI_E) only if Subject(C) == Subject(CI_E)).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


STANDARD_CI_FINDINGS: Tuple[str, ...] = (
    "CI_WORKFLOW_NOT_FOUND",
    "CI_WORKFLOW_CONFIGURED",
    "CI_TRIGGER_NOT_OBSERVED",
    "CI_RUN_FOUND",
    "CI_RUN_IN_PROGRESS",
    "CI_RUN_SUCCESS",
    "CI_RUN_FAILURE",
    "CI_RUN_CANCELLED",
    "CI_RUN_STALE",
    "CI_SNAPSHOT_MISMATCH",
    "CI_WORKFLOW_MISMATCH",
    "CI_JOB_FAILURE",
    "CI_REQUIRED_JOB_MISSING",
    "CI_REQUIRED_STEP_MISSING",
    "CI_ARTIFACT_MISSING",
    "CI_ARTIFACT_MISMATCH",
    "CI_EVIDENCE_INCOMPLETE",
    "CI_PERMISSIONS_BROAD",
    "CI_UNPINNED_ACTION",
    "CI_TRIGGER_POLICY_RISK",
)

FULL_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def is_action_pinned_to_full_sha(uses_ref: str) -> bool:
    if "@" not in uses_ref:
        return False
    _, ref_part = uses_ref.rsplit("@", 1)
    return bool(FULL_SHA_RE.match(ref_part.strip()))


def audit_ci_workflow(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate workflow configuration, trigger policy, action pinning, permissions,
    CIExecutionRecord, artifacts, and claim-specific verification (Q1..Q6).
    """
    repo = payload.get("repository", "streamforge-stremio")
    branch = payload.get("ref", "arena/01a0e9bd-streamforge-stremio")
    target_commit = payload.get("target_commit", "sha-current-b")
    target_snapshot = payload.get("target_snapshot", target_commit)
    working_tree_dirty = payload.get("working_tree_dirty", False)
    current_workflow_sha = payload.get("current_workflow_sha")

    workflows: List[Dict[str, Any]] = payload.get("workflows", [])
    ci_observable: bool = payload.get("ci_observable", True)
    runs: List[Dict[str, Any]] = payload.get("ci_runs", [])
    required_job: Optional[str] = payload.get("required_job")
    required_step: Optional[str] = payload.get("required_step")
    required_artifact: Optional[str] = payload.get("required_artifact")
    repo_trigger_policy_observed: Optional[bool] = payload.get("trigger_policy_observed")

    findings: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    limitations: List[str] = []

    def add_finding(code: str, category: str, proposition: str, extra: Optional[Dict[str, Any]] = None) -> None:
        item: Dict[str, Any] = {
            "finding_id": f"find-ci-{len(findings) + 1:03d}",
            "code": code,
            "category": category,
            "proposition": proposition,
            "remediation_authorized": False,
        }
        if extra:
            item.update(extra)
        findings.append(item)

    # Q1 & Q2: Configuration and Declared Capability
    if not workflows:
        q1_state = "NOT_FOUND"
        add_finding(
            "CI_WORKFLOW_NOT_FOUND",
            "CI_CONFIGURATION",
            "No GitHub Actions workflow files were observed in the inspected branch.",
            {
                "status": "VERIFIED_OBSERVATION",
                "not_implied": [
                    "CI_FAILED",
                    "TESTS_FAILED",
                    "REPOSITORY_UNTESTED",
                    "RELEASE_BLOCKED",
                ],
            },
        )
        return {
            "repository": repo,
            "ref": branch,
            "questions": {
                "Q1_configured": "NOT_FOUND",
                "Q2_declared_capability": [],
                "Q3_triggered": "TRIGGER_NOT_OBSERVED",
                "Q4_subject_match": "UNKNOWN",
                "Q5_run_result": "NOT_FOUND",
                "Q6_claim_verification": {
                    "C1_workflow_succeeded_for_commit": "UNVERIFIED",
                    "C2_required_job_passed_for_commit": "UNVERIFIED",
                    "C3_required_artifact_for_commit": "UNVERIFIED",
                    "C4_repository_has_ci_configured": "UNVERIFIED",
                },
            },
            "ci_state": "NOT_FOUND",
            "subject_match": "UNKNOWN",
            "trigger_policy_state": "TRIGGER_POLICY_UNKNOWN",
            "findings": findings,
            "evidence": evidence,
            "limitations": ["No .github/workflows/ files present in branch"],
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    q1_state = "CONFIGURED"
    declared_capabilities: List[Dict[str, Any]] = []
    trigger_policy_state = (
        "TRIGGER_POLICY_OBSERVED"
        if repo_trigger_policy_observed is True
        else "TRIGGER_POLICY_UNKNOWN"
    )

    for wf in workflows:
        wf_file = wf.get("workflow_file", ".github/workflows/ci.yml")
        wf_name = wf.get("workflow_name", "ci")
        triggers: List[str] = wf.get("triggers", [])
        jobs_decl: List[Dict[str, Any]] = wf.get("jobs", [])
        perms = wf.get("permissions")
        actions_used: List[str] = wf.get("uses", [])

        declared_capabilities.append(
            {
                "workflow_file": wf_file,
                "workflow_name": wf_name,
                "triggers": triggers,
                "jobs": [j.get("name") for j in jobs_decl],
                "trigger_status": "TRIGGER_DECLARED" if triggers else "NONE",
            }
        )
        add_finding(
            "CI_WORKFLOW_CONFIGURED",
            "CI_CONFIGURATION",
            f"Workflow '{wf_name}' ({wf_file}) is configured and declares jobs {[j.get('name') for j in jobs_decl]}.",
        )

        # Section 6.8: Permissions check
        if perms in (None, "write-all", "broad") or (
            isinstance(perms, dict) and perms.get("contents") == "write"
        ):
            add_finding(
                "CI_PERMISSIONS_BROAD",
                "SECURITY_CONFIGURATION_FINDING",
                f"Workflow '{wf_file}' declares broad or default permissions ({perms!r}); security configuration finding, not proof of compromise.",
                {"compromised": False},
            )

        # Section 6.8: Action pinning check
        for act_ref in actions_used:
            if not is_action_pinned_to_full_sha(act_ref):
                add_finding(
                    "CI_UNPINNED_ACTION",
                    "SUPPLY_CHAIN_CONFIGURATION_FINDING",
                    f"Action '{act_ref}' in '{wf_file}' is not pinned to a full 40-character commit SHA (UNPINNED_ACTION != COMPROMISED_ACTION).",
                    {"action": act_ref, "compromised": False},
                )

        # Section 6.9: Trigger security & coverage check
        if "pull_request_target" in triggers:
            add_finding(
                "CI_TRIGGER_POLICY_RISK",
                "SECURITY_CONFIGURATION_FINDING",
                f"Workflow '{wf_file}' declares 'pull_request_target' trigger; requires explicit security boundary review.",
            )
        if triggers == ["workflow_dispatch"]:
            limitations.append(
                f"Workflow '{wf_file}' is triggered by manual workflow_dispatch only; push/PR events are not automatically covered."
            )

    # Check if CI API/observation is unavailable (CI-18)
    if not ci_observable:
        add_finding(
            "CI_EVIDENCE_INCOMPLETE",
            "CI_OBSERVABILITY",
            "CI run status is NOT_OBSERVABLE (API/network unavailable); not classified as CI_FAILED.",
        )
        return {
            "repository": repo,
            "ref": branch,
            "questions": {
                "Q1_configured": q1_state,
                "Q2_declared_capability": declared_capabilities,
                "Q3_triggered": "NOT_OBSERVABLE",
                "Q4_subject_match": "UNKNOWN",
                "Q5_run_result": "NOT_OBSERVABLE",
                "Q6_claim_verification": {
                    "C1_workflow_succeeded_for_commit": "NOT_OBSERVABLE",
                    "C2_required_job_passed_for_commit": "NOT_OBSERVABLE",
                    "C3_required_artifact_for_commit": "NOT_OBSERVABLE",
                    "C4_repository_has_ci_configured": "VERIFIED",
                },
            },
            "ci_state": "NOT_OBSERVABLE",
            "subject_match": "UNKNOWN",
            "trigger_policy_state": trigger_policy_state,
            "findings": findings,
            "evidence": evidence,
            "limitations": limitations + ["CI execution status NOT_OBSERVABLE"],
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # Q3: Was a workflow run actually triggered?
    if not runs:
        add_finding(
            "CI_TRIGGER_NOT_OBSERVED",
            "CI_EXECUTION",
            "Workflow file is configured, but no workflow run was observed.",
        )
        return {
            "repository": repo,
            "ref": branch,
            "questions": {
                "Q1_configured": q1_state,
                "Q2_declared_capability": declared_capabilities,
                "Q3_triggered": "TRIGGER_NOT_OBSERVED",
                "Q4_subject_match": "UNKNOWN",
                "Q5_run_result": "NOT_EXECUTED",
                "Q6_claim_verification": {
                    "C1_workflow_succeeded_for_commit": "UNVERIFIED",
                    "C2_required_job_passed_for_commit": "UNVERIFIED",
                    "C3_required_artifact_for_commit": "UNVERIFIED",
                    "C4_repository_has_ci_configured": "VERIFIED",
                },
            },
            "ci_state": "CONFIGURED",
            "subject_match": "UNKNOWN",
            "trigger_policy_state": trigger_policy_state,
            "findings": findings,
            "evidence": evidence,
            "limitations": limitations,
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # Select latest run attempt (CI-19 rerun handling)
    selected_run = sorted(runs, key=lambda r: int(r.get("run_attempt", 1)))[-1]
    run_id = str(selected_run.get("run_id", "run-001"))
    run_attempt = int(selected_run.get("run_attempt", 1))
    run_status = selected_run.get("status", "COMPLETED")
    run_conclusion = selected_run.get("conclusion", "UNKNOWN")
    run_commit = selected_run.get("commit_sha", "")
    run_wf_sha = selected_run.get("workflow_sha", run_commit)
    run_jobs: List[Dict[str, Any]] = selected_run.get("jobs", [])
    run_artifacts: List[Dict[str, Any]] = selected_run.get("artifacts", [])

    add_finding(
        "CI_RUN_FOUND",
        "CI_EXECUTION",
        f"Observed workflow run '{run_id}' (attempt {run_attempt}) for commit '{run_commit}'.",
    )

    # Emit CI EvidenceRef (Section 6.5)
    ev_id = f"E-CI-{run_id}-ATTEMPT-{run_attempt}"
    evidence.append(
        {
            "evidence_id": ev_id,
            "producer": "ci-workflow-audit",
            "producer_version": "0.1.0",
            "source_type": "CI_RUN",
            "source_locator": f"https://github.com/{repo}/actions/runs/{run_id}/attempts/{run_attempt}",
            "subject_snapshot": run_commit,
            "scope": {
                "repository": repo,
                "workflow": selected_run.get("workflow_name", "ci"),
                "workflow_file": selected_run.get("workflow_file", ".github/workflows/ci.yml"),
                "event": selected_run.get("event", "push"),
                "ref": selected_run.get("ref", branch),
                "commit_sha": run_commit,
                "workflow_sha": run_wf_sha,
                "run_id": run_id,
                "attempt": run_attempt,
                "jobs": [j.get("name") for j in run_jobs],
                "conclusion": run_conclusion,
            },
            "captured_at": selected_run.get("completed_at") or "2026-09-29T12:00:00Z",
            "content_digest": f"sha256:ci.{run_id}.{run_attempt}",
            "provenance": [f"ci:run:{run_id}:attempt:{run_attempt}:sha:{run_commit}"],
        }
    )

    # Q4: Subject Match (AIF-028)
    commit_matches = run_commit == target_commit
    workflow_matches = (current_workflow_sha is None) or (run_wf_sha == current_workflow_sha)

    if not commit_matches:
        subject_match = "MISMATCH"
        add_finding(
            "CI_SNAPSHOT_MISMATCH",
            "CI_SUBJECT_BINDING",
            f"CI run '{run_id}' executed against commit '{run_commit}', which mismatches current target commit '{target_commit}' (AIF-028).",
        )
        add_finding(
            "CI_RUN_STALE",
            "CI_SUBJECT_BINDING",
            f"CI run '{run_id}' for prior commit '{run_commit}' is STALE for current commit '{target_commit}'.",
        )
    elif working_tree_dirty:
        subject_match = "MISMATCH"
        add_finding(
            "CI_RUN_STALE",
            "CI_SUBJECT_BINDING",
            f"CI run '{run_id}' succeeded on commit '{run_commit}', but local working tree was modified afterward ('{target_snapshot}').",
        )
        add_finding(
            "CI_SNAPSHOT_MISMATCH",
            "CI_SUBJECT_BINDING",
            f"Dirty local snapshot '{target_snapshot}' does not match clean CI commit '{run_commit}'.",
        )
    else:
        subject_match = "MATCH"

    if not workflow_matches:
        add_finding(
            "CI_WORKFLOW_MISMATCH",
            "CI_SUBJECT_BINDING",
            f"Workflow file changed after run '{run_id}' (GITHUB_WORKFLOW_SHA='{run_wf_sha}' != current '{current_workflow_sha}').",
        )

    # Q5: Run Lifecycle & Conclusion
    if run_status in ("RUNNING", "IN_PROGRESS", "QUEUED"):
        add_finding(
            "CI_RUN_IN_PROGRESS",
            "CI_EXECUTION",
            f"Workflow run '{run_id}' is still in progress ({run_status}).",
        )
        ci_state = "RUNNING"
        q5_result = "IN_PROGRESS"
    elif run_status == "CANCELLED" or run_conclusion == "CANCELLED":
        add_finding(
            "CI_RUN_CANCELLED",
            "CI_EXECUTION",
            f"Workflow run '{run_id}' was cancelled.",
        )
        ci_state = "CANCELLED"
        q5_result = "CANCELLED"
    else:
        ci_state = "COMPLETED"
        q5_result = run_conclusion
        if run_conclusion == "SUCCESS":
            add_finding(
                "CI_RUN_SUCCESS",
                "CI_EXECUTION",
                f"Workflow run '{run_id}' (attempt {run_attempt}) completed with conclusion SUCCESS on commit '{run_commit}'.",
            )
        elif run_conclusion == "FAILURE":
            add_finding(
                "CI_RUN_FAILURE",
                "CI_EXECUTION",
                f"Workflow run '{run_id}' completed with conclusion FAILURE.",
            )

    # Job & step checks (CI-08, CI-09, CI-10)
    jobs_by_name = {j.get("name"): j for j in run_jobs}
    for j in run_jobs:
        if j.get("conclusion") == "FAILURE":
            add_finding(
                "CI_JOB_FAILURE",
                "CI_EXECUTION",
                f"Job '{j.get('name')}' failed in run '{run_id}'.",
            )

    req_job_ok = True
    if required_job:
        if required_job not in jobs_by_name:
            req_job_ok = False
            add_finding(
                "CI_REQUIRED_JOB_MISSING",
                "CI_EXECUTION",
                f"Required job '{required_job}' was not present or not executed in run '{run_id}'.",
            )
        else:
            rj = jobs_by_name[required_job]
            if rj.get("conclusion") != "SUCCESS":
                req_job_ok = False
            if required_step and required_step not in rj.get("steps", []):
                req_job_ok = False
                add_finding(
                    "CI_REQUIRED_STEP_MISSING",
                    "CI_EXECUTION",
                    f"Required step '{required_step}' was missing from job '{required_job}'.",
                )

    # Artifact checks (Section 6.10, CI-11, CI-12)
    req_artifact_state = "VERIFIED"
    if required_artifact:
        matching_arts = [a for a in run_artifacts if a.get("name") == required_artifact]
        if not matching_arts:
            req_artifact_state = "UNVERIFIED"
            add_finding(
                "CI_ARTIFACT_MISSING",
                "CI_ARTIFACT",
                f"Required artifact '{required_artifact}' was not produced in run '{run_id}'.",
            )
        else:
            art = matching_arts[0]
            if str(art.get("run_id", run_id)) != run_id or art.get("subject_commit", run_commit) != target_commit:
                req_artifact_state = "MISMATCH"
                add_finding(
                    "CI_ARTIFACT_MISMATCH",
                    "CI_ARTIFACT",
                    f"Artifact '{required_artifact}' belongs to run '{art.get('run_id')}' / commit '{art.get('subject_commit')}', mismatching run '{run_id}' / commit '{target_commit}'.",
                )

    # Q6: Claim-specific verification (C1..C4) enforcing AIF-028
    if ci_state == "COMPLETED" and q5_result == "SUCCESS":
        if subject_match == "MATCH" and workflow_matches:
            c1_status = "VERIFIED"
        elif working_tree_dirty:
            c1_status = "STALE"
        elif not commit_matches:
            c1_status = "MISMATCH"
        else:
            c1_status = "UNVERIFIED"
    else:
        c1_status = "UNVERIFIED"

    if c1_status == "VERIFIED" and req_job_ok:
        c2_status = "VERIFIED"
    elif required_job and required_job in jobs_by_name and jobs_by_name[required_job].get("conclusion") == "FAILURE":
        c2_status = "FAILURE"
    else:
        c2_status = "UNVERIFIED"

    if not required_artifact:
        c3_status = c1_status
    elif req_artifact_state == "MISMATCH":
        c3_status = "MISMATCH"
    elif req_artifact_state == "VERIFIED" and c1_status == "VERIFIED":
        c3_status = "VERIFIED"
    else:
        c3_status = "UNVERIFIED"

    return {
        "repository": repo,
        "ref": branch,
        "questions": {
            "Q1_configured": q1_state,
            "Q2_declared_capability": declared_capabilities,
            "Q3_triggered": "TRIGGERED",
            "Q4_subject_match": subject_match,
            "Q5_run_result": q5_result,
            "Q6_claim_verification": {
                "C1_workflow_succeeded_for_commit": c1_status,
                "C2_required_job_passed_for_commit": c2_status,
                "C3_required_artifact_for_commit": c3_status,
                "C4_repository_has_ci_configured": "VERIFIED",
            },
        },
        "ci_state": ci_state,
        "subject_match": subject_match,
        "selected_run_attempt": run_attempt,
        "trigger_policy_state": trigger_policy_state,
        "findings": findings,
        "evidence": evidence,
        "limitations": limitations,
        "mutates_repository": False,
        "authority": False,
        "completion": False,
    }


def run_self_tests() -> int:
    """Execute the 21-case Phase 6 CI test corpus (CI-01..CI-20 + StreamForge NOT_FOUND)."""
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

    base_wf = {
        "workflow_file": ".github/workflows/ci.yml",
        "workflow_name": "ci",
        "triggers": ["push", "pull_request"],
        "permissions": {"contents": "read"},
        "uses": ["actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683"],
        "jobs": [{"name": "test", "steps": ["npm ci", "npm test"]}],
    }

    # CI-01: no workflow directory -> NOT_FOUND
    r01 = audit_ci_workflow({"workflows": []})
    check(
        "CI-01 (no workflow directory -> NOT_FOUND & CI_WORKFLOW_NOT_FOUND)",
        r01["ci_state"] == "NOT_FOUND"
        and r01["questions"]["Q1_configured"] == "NOT_FOUND"
        and any(f["code"] == "CI_WORKFLOW_NOT_FOUND" for f in r01["findings"]),
        str(r01),
    )

    # CI-02: workflow exists -> CONFIGURED
    r02 = audit_ci_workflow({"workflows": [base_wf], "ci_runs": []})
    check(
        "CI-02 (workflow exists -> CONFIGURED & C4_repository_has_ci_configured=VERIFIED)",
        r02["questions"]["Q1_configured"] == "CONFIGURED"
        and r02["questions"]["Q6_claim_verification"]["C4_repository_has_ci_configured"] == "VERIFIED"
        and any(f["code"] == "CI_WORKFLOW_CONFIGURED" for f in r02["findings"]),
        str(r02),
    )

    # CI-03: workflow exists but no run -> TRIGGER_NOT_OBSERVED
    check(
        "CI-03 (workflow exists but no run -> TRIGGER_NOT_OBSERVED & C1=UNVERIFIED)",
        r02["questions"]["Q3_triggered"] == "TRIGGER_NOT_OBSERVED"
        and r02["questions"]["Q6_claim_verification"]["C1_workflow_succeeded_for_commit"] == "UNVERIFIED"
        and any(f["code"] == "CI_TRIGGER_NOT_OBSERVED" for f in r02["findings"]),
        str(r02),
    )

    # CI-04: successful run for current SHA -> VERIFIED for matching claim
    r04 = audit_ci_workflow(
        {
            "target_commit": "sha-S",
            "workflows": [base_wf],
            "ci_runs": [
                {
                    "run_id": "104",
                    "commit_sha": "sha-S",
                    "status": "COMPLETED",
                    "conclusion": "SUCCESS",
                    "jobs": [{"name": "test", "conclusion": "SUCCESS", "steps": ["npm test"]}],
                }
            ],
        }
    )
    check(
        "CI-04 (successful run for current SHA -> SUBJECT_MATCH=MATCH & C1=VERIFIED)",
        r04["subject_match"] == "MATCH"
        and r04["questions"]["Q6_claim_verification"]["C1_workflow_succeeded_for_commit"] == "VERIFIED",
        str(r04),
    )

    # CI-05: successful run for previous SHA -> STALE/MISMATCH (AIF-028)
    r05 = audit_ci_workflow(
        {
            "target_commit": "sha-B",
            "workflows": [base_wf],
            "ci_runs": [
                {
                    "run_id": "105",
                    "commit_sha": "sha-A",
                    "status": "COMPLETED",
                    "conclusion": "SUCCESS",
                    "jobs": [{"name": "test", "conclusion": "SUCCESS"}],
                }
            ],
        }
    )
    check(
        "CI-05 / AIF-028 (successful run on sha-A while HEAD=sha-B -> SUBJECT_MATCH=MISMATCH & C1(B)=MISMATCH/UNVERIFIED)",
        r05["subject_match"] == "MISMATCH"
        and r05["questions"]["Q6_claim_verification"]["C1_workflow_succeeded_for_commit"] == "MISMATCH"
        and any(f["code"] == "CI_SNAPSHOT_MISMATCH" for f in r05["findings"]),
        str(r05),
    )

    # CI-06: run still executing -> IN_PROGRESS
    r06 = audit_ci_workflow(
        {
            "target_commit": "sha-S",
            "workflows": [base_wf],
            "ci_runs": [{"run_id": "106", "commit_sha": "sha-S", "status": "RUNNING", "conclusion": "UNKNOWN"}],
        }
    )
    check(
        "CI-06 (run still executing -> IN_PROGRESS & CI_RUN_IN_PROGRESS)",
        r06["questions"]["Q5_run_result"] == "IN_PROGRESS"
        and any(f["code"] == "CI_RUN_IN_PROGRESS" for f in r06["findings"]),
        str(r06),
    )

    # CI-07: cancelled run -> CANCELLED
    r07 = audit_ci_workflow(
        {
            "target_commit": "sha-S",
            "workflows": [base_wf],
            "ci_runs": [{"run_id": "107", "commit_sha": "sha-S", "status": "CANCELLED", "conclusion": "CANCELLED"}],
        }
    )
    check(
        "CI-07 (cancelled run -> CANCELLED & CI_RUN_CANCELLED)",
        r07["ci_state"] == "CANCELLED"
        and any(f["code"] == "CI_RUN_CANCELLED" for f in r07["findings"]),
        str(r07),
    )

    # CI-08: required job failed -> FAILURE
    r08 = audit_ci_workflow(
        {
            "target_commit": "sha-S",
            "required_job": "test",
            "workflows": [base_wf],
            "ci_runs": [
                {
                    "run_id": "108",
                    "commit_sha": "sha-S",
                    "status": "COMPLETED",
                    "conclusion": "FAILURE",
                    "jobs": [{"name": "test", "conclusion": "FAILURE"}],
                }
            ],
        }
    )
    check(
        "CI-08 (required job failed -> FAILURE & CI_JOB_FAILURE)",
        r08["questions"]["Q6_claim_verification"]["C2_required_job_passed_for_commit"] == "FAILURE"
        and any(f["code"] == "CI_JOB_FAILURE" for f in r08["findings"]),
        str(r08),
    )

    # CI-09: unrelated job passed -> cannot satisfy required-job claim
    r09 = audit_ci_workflow(
        {
            "target_commit": "sha-S",
            "required_job": "test",
            "workflows": [base_wf],
            "ci_runs": [
                {
                    "run_id": "109",
                    "commit_sha": "sha-S",
                    "status": "COMPLETED",
                    "conclusion": "SUCCESS",
                    "jobs": [{"name": "lint", "conclusion": "SUCCESS"}],
                }
            ],
        }
    )
    check(
        "CI-09 (unrelated job 'lint' passed -> C2_required_job_passed_for_commit=UNVERIFIED)",
        r09["questions"]["Q6_claim_verification"]["C2_required_job_passed_for_commit"] == "UNVERIFIED",
        str(r09),
    )

    # CI-10: missing required job -> REQUIRED_JOB_MISSING
    check(
        "CI-10 (missing required job -> CI_REQUIRED_JOB_MISSING finding)",
        any(f["code"] == "CI_REQUIRED_JOB_MISSING" for f in r09["findings"]),
        str(r09),
    )

    # CI-11: artifact absent -> ARTIFACT_MISSING
    r11 = audit_ci_workflow(
        {
            "target_commit": "sha-S",
            "required_artifact": "test-report.xml",
            "workflows": [base_wf],
            "ci_runs": [
                {
                    "run_id": "111",
                    "commit_sha": "sha-S",
                    "status": "COMPLETED",
                    "conclusion": "SUCCESS",
                    "artifacts": [],
                }
            ],
        }
    )
    check(
        "CI-11 (artifact absent -> CI_ARTIFACT_MISSING & C3=UNVERIFIED)",
        r11["questions"]["Q6_claim_verification"]["C3_required_artifact_for_commit"] == "UNVERIFIED"
        and any(f["code"] == "CI_ARTIFACT_MISSING" for f in r11["findings"]),
        str(r11),
    )

    # CI-12: artifact from different run -> MISMATCH
    r12 = audit_ci_workflow(
        {
            "target_commit": "sha-S",
            "required_artifact": "test-report.xml",
            "workflows": [base_wf],
            "ci_runs": [
                {
                    "run_id": "112",
                    "commit_sha": "sha-S",
                    "status": "COMPLETED",
                    "conclusion": "SUCCESS",
                    "artifacts": [
                        {
                            "artifact_id": "art-1",
                            "name": "test-report.xml",
                            "digest": "sha256:art1",
                            "run_id": "999-other-run",
                            "subject_commit": "sha-OLD",
                            "created_at": "2026-09-29T10:00:00Z",
                        }
                    ],
                }
            ],
        }
    )
    check(
        "CI-12 (artifact from different run -> CI_ARTIFACT_MISMATCH & C3=MISMATCH)",
        r12["questions"]["Q6_claim_verification"]["C3_required_artifact_for_commit"] == "MISMATCH"
        and any(f["code"] == "CI_ARTIFACT_MISMATCH" for f in r12["findings"]),
        str(r12),
    )

    # CI-13: workflow changed after run -> CI_WORKFLOW_MISMATCH
    r13 = audit_ci_workflow(
        {
            "target_commit": "sha-S",
            "current_workflow_sha": "wf-sha-NEW",
            "workflows": [base_wf],
            "ci_runs": [
                {
                    "run_id": "113",
                    "commit_sha": "sha-S",
                    "workflow_sha": "wf-sha-OLD",
                    "status": "COMPLETED",
                    "conclusion": "SUCCESS",
                }
            ],
        }
    )
    check(
        "CI-13 (workflow changed after run -> CI_WORKFLOW_MISMATCH & C1=UNVERIFIED)",
        r13["questions"]["Q6_claim_verification"]["C1_workflow_succeeded_for_commit"] == "UNVERIFIED"
        and any(f["code"] == "CI_WORKFLOW_MISMATCH" for f in r13["findings"]),
        str(r13),
    )

    # CI-14: broad permissions -> finding, not compromise
    wf_broad = dict(base_wf, permissions="write-all")
    r14 = audit_ci_workflow({"workflows": [wf_broad], "ci_runs": []})
    check(
        "CI-14 (broad permissions -> CI_PERMISSIONS_BROAD finding with compromised=False)",
        any(f["code"] == "CI_PERMISSIONS_BROAD" and f.get("compromised") is False for f in r14["findings"]),
        str(r14),
    )

    # CI-15: unpinned third-party action -> supply-chain finding
    wf_unpinned = dict(base_wf, uses=["actions/checkout@v6"])
    r15 = audit_ci_workflow({"workflows": [wf_unpinned], "ci_runs": []})
    check(
        "CI-15 (unpinned action actions/checkout@v6 -> CI_UNPINNED_ACTION finding with compromised=False)",
        any(f["code"] == "CI_UNPINNED_ACTION" and f.get("compromised") is False for f in r15["findings"]),
        str(r15),
    )

    # CI-16: pull_request_target -> security review required
    wf_prt = dict(base_wf, triggers=["pull_request_target"])
    r16 = audit_ci_workflow({"workflows": [wf_prt], "ci_runs": []})
    check(
        "CI-16 (pull_request_target -> CI_TRIGGER_POLICY_RISK finding)",
        any(f["code"] == "CI_TRIGGER_POLICY_RISK" for f in r16["findings"]),
        str(r16),
    )

    # CI-17: manual dispatch only -> trigger coverage limited
    wf_manual = dict(base_wf, triggers=["workflow_dispatch"])
    r17 = audit_ci_workflow({"workflows": [wf_manual], "ci_runs": []})
    check(
        "CI-17 (manual workflow_dispatch only -> trigger coverage limitation recorded)",
        any("workflow_dispatch only" in lim for lim in r17["limitations"]),
        str(r17),
    )

    # CI-18: CI unavailable -> NOT_OBSERVABLE, not failure
    r18 = audit_ci_workflow({"workflows": [base_wf], "ci_observable": False})
    check(
        "CI-18 (CI unavailable -> NOT_OBSERVABLE, not failure)",
        r18["ci_state"] == "NOT_OBSERVABLE"
        and r18["questions"]["Q6_claim_verification"]["C1_workflow_succeeded_for_commit"] == "NOT_OBSERVABLE",
        str(r18),
    )

    # CI-19: rerun successful -> bind to correct run attempt
    r19 = audit_ci_workflow(
        {
            "target_commit": "sha-orig",
            "workflows": [base_wf],
            "ci_runs": [
                {"run_id": "119", "run_attempt": 1, "commit_sha": "sha-orig", "status": "COMPLETED", "conclusion": "FAILURE"},
                {"run_id": "119", "run_attempt": 2, "commit_sha": "sha-orig", "status": "COMPLETED", "conclusion": "SUCCESS"},
            ],
        }
    )
    check(
        "CI-19 (rerun successful -> bound to run_attempt=2 and original GITHUB_SHA)",
        r19["selected_run_attempt"] == 2
        and r19["evidence"][0]["scope"]["attempt"] == 2
        and r19["questions"]["Q6_claim_verification"]["C1_workflow_succeeded_for_commit"] == "VERIFIED",
        str(r19),
    )

    # CI-20: CI passes, local tree changed afterward -> old evidence STALE
    r20 = audit_ci_workflow(
        {
            "target_commit": "sha-S",
            "target_snapshot": "sha-S:dirty-worktree",
            "working_tree_dirty": True,
            "workflows": [base_wf],
            "ci_runs": [
                {"run_id": "120", "commit_sha": "sha-S", "status": "COMPLETED", "conclusion": "SUCCESS"},
            ],
        }
    )
    check(
        "CI-20 (CI passes on sha-S, local working tree changed afterward -> C1=STALE & CI_RUN_STALE)",
        r20["questions"]["Q6_claim_verification"]["C1_workflow_succeeded_for_commit"] == "STALE"
        and any(f["code"] == "CI_RUN_STALE" for f in r20["findings"]),
        str(r20),
    )

    # Section 6.13: Current StreamForge branch representation check
    sf_finding = r01["findings"][0]
    check(
        "SEC-6.13 (StreamForge arena/01a0e9bd-streamforge-stremio -> VERIFIED_OBSERVATION, not CI_FAILED/TESTS_FAILED/REPOSITORY_UNTESTED/RELEASE_BLOCKED)",
        sf_finding["category"] == "CI_CONFIGURATION"
        and sf_finding["status"] == "VERIFIED_OBSERVATION"
        and set(sf_finding["not_implied"])
        == {"CI_FAILED", "TESTS_FAILED", "REPOSITORY_UNTESTED", "RELEASE_BLOCKED"},
        str(sf_finding),
    )

    print(f"\nci-workflow-audit Self-Test Summary: {passed} passed, {failed} failed")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit CI workflow configuration, runs, artifacts, and subject binding under AIF-0.1.0."
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to JSON file containing CI audit input.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the 21-case Phase 6 CI test suite (CI-01..CI-20 + StreamForge check).",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_tests()

    if not args.input_path:
        parser.error("Provide an input JSON path or --self-test")

    payload = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
    result = audit_ci_workflow(payload)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
