---
name: evidence-receipt-generator
description: Assembles, normalizes, canonicalizes (RFC 8785 JCS), and validates immutable snapshot-bound ArenaEvidenceReceipts across authority, scope, CI, test execution, supply-chain, and detector producers under AIF-0.1.0 without granting authority or completion (`VALID_RECEIPT != VERIFIED_CLAIMS`). Enforces AIF-041..AIF-048 (SCOPE: ARENA_GENERIC).
---

# Evidence Receipt Generator (`evidence-receipt-generator` — Component `C-06`)

```text
SCOPE: ARENA_GENERIC
AIF_VERSION: 0.1.0
COMPONENT_ID: C-06
MUTATES_REPOSITORY: false
```

- **Protocol Binding**: `AIF-0.1.0` ([`../_shared/aif/VERSION`](../_shared/aif/VERSION))
- **Contract ID**: `C-06` ([`../../assurance/component-contracts.md`](../../assurance/component-contracts.md))
- **Governing Invariants**: `AIF-006`–`AIF-008A`, `AIF-013`–`AIF-020`, `AIF-026`, `AIF-027`, `AIF-041` (Receipt Immutability), `AIF-042` (Receipt Determinism), `AIF-043` (Evidence Referential Integrity), `AIF-044` (Receipt Validation Non-Transitivity), `AIF-045` (Normalization Non-Expansion), `AIF-046` (Contradiction Preservation), `AIF-047` (Historical Snapshot Preservation), `AIF-048` (Completion Separation)

---

## 1. Purpose & Core Boundary (`9.1` & `9.24`)

`evidence-receipt-generator` answers:
> **What exactly was observed, against which repository state, by which execution, from which evidence, and which claims can legitimately be verified from it?**

It must **not** answer *"Is the task done?"* — that belongs exclusively to `arena-completion-gate` (`C-07`).

```text
Evidence Producer → Evidence Normalization → Evidence Receipt → Verification → Acceptance
```

---

## 2. Historical Immutability, Optional `completion_result` & RFC 8785 Canonicalization (`9.2`–`9.6`)

1. **Historical Immutability (`AIF-041`)**:
   `Receipt R1` describes what the assurance system knew at a point in time and is never mutated in place. Repository changes produce `Receipt R2` with `previous_receipt_id = R1.receipt_id` (`R1 → R2 → R3`).
2. **Optional `acceptance_expression` & `completion_result` (`9.4` & `AIF-048`)**:
   In [`evidence-receipt.schema.json`](../_shared/aif/schema/evidence-receipt.schema.json), `acceptance_expression` and `completion_result` are optional so `Receipt R1` can represent pure evidence state before completion evaluation.
3. **Deterministic `receipt_id` via RFC 8785 JCS (`9.5` & `9.6`, `AIF-042`)**:
   ```text
   receipt_id = "sha256:" + sha256(JCS(receipt_without_receipt_id + canonical_schema_version))
   ```
   Semantically equivalent JSON inputs (`{"a":1,"b":2}` and `{"b":2,"a":1}`) canonicalize to identical bytes and identical `receipt_id` (`RECEIPT-05`, `RED-36`).

---

## 3. Evidence Normalization, Coverage Matrix & Validator $\neq$ Verifier (`9.7`–`9.18`)

- **Normalization Non-Expansion (`AIF-016`, `AIF-045`)**: `"No matches in scanned paths"` normalizes to `"No matching patterns were observed in the scanned paths"` — never `"No secrets exist in the repository"` (`RECEIPT-03`).
- **Standardized `source_locator` URIs (`9.9`)**: `execution://...`, `git://blob/...`, `ci://run/...`, `ci://run/.../artifact/...`, `test://execution/.../report`, `scanner://...`, `authority://event/...`.
- **Coverage & Contradictions (`9.10`–`9.13`, `AIF-046`)**: Computes `EvidenceCoverage` (`subject_match`, `snapshot_match`, `scope_match`, `method_match`, `freshness`, `adequacy`, `limitations`), preserves conflicting evidence as `CONTRADICTED` (`[E1, E2, E3]`), and represents missing evidence explicitly (`{"status": "NOT_OBSERVED", "reason": "NO_CI_RUN_EVIDENCE"}`, never generic `null`).
- **Validator $\neq$ Verifier (`9.15`–`9.16`, `AIF-044`)**: `validate_receipt.py` checks Structural, Referential, Semantic, and Integrity rules, keeping `RECEIPT_VALID ≠ CLAIMS_VERIFIED`.

---

## 4. Deterministic Execution

```bash
# Run the 19-case Phase 9 self-test suite (RECEIPT-01..12 + P-REC-01..07)
python3 .claude/skills/evidence-receipt-generator/scripts/generate_receipt.py --self-test

# Canonicalize a receipt JSON file and print its deterministic receipt_id
python3 .claude/skills/evidence-receipt-generator/scripts/canonicalize_receipt.py path/to/receipt.json

# Validate structural, referential, semantic, and integrity properties of a receipt
python3 .claude/skills/evidence-receipt-generator/scripts/validate_receipt.py path/to/receipt.json
```

See [`README.md`](README.md), [`references/receipt-model.md`](references/receipt-model.md), [`references/evidence-normalization.md`](references/evidence-normalization.md), [`references/claim-coverage.md`](references/claim-coverage.md), and [`references/receipt-versioning.md`](references/receipt-versioning.md).
