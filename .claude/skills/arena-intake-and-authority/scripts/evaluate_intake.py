#!/usr/bin/env python3
"""
evaluate_intake.py — Deterministic Phase 3 Intake & Authority Evaluator for
.claude/skills/arena-intake-and-authority (Component C-01, AIF-0.1.0).

Evaluates:
  AUTHORIZED(action, path, actor, time)
and produces a deterministic AdmissionRecord, per-action authority_matrix,
authority findings, and clarification requirements without mutating the repository.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


ALL_ACTIONS: Tuple[str, ...] = (
    "READ",
    "LIST",
    "SEARCH",
    "EXECUTE",
    "CREATE",
    "MODIFY",
    "DELETE",
    "RENAME",
    "GENERATE",
    "COMMIT",
    "PUSH",
    "RELEASE",
)

INSPECT_ACTIONS: Tuple[str, ...] = ("READ", "LIST", "SEARCH")
MUTATING_ACTIONS: Set[str] = {
    "CREATE",
    "MODIFY",
    "DELETE",
    "RENAME",
    "GENERATE",
    "COMMIT",
    "PUSH",
    "RELEASE",
}

ACTION_SYNONYMS: Dict[str, List[str]] = {
    "INSPECT": ["READ", "LIST", "SEARCH"],
    "READ_ONLY": ["READ", "LIST", "SEARCH"],
    "TEST": ["EXECUTE"],
    "RUN_TESTS": ["EXECUTE"],
    "VERIFY": ["EXECUTE"],
    "EDIT": ["MODIFY"],
    "EDIT_SOURCE": ["MODIFY"],
    "WRITE": ["CREATE", "MODIFY"],
    "GIT_PUSH": ["PUSH"],
}


def normalize_actions(raw_actions: List[str]) -> List[str]:
    result: List[str] = []
    for act in raw_actions:
        up = act.strip().upper()
        expanded = ACTION_SYNONYMS.get(up, [up])
        for item in expanded:
            if item not in result:
                result.append(item)
    return result


def path_overlaps(pat_a: str, pat_b: str) -> bool:
    a = pat_a.rstrip("/")
    b = pat_b.rstrip("/")
    if a == b or a == "**/*" or b == "**/*":
        return True
    a_base = a[:-3] if a.endswith("/**") else a
    b_base = b[:-3] if b.endswith("/**") else b
    if a.endswith("/**") and (b_base == a_base or b_base.startswith(a_base + "/")):
        return True
    if b.endswith("/**") and (a_base == b_base or a_base.startswith(b_base + "/")):
        return True
    return fnmatch.fnmatch(a_base, b) or fnmatch.fnmatch(b_base, a)


def path_covered_by_scope(target: str, scope_patterns: List[str]) -> bool:
    for pat in scope_patterns:
        if pat == target or pat == "**/*":
            return True
        if pat.endswith("/**"):
            prefix = pat[:-3]
            if target == prefix or target.startswith(prefix + "/"):
                return True
        if fnmatch.fnmatch(target, pat):
            return True
    return False


def compute_scoped_authority_view(
    authority_matrix: Dict[str, str],
    admitted_paths: List[str],
    excluded_paths: List[str],
) -> Dict[str, str]:
    """
    Build the Section 3 fine-grained action + path-group authority view:
      inspect, run_tests, modify_src, modify_docs, modify_package, push, release
    """
    inspect_ok = any(authority_matrix.get(a) == "AUTHORIZED" for a in INSPECT_ACTIONS)
    modify_status = authority_matrix.get("MODIFY", "NOT_AUTHORIZED")

    def path_mod_state(sample_path: str) -> str:
        if modify_status in ("EXPIRED", "CONFLICTING"):
            return modify_status
        if modify_status != "AUTHORIZED":
            return "NOT_AUTHORIZED"
        if path_covered_by_scope(sample_path, excluded_paths):
            return "NOT_AUTHORIZED"
        if path_covered_by_scope(sample_path, admitted_paths):
            return "AUTHORIZED"
        return "NOT_AUTHORIZED"

    return {
        "inspect": "AUTHORIZED" if inspect_ok else "NOT_AUTHORIZED",
        "run_tests": authority_matrix.get("EXECUTE", "NOT_AUTHORIZED"),
        "modify_src": path_mod_state("src/index.ts"),
        "modify_docs": path_mod_state("README.md"),
        "modify_package": path_mod_state("package.json"),
        "push": authority_matrix.get("PUSH", "UNKNOWN"),
        "release": authority_matrix.get("RELEASE", "NOT_AUTHORIZED"),
    }


def evaluate_intake(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate Request + AuthorityEvent[] + SnapshotRef + Policy into a deterministic
    AdmissionRecord and authority evaluation report.
    """
    req = payload.get("request", {})
    req_id = req.get("request_id", "req-unknown")
    req_actor = req.get("actor", "arena-agent")
    req_time = payload.get("evaluation_time") or req.get("created_at", "2026-09-29T12:00:00Z")
    req_actions = normalize_actions(req.get("requested_actions", []))
    req_paths: List[str] = req.get("requested_paths", [])
    req_text = (req.get("text") or "").strip()
    ambiguity = req.get("ambiguity_level", "CLEAR")

    snap = payload.get("intake_snapshot", "snap-s0-intake")
    snap_id = snap.get("snapshot_id", "snap-s0-intake") if isinstance(snap, dict) else str(snap)

    auth_events: List[Dict[str, Any]] = payload.get("authority_events", [])
    exec_records: List[Dict[str, Any]] = payload.get("execution_records", [])
    prior_admission: Dict[str, Any] | None = payload.get("prior_admission")
    policy: Dict[str, Any] = payload.get("policy", {})

    findings: List[Dict[str, Any]] = []
    blockers: List[str] = []
    clarifications: List[str] = []
    authority_refs: List[str] = []

    # Per-action authority state table across the 12-action vocabulary
    authority_matrix: Dict[str, str] = {act: "NOT_AUTHORIZED" for act in ALL_ACTIONS}
    authority_matrix["PUSH"] = "UNKNOWN"

    admitted_paths: List[str] = []
    excluded_paths: List[str] = list(
        policy.get("excluded_paths", [".github/**", "package.json", "README.md"])
    )

    has_expired = False
    has_conflict = False
    has_retroactive = False
    has_actor_mismatch = False

    # 1. Check for vague mutation requests (Section 8: "Fix whatever is wrong.")
    vague_phrases = (
        "fix whatever is wrong",
        "clean up the repository and fix anything necessary",
        "fix anything necessary",
    )
    is_vague = ambiguity in ("AMBIGUOUS", "UNSCOPED") or any(
        vp in req_text.lower() for vp in vague_phrases
    )

    # 2. Evaluate AuthorityEvents across ACTOR, TIME, ACTION, and PATH dimensions
    positive_paths_by_action: Dict[str, List[str]] = {}
    negative_paths_by_action: Dict[str, List[str]] = {}

    for ev in auth_events:
        ev_id = ev.get("event_id", "AUTH-UNKNOWN")
        ev_actor = ev.get("actor", req_actor)
        ev_status = ev.get("authority_status", "AUTHORIZED")
        ev_actions = normalize_actions(ev.get("action_scope", []))
        ev_paths = ev.get("path_scope", [])
        ev_denied_paths = ev.get("denied_paths", [])
        ev_restrictions = ev.get("restrictions", [])

        for r_item in ev_restrictions:
            if r_item.startswith("do_not_modify:"):
                ev_denied_paths.append(r_item.split(":", 1)[1].strip())

        # AIF-022: Actor non-transitivity
        if ev_actor != req_actor:
            has_actor_mismatch = True
            findings.append(
                {
                    "finding_id": f"find-actor-{ev_id}",
                    "invariant": "AIF-022",
                    "category": "ACTOR_SCOPE_MISMATCH",
                    "proposition": f"AuthorityEvent '{ev_id}' granted to '{ev_actor}' does not transitively authorize '{req_actor}'.",
                }
            )
            continue

        # AIF-021: No retroactive authorization check against any prior ExecutionRecord
        issued_at = ev.get("issued_at", "")
        effective_from = ev.get("effective_from", "")
        expires_at = ev.get("expires_at", "")

        for ex in exec_records:
            ex_start = ex.get("started_at", "")
            if ex_start and ((issued_at and issued_at > ex_start) or (effective_from and effective_from > ex_start)):
                has_retroactive = True
                findings.append(
                    {
                        "finding_id": f"find-retroactive-{ev_id}",
                        "invariant": "AIF-021",
                        "category": "RETROACTIVE_AUTHORIZATION",
                        "proposition": f"AuthorityEvent '{ev_id}' issued/effective at '{issued_at or effective_from}' cannot retroactively authorize execution at '{ex_start}'.",
                    }
                )

        # AIF-001A: Temporal validity check
        if expires_at and req_time >= expires_at:
            has_expired = True
            for act in ev_actions:
                authority_matrix[act] = "EXPIRED"
            findings.append(
                {
                    "finding_id": f"find-expired-{ev_id}",
                    "invariant": "AIF-001A",
                    "category": "AUTHORITY_EXPIRED",
                    "proposition": f"AuthorityEvent '{ev_id}' expired at '{expires_at}' prior to evaluation time '{req_time}'.",
                }
            )
            continue

        if effective_from and req_time < effective_from:
            for act in ev_actions:
                authority_matrix[act] = "NOT_AUTHORIZED"
            continue

        if ev_status == "CONFLICTING":
            has_conflict = True
            for act in ev_actions:
                authority_matrix[act] = "CONFLICTING"
            continue

        if ev_status == "NOT_AUTHORIZED":
            for act in ev_actions:
                negative_paths_by_action.setdefault(act, []).extend(ev_paths or ["**/*"])
            continue

        if ev_status == "AUTHORIZED":
            authority_refs.append(ev_id)
            for act in ev_actions:
                authority_matrix[act] = "AUTHORIZED"
                positive_paths_by_action.setdefault(act, []).extend(ev_paths)
                if ev_denied_paths:
                    negative_paths_by_action.setdefault(act, []).extend(ev_denied_paths)
            for p in ev_paths:
                if p not in admitted_paths:
                    admitted_paths.append(p)
            for dp in ev_denied_paths:
                if dp not in excluded_paths:
                    excluded_paths.append(dp)

    # 3. Check for conflicting authority across AuthorityEvents (Section 6: AUTH-001 vs AUTH-002)
    for act, pos_pats in positive_paths_by_action.items():
        neg_pats = negative_paths_by_action.get(act, [])
        for pp in pos_pats:
            for np in neg_pats:
                if path_overlaps(pp, np):
                    has_conflict = True
                    authority_matrix[act] = "CONFLICTING"
                    findings.append(
                        {
                            "finding_id": f"find-conflict-{act.lower()}",
                            "invariant": "AIF-001",
                            "category": "CONFLICTING_AUTHORITY",
                            "proposition": f"Conflicting authority for action '{act}' between permitted scope '{pp}' and denied scope '{np}'.",
                        }
                    )

    # Remove any explicitly admitted paths from default excluded_paths unless also in negative_paths
    denied_all = [p for pats in negative_paths_by_action.values() for p in pats]
    excluded_paths = [
        ep for ep in excluded_paths if ep in denied_all or not path_covered_by_scope(ep, admitted_paths)
    ]

    # 4. Check mid-task scope expansion against prior AdmissionRecord (Section 12 / A-05)
    if prior_admission:
        prior_admitted_paths = prior_admission.get("admitted_paths", [])
        prior_auth_refs = set(prior_admission.get("authority_refs", []))
        new_auth_refs = set(authority_refs) - prior_auth_refs
        for rp in req_paths:
            if not path_covered_by_scope(rp, prior_admitted_paths) and not new_auth_refs:
                blockers.append("NEW_AUTHORITY_EVENT_REQUIRED")
                findings.append(
                    {
                        "finding_id": "find-scope-expansion",
                        "invariant": "AIF-001",
                        "category": "SCOPE_VIOLATION",
                        "proposition": f"Requested path '{rp}' expands prior admission scope {prior_admitted_paths} without a new AuthorityEvent.",
                    }
                )

    # 5. Determine fundamental intake outcome: ADMITTED, INSPECT_ONLY, BLOCKED, or REJECTED
    requested_mutating = [a for a in req_actions if a in MUTATING_ACTIONS]
    requested_inspect_only = bool(req_actions) and all(a in INSPECT_ACTIONS for a in req_actions)

    # Section 13: Report observed repository metadata/config issues without mutating or repairing them
    for issue_msg in payload.get("observed_repository_issues", []):
        findings.append(
            {
                "finding_id": f"find-repo-issue-{len(findings) + 1}",
                "invariant": "AIF-010",
                "category": "REPOSITORY_ISSUE_OBSERVED",
                "proposition": f"{issue_msg} (reported only; arena-intake-and-authority never repairs or mutates files)",
            }
        )

    def make_record(
        status: str,
        adm_actions: List[str],
        adm_paths: List[str],
        exc_actions: List[str],
        rec_blockers: List[str],
        rec_clarifications: List[str],
    ) -> Dict[str, Any]:
        return {
            "request_id": req_id,
            "admission_status": status,
            "admitted_actions": adm_actions,
            "admitted_paths": adm_paths,
            "excluded_actions": exc_actions,
            "excluded_paths": excluded_paths,
            "blockers": rec_blockers,
            "clarifications": rec_clarifications,
            "authority_refs": authority_refs,
            "intake_snapshot": snap if isinstance(snap, dict) else snap_id,
            "authority_matrix": authority_matrix,
            "scoped_authority_view": compute_scoped_authority_view(
                authority_matrix, adm_paths, excluded_paths
            ),
            "findings": findings,
            "mutates_repository": False,
        }

    # Vague request handling (Section 8 / RED-01)
    if is_vague and (requested_mutating or not req_paths and not admitted_paths):
        clarifications.extend(
            [
                "define intended problem",
                "define permitted actions",
                "define permitted paths",
            ]
        )
        blockers.append("SCOPE_UNDEFINED")
        return make_record(
            status="BLOCKED",
            adm_actions=["READ", "LIST", "SEARCH"],
            adm_paths=["repository_readable_scope"],
            exc_actions=[a for a in ALL_ACTIONS if a not in INSPECT_ACTIONS],
            rec_blockers=blockers,
            rec_clarifications=clarifications,
        )

    if has_retroactive:
        blockers.append("RETROACTIVE_AUTHORIZATION_FORBIDDEN")
    if has_actor_mismatch and not authority_refs:
        blockers.append("ACTOR_NOT_AUTHORIZED")
    if has_expired:
        blockers.append("AUTHORITY_EXPIRED")
    if has_conflict:
        blockers.append("AUTHORITY_CONFLICTING")

    if blockers:
        return make_record(
            status="BLOCKED",
            adm_actions=[a for a in INSPECT_ACTIONS if authority_matrix.get(a) == "AUTHORIZED"],
            adm_paths=admitted_paths if not has_conflict else [],
            exc_actions=[a for a in ALL_ACTIONS if authority_matrix.get(a) != "AUTHORIZED"],
            rec_blockers=blockers,
            rec_clarifications=clarifications,
        )

    # Check if requested path is explicitly excluded while action is authorized (A-03 -> REJECTED)
    for rp in req_paths:
        if path_covered_by_scope(rp, excluded_paths) or (
            admitted_paths and not path_covered_by_scope(rp, admitted_paths)
        ):
            if any(authority_matrix.get(a) == "AUTHORIZED" for a in requested_mutating):
                blockers.append(f"PATH_EXCLUDED:{rp}")
                return make_record(
                    status="REJECTED",
                    adm_actions=[],
                    adm_paths=[],
                    exc_actions=list(ALL_ACTIONS),
                    rec_blockers=blockers,
                    rec_clarifications=clarifications,
                )

    # Investigation / read-only mode (Section 7 / RED-02 / A-04 -> INSPECT_ONLY)
    all_inspect_authorized = any(authority_matrix.get(a) == "AUTHORIZED" for a in INSPECT_ACTIONS)
    any_mutating_authorized = any(authority_matrix.get(a) == "AUTHORIZED" for a in MUTATING_ACTIONS)

    if all_inspect_authorized and not any_mutating_authorized:
        if not requested_mutating or payload.get("allow_inspect_fallback", True):
            return make_record(
                status="INSPECT_ONLY",
                adm_actions=[a for a in INSPECT_ACTIONS if authority_matrix.get(a) == "AUTHORIZED"],
                adm_paths=admitted_paths or ["repository_readable_scope"],
                exc_actions=[a for a in ALL_ACTIONS if a not in INSPECT_ACTIONS],
                rec_blockers=[],
                rec_clarifications=clarifications,
            )

    # Check if required approval/authority is absent for requested mutating actions (RED-04)
    unauthed_req_actions = [
        a for a in req_actions if authority_matrix.get(a) != "AUTHORIZED"
    ]
    if unauthed_req_actions or not authority_refs:
        blockers.append("AUTHORITY_MISSING")
        return make_record(
            status="BLOCKED",
            adm_actions=[a for a in INSPECT_ACTIONS if authority_matrix.get(a) == "AUTHORIZED"],
            adm_paths=admitted_paths,
            exc_actions=[a for a in ALL_ACTIONS if authority_matrix.get(a) != "AUTHORIZED"],
            rec_blockers=blockers,
            rec_clarifications=clarifications,
        )

    # ADMITTED (Section 9 & Section 11)
    admitted_action_list = [
        a for a in ALL_ACTIONS if authority_matrix.get(a) == "AUTHORIZED"
    ]
    excluded_action_list = [
        a for a in ALL_ACTIONS if authority_matrix.get(a) != "AUTHORIZED"
    ]

    return make_record(
        status="ADMITTED",
        adm_actions=admitted_action_list,
        adm_paths=admitted_paths,
        exc_actions=excluded_action_list,
        rec_blockers=[],
        rec_clarifications=[],
    )


def run_self_tests() -> int:
    """Execute the 13 Phase 3 adversarial tests (RED-01..04, A-01..07, AIF-021, AIF-022)."""
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

    # RED-01: vague mutation request -> BLOCKED with clarifications & inspect-only admitted_actions
    r_red01 = evaluate_intake(
        {
            "request": {
                "request_id": "R-RED-01",
                "actor": "arena-agent",
                "text": "Fix whatever is wrong.",
                "requested_actions": ["MODIFY"],
            },
            "authority_events": [],
            "intake_snapshot": "S0",
        }
    )
    check(
        "RED-01 (vague mutation request -> BLOCKED + clarifications + inspect-only actions)",
        r_red01["admission_status"] == "BLOCKED"
        and r_red01["admitted_actions"] == ["READ", "LIST", "SEARCH"]
        and r_red01["admitted_paths"] == ["repository_readable_scope"]
        and len(r_red01["clarifications"]) == 3,
        str(r_red01),
    )

    # RED-02: CI investigation only -> INSPECT_ONLY
    r_red02 = evaluate_intake(
        {
            "request": {
                "request_id": "R-RED-02",
                "actor": "arena-agent",
                "text": "Investigate why CI fails.",
                "requested_actions": ["INSPECT"],
            },
            "authority_events": [
                {
                    "event_id": "AUTH-002",
                    "actor": "arena-agent",
                    "authority_status": "AUTHORIZED",
                    "action_scope": ["READ", "LIST", "SEARCH"],
                    "path_scope": ["**/*"],
                }
            ],
            "intake_snapshot": "S0",
        }
    )
    check(
        "RED-02 (CI investigation only -> INSPECT_ONLY)",
        r_red02["admission_status"] == "INSPECT_ONLY"
        and "MODIFY" in r_red02["excluded_actions"],
        str(r_red02),
    )

    # RED-03: explicit narrow file scope ("Update src/resolver.ts and run the resolver tests.")
    r_red03 = evaluate_intake(
        {
            "request": {
                "request_id": "R-RED-03",
                "actor": "arena-agent",
                "text": "Update src/resolver.ts and run the resolver tests.",
                "requested_actions": ["READ", "MODIFY", "EXECUTE"],
                "requested_paths": ["src/resolver.ts"],
            },
            "authority_events": [
                {
                    "event_id": "AUTH-003",
                    "actor": "arena-agent",
                    "authority_status": "AUTHORIZED",
                    "action_scope": ["READ", "MODIFY", "EXECUTE"],
                    "path_scope": ["src/resolver.ts"],
                }
            ],
            "intake_snapshot": "S0",
        }
    )
    check(
        "RED-03 (explicit narrow file scope -> ADMITTED with exact path scope, test/resolver/** not auto-added)",
        r_red03["admission_status"] == "ADMITTED"
        and r_red03["admitted_paths"] == ["src/resolver.ts"]
        and "test/resolver/**" not in r_red03["admitted_paths"],
        str(r_red03),
    )

    # RED-04: required approval absent -> BLOCKED
    r_red04 = evaluate_intake(
        {
            "request": {
                "request_id": "R-RED-04",
                "actor": "arena-agent",
                "text": "Modify .github/workflows/ci.yml",
                "requested_actions": ["MODIFY"],
                "requested_paths": [".github/workflows/ci.yml"],
            },
            "authority_events": [],
            "intake_snapshot": "S0",
        }
    )
    check(
        "RED-04 (required approval absent -> BLOCKED)",
        r_red04["admission_status"] == "BLOCKED"
        and "AUTHORITY_MISSING" in r_red04["blockers"],
        str(r_red04),
    )

    # A-01: expired authority -> EXPIRED / BLOCKED
    r_a01 = evaluate_intake(
        {
            "request": {
                "request_id": "R-A01",
                "actor": "arena-agent",
                "created_at": "2026-09-29T19:05:00Z",
                "requested_actions": ["MODIFY"],
                "requested_paths": ["src/a.ts"],
            },
            "evaluation_time": "2026-09-29T19:05:00Z",
            "authority_events": [
                {
                    "event_id": "AUTH-EXP",
                    "actor": "arena-agent",
                    "authority_status": "AUTHORIZED",
                    "action_scope": ["MODIFY"],
                    "path_scope": ["src/**"],
                    "issued_at": "2026-09-29T18:00:00Z",
                    "effective_from": "2026-09-29T18:00:00Z",
                    "expires_at": "2026-09-29T19:00:00Z",
                }
            ],
            "intake_snapshot": "S0",
        }
    )
    check(
        "A-01 (expired authority at 19:05 after 19:00 expiry -> EXPIRED & BLOCKED)",
        r_a01["authority_matrix"]["MODIFY"] == "EXPIRED"
        and r_a01["admission_status"] == "BLOCKED",
        str(r_a01),
    )

    # A-02: conflicting authority (AUTH-001 modify src/** vs AUTH-002 do not modify src/auth/**) -> CONFLICTING & BLOCKED
    r_a02 = evaluate_intake(
        {
            "request": {
                "request_id": "R-A02",
                "actor": "arena-agent",
                "requested_actions": ["MODIFY"],
                "requested_paths": ["src/auth/login.ts"],
            },
            "authority_events": [
                {
                    "event_id": "AUTH-001",
                    "actor": "arena-agent",
                    "authority_status": "AUTHORIZED",
                    "action_scope": ["MODIFY"],
                    "path_scope": ["src/**"],
                },
                {
                    "event_id": "AUTH-002",
                    "actor": "arena-agent",
                    "authority_status": "NOT_AUTHORIZED",
                    "action_scope": ["MODIFY"],
                    "path_scope": ["src/auth/**"],
                },
            ],
            "intake_snapshot": "S0",
        }
    )
    check(
        "A-02 (conflicting authority src/** vs src/auth/** -> CONFLICTING & BLOCKED)",
        r_a02["authority_matrix"]["MODIFY"] == "CONFLICTING"
        and r_a02["admission_status"] == "BLOCKED",
        str(r_a02),
    )

    # A-03: action authorized, path excluded -> REJECTED
    r_a03 = evaluate_intake(
        {
            "request": {
                "request_id": "R-A03",
                "actor": "arena-agent",
                "requested_actions": ["MODIFY"],
                "requested_paths": ["package.json"],
            },
            "authority_events": [
                {
                    "event_id": "AUTH-001",
                    "actor": "arena-agent",
                    "authority_status": "AUTHORIZED",
                    "action_scope": ["MODIFY"],
                    "path_scope": ["src/**"],
                }
            ],
            "intake_snapshot": "S0",
        }
    )
    check(
        "A-03 (action MODIFY authorized on src/**, requested path package.json excluded -> REJECTED)",
        r_a03["admission_status"] == "REJECTED",
        str(r_a03),
    )

    # A-04: read authorized, write unauthorized -> INSPECT_ONLY
    r_a04 = evaluate_intake(
        {
            "request": {
                "request_id": "R-A04",
                "actor": "arena-agent",
                "requested_actions": ["READ", "MODIFY"],
                "requested_paths": ["src/a.ts"],
            },
            "allow_inspect_fallback": True,
            "authority_events": [
                {
                    "event_id": "AUTH-READ",
                    "actor": "arena-agent",
                    "authority_status": "AUTHORIZED",
                    "action_scope": ["READ", "LIST", "SEARCH"],
                    "path_scope": ["src/**"],
                }
            ],
            "intake_snapshot": "S0",
        }
    )
    check(
        "A-04 (read authorized, write unauthorized -> INSPECT_ONLY)",
        r_a04["admission_status"] == "INSPECT_ONLY"
        and r_a04["admitted_actions"] == ["READ", "LIST", "SEARCH"]
        and "MODIFY" in r_a04["excluded_actions"],
        str(r_a04),
    )

    # A-05: mid-task scope expansion without new AuthorityEvent -> BLOCKED (NEW_AUTHORITY_EVENT_REQUIRED)
    r_a05 = evaluate_intake(
        {
            "request": {
                "request_id": "R-A05",
                "actor": "arena-agent",
                "requested_actions": ["MODIFY"],
                "requested_paths": ["package.json"],
            },
            "prior_admission": {
                "request_id": "R-001",
                "admission_status": "ADMITTED",
                "admitted_actions": ["READ", "MODIFY"],
                "admitted_paths": ["src/**"],
                "excluded_paths": ["package.json"],
                "authority_refs": ["AUTH-001"],
            },
            "authority_events": [
                {
                    "event_id": "AUTH-001",
                    "actor": "arena-agent",
                    "authority_status": "AUTHORIZED",
                    "action_scope": ["READ", "MODIFY"],
                    "path_scope": ["src/**"],
                }
            ],
            "intake_snapshot": "S0",
        }
    )
    check(
        "A-05 (mid-task scope expansion without new AuthorityEvent -> BLOCKED + NEW_AUTHORITY_EVENT_REQUIRED)",
        r_a05["admission_status"] == "BLOCKED"
        and "NEW_AUTHORITY_EVENT_REQUIRED" in r_a05["blockers"],
        str(r_a05),
    )

    # A-06 & A-07: push and release remain excluded when only READ/MODIFY/EXECUTE are authorized
    r_a06_07 = evaluate_intake(
        {
            "request": {
                "request_id": "R-001",
                "actor": "arena-agent",
                "requested_actions": ["READ", "MODIFY", "EXECUTE"],
                "requested_paths": ["src/a.ts"],
            },
            "authority_events": [
                {
                    "event_id": "AUTH-001",
                    "actor": "arena-agent",
                    "authority_status": "AUTHORIZED",
                    "action_scope": ["READ", "MODIFY", "EXECUTE"],
                    "path_scope": ["src/**", "test/**"],
                }
            ],
            "intake_snapshot": "S0",
        }
    )
    check(
        "A-06 (push unauthorized -> PUSH remains in excluded_actions)",
        r_a06_07["admission_status"] == "ADMITTED"
        and "PUSH" in r_a06_07["excluded_actions"]
        and r_a06_07["authority_matrix"]["PUSH"] == "UNKNOWN",
        str(r_a06_07),
    )
    check(
        "A-07 (release unauthorized -> RELEASE remains in excluded_actions)",
        r_a06_07["admission_status"] == "ADMITTED"
        and "RELEASE" in r_a06_07["excluded_actions"]
        and r_a06_07["authority_matrix"]["RELEASE"] == "NOT_AUTHORIZED",
        str(r_a06_07),
    )

    # AIF-021: No retroactive authorization (executed at T1=18:00, authorized at T2=18:30)
    r_aif021 = evaluate_intake(
        {
            "request": {
                "request_id": "R-AIF021",
                "actor": "arena-agent",
                "requested_actions": ["MODIFY"],
                "requested_paths": ["src/a.ts"],
            },
            "authority_events": [
                {
                    "event_id": "AUTH-T2",
                    "actor": "arena-agent",
                    "authority_status": "AUTHORIZED",
                    "action_scope": ["MODIFY"],
                    "path_scope": ["src/**"],
                    "issued_at": "2026-09-29T18:30:00Z",
                    "effective_from": "2026-09-29T18:30:00Z",
                    "expires_at": "2026-09-29T19:30:00Z",
                }
            ],
            "execution_records": [
                {
                    "execution_id": "EX-T1",
                    "started_at": "2026-09-29T18:00:00Z",
                }
            ],
            "evaluation_time": "2026-09-29T18:35:00Z",
            "intake_snapshot": "S0",
        }
    )
    check(
        "AIF-021 (authorization at T2=18:30 cannot retroactively authorize execution at T1=18:00 -> BLOCKED)",
        r_aif021["admission_status"] == "BLOCKED"
        and "RETROACTIVE_AUTHORIZATION_FORBIDDEN" in r_aif021["blockers"],
        str(r_aif021),
    )

    # AIF-022: Non-transitive actor authority (Agent A authority used by Agent B)
    r_aif022 = evaluate_intake(
        {
            "request": {
                "request_id": "R-AIF022",
                "actor": "agent-B",
                "requested_actions": ["MODIFY"],
                "requested_paths": ["src/a.ts"],
            },
            "authority_events": [
                {
                    "event_id": "AUTH-AGENT-A",
                    "actor": "agent-A",
                    "authority_status": "AUTHORIZED",
                    "action_scope": ["MODIFY"],
                    "path_scope": ["src/**"],
                }
            ],
            "intake_snapshot": "S0",
        }
    )
    check(
        "AIF-022 (Agent A authority does not transitively authorize Agent B -> BLOCKED)",
        r_aif022["admission_status"] == "BLOCKED"
        and "ACTOR_NOT_AUTHORIZED" in r_aif022["blockers"],
        str(r_aif022),
    )

    # Section 3 & 11: Fine-grained scoped_authority_view & deterministic AdmissionRecord with intake_snapshot object
    r_sec11 = evaluate_intake(
        {
            "request": {
                "request_id": "R-001",
                "actor": "arena-agent",
                "requested_actions": ["inspect", "modify", "test"],
                "requested_paths": ["src/index.ts"],
            },
            "authority_events": [
                {
                    "event_id": "AUTH-001",
                    "actor": "arena-agent",
                    "authority_status": "AUTHORIZED",
                    "action_scope": ["inspect", "modify", "test"],
                    "path_scope": ["src/**", "test/**"],
                }
            ],
            "intake_snapshot": {"snapshot_id": "S0"},
            "observed_repository_issues": ["package.json is invalid"],
        }
    )
    sav = r_sec11.get("scoped_authority_view", {})
    check(
        "SEC-03/11/13 (fine-grained scoped_authority_view, intake_snapshot={snapshot_id: S0}, and AIF-010 report-without-mutation)",
        r_sec11["admission_status"] == "ADMITTED"
        and sav.get("inspect") == "AUTHORIZED"
        and sav.get("run_tests") == "AUTHORIZED"
        and sav.get("modify_src") == "AUTHORIZED"
        and sav.get("modify_docs") == "NOT_AUTHORIZED"
        and sav.get("modify_package") == "NOT_AUTHORIZED"
        and sav.get("push") == "UNKNOWN"
        and sav.get("release") == "NOT_AUTHORIZED"
        and r_sec11["intake_snapshot"] == {"snapshot_id": "S0"}
        and r_sec11["mutates_repository"] is False
        and any(f.get("category") == "REPOSITORY_ISSUE_OBSERVED" for f in r_sec11["findings"]),
        str(r_sec11),
    )

    print(f"\narena-intake-and-authority Self-Test Summary: {passed} passed, {failed} failed")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate task authority and scope admission under AIF-0.1.0."
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to JSON file containing request, authority_events, and intake_snapshot.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the 13-case Phase 3 adversarial test suite.",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_tests()

    if not args.input_path:
        parser.error("Provide an input JSON path or --self-test")

    payload = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
    result = evaluate_intake(payload)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
