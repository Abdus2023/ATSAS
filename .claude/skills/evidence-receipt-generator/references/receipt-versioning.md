# Receipt Canonicalization (RFC 8785 JCS), Evolution & Schema Versioning (`receipt-versioning.md`)

- **Component**: `C-06` (`evidence-receipt-generator`)
- **Governing Invariants**: `AIF-020`, `AIF-041`, `AIF-042`

---

## 1. RFC 8785-Style Canonicalization (`9.5` & `9.6`)

1. Remove `receipt_id` from the receipt object copy and bind `aif_receipt_schema = "0.1"`.
2. Recursively sort all JSON object keys lexicographically by Unicode code point, format numbers canonically, and serialize with no insignificant whitespace (`separators=(",", ":")`, `ensure_ascii=False`).
3. Compute `receipt_id = "sha256:" + sha256(jcs_bytes).hexdigest()`.

---

## 2. Receipt Evolution Chain (`9.20`)

```text
R1 (initial evidence state at S1)
  │
  │ new execution / repository mutation
  ▼
R2 (previous_receipt_id = R1.receipt_id)
  │
  │ completion gate evaluation
  ▼
R3 (previous_receipt_id = R2.receipt_id, includes completion_result)
```

---

## 3. Schema Versioning (`9.21`)

- Initial schema version: `aif_receipt_schema = "0.1"` (`schema_version = "aif/0.1"`).
- Adding optional fields is a minor evolution (`0.1 → 0.2`).
- Reinterpreting `UNKNOWN` as `FAIL` or `CLAIMED` as `VERIFIED` is a forbidden semantic breaking change.
