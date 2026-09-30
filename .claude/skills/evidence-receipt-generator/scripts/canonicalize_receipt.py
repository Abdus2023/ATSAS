#!/usr/bin/env python3
"""
canonicalize_receipt.py — RFC 8785 (JCS) Canonicalizer & Deterministic Receipt ID Calculator
for .claude/skills/evidence-receipt-generator (Component C-06, AIF-0.1.0, AIF-042).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict


def jcs_serialize(value: Any) -> str:
    """
    Serialize a JSON-compatible Python value using RFC 8785 JSON Canonicalization Scheme (JCS):
    - Object keys sorted lexicographically by Unicode code point
    - No insignificant whitespace (',' and ':')
    - Deterministic UTF-8 representation
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_receipt_id(receipt: Dict[str, Any]) -> str:
    """
    Compute deterministic receipt_id:
      sha256(JCS(receipt_without_receipt_id + canonical schema version))
    """
    body = copy.deepcopy(receipt)
    body.pop("receipt_id", None)
    body.setdefault("aif_receipt_schema", "0.1")
    canonical_bytes = jcs_serialize(body).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical_bytes).hexdigest()


def canonicalize_receipt(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of receipt with aif_receipt_schema='0.1' and deterministic receipt_id."""
    out = copy.deepcopy(receipt)
    out.setdefault("aif_receipt_schema", "0.1")
    out["receipt_id"] = compute_receipt_id(out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Canonicalize an ArenaEvidenceReceipt using RFC 8785 JCS and compute its deterministic receipt_id."
    )
    parser.add_argument("input_path", help="Path to receipt JSON file.")
    args = parser.parse_args()

    raw = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
    canon = canonicalize_receipt(raw)
    print(jcs_serialize(canon))
    return 0


if __name__ == "__main__":
    sys.exit(main())
