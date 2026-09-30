#!/usr/bin/env python3
"""
audit_change_scope.py — Deterministic Phase 4 Change Scope & Provenance Auditor for
.claude/skills/agent-change-scope-audit (Component C-02, AIF-0.1.0).

Enforces:
  STATE_CHANGE != AGENT_CHANGE != AUTHORIZED_CHANGE
  UNAUTHORIZED_AGENT_CHANGE <=> AGENT_ATTRIBUTED_CHANGE AND NOT IN_AUTHORIZED_SCOPE
  AIF-023 (Attribution is evidence-dependent)
  AIF-024 (Pre-existing state is not agent responsibility)
  AIF-025 (Scope audit is snapshot-relative)
  AIF-010 (Audit must not repair or mutate repository)
"""

from __future__ import annotations

import argparse
import fnmatch
import importlib.machinery
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[4]
CHANGE_RECORD_SCHEMA_PATH = (
    REPO_ROOT / ".claude" / "skills" / "_shared" / "aif" / "schema" / "change-record.schema.json"
)


def is_unresolvable_pattern(pat: str, matcher_available: bool = True) -> bool:
    if not matcher_available and "**" in pat:
        return True
    return pat.startswith("UNRESOLVABLE:") or "{{" in pat


def evaluate_path_scope(
    path: str,
    admitted_paths: List[str],
    excluded_paths: List[str],
    is_generated: bool = False,
    matcher_available: bool = True,
) -> str:
    """
    Evaluate whether `path` is IN_SCOPE, OUT_OF_SCOPE, or UNKNOWN.
    Never collapses UNKNOWN into OUT_OF_SCOPE (Section 8).
    """
    for pat in admitted_paths + excluded_paths:
        if is_unresolvable_pattern(pat, matcher_available):
            return "UNKNOWN"

    def matches_any(target: str, patterns: List[str]) -> bool:
        for pat in patterns:
            if pat == target or pat == "**/*":
                return True
            if pat.endswith("/**"):
                prefix = pat[:-3]
                if target == prefix or target.startswith(prefix + "/"):
                    return True
            if fnmatch.fnmatch(target, pat):
                return True
        return False

    if is_generated and not matches_any(path, admitted_paths) and not matches_any(path, excluded_paths):
        return "UNKNOWN"

    if matches_any(path, excluded_paths):
        return "OUT_OF_SCOPE"
    if matches_any(path, admitted_paths):
        return "IN_SCOPE"
    return "OUT_OF_SCOPE"


def audit_change_scope(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Consume intake_snapshot (S0), execution_snapshot (S1), optional current_snapshot (S2),
    AdmissionRecord, repository_state, and ExecutionRecord[] to produce:
      ChangeRecord[], Finding[], EvidenceRef[], result summary, and verification.scope_claim.
    """
    s0_raw = payload.get("intake_snapshot", {"snapshot_id": "S0"})
    s1_raw = payload.get("execution_snapshot", {"snapshot_id": "S1"})
    s2_raw = payload.get("current_snapshot")

    s0_id = s0_raw.get("snapshot_id", "S0") if isinstance(s0_raw, dict) else str(s0_raw)
    s1_id = s1_raw.get("snapshot_id", "S1") if isinstance(s1_raw, dict) else str(s1_raw)
    s2_id = (
        (s2_raw.get("snapshot_id") if isinstance(s2_raw, dict) else str(s2_raw))
        if s2_raw is not None
        else s1_id
    )

    comparison = f"{s0_id} -> {s1_id}"
    is_stale_snapshot = s2_id != s1_id

    admission = payload.get("admission_record", {})
    admitted_paths: List[str] = admission.get("admitted_paths", [])
    excluded_paths: List[str] = admission.get("excluded_paths", [])
    matcher_available: bool = payload.get("matcher_available", True)

    exec_records: List[Dict[str, Any]] = payload.get("execution_records", [])
    external_events: List[Dict[str, Any]] = payload.get("external_events", [])
    observed_files: List[Dict[str, Any]] = payload.get("observed_files", [])

    # Emit canonical scope audit EvidenceRefs (Section 17)
    ev_s0_id = "E-SCOPE-001"
    ev_s1_id = "E-SCOPE-002"
    evidence: List[Dict[str, Any]] = [
        {
            "evidence_id": ev_s0_id,
            "producer": "agent-change-scope-audit",
            "producer_version": "0.1.0",
            "source_type": "GIT_OBJECT",
            "source_locator": f"git:tree:{s0_id}",
            "captured_at": "2026-09-29T12:00:00Z",
            "subject_snapshot": s0_id,
            "scope": admitted_paths or ["**/*"],
            "content_digest": f"sha256:scope.{s0_id}",
            "claim_scope": f"Baseline repository tree and working-tree state captured at intake snapshot {s0_id}.",
            "provenance": [f"git:snapshot:{s0_id}"],
        },
        {
            "evidence_id": ev_s1_id,
            "producer": "agent-change-scope-audit",
            "producer_version": "0.1.0",
            "source_type": "GIT_OBJECT",
            "source_locator": f"git:tree:{s1_id}",
            "captured_at": "2026-09-29T12:05:00Z",
            "subject_snapshot": s1_id,
            "scope": admitted_paths or ["**/*"],
            "content_digest": f"sha256:scope.{s1_id}",
            "claim_scope": f"Post-execution repository tree and working-tree state captured at execution snapshot {s1_id}.",
            "provenance": [f"git:snapshot:{s1_id}"],
        },
    ]

    # Index agent execution records and build commands by path
    agent_exec_by_path: Dict[str, List[str]] = {}
    generated_by_path: Dict[str, Tuple[str, str]] = {}
    for ex in exec_records:
        ex_id = ex.get("execution_id", "E-EXEC-001")
        cmd = ex.get("command", "")
        for p in ex.get("touched_paths", []):
            agent_exec_by_path.setdefault(p, []).append(ex_id)
        for gp in ex.get("generated_paths", []):
            generated_by_path[gp] = (ex_id, cmd or "build command")

    external_by_path: Dict[str, List[str]] = {}
    for ext in external_events:
        ext_id = ext.get("event_id", "EXT-001")
        for p in ext.get("touched_paths", []):
            external_by_path.setdefault(p, []).append(ext_id)

    change_records: List[Dict[str, Any]] = []
    findings: List[Dict[str, Any]] = []

    in_scope_count = 0
    out_of_scope_count = 0
    generated_count = 0
    attribution_unknown_count = 0
    has_unauthorized_agent_change = False

    for f_entry in observed_files:
        path = f_entry["path"]
        intake_state = f_entry.get("intake_state", "CLEAN")
        execution_state = f_entry.get("execution_state", "DIRTY")
        before_digest = f_entry.get("before_digest", "sha256:before")
        after_digest = f_entry.get("after_digest", "sha256:after")
        raw_change_type = f_entry.get("change_type", "MODIFIED")
        interleaved_external = f_entry.get("interleaved_external", False)

        # Determine attribution & attribution_basis (Sections 4, 5, 6, 7, 12, 13, 15)
        is_generated = path in generated_by_path or f_entry.get("generated", False)
        generated_by: Optional[str] = None
        attribution: str
        attribution_basis: List[str]

        if intake_state == "DIRTY" and before_digest == after_digest:
            # Section 4 & 13 (AIF-024, RED-38): Dirty at S0, unchanged in S0 -> S1
            attribution = "PREEXISTING"
            attribution_basis = [f"GIT_OBJECT:{ev_s0_id}", f"GIT_OBJECT:{ev_s1_id}"]
        elif is_generated:
            # Section 7 (RED-39): Generated by build command
            attribution = "GENERATED"
            if path in generated_by_path:
                gen_ex_id, gen_cmd = generated_by_path[path]
                generated_by = gen_cmd
                attribution_basis = [f"EXECUTION_RECORD:{gen_ex_id}", f"GIT_OBJECT:{ev_s1_id}"]
            else:
                generated_by = f_entry.get("generated_by") or "build command"
                attribution_basis = [f"BUILD_OUTPUT:{generated_by}", f"GIT_OBJECT:{ev_s1_id}"]
            raw_change_type = "GENERATED"
        elif path in agent_exec_by_path and not interleaved_external and path not in external_by_path:
            # Section 6: Execution record + snapshot diff supports AGENT_ATTRIBUTED
            attribution = "AGENT_ATTRIBUTED"
            attribution_basis = [
                f"EXECUTION_RECORD:{ex_id}" for ex_id in agent_exec_by_path[path]
            ] + [f"GIT_OBJECT:{ev_s1_id}"]
        elif path in external_by_path and path not in agent_exec_by_path:
            # Section 15 (RED-40): Sufficient external event evidence & no agent action
            attribution = "EXTERNAL_ATTRIBUTED"
            attribution_basis = [
                f"EXTERNAL_EVENT:{ext_id}" for ext_id in external_by_path[path]
            ] + [f"GIT_OBJECT:{ev_s1_id}"]
        else:
            # Section 5 & 12 (AIF-023, RED-37): State transition without sufficient actor causality
            attribution = "UNKNOWN"
            attribution_basis = [f"GIT_OBJECT:{ev_s0_id}", f"GIT_OBJECT:{ev_s1_id}"]

        scope = evaluate_path_scope(
            path=path,
            admitted_paths=admitted_paths,
            excluded_paths=excluded_paths,
            is_generated=(attribution == "GENERATED"),
            matcher_available=matcher_available,
        )

        # Formal rule (Section 11):
        # UNAUTHORIZED_AGENT_CHANGE iff AGENT_ATTRIBUTED_CHANGE AND NOT IN_AUTHORIZED_SCOPE
        if attribution == "AGENT_ATTRIBUTED":
            if scope == "IN_SCOPE":
                authority = "AUTHORIZED"
            elif scope == "OUT_OF_SCOPE":
                authority = "UNAUTHORIZED"
                has_unauthorized_agent_change = True
            else:
                authority = "UNKNOWN"
        elif attribution in ("PREEXISTING", "GENERATED"):
            authority = "AUTHORIZED"
        elif attribution == "EXTERNAL_ATTRIBUTED":
            authority = "UNKNOWN"
        else:
            authority = "UNKNOWN"

        if scope == "IN_SCOPE":
            in_scope_count += 1
        elif scope == "OUT_OF_SCOPE":
            out_of_scope_count += 1
        if attribution == "GENERATED":
            generated_count += 1
        if attribution == "UNKNOWN":
            attribution_unknown_count += 1

        # Record findings per Section 10, 16, 18
        if attribution == "AGENT_ATTRIBUTED" and scope == "OUT_OF_SCOPE":
            findings.append(
                {
                    "finding_id": f"find-oos-agent-{len(findings) + 1}",
                    "code": "OUT_OF_SCOPE_AGENT_CHANGE",
                    "invariant": "AIF-003",
                    "path": path,
                    "attribution": attribution,
                    "remediation_authorized": False,
                    "message": f"Agent-attributed change on '{path}' is outside admitted scope {admitted_paths}.",
                }
            )
        elif attribution == "PREEXISTING" and scope == "OUT_OF_SCOPE":
            findings.append(
                {
                    "finding_id": f"find-oos-preexisting-{len(findings) + 1}",
                    "code": "OUT_OF_SCOPE_PREEXISTING_CHANGE",
                    "invariant": "AIF-024",
                    "path": path,
                    "attribution": attribution,
                    "remediation_authorized": False,
                    "message": f"Path '{path}' was already dirty at intake snapshot {s0_id} (PREEXISTING) and is not an agent violation.",
                }
            )
        elif attribution in ("UNKNOWN", "EXTERNAL_ATTRIBUTED") and scope == "OUT_OF_SCOPE":
            findings.append(
                {
                    "finding_id": f"find-oos-uncertain-{len(findings) + 1}",
                    "code": "OUT_OF_SCOPE_CHANGE",
                    "invariant": "AIF-023",
                    "path": path,
                    "attribution": attribution,
                    "remediation_authorized": False,
                    "message": f"Out-of-scope state change on '{path}' with attribution={attribution}.",
                }
            )

        change_records.append(
            {
                "path": path,
                "change_type": raw_change_type,
                "state": "CHANGED",
                "scope": scope,
                "authority": authority,
                "comparison": comparison,
                "before_digest": before_digest,
                "after_digest": after_digest,
                "intake_state": intake_state,
                "execution_state": execution_state,
                "attribution": attribution,
                "attribution_basis": attribution_basis,
                "generated": attribution == "GENERATED",
                "generated_by": generated_by,
                "evidence_refs": [ev_s0_id, ev_s1_id],
            }
        )

    if is_stale_snapshot:
        findings.append(
            {
                "finding_id": f"find-stale-scope-{len(findings) + 1}",
                "code": "STALE_SCOPE_AUDIT",
                "invariant": "AIF-025",
                "attribution": "UNKNOWN",
                "remediation_authorized": False,
                "message": f"Scope audit comparison '{comparison}' is STALE with respect to current repository snapshot '{s2_id}'.",
            }
        )

    # Determine verification.scope_claim.status (Section 18 & 19)
    if is_stale_snapshot:
        scope_claim_status = "STALE"
    elif has_unauthorized_agent_change:
        scope_claim_status = "VIOLATED"
    elif attribution_unknown_count > 0 or any(
        cr["scope"] == "UNKNOWN" and cr["attribution"] != "GENERATED" for cr in change_records
    ) or any(cr["attribution"] == "EXTERNAL_ATTRIBUTED" and cr["scope"] == "OUT_OF_SCOPE" for cr in change_records):
        scope_claim_status = "PARTIAL"
    else:
        scope_claim_status = "VERIFIED"

    return {
        "comparison": comparison,
        "intake_snapshot": s0_id,
        "execution_snapshot": s1_id,
        "current_snapshot": s2_id,
        "result": {
            "changed_paths": len(change_records),
            "in_scope": in_scope_count,
            "out_of_scope": out_of_scope_count,
            "generated": generated_count,
            "attribution_unknown": attribution_unknown_count,
        },
        "change_records": change_records,
        "findings": findings,
        "evidence": evidence,
        "verification": {
            "scope_claim": {
                "status": scope_claim_status,
                "subject_snapshot": s1_id,
                "current_snapshot": s2_id,
            }
        },
        "mutates_repository": False,
        "performs_remediation": False,
    }


def run_self_tests() -> int:
    """Execute the Phase 4 adversarial test suite for agent-change-scope-audit."""
    passed = 0
    failed = 0

    loader = importlib.machinery.SourceFileLoader(
        "aif_verify", str(REPO_ROOT / "bin" / "aif-verify")
    )
    aif_verify = loader.load_module()
    cr_schema = json.loads(CHANGE_RECORD_SCHEMA_PATH.read_text(encoding="utf-8"))

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if cond:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}: {detail}", file=sys.stderr)
            failed += 1

    def validate_all_change_records(audit_out: Dict[str, Any]) -> bool:
        for cr in audit_out.get("change_records", []):
            errs = aif_verify.validate_schema(cr, cr_schema, CHANGE_RECORD_SCHEMA_PATH.parent)
            if errs:
                return False
        return True

    # 1. Section 10 Canonical 4-Path Example: src/a.ts, test/a.test.ts, README.md (PREEXISTING), dist/a.js (GENERATED)
    r_sec10 = audit_change_scope(
        {
            "intake_snapshot": "S0",
            "execution_snapshot": "S1",
            "admission_record": {
                "admitted_paths": ["src/**", "test/**"],
                "excluded_paths": [".github/**"],
            },
            "execution_records": [
                {
                    "execution_id": "E-EXEC-001",
                    "command": "edit src/a.ts test/a.test.ts",
                    "touched_paths": ["src/a.ts", "test/a.test.ts"],
                },
                {
                    "execution_id": "E-EXEC-002",
                    "command": "npm run build",
                    "touched_paths": [],
                    "generated_paths": ["dist/a.js"],
                },
            ],
            "observed_files": [
                {
                    "path": "src/a.ts",
                    "intake_state": "CLEAN",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:a0",
                    "after_digest": "sha256:a1",
                },
                {
                    "path": "test/a.test.ts",
                    "intake_state": "CLEAN",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:t0",
                    "after_digest": "sha256:t1",
                },
                {
                    "path": "README.md",
                    "intake_state": "DIRTY",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:r0",
                    "after_digest": "sha256:r0",
                },
                {
                    "path": "dist/a.js",
                    "intake_state": "CLEAN",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:d0",
                    "after_digest": "sha256:d1",
                },
            ],
        }
    )
    by_path_10 = {cr["path"]: cr for cr in r_sec10["change_records"]}
    check(
        "SEC-10/18 (4-path canonical example: src/a.ts & test/a.test.ts AGENT_ATTRIBUTED, README.md PREEXISTING, dist/a.js GENERATED -> VERIFIED)",
        validate_all_change_records(r_sec10)
        and r_sec10["result"]
        == {
            "changed_paths": 4,
            "in_scope": 2,
            "out_of_scope": 1,
            "generated": 1,
            "attribution_unknown": 0,
        }
        and by_path_10["src/a.ts"]["attribution"] == "AGENT_ATTRIBUTED"
        and by_path_10["test/a.test.ts"]["attribution"] == "AGENT_ATTRIBUTED"
        and by_path_10["README.md"]["attribution"] == "PREEXISTING"
        and by_path_10["README.md"]["scope"] == "OUT_OF_SCOPE"
        and by_path_10["README.md"]["authority"] == "AUTHORIZED"
        and by_path_10["dist/a.js"]["attribution"] == "GENERATED"
        and by_path_10["dist/a.js"]["scope"] == "UNKNOWN"
        and r_sec10["verification"]["scope_claim"]["status"] == "VERIFIED"
        and any(f["code"] == "OUT_OF_SCOPE_PREEXISTING_CHANGE" for f in r_sec10["findings"]),
        str(r_sec10),
    )

    # 2. RED-37 (AIF-023): Diff does not prove attribution (package.json modified in S0 -> S1 with no execution evidence)
    r_red37 = audit_change_scope(
        {
            "intake_snapshot": "S0",
            "execution_snapshot": "S1",
            "admission_record": {"admitted_paths": ["src/**"]},
            "execution_records": [],
            "observed_files": [
                {
                    "path": "package.json",
                    "intake_state": "CLEAN",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:pkg0",
                    "after_digest": "sha256:pkg1",
                }
            ],
        }
    )
    cr_red37 = r_red37["change_records"][0]
    check(
        "RED-37 / AIF-023 (S0 -> S1 package.json diff with no actor execution evidence -> STATE_CHANGE=CHANGED, ATTRIBUTION=UNKNOWN, verification=PARTIAL)",
        validate_all_change_records(r_red37)
        and cr_red37["state"] == "CHANGED"
        and cr_red37["attribution"] == "UNKNOWN"
        and cr_red37["attribution"] != "AGENT_ATTRIBUTED"
        and r_red37["verification"]["scope_claim"]["status"] == "PARTIAL",
        str(r_red37),
    )

    # 3. RED-38 (AIF-024): Pre-existing dirty file (README.md changed at S0, unchanged during S0 -> S1)
    r_red38 = audit_change_scope(
        {
            "intake_snapshot": "S0",
            "execution_snapshot": "S1",
            "admission_record": {"admitted_paths": ["src/**"]},
            "execution_records": [],
            "observed_files": [
                {
                    "path": "README.md",
                    "intake_state": "DIRTY",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:dirty0",
                    "after_digest": "sha256:dirty0",
                }
            ],
        }
    )
    cr_red38 = r_red38["change_records"][0]
    check(
        "RED-38 / AIF-024 (README.md dirty at S0 and unchanged in S0 -> S1 -> PREEXISTING, never AGENT_ATTRIBUTED)",
        validate_all_change_records(r_red38)
        and cr_red38["attribution"] == "PREEXISTING"
        and cr_red38["authority"] == "AUTHORIZED"
        and r_red38["verification"]["scope_claim"]["status"] == "VERIFIED",
        str(r_red38),
    )

    # 4. RED-39 (Section 7): Generated artifact (src/a.ts modified, build generates dist/a.js)
    r_red39 = audit_change_scope(
        {
            "intake_snapshot": "S0",
            "execution_snapshot": "S1",
            "admission_record": {"admitted_paths": ["src/**"]},
            "execution_records": [
                {
                    "execution_id": "E-EXEC-010",
                    "command": "edit src/a.ts",
                    "touched_paths": ["src/a.ts"],
                },
                {
                    "execution_id": "E-EXEC-011",
                    "command": "npm run build",
                    "touched_paths": [],
                    "generated_paths": ["dist/a.js"],
                },
            ],
            "observed_files": [
                {
                    "path": "src/a.ts",
                    "intake_state": "CLEAN",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:a0",
                    "after_digest": "sha256:a1",
                },
                {
                    "path": "dist/a.js",
                    "intake_state": "CLEAN",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:d0",
                    "after_digest": "sha256:d1",
                },
            ],
        }
    )
    by_path_39 = {cr["path"]: cr for cr in r_red39["change_records"]}
    check(
        "RED-39 (src/a.ts=AGENT_ATTRIBUTED, dist/a.js=GENERATED with generated_by='npm run build')",
        validate_all_change_records(r_red39)
        and by_path_39["src/a.ts"]["attribution"] == "AGENT_ATTRIBUTED"
        and by_path_39["dist/a.js"]["attribution"] == "GENERATED"
        and by_path_39["dist/a.js"]["change_type"] == "GENERATED"
        and by_path_39["dist/a.js"]["generated_by"] == "npm run build",
        str(r_red39),
    )

    # 5. RED-40 (Section 15): External mutation with sufficient external event evidence vs without
    r_red40_ext = audit_change_scope(
        {
            "intake_snapshot": "S0",
            "execution_snapshot": "S1",
            "admission_record": {"admitted_paths": ["src/**"]},
            "execution_records": [
                {
                    "execution_id": "E-EXEC-020",
                    "command": "edit src/a.ts",
                    "touched_paths": ["src/a.ts"],
                }
            ],
            "external_events": [
                {
                    "event_id": "EXT-FS-001",
                    "touched_paths": ["package.json"],
                }
            ],
            "observed_files": [
                {
                    "path": "package.json",
                    "intake_state": "CLEAN",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:p0",
                    "after_digest": "sha256:p1",
                }
            ],
        }
    )
    r_red40_no_ext = audit_change_scope(
        {
            "intake_snapshot": "S0",
            "execution_snapshot": "S1",
            "admission_record": {"admitted_paths": ["src/**"]},
            "execution_records": [
                {
                    "execution_id": "E-EXEC-020",
                    "command": "edit src/a.ts",
                    "touched_paths": ["src/a.ts"],
                }
            ],
            "external_events": [],
            "observed_files": [
                {
                    "path": "package.json",
                    "intake_state": "CLEAN",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:p0",
                    "after_digest": "sha256:p1",
                }
            ],
        }
    )
    check(
        "RED-40 (external mutation -> EXTERNAL_ATTRIBUTED when external evidence exists, UNKNOWN when absent)",
        validate_all_change_records(r_red40_ext)
        and r_red40_ext["change_records"][0]["attribution"] == "EXTERNAL_ATTRIBUTED"
        and r_red40_no_ext["change_records"][0]["attribution"] == "UNKNOWN",
        str((r_red40_ext, r_red40_no_ext)),
    )

    # 6. RED-41 (AIF-025): Snapshot mismatch (scope audit produced against S1, current repository = S2 -> STALE)
    r_red41 = audit_change_scope(
        {
            "intake_snapshot": "S0",
            "execution_snapshot": "S1",
            "current_snapshot": "S2",
            "admission_record": {"admitted_paths": ["src/**"]},
            "execution_records": [
                {
                    "execution_id": "E-EXEC-030",
                    "command": "edit src/a.ts",
                    "touched_paths": ["src/a.ts"],
                }
            ],
            "observed_files": [
                {
                    "path": "src/a.ts",
                    "intake_state": "CLEAN",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:a0",
                    "after_digest": "sha256:a1",
                }
            ],
        }
    )
    check(
        "RED-41 / AIF-025 (scope audit for S0 -> S1 evaluated when current repository is S2 -> STALE)",
        validate_all_change_records(r_red41)
        and r_red41["comparison"] == "S0 -> S1"
        and r_red41["verification"]["scope_claim"]["status"] == "STALE"
        and any(f["code"] == "STALE_SCOPE_AUDIT" for f in r_red41["findings"]),
        str(r_red41),
    )

    # 7. Section 5: package.json dirty at S0, modified differently at S1 with interleaved external/agent ambiguity -> UNKNOWN
    r_sec5 = audit_change_scope(
        {
            "intake_snapshot": "S0",
            "execution_snapshot": "S1",
            "admission_record": {"admitted_paths": ["src/**"]},
            "execution_records": [
                {
                    "execution_id": "E-EXEC-040",
                    "command": "edit package.json",
                    "touched_paths": ["package.json"],
                }
            ],
            "observed_files": [
                {
                    "path": "package.json",
                    "intake_state": "DIRTY",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:pkg-s0-dirty",
                    "after_digest": "sha256:pkg-s1-dirty-different",
                    "interleaved_external": True,
                }
            ],
        }
    )
    check(
        "SEC-05 (package.json modified at S0 and modified differently at S1 with interleaved external edits -> attribution UNKNOWN)",
        validate_all_change_records(r_sec5)
        and r_sec5["change_records"][0]["attribution"] == "UNKNOWN",
        str(r_sec5),
    )

    # 8. Section 8: Unresolvable glob matcher preserves scope = UNKNOWN (never collapsed into OUT_OF_SCOPE)
    r_sec8 = audit_change_scope(
        {
            "intake_snapshot": "S0",
            "execution_snapshot": "S1",
            "admission_record": {"admitted_paths": ["src/**/generated/*"]},
            "matcher_available": False,
            "execution_records": [
                {
                    "execution_id": "E-EXEC-050",
                    "command": "edit src/deep/generated/out.ts",
                    "touched_paths": ["src/deep/generated/out.ts"],
                }
            ],
            "observed_files": [
                {
                    "path": "src/deep/generated/out.ts",
                    "intake_state": "CLEAN",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:g0",
                    "after_digest": "sha256:g1",
                }
            ],
        }
    )
    check(
        "SEC-08 (unavailable matcher for 'src/**/generated/*' preserves scope=UNKNOWN rather than collapsing into OUT_OF_SCOPE)",
        validate_all_change_records(r_sec8)
        and r_sec8["change_records"][0]["scope"] == "UNKNOWN"
        and r_sec8["verification"]["scope_claim"]["status"] == "PARTIAL",
        str(r_sec8),
    )

    # 9. Section 11 & 16 (RED-05 / AIF-010): Out-of-scope agent change produces OUT_OF_SCOPE_AGENT_CHANGE and does not remediate
    r_sec16 = audit_change_scope(
        {
            "intake_snapshot": "S0",
            "execution_snapshot": "S1",
            "admission_record": {"admitted_paths": ["src/**"]},
            "execution_records": [
                {
                    "execution_id": "E-EXEC-060",
                    "command": "edit README.md",
                    "touched_paths": ["README.md"],
                }
            ],
            "observed_files": [
                {
                    "path": "README.md",
                    "intake_state": "CLEAN",
                    "execution_state": "DIRTY",
                    "before_digest": "sha256:r0",
                    "after_digest": "sha256:r1",
                }
            ],
        }
    )
    check(
        "SEC-11/16 / RED-05 (README.md OUT_OF_SCOPE + AGENT_ATTRIBUTED -> UNAUTHORIZED & OUT_OF_SCOPE_AGENT_CHANGE finding, performs_remediation=False)",
        validate_all_change_records(r_sec16)
        and r_sec16["change_records"][0]["authority"] == "UNAUTHORIZED"
        and r_sec16["verification"]["scope_claim"]["status"] == "VIOLATED"
        and r_sec16["mutates_repository"] is False
        and r_sec16["performs_remediation"] is False
        and any(f["code"] == "OUT_OF_SCOPE_AGENT_CHANGE" for f in r_sec16["findings"]),
        str(r_sec16),
    )

    print(f"\nagent-change-scope-audit Self-Test Summary: {passed} passed, {failed} failed")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit repository change scope and actor provenance under AIF-0.1.0."
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to JSON file containing intake_snapshot, execution_snapshot, admission_record, and observed_files.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the Phase 4 adversarial scope and provenance test suite.",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_tests()

    if not args.input_path:
        parser.error("Provide an input JSON path or --self-test")

    payload = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
    result = audit_change_scope(payload)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
