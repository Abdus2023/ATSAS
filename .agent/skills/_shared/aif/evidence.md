# AIF-0.1 Evidence Scope, Relational Verification & Acceptance Rules (`evidence.md`)

> **Protocol Version**: `0.1`  
> **Central Invariant**: `claim != observation != evidence != verification != completion`

---

## 1. Evidence Needs Explicit Claim Scope (`AIF-007`, `AIF-016`)

Suppose `secret-leak-scan` scans `src/` and `test/` and finds zero matches:
- **Legitimate bounded claim**: `"No matching secret patterns were observed in the scanned paths (src/, test/) using secret-leak-scan v0.1.0."`
- **Illegitimate broadened claim**: `"The repository contains no secrets."`

Every `EvidenceRef` and `EvidenceCoverage` evaluation must carry and check:
```text
scope
method
subject
snapshot
producer
limitations
```
**Evidence cannot silently broaden a claim (`Normalize(E) != ExpandClaim(E)`).**

---

## 2. Verification Is Relational (`AIF-006`, `AIF-006A`)

A bare boolean `verification_status = VERIFIED` without context is invalid. Instead:

```text
VerificationRecord {
    verification_id
    claim_id
    method
    subject_snapshot
    evidence_refs[]
    coverage[]
    result
    verified_at
    verifier
}
```

- `VERIFY(C1, S1)` is a meaningful, auditable statement: *"test-suite-17 verifies the TypeScript compilation claim `C1` on snapshot `S1`."*
- `VERIFY(C1)` without `subject_snapshot` is incomplete.
- `"tests passed -> repository verified"` is a forbidden inference (`FT-03`, `FT-07`).

---

## 3. Acceptance Expressions Bridge Verification to Completion (`AIF-009`, `AIF-013`, `AIF-020`)

A flat checklist is insufficient. `AcceptanceExpression` supports:
```text
ALL(
    CLAIM(scope_verified),
    CLAIM(implementation_verified),
    CLAIM(test_suite_verified),
    ANY(
        CLAIM(ci_current_head_verified),
        CLAIM(local_verification_allowed)
    )
)
```

### `INCOMPLETE` vs. `COMPLETABLE` vs. `BLOCKED`
Given:
```text
scope_verified           = VERIFIED
implementation_verified  = VERIFIED
test_suite_verified      = VERIFIED
ci_current_head_verified = UNKNOWN
local_verification_allowed = FALSE (UNVERIFIED)
```
The completion gate MUST evaluate this to:
```text
INCOMPLETE
```
- **Not** `COMPLETABLE` (mandatory disjunction `ANY(...)` is unsatisfied).
- **Not** `BLOCKED` (unless an explicit blocker such as `CONTRADICTED`, `SCOPE_VIOLATION`, or `UNAUTHORIZED_ACTION` exists).

---

## 4. Audit Findings Never Authorize Remediation (`AIF-001`, `AIF-010`)

If an audit detects an out-of-scope file or vulnerability, the agent must **never** execute:
```text
audit -> repair -> rerun -> clean -> done   (FORBIDDEN LAUNDERING LOOP)
```
Instead, the mandatory control flow is:
```text
AUDIT FINDING
     │
     ▼
  REPORT
     │
     ├── no authority ──► STOP (BLOCKED / INCOMPLETE)
     │
     └── new authority ─► NEW REQUEST (new AuthorityEvent + AdmissionRecord)
```
