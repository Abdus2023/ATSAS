# AIF-0.1 State Machines & Canonical Transition Theorem

> **Protocol Version**: `0.1`  
> **Core Rule**: The four state machines (`Authority`, `Execution`, `Verification`, `Completion`) + `Snapshot` states must **never** collapse into a single status enum.

---

## 1. Snapshot Working-Tree & Index States

```text
CLEAN
DIRTY
PARTIAL
UNKNOWN
```

### Non-Equivalence Axiom (`AIF-002A`)
```text
HEAD = abc123, working_tree_state = DIRTY
  ≢
HEAD = abc123, working_tree_state = CLEAN
```

### Canonical Snapshot Roles (`AIF-002`)
1. `comparison_base` — reference used for historical/diff comparison
2. `intake_snapshot` — state observed when the task was admitted
3. `execution_snapshot` — state after the relevant agent execution
4. `verification_snapshot` — state actually subjected to verification
5. `current_snapshot` — state observed when the receipt/gate runs

---

## 2. Four Orthogonal State Machines

### 2.1 Authority State Machine (`AuthorityEvent.authority_status`)
```text
UNKNOWN
  │
  ├──► AUTHORIZED ──► EXPIRED
  │
  ├──► NOT_AUTHORIZED
  │
  └──► CONFLICTING
```

### 2.2 Admission State Machine (`AdmissionRecord.admission_status`)
```text
ADMITTED
INSPECT_ONLY
BLOCKED
REJECTED
```

### 2.3 Execution State Machine (`ExecutionRecord.execution_state`)
```text
NOT_STARTED
    ↓
STARTED
    ├──► EXECUTED
    ├──► FAILED
    ├──► CANCELLED
    └──► INTERRUPTED
(plus independent state: NOT_OBSERVABLE)
```

### 2.4 Verification State Machine (`VerificationRecord.result`)
```text
NOT_VERIFIED
    ↓
VERIFYING
    ├──► VERIFIED
    ├──► PARTIAL
    ├──► CONTRADICTED
    ├──► STALE
    ├──► MISMATCH
    └──► NOT_OBSERVABLE
```

### 2.5 Completion State Machine (`CompletionResult.status`)
```text
EVALUATING
    ├──► COMPLETABLE
    ├──► INCOMPLETE
    ├──► BLOCKED
    ├──► REJECTED
    └──► UNVERIFIED
```

---

## 3. Canonical Transition Theorem

1. **Authorized & Admitted Execution (`AIF-001`, `AIF-001A`)**:
   ```text
   EXECUTED(A, t)  ⇒  AUTHORIZED(A, t) ∧ ADMITTED(A)
   ```
2. **Evidence-Backed Verification (`AIF-006A`, `AIF-007`, `AIF-015`)**:
   ```text
   VERIFIED(C, S)  ⇒  ∃ evidence E: EvidenceCoverage(E, C, S) = SUFFICIENT
   ```
3. **Receipt-Backed Completion (`AIF-009`, `AIF-020`)**:
   ```text
   COMPLETABLE(R, S)  ⇒  Evaluate(R.acceptance_expression, R.receipt, S) = TRUE
   ```
4. **No Epistemic Laundering (`AIF-008`, `AIF-008A`, `AIF-013`, `AIF-017`, `AIF-019`)**:
   ```text
   Evaluate(...) = TRUE  ⇒  no mandatory requirement is UNKNOWN, UNVERIFIED,
                            BLOCKED, MISMATCH, STALE, or CONTRADICTED
   ```
   *(unless the `AcceptanceExpression` explicitly permits that state).*

---

## 4. Ten Forbidden State Transitions (`FT-01` – `FT-10`)

| ID | Forbidden Transition | Violated Invariants |
|---|---|---|
| `FT-01` | `CLAIMED → VERIFIED` | `AIF-006`, `AIF-013`, `AIF-018` |
| `FT-02` | `DECLARED → EXECUTED` | `AIF-004`, `AIF-004A` |
| `FT-03` | `EXECUTED → PASSED` | `AIF-005`, `AIF-005A` |
| `FT-04` | `CI_CONFIGURED → CI_PASSED` | `AIF-004`, `AIF-005` |
| `FT-05` | `SCANNER_CLEAN → REPOSITORY_SAFE` | `AIF-007`, `AIF-016` |
| `FT-06` | `CODE_PRESENT → IMPLEMENTED` | `AIF-006`, `AIF-007` |
| `FT-07` | `IMPLEMENTED → VERIFIED` | `AIF-006`, `AIF-006A` |
| `FT-08` | `VERIFIED@snapshot_A → VERIFIED@snapshot_B` | `AIF-002A`, `AIF-014`, `AIF-014A`, `AIF-015` |
| `FT-09` | `AUDIT_FINDING → REMEDIATED` | `AIF-001`, `AIF-010` |
| `FT-10` | `UNKNOWN → PASS` | `AIF-008`, `AIF-008A`, `AIF-013`, `AIF-019` |
