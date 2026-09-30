# AIF-0.1 Canonical Object Graph, 4 State Machines & Semantic Rules

## 1. Canonical Object Graph (14 Kernel Types)

```text
Request
  ├── AcceptanceExpression
  └── AuthorityEvent[]
             │
             ▼
        AdmissionRecord
             │
             ▼
       ExecutionRecord[]
             │
       ┌─────┴─────┐
       ▼           ▼
SnapshotRef    ChangeRecord[]
       │
       ▼
VerificationRecord[]
       │
       ▼
Claim ───────────────┐
       │             │
       ▼             ▼
EvidenceRef[]   EvidenceCoverage
       │             │
       └──────┬──────┘
              ▼
       ArenaEvidenceReceipt
              │
              ▼
      AcceptanceExpression
              │
              ▼
       CompletionResult
```

## 2. Core Semantic Rules

1. **Claims and Evidence Are Separate Objects (`AIF-018`)**: A skill cannot turn its own conclusion into evidence merely by setting `"verified": true`.
2. **Five Snapshot Roles (`AIF-002`, `AIF-002A`)**: `comparison_base`, `intake_snapshot`, `execution_snapshot`, `verification_snapshot`, `current_snapshot`. `HEAD=abc123, DIRTY != HEAD=abc123, CLEAN`.
3. **Receipt Immutability**: `R1 -> snapshot S`, `R2 -> snapshot S'`. Never mutate an old receipt in place.
4. **Claim-Scope-Dependent Invalidation (`AIF-014A`)**: `Evidence becomes stale iff Evidence.subject_snapshot = S AND later change S -> S' AND Intersects(change, claim_subject)`.
5. **Contradiction Preservation (`AIF-017`)**: `E1: CLEAN` + `E2: FINDING` -> `Claim.status = CONTRADICTED`.
6. **Normalization Without Expansion (`AIF-016`)**: `Normalize(E) != ExpandClaim(E)`.
7. **No Implicit Trust Hierarchy (`AIF-011`)**: Criterion determines required evidence class (`CI_RUN` vs. `COMMAND_OUTPUT`).
