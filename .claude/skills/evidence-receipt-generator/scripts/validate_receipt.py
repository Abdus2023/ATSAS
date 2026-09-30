#!/usr/bin/env python3
"""
validate_receipt.py — Structural, Referential, Semantic, and Integrity Validator
for ArenaEvidenceReceipt (.claude/skills/evidence-receipt-generator, Component C-06).

Enforces Section 9.15 & 9.16:
  RECEIPT_VALID != CLAIMS_VERIFIED (AIF-044)
  AIF-041..AIF-048
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from canonicalize_receipt import compute_receipt_id


REQUIRED_FIELDS = (
    "schema_version",
    "receipt_id",
    "request",
    "admission",
    "snapshots",
    "authority_events",
    "execution_records",
    "change_records",
    "claims",
    "evidence",
    "coverage",
    "verifications",
    "findings",
    "generated_at",
)


def validate_receipt(
    receipt: Dict[str, Any],
    observed_contents_by_evidence_id: Dict[str, bytes] | None = None,
) -> Dict[str, Any]:
    """
    Validate Structural, Referential, Semantic, and Integrity constraints of an ArenaEvidenceReceipt.
    Explicitly separates `receipt_valid` from `claims_verified` (AIF-044).
    """
    errors: List[Dict[str, str]] = []

    def add_err(layer: str, code: str, message: str, invariant: str) -> None:
        errors.append(
            {
                "layer": layer,
                "code": code,
                "invariant": invariant,
                "message": message,
            }
        )

    # 1. Structural checks
    for field in REQUIRED_FIELDS:
        if field not in receipt:
            add_err("STRUCTURAL", "MISSING_REQUIRED_FIELD", f"Missing required field '{field}'.", "AIF-043")

    if errors:
        return {
            "receipt_valid": False,
            "claims_verified": False,
            "errors": errors,
        }

    # 2. Referential checks (evidence_id, claim_id, snapshot_id, execution_id)
    snapshots_by_id = {s.get("snapshot_id"): s for s in receipt.get("snapshots", []) if isinstance(s, dict)}
    claims_by_id = {c.get("claim_id"): c for c in receipt.get("claims", []) if isinstance(c, dict)}
    evidence_by_id = {e.get("evidence_id"): e for e in receipt.get("evidence", []) if isinstance(e, dict)}
    execs_by_id = {x.get("execution_id"): x for x in receipt.get("execution_records", []) if isinstance(x, dict)}

    for ev_id, ev in evidence_by_id.items():
        if not (ev.get("source_locator") or "").strip():
            add_err(
                "REFERENTIAL",
                "EVIDENCE_INCOMPLETE",
                f"EvidenceRef '{ev_id}' has missing or empty source_locator.",
                "AIF-043",
            )
        subj_snap = ev.get("subject_snapshot")
        if subj_snap not in snapshots_by_id:
            add_err(
                "REFERENTIAL",
                "SNAPSHOT_NOT_FOUND",
                f"EvidenceRef '{ev_id}' references unknown snapshot '{subj_snap}'.",
                "AIF-043",
            )

    for cov in receipt.get("coverage", []):
        cid = cov.get("claim_id")
        eid = cov.get("evidence_id")
        if cid not in claims_by_id:
            add_err("REFERENTIAL", "CLAIM_NOT_FOUND", f"Coverage references unknown claim_id '{cid}'.", "AIF-043")
        if eid and eid not in evidence_by_id:
            add_err("REFERENTIAL", "EVIDENCE_NOT_FOUND", f"Coverage references unknown evidence_id '{eid}'.", "AIF-043")
        # Semantic check: coverage cannot be SUFFICIENT when snapshot mismatches
        if cov.get("snapshot_match") in (False, "MISMATCH") and cov.get("adequacy") == "SUFFICIENT":
            add_err(
                "SEMANTIC",
                "MISMATCHED_SNAPSHOT_SUFFICIENT",
                f"Coverage for claim '{cid}' claims adequacy=SUFFICIENT despite snapshot MISMATCH.",
                "AIF-047",
            )

    for ver in receipt.get("verifications", []):
        cid = ver.get("claim_id")
        if cid not in claims_by_id:
            add_err("REFERENTIAL", "CLAIM_NOT_FOUND", f"Verification references unknown claim_id '{cid}'.", "AIF-043")
        ev_refs = ver.get("evidence_refs", [])
        if ver.get("result") == "VERIFIED" and not ev_refs:
            add_err(
                "SEMANTIC",
                "VERIFIED_WITHOUT_EVIDENCE",
                f"Verification '{ver.get('verification_id')}' claims VERIFIED with empty evidence_refs.",
                "AIF-043",
            )
        for eid in ev_refs:
            if eid not in evidence_by_id:
                add_err(
                    "REFERENTIAL",
                    "EVIDENCE_NOT_FOUND",
                    f"Verification '{ver.get('verification_id')}' references unknown evidence_id '{eid}'.",
                    "AIF-043",
                )
            else:
                ev_obj = evidence_by_id[eid]
                cl_obj = claims_by_id.get(cid, {})
                if (
                    ver.get("result") == "VERIFIED"
                    and not ev_obj.get("snapshot_independent", False)
                    and ev_obj.get("subject_snapshot") != cl_obj.get("snapshot")
                ):
                    add_err(
                        "SEMANTIC",
                        "VERIFICATION_SNAPSHOT_MISMATCH",
                        f"Verification for claim '{cid}' (snapshot '{cl_obj.get('snapshot')}') uses evidence '{eid}' from mismatched snapshot '{ev_obj.get('subject_snapshot')}'.",
                        "AIF-047",
                    )

    # 3. Integrity checks (content_digest & receipt_id)
    if observed_contents_by_evidence_id:
        for eid, raw_bytes in observed_contents_by_evidence_id.items():
            if eid in evidence_by_id:
                actual_digest = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
                recorded_digest = evidence_by_id[eid].get("content_digest")
                if recorded_digest != actual_digest:
                    add_err(
                        "INTEGRITY",
                        "EVIDENCE_INTEGRITY_FAILURE",
                        f"EvidenceRef '{eid}' content_digest '{recorded_digest}' != observed '{actual_digest}'.",
                        "AIF-043",
                    )

    expected_receipt_id = compute_receipt_id(receipt)
    if receipt.get("receipt_id") != expected_receipt_id:
        add_err(
            "INTEGRITY",
            "RECEIPT_ID_MISMATCH",
            f"receipt_id '{receipt.get('receipt_id')}' != canonical digest '{expected_receipt_id}'.",
            "AIF-042",
        )

    receipt_valid = len(errors) == 0
    verifications = receipt.get("verifications", [])
    claims_verified = bool(verifications) and all(v.get("result") == "VERIFIED" for v in verifications)

    return {
        "receipt_valid": receipt_valid,
        "claims_verified": claims_verified if receipt_valid else False,
        "valid_receipt_implies_verified_claims": False,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Structural, Referential, Semantic, and Integrity properties of an ArenaEvidenceReceipt."
    )
    parser.add_argument("input_path", help="Path to receipt JSON file.")
    args = parser.parse_args()

    receipt = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
    res = validate_receipt(receipt)
    print(json.dumps(res, indent=2))
    return 0 if res["receipt_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
