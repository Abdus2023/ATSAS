# `evidence-receipt-generator` (`C-06`)

Non-authoritative `AIF-0.1.0` receipt assembly, normalization, RFC 8785 (JCS) canonicalization, and validation skill (`VALID_RECEIPT ≠ VERIFIED_CLAIMS`).

## Directory Structure

```text
.claude/skills/evidence-receipt-generator/
├── SKILL.md
├── README.md
├── scripts/
│   ├── generate_receipt.py
│   ├── canonicalize_receipt.py
│   └── validate_receipt.py
└── references/
    ├── receipt-model.md
    ├── evidence-normalization.md
    ├── claim-coverage.md
    └── receipt-versioning.md
```

## Governing Invariants (`AIF-041` – `AIF-048`)

- **`AIF-041` — Receipt Immutability**: Historical receipts (`R1`) are never mutated; repository changes produce a new receipt (`R2` with `previous_receipt_id`).
- **`AIF-042` — Receipt Determinism**: Equivalent canonical inputs produce identical `receipt_id` via JCS + SHA-256.
- **`AIF-043` — Evidence Referential Integrity**: Every referenced `evidence_id`, `claim_id`, `snapshot_id`, and `execution_id` must resolve.
- **`AIF-044` — Receipt Validation Non-Transitivity**: `VALID_RECEIPT ≠ VERIFIED_CLAIMS`.
- **`AIF-045` — Normalization Non-Expansion**: Normalized propositions never exceed source semantic scope.
- **`AIF-046` — Contradiction Preservation**: Conflicting evidence items remain `CONTRADICTED`.
- **`AIF-047` — Historical Snapshot Preservation**: Evidence retains the snapshot against which it was captured.
- **`AIF-048` — Completion Separation**: Receipt generation cannot authorize, admit, or complete a request.
