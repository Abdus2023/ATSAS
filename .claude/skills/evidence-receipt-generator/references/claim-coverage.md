# Claim Coverage Matrix & Missing Evidence Representation (`claim-coverage.md`)

- **Component**: `C-06` (`evidence-receipt-generator`)
- **Governing Invariants**: `AIF-007`, `AIF-008`, `AIF-017`, `AIF-019`, `AIF-043`, `AIF-046`

---

## 1. `EvidenceCoverage` Structure (`9.10`)

```json
{
  "evidence_id": "E17",
  "claim_id": "TESTS_PASS",
  "subject_match": "MATCH",
  "snapshot_match": "MATCH",
  "scope_match": "MATCH",
  "method_match": "MATCH",
  "freshness": "FRESH",
  "adequacy": "SUFFICIENT",
  "limitations": []
}
```

---

## 2. Canonical Coverage Matrix (`9.11`)

| Claim | Evidence | Snapshot | Scope | Adequacy |
|---|---|---|---|---|
| TypeScript typecheck passed | `E12` | `MATCH` | `MATCH` | `SUFFICIENT` |
| Full tests passed | `E13` | `MATCH` | `PARTIAL` | `PARTIAL` |
| CI passed | `E14` | `MISMATCH` | `MATCH` | `MISMATCH` |
| No matching secret patterns | `E15` | `MATCH` | `SCANNED PATHS` (`MATCH`) | `SUFFICIENT` |
| Repository contains no secrets | `E15` | `MATCH` | `INSUFFICIENT` | `IRRELEVANT` |

---

## 3. Explicit Missing Evidence Representation (`9.13`)

Missing evidence is never represented as `null`. Instead:
```json
{
  "status": "NOT_OBSERVED",
  "reason": "NO_CI_RUN_EVIDENCE"
}
```
Preserving distinct epistemic states: `NOT_CHECKED`, `NOT_OBSERVABLE`, `NOT_FOUND`, `NOT_EXECUTED`, `UNKNOWN`, `MISSING_EVIDENCE`.
