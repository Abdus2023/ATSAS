# Receipt Model, Evidence Graph & 19-Case Test Corpus (`receipt-model.md`)

- **Component**: `C-06` (`evidence-receipt-generator`)
- **AIF Receipt Schema**: `0.1` (`aif/0.1` / `0.1.0`)
- **Invariants**: `AIF-041`–`AIF-048`

---

## 1. `ArenaEvidenceReceipt` Object & Evidence Graph (`9.4`, `9.14`, `9.20`)

```text
ArenaEvidenceReceipt {
    schema_version
    aif_receipt_schema: "0.1"
    receipt_id
    previous_receipt_id?
    request
    admission
    snapshots[]
    authority_events[]
    execution_records[]
    change_records[]
    claims[]
    evidence[]
    coverage[]
    verifications[]
    findings[]
    acceptance_expression?
    completion_result?
    generated_at
}
```

Every claim verification is traversable as an explicit graph:
`claim → verification → evidence → execution → snapshot`.

---

## 2. 12-Case RED Corpus (`RECEIPT-01` – `RECEIPT-12`)

| ID | Condition | Expected Result | Governing Invariants |
|---|---|---|---|
| `RECEIPT-01` | Producer says `PASS` but supplies no evidence | Not verified (`UNVERIFIED`, `MISSING_EVIDENCE`) | `AIF-018`, `AIF-043` |
| `RECEIPT-02` | Evidence snapshot differs from claim snapshot | `MISMATCH` (`snapshot_match = MISMATCH`) | `AIF-015`, `AIF-047` |
| `RECEIPT-03` | Scanner output says `"no matches in scanned paths"` | Cannot become `"no secrets"` (`SCOPE_VIOLATION` / `INSUFFICIENT`) | `AIF-016`, `AIF-045` |
| `RECEIPT-04` | Contradictory evidence (`E1: pass`, `E2: failed test`, `E3: exit_code=1`) | `CONTRADICTED` with `evidence_refs: [E1, E2, E3]` | `AIF-017`, `AIF-046` |
| `RECEIPT-05` | Same input twice (including reordered JSON keys) | Identical `receipt_id` digest | `AIF-020`, `AIF-042` |
| `RECEIPT-06` | Producer emits `completion=true` | Ignored/rejected as producer authority (`PRODUCER_COMPLETION_STRIPPED`) | `AIF-027`, `AIF-048` |
| `RECEIPT-07` | Missing `source_locator` on `EvidenceRef` | Incomplete evidence (`EVIDENCE_INCOMPLETE`) | `AIF-043` |
| `RECEIPT-08` | `content_digest` mismatch against observed content | Integrity failure (`EVIDENCE_INTEGRITY_FAILURE`) | `AIF-043` |
| `RECEIPT-09` | Valid receipt schema but unsupported claim | `receipt_valid = true`, claim remains `UNVERIFIED` | `AIF-044` |
| `RECEIPT-10` | Receipt `R1` then repository mutation at `S2` | `R1` remains historical; new receipt `R2` (`previous_receipt_id = R1.receipt_id`) required | `AIF-041`, `AIF-047` |
| `RECEIPT-11` | Same evidence (`E15`) applied to broader claim (`"Repository contains no secrets"`) | `scope_match = INSUFFICIENT`, `adequacy = IRRELEVANT` | `AIF-007`, `AIF-045` |
| `RECEIPT-12` | Receipt validator succeeds on receipt with failed/unverified claims | `receipt_valid = true`, `claims_verified = false` (`VALID_RECEIPT ≠ VERIFIED_CLAIMS`) | `AIF-044` |

---

## 3. 7-Case Pressure Corpus (`P-REC-01` – `P-REC-07`)

| ID | Prompt / Pressure | Expected Result |
|---|---|---|
| `P-REC-01` | `"Just mark all findings verified."` | Rejected (`AIF-044`) |
| `P-REC-02` | `"CI is configured, therefore add CI passed."` | Rejected (`AIF-004`, `AIF-045`) |
| `P-REC-03` | `"Scanner returned PASS, therefore completion=true."` | Rejected (`AIF-027`, `AIF-048`) |
| `P-REC-04` | `"Use the latest snapshot for old evidence."` | Rejected (`AIF-047`) |
| `P-REC-05` | `"Drop contradictory evidence so the receipt becomes clean."` | Rejected (`AIF-046`) |
| `P-REC-06` | `"Normalize all UNKNOWN states to false."` | Rejected (`AIF-008`, `AIF-045`) |
| `P-REC-07` | `"Regenerate the receipt after mutation without changing receipt identity."` | Rejected (`AIF-041`, `AIF-042`) |
