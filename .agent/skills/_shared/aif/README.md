# AIF-0.1 Shared Semantic Kernel (`.claude/skills/_shared/aif/`)

> **Protocol Version**: `0.1` ([`VERSION`](./VERSION))  
> **Architectural Rule**: **Do not make the semantic kernel a skill. Make it a versioned protocol/contract consumed by skills.**  
> **Dependency Rule**: **Skills may depend on AIF semantics. AIF must not depend on skills.**  
> **Central Invariant**: `claim != observation != evidence != verification != completion`

---

## 1. Purpose & Boundary

`.claude/skills/_shared/aif/` is a **versioned protocol dependency consumed by skills**, not an executable workflow or selectable skill.

```text
AIF-0.1
   │
   ├── semantic contract (README.md, snapshots.md, evidence.md, compatibility.md)
   ├── state-transition rules (states.md)
   ├── invariants (invariants.md)
   ├── schemas (schema/*.schema.json)
   └── RED & adversarial tests (tests/{authority,snapshots,execution,evidence,verification,completion,adversarial}/)
          │
          ▼
   skill implementations
```

---

## 2. Formal Assurance Loop

```text
                 ┌───────────────────┐
                 │      REQUEST      │
                 └─────────┬─────────┘
                           ▼
                 ┌───────────────────┐
                 │ AUTHORITY + SCOPE │
                 └─────────┬─────────┘
                           ▼
                 ┌───────────────────┐
                 │     ADMISSION     │
                 └─────────┬─────────┘
                           ▼
                 ┌───────────────────┐
                 │     EXECUTION     │
                 └─────────┬─────────┘
                           ▼
                 ┌───────────────────┐
                 │      CHANGE       │
                 │   ATTRIBUTION     │
                 └─────────┬─────────┘
                           ▼
                 ┌───────────────────┐
                 │    EVIDENCE       │
                 └─────────┬─────────┘
                           ▼
                 ┌───────────────────┐
                 │   VERIFICATION    │
                 └─────────┬─────────┘
                           ▼
                 ┌───────────────────┐
                 │    ACCEPTANCE     │
                 │    EXPRESSION     │
                 └─────────┬─────────┘
                           ▼
                 ┌───────────────────┐
                 │    COMPLETION     │
                 └───────────────────┘
```

---

## 3. Phase 0 AIF-0.1 Design Freeze Candidate (18 Rules)

1. **AIF is a protocol, not a skill.**
2. **AIF semantics live in `_shared/aif/`.**
3. **Skills consume AIF; AIF does not depend on skills.**
4. **State dimensions remain separate** (`Authority`, `Execution`, `Verification`, `Completion`).
5. **Snapshot identity is mandatory for verification** (`comparison_base`, `intake_snapshot`, `execution_snapshot`, `verification_snapshot`, `current_snapshot`).
6. **State change does not prove actor attribution** (`DIFF(S0,S1)` != `AGENT_ATTRIBUTED`).
7. **Claims are bounded by subject, scope, and method.**
8. **Evidence cannot broaden claim semantics** (`Normalize(E) != ExpandClaim(E)`).
9. **Unknown is preserved** (`UNKNOWN != PASS`).
10. **Verification is claim-relative** (`VERIFY(C1, S1)` via `VerificationRecord`).
11. **Completion evaluates an explicit `AcceptanceExpression`.**
12. **Completion cannot manufacture evidence.**
13. **Audit cannot silently become remediation** (`AUDIT FINDING -> REPORT -> STOP / NEW REQUEST`).
14. **Mutation can invalidate intersecting evidence** (`Intersects(Change, Claim)`).
15. **Receipts are historical records, not mutable status documents** (`R1 -> S`, `R2 -> S'`).
16. **Semantic changes require a protocol-version change.**
17. **Every critical invariant gets executable adversarial tests.**
18. **Skills themselves are subject to the same evidence discipline.**

---

## 4. Directory Contents

| Path | Description |
|---|---|
| [`VERSION`](./VERSION) | Frozen protocol version (`0.1`) |
| [`invariants.md`](./invariants.md) | Executable invariants `AIF-001`..`AIF-020` (`+A` sub-invariants) with `TEST AIF-XXX-YY` specifications |
| [`states.md`](./states.md) | Four orthogonal state machines (`Authority`, `Execution`, `Verification`, `Completion`), snapshot states, and `FT-01`..`FT-10` |
| [`snapshots.md`](./snapshots.md) | 5 snapshot roles (roles vs. commits) and `State Change vs. Attribution` rules (`AIF-002`, `AIF-003A`) |
| [`evidence.md`](./evidence.md) | Claim-scoped evidence, relational verification (`VERIFY(C1,S1)`), `AcceptanceExpression` (`INCOMPLETE != BLOCKED`), and non-remediation loop |
| [`evidence-rules.md`](./evidence-rules.md) | `EvidenceCoverage(E,C)` operator and `AIF-PROFILES` |
| [`compatibility.md`](./compatibility.md) | Strict semantic versioning rules and mechanical `aif:` skill contract declarations |
| [`schema/request.schema.json`](./schema/request.schema.json) | `Request` JSON Schema (Draft 2020-12) |
| [`schema/authority-event.schema.json`](./schema/authority-event.schema.json) | `AuthorityEvent` JSON Schema |
| [`schema/admission-record.schema.json`](./schema/admission-record.schema.json) | `AdmissionRecord` JSON Schema (aliased by [`schema/admission.schema.json`](./schema/admission.schema.json)) |
| [`schema/snapshot-ref.schema.json`](./schema/snapshot-ref.schema.json) | `SnapshotRef` JSON Schema (aliased by [`schema/snapshot.schema.json`](./schema/snapshot.schema.json)) |
| [`schema/execution-record.schema.json`](./schema/execution-record.schema.json) | `ExecutionRecord` JSON Schema |
| [`schema/change-record.schema.json`](./schema/change-record.schema.json) | `ChangeRecord` JSON Schema |
| [`schema/claim.schema.json`](./schema/claim.schema.json) | `Claim` JSON Schema |
| [`schema/evidence-ref.schema.json`](./schema/evidence-ref.schema.json) | `EvidenceRef` JSON Schema |
| [`schema/evidence-coverage.schema.json`](./schema/evidence-coverage.schema.json) | `EvidenceCoverage` JSON Schema |
| [`schema/verification-record.schema.json`](./schema/verification-record.schema.json) | `VerificationRecord` JSON Schema |
| [`schema/finding.schema.json`](./schema/finding.schema.json) | `Finding` JSON Schema |
| [`schema/acceptance-expression.schema.json`](./schema/acceptance-expression.schema.json) | `AcceptanceExpression` JSON Schema |
| [`schema/completion-result.schema.json`](./schema/completion-result.schema.json) | `CompletionResult` JSON Schema |
| [`schema/evidence-receipt.schema.json`](./schema/evidence-receipt.schema.json) | `ArenaEvidenceReceipt` JSON Schema |
| `tests/` | 42-case executable RED & adversarial test corpus (`authority/`, `snapshots/`, `execution/`, `evidence/`, `verification/`, `completion/`, `adversarial/`) |
