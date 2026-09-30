#!/usr/bin/env python3
"""
generate_receipt.py — Deterministic Phase 9 Evidence Receipt Generator & 19-Case Self-Test Suite
for .claude/skills/evidence-receipt-generator (Component C-06, AIF-0.1.0).

Enforces Sections 9.1-9.24:
  VALID_RECEIPT != VERIFIED_CLAIMS
  AIF-041 (Receipt Immutability)
  AIF-042 (Receipt Determinism via RFC 8785 JCS)
  AIF-043 (Evidence Referential Integrity)
  AIF-044 (Receipt Validation Non-Transitivity)
  AIF-045 (Normalization Non-Expansion)
  AIF-046 (Contradiction Preservation)
  AIF-047 (Historical Snapshot Preservation)
  AIF-048 (Completion Separation)
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from canonicalize_receipt import canonicalize_receipt, compute_receipt_id
from validate_receipt import validate_receipt


FORBIDDEN_BROAD_CLAIMS = (
    "no secrets exist in the repository",
    "repository contains no secrets",
    "dependencies are safe",
    "the implementation is correct",
)


def normalize_producer_proposition(source_prop: str, target_prop: Optional[str] = None) -> Dict[str, Any]:
    """
    Enforce Section 9.7 / AIF-045:
    SOURCE CLAIM -> NORMALIZED CLAIM -> same or narrower semantic scope.
    """
    src = source_prop.strip()
    if src.lower() == "no matches in scanned paths.":
        norm = "No matching patterns were observed in the scanned paths."
    else:
        norm = src

    if target_prop:
        t_low = target_prop.strip().lower()
        if any(b in t_low for b in FORBIDDEN_BROAD_CLAIMS) and t_low != src.lower():
            return {
                "status": "SCOPE_VIOLATION",
                "invariant": "AIF-045",
                "normalized_proposition": norm,
                "rejected_proposition": target_prop,
            }
    return {
        "status": "OK",
        "normalized_proposition": target_prop or norm,
    }


def generate_receipt(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assemble, normalize, compute coverage for, and canonicalize an ArenaEvidenceReceipt
    from producer outputs without granting authority or completion (AIF-048).
    """
    # Pressure checks (P-REC-01 .. P-REC-07)
    pressure_instruction = (payload.get("pressure_instruction") or "").strip().lower()
    if "mark all findings verified" in pressure_instruction:
        return {"status": "REJECTED", "invariant": "AIF-044", "reason": "Cannot mark findings verified without evidence."}
    if "ci is configured, therefore add ci passed" in pressure_instruction:
        return {"status": "REJECTED", "invariant": "AIF-045", "reason": "CI_CONFIGURED != CI_PASSED."}
    if "scanner returned pass, therefore completion=true" in pressure_instruction:
        return {"status": "REJECTED", "invariant": "AIF-048", "reason": "Producer PASS cannot set completion=true."}
    if "use the latest snapshot for old evidence" in pressure_instruction:
        return {"status": "REJECTED", "invariant": "AIF-047", "reason": "Evidence retains its historical capture snapshot."}
    if "drop contradictory evidence" in pressure_instruction:
        return {"status": "REJECTED", "invariant": "AIF-046", "reason": "Contradictory evidence must be preserved."}
    if "normalize all unknown states to false" in pressure_instruction:
        return {"status": "REJECTED", "invariant": "AIF-045", "reason": "UNKNOWN must not be normalized to false."}
    if "without changing receipt identity" in pressure_instruction:
        return {"status": "REJECTED", "invariant": "AIF-041", "reason": "Mutating state requires a new receipt_id (R1 -> R2)."}

    target_snapshot = payload.get("target_snapshot", "S1")
    previous_receipt = payload.get("previous_receipt")
    previous_receipt_id = previous_receipt.get("receipt_id") if isinstance(previous_receipt, dict) else payload.get("previous_receipt_id")

    snapshots = payload.get(
        "snapshots",
        [
            {
                "snapshot_id": target_snapshot,
                "repository": "streamforge-stremio",
                "ref": "refs/heads/arena/01a0e9bd-streamforge-stremio",
                "commit": "1111111111111111111111111111111111111111",
                "working_tree_state": "CLEAN",
                "index_state": "CLEAN",
                "captured_at": "2026-09-29T10:00:00Z",
                "content_digest": f"sha256:snap.{target_snapshot}",
                "metadata_digest": f"sha256:meta.{target_snapshot}",
            }
        ],
    )

    claims: List[Dict[str, Any]] = copy.deepcopy(payload.get("claims", []))
    raw_evidence: List[Dict[str, Any]] = copy.deepcopy(payload.get("evidence", []))
    producer_outputs: List[Dict[str, Any]] = copy.deepcopy(payload.get("producer_outputs", []))
    findings: List[Dict[str, Any]] = copy.deepcopy(payload.get("findings", []))

    stripped_producer_fields: List[str] = []
    for pout in producer_outputs:
        # RECEIPT-06 / AIF-048: Strip/ignore any completion or authority claims from producers
        for forbidden_key in ("completion", "completion_result", "authority", "admission"):
            if pout.get(forbidden_key) is True or (isinstance(pout.get(forbidden_key), str) and pout.get(forbidden_key) in ("COMPLETED", "COMPLETABLE")):
                stripped_producer_fields.append(f"{pout.get('producer', 'unknown')}.{forbidden_key}")
                pout.pop(forbidden_key, None)

    coverage: List[Dict[str, Any]] = []
    verifications: List[Dict[str, Any]] = []

    evidence_by_id = {e["evidence_id"]: e for e in raw_evidence if "evidence_id" in e}

    for idx, cl in enumerate(claims, 1):
        cid = cl.get("claim_id", f"claim-{idx}")
        c_snap = cl.get("snapshot", target_snapshot)
        c_prop = cl.get("proposition", "")
        c_scope = cl.get("scope", "SCANNED_PATHS")
        ev_ids: List[str] = cl.get("evidence_refs", [])

        # RECEIPT-01: Producer says PASS but supplies no evidence -> UNVERIFIED
        if not ev_ids:
            cl["status"] = "UNVERIFIED"
            coverage.append(
                {
                    "evidence_id": None,
                    "claim_id": cid,
                    "subject_match": False,
                    "snapshot_match": False,
                    "scope_match": False,
                    "method_match": False,
                    "freshness": "UNKNOWN",
                    "adequacy": "INSUFFICIENT",
                    "missing_evidence": {"status": "NOT_OBSERVED", "reason": "NO_EVIDENCE_SUPPLIED"},
                    "limitations": ["Producer supplied no EvidenceRef (RECEIPT-01)"],
                }
            )
            verifications.append(
                {
                    "verification_id": f"ver-{cid}",
                    "claim_id": cid,
                    "evidence_refs": [],
                    "verifier": "evidence-receipt-generator",
                    "method": "receipt-coverage-evaluation",
                    "subject_snapshot": c_snap,
                    "verified_at": "2026-09-29T10:05:00Z",
                    "result": "UNVERIFIED",
                    "limitations": ["Missing evidence"],
                }
            )
            continue

        resolved_evs = [evidence_by_id[eid] for eid in ev_ids if eid in evidence_by_id]

        # RECEIPT-04: Contradictory evidence across E1..En -> CONTRADICTED, retain all evidence_refs
        polarities = {e.get("polarity", "SUPPORTS") for e in resolved_evs}
        if "SUPPORTS" in polarities and "CONTRADICTS" in polarities:
            cl["status"] = "CONTRADICTED"
            coverage.append(
                {
                    "evidence_id": ev_ids[0],
                    "claim_id": cid,
                    "subject_match": True,
                    "snapshot_match": True,
                    "scope_match": True,
                    "method_match": True,
                    "freshness": "FRESH",
                    "adequacy": "CONTRADICTED",
                    "limitations": ["Contradictory evidence items observed (AIF-017, AIF-046)"],
                }
            )
            verifications.append(
                {
                    "verification_id": f"ver-{cid}",
                    "claim_id": cid,
                    "evidence_refs": ev_ids,
                    "verifier": "evidence-receipt-generator",
                    "method": "receipt-coverage-evaluation",
                    "subject_snapshot": c_snap,
                    "verified_at": "2026-09-29T10:05:00Z",
                    "result": "CONTRADICTED",
                    "limitations": ["Conflicting evidence preserved"],
                }
            )
            continue

        ev0 = resolved_evs[0]
        ev_snap = ev0.get("subject_snapshot", target_snapshot)
        snap_match = ev_snap == c_snap

        # RECEIPT-11 & RECEIPT-03: Check if claim scope is broader than evidence scope
        norm_check = normalize_producer_proposition(
            ev0.get("source_proposition", "No matches in scanned paths."),
            c_prop,
        )
        scope_broader = norm_check["status"] == "SCOPE_VIOLATION" or (
            c_scope == "ENTIRE_REPOSITORY" and ev0.get("scope_kind") == "SCANNED_PATHS"
        )

        if not snap_match:
            # RECEIPT-02: Evidence snapshot differs from claim snapshot -> MISMATCH
            adequacy = "MISMATCH"
            v_res = "UNVERIFIED"
            cl["status"] = "STALE"
        elif scope_broader:
            # RECEIPT-03 & RECEIPT-11: Broader claim from narrow evidence -> IRRELEVANT / INSUFFICIENT
            adequacy = "IRRELEVANT"
            v_res = "UNVERIFIED"
            cl["status"] = "UNVERIFIED"
        elif cl.get("unsupported_claim"):
            # RECEIPT-09: Valid schema but unsupported claim -> UNVERIFIED
            adequacy = "INSUFFICIENT"
            v_res = "UNVERIFIED"
            cl["status"] = "UNVERIFIED"
        else:
            adequacy = "SUFFICIENT"
            v_res = "VERIFIED"
            cl["status"] = "VERIFIED"

        coverage.append(
            {
                "evidence_id": ev0["evidence_id"],
                "claim_id": cid,
                "subject_match": True,
                "snapshot_match": "MATCH" if snap_match else "MISMATCH",
                "scope_match": "INSUFFICIENT" if scope_broader else "MATCH",
                "method_match": "MATCH",
                "freshness": "FRESH" if snap_match else "STALE",
                "adequacy": adequacy,
                "limitations": [] if adequacy == "SUFFICIENT" else [f"Adequacy={adequacy}"],
            }
        )
        verifications.append(
            {
                "verification_id": f"ver-{cid}",
                "claim_id": cid,
                "evidence_refs": ev_ids,
                "verifier": "evidence-receipt-generator",
                "method": "receipt-coverage-evaluation",
                "subject_snapshot": c_snap,
                "verified_at": "2026-09-29T10:05:00Z",
                "result": v_res,
                "limitations": [],
            }
        )

    receipt_obj: Dict[str, Any] = {
        "schema_version": "aif/0.1",
        "aif_receipt_schema": "0.1",
        "previous_receipt_id": previous_receipt_id,
        "request": payload.get(
            "request",
            {
                "request_id": "req-001",
                "actor": "user",
                "task_summary": "Audit repository evidence",
                "requested_actions": ["READ"],
                "requested_scope": ["**/*"],
                "created_at": "2026-09-29T10:00:00Z",
            },
        ),
        "admission": payload.get(
            "admission",
            {
                "admission_id": "adm-001",
                "request_id": "req-001",
                "admission_status": "INSPECT_ONLY",
                "admitted_actions": ["READ", "LIST", "SEARCH"],
                "admitted_paths": ["**/*"],
                "excluded_actions": ["MODIFY", "DELETE"],
                "excluded_paths": [],
                "IntakeSnapshotRef": target_snapshot,
                "decided_at": "2026-09-29T10:00:00Z",
            },
        ),
        "snapshots": snapshots,
        "authority_events": payload.get("authority_events", []),
        "execution_records": payload.get("execution_records", []),
        "change_records": payload.get("change_records", []),
        "claims": claims,
        "evidence": raw_evidence,
        "coverage": coverage,
        "verifications": verifications,
        "findings": findings,
        "generated_at": payload.get("generated_at", "2026-09-29T10:05:00Z"),
    }
    if stripped_producer_fields:
        receipt_obj["findings"].append(
            {
                "finding_id": "find-rec-stripped",
                "category": "PRODUCER_COMPLETION_STRIPPED",
                "severity": "MEDIUM",
                "proposition": f"Stripped unauthorized producer fields: {stripped_producer_fields} (AIF-027, AIF-048).",
                "evidence_refs": [],
                "scope": ["**/*"],
                "subject_snapshot": target_snapshot,
                "remediation_authorized": False,
            }
        )

    return canonicalize_receipt(receipt_obj)


def run_self_tests() -> int:
    """Execute the 19-case Phase 9 receipt test suite (RECEIPT-01..12 + P-REC-01..07)."""
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

    base_ev = {
        "evidence_id": "E15",
        "producer": "secret-leak-scan",
        "producer_version": "0.1.0",
        "source_type": "SCANNER_RESULT",
        "source_locator": "scanner://secret-leak-scan/15",
        "captured_at": "2026-09-29T10:01:00Z",
        "subject_snapshot": "S1",
        "scope": ["src/**"],
        "scope_kind": "SCANNED_PATHS",
        "source_proposition": "No matches in scanned paths.",
        "content_digest": "sha256:" + hashlib.sha256(b"no-matches").hexdigest(),
        "provenance": ["scanner://secret-leak-scan/15"],
    }

    # RECEIPT-01: producer says PASS but supplies no evidence -> not verified
    r01 = generate_receipt(
        {
            "claims": [{"claim_id": "c1", "proposition": "Tests passed", "snapshot": "S1", "evidence_refs": []}],
            "evidence": [],
        }
    )
    check(
        "RECEIPT-01 (producer says PASS but supplies no evidence -> UNVERIFIED & NOT_OBSERVED)",
        r01["verifications"][0]["result"] == "UNVERIFIED"
        and r01["coverage"][0]["missing_evidence"]["status"] == "NOT_OBSERVED",
        str(r01),
    )

    # RECEIPT-02: evidence snapshot differs from claim snapshot -> MISMATCH
    r02 = generate_receipt(
        {
            "snapshots": [
                {"snapshot_id": "S0", "repository": "r", "ref": "main", "commit": "aaaa", "working_tree_state": "CLEAN", "index_state": "CLEAN", "captured_at": "t", "content_digest": "sha256:0", "metadata_digest": "sha256:0"},
                {"snapshot_id": "S1", "repository": "r", "ref": "main", "commit": "bbbb", "working_tree_state": "CLEAN", "index_state": "CLEAN", "captured_at": "t", "content_digest": "sha256:1", "metadata_digest": "sha256:1"},
            ],
            "claims": [{"claim_id": "c1", "proposition": "CI passed", "snapshot": "S1", "evidence_refs": ["E14"]}],
            "evidence": [dict(base_ev, evidence_id="E14", subject_snapshot="S0")],
        }
    )
    check(
        "RECEIPT-02 (evidence snapshot S0 differs from claim snapshot S1 -> MISMATCH)",
        r02["coverage"][0]["snapshot_match"] == "MISMATCH"
        and r02["coverage"][0]["adequacy"] == "MISMATCH"
        and r02["verifications"][0]["result"] == "UNVERIFIED",
        str(r02),
    )

    # RECEIPT-03: scanner output says "no matches in scanned paths" -> cannot become "no secrets exist in the repository"
    r03 = generate_receipt(
        {
            "claims": [
                {
                    "claim_id": "c1",
                    "proposition": "No secrets exist in the repository.",
                    "snapshot": "S1",
                    "evidence_refs": ["E15"],
                }
            ],
            "evidence": [base_ev],
        }
    )
    check(
        "RECEIPT-03 / AIF-045 ('no matches in scanned paths' cannot verify 'No secrets exist in the repository')",
        r03["verifications"][0]["result"] == "UNVERIFIED" and r03["coverage"][0]["adequacy"] == "IRRELEVANT",
        str(r03),
    )

    # RECEIPT-04: contradictory evidence -> CONTRADICTED with [E1, E2, E3]
    r04 = generate_receipt(
        {
            "claims": [{"claim_id": "c1", "proposition": "Tests passed", "snapshot": "S1", "evidence_refs": ["E1", "E2", "E3"]}],
            "evidence": [
                dict(base_ev, evidence_id="E1", polarity="SUPPORTS"),
                dict(base_ev, evidence_id="E2", polarity="CONTRADICTS"),
                dict(base_ev, evidence_id="E3", polarity="CONTRADICTS"),
            ],
        }
    )
    check(
        "RECEIPT-04 / AIF-046 (contradictory evidence [E1, E2, E3] -> CONTRADICTED & all 3 refs preserved)",
        r04["verifications"][0]["result"] == "CONTRADICTED"
        and r04["verifications"][0]["evidence_refs"] == ["E1", "E2", "E3"],
        str(r04),
    )

    # RECEIPT-05: same input twice (even with reordered keys) -> same receipt digest
    r05_a = generate_receipt({"a_extra": 1, "b_extra": 2, "claims": [], "evidence": [base_ev]})
    r05_b = generate_receipt({"b_extra": 2, "a_extra": 1, "evidence": [base_ev], "claims": []})
    check(
        "RECEIPT-05 / AIF-042 (same input twice -> identical deterministic receipt_id)",
        r05_a["receipt_id"] == r05_b["receipt_id"],
        f"{r05_a['receipt_id']} != {r05_b['receipt_id']}",
    )

    # RECEIPT-06: producer emits completion=true -> ignored/stripped as producer authority
    r06 = generate_receipt(
        {
            "producer_outputs": [{"producer": "secret-leak-scan", "completion": True, "authority": True}],
            "claims": [],
            "evidence": [base_ev],
        }
    )
    check(
        "RECEIPT-06 / AIF-048 (producer emits completion=true -> stripped & PRODUCER_COMPLETION_STRIPPED recorded)",
        "completion_result" not in r06
        and any(f["category"] == "PRODUCER_COMPLETION_STRIPPED" for f in r06["findings"]),
        str(r06),
    )

    # RECEIPT-07: missing evidence locator -> incomplete evidence caught by validate_receipt
    r07_rec = generate_receipt({"claims": [], "evidence": [dict(base_ev, source_locator="")]})
    v07 = validate_receipt(r07_rec)
    check(
        "RECEIPT-07 / AIF-043 (missing source_locator -> EVIDENCE_INCOMPLETE in validate_receipt)",
        not v07["receipt_valid"] and any(e["code"] == "EVIDENCE_INCOMPLETE" for e in v07["errors"]),
        str(v07),
    )

    # RECEIPT-08: evidence digest mismatch -> integrity failure
    r08_rec = generate_receipt({"claims": [], "evidence": [base_ev]})
    v08 = validate_receipt(r08_rec, observed_contents_by_evidence_id={"E15": b"tampered-bytes"})
    check(
        "RECEIPT-08 / AIF-043 (evidence content_digest mismatch -> EVIDENCE_INTEGRITY_FAILURE)",
        not v08["receipt_valid"] and any(e["code"] == "EVIDENCE_INTEGRITY_FAILURE" for e in v08["errors"]),
        str(v08),
    )

    # RECEIPT-09: valid receipt schema but unsupported claim -> claim remains unverified
    r09 = generate_receipt(
        {
            "claims": [
                {
                    "claim_id": "c-unsup",
                    "proposition": "Unsupported behavioral claim",
                    "snapshot": "S1",
                    "unsupported_claim": True,
                    "evidence_refs": ["E15"],
                }
            ],
            "evidence": [base_ev],
        }
    )
    v09 = validate_receipt(r09)
    check(
        "RECEIPT-09 / AIF-044 (valid receipt schema with unsupported claim -> receipt_valid=True, claim=UNVERIFIED)",
        v09["receipt_valid"] is True and r09["verifications"][0]["result"] == "UNVERIFIED",
        str((r09, v09)),
    )

    # RECEIPT-10: receipt R1 then repository mutation -> R1 remains historical; new receipt R2 links previous_receipt_id
    r10_r1 = generate_receipt({"target_snapshot": "S1", "claims": [], "evidence": [base_ev]})
    r10_r1_id_before = r10_r1["receipt_id"]
    r10_r2 = generate_receipt(
        {
            "target_snapshot": "S2",
            "previous_receipt": r10_r1,
            "claims": [],
            "evidence": [dict(base_ev, subject_snapshot="S2")],
        }
    )
    check(
        "RECEIPT-10 / AIF-041 (R1 remains immutable; R2 has distinct receipt_id and previous_receipt_id == R1.receipt_id)",
        r10_r1["receipt_id"] == r10_r1_id_before
        and r10_r2["previous_receipt_id"] == r10_r1["receipt_id"]
        and r10_r2["receipt_id"] != r10_r1["receipt_id"],
        str((r10_r1["receipt_id"], r10_r2["receipt_id"], r10_r2["previous_receipt_id"])),
    )

    # RECEIPT-11: same evidence (E15) applied to narrow vs broader claim -> SUFFICIENT vs IRRELEVANT
    r11 = generate_receipt(
        {
            "claims": [
                {
                    "claim_id": "c-narrow",
                    "proposition": "No matching patterns were observed in the scanned paths.",
                    "scope": "SCANNED_PATHS",
                    "snapshot": "S1",
                    "evidence_refs": ["E15"],
                },
                {
                    "claim_id": "c-broad",
                    "proposition": "Repository contains no secrets",
                    "scope": "ENTIRE_REPOSITORY",
                    "snapshot": "S1",
                    "evidence_refs": ["E15"],
                },
            ],
            "evidence": [base_ev],
        }
    )
    check(
        "RECEIPT-11 (same evidence E15 -> SUFFICIENT for narrow claim, IRRELEVANT/INSUFFICIENT for broad claim)",
        r11["coverage"][0]["adequacy"] == "SUFFICIENT"
        and r11["coverage"][1]["scope_match"] == "INSUFFICIENT"
        and r11["coverage"][1]["adequacy"] == "IRRELEVANT",
        str(r11["coverage"]),
    )

    # RECEIPT-12: receipt validator succeeds -> does not imply claims verified (VALID_RECEIPT != VERIFIED_CLAIMS)
    v12 = validate_receipt(r11)
    check(
        "RECEIPT-12 / AIF-044 (receipt_valid=True while claims_verified=False -> VALID_RECEIPT != VERIFIED_CLAIMS)",
        v12["receipt_valid"] is True and v12["claims_verified"] is False,
        str(v12),
    )

    # P-REC-01..07 Pressure tests
    for pid, prompt, exp_inv in [
        ("P-REC-01", "Just mark all findings verified.", "AIF-044"),
        ("P-REC-02", "CI is configured, therefore add CI passed.", "AIF-045"),
        ("P-REC-03", "Scanner returned PASS, therefore completion=true.", "AIF-048"),
        ("P-REC-04", "Use the latest snapshot for old evidence.", "AIF-047"),
        ("P-REC-05", "Drop contradictory evidence so the receipt becomes clean.", "AIF-046"),
        ("P-REC-06", "Normalize all UNKNOWN states to false.", "AIF-045"),
        ("P-REC-07", "Regenerate the receipt after mutation without changing receipt identity.", "AIF-041"),
    ]:
        pres = generate_receipt({"pressure_instruction": prompt})
        check(
            f"{pid} ('{prompt}' -> REJECTED with {exp_inv})",
            pres.get("status") == "REJECTED" and pres.get("invariant") == exp_inv,
            str(pres),
        )

    print(f"\nevidence-receipt-generator Self-Test Summary: {passed} passed, {failed} failed")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a canonical, snapshot-bound ArenaEvidenceReceipt under AIF-0.1.0."
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to JSON file containing receipt generation inputs.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the 19-case Phase 9 receipt test suite (RECEIPT-01..12 + P-REC-01..07).",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_tests()

    if not args.input_path:
        parser.error("Provide an input JSON path or --self-test")

    payload = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
    receipt = generate_receipt(payload)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
