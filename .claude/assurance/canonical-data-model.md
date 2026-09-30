# Arena Assurance Interface v0.1 — Canonical Data Model (Semantic Kernel)

> **Status**: Semantic Boundaries `VERIFIED` · State Families `VERIFIED` · Snapshot Taxonomy `VERIFIED` · Core Object Models `PROVISIONAL → FREEZE CANDIDATE`  
> **Scope**: `ARENA_GENERIC` (Domain-agnostic across all Arena repositories; zero StreamForge-specific domain coupling)  
> **Companion Artifacts**: [`.claude/assurance/aif-v01-freeze-review.md`](./aif-v01-freeze-review.md), [`.claude/assurance/component-contracts.md`](./component-contracts.md), [`.claude/assurance/semantic-kernel-layout-review.md`](./semantic-kernel-layout-review.md), [`schemas/aif-canonical-data-model.schema.json`](../../schemas/aif-canonical-data-model.schema.json)

---

## Design Goal: A Small Semantic Kernel

The Canonical Data Model is a **small semantic kernel**, not eight independent skill schemas:

```text
one vocabulary
  + many specialized producers
  + one evidence envelope
  + one completion evaluator
```

The kernel remains completely independent of StreamForge-specific domain semantics.

---

## 1. Canonical Object Graph

```text
Request
  │
  ├── AcceptanceExpression
  │
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

### Crucial Design Decision
**Claims and evidence are separate objects.**  
A skill cannot turn its own conclusion into evidence merely by placing `"verified": true` in its output (`AIF-018`).

---

## 2. `SnapshotRef`

The foundation for temporal and state binding across all observations, executions, claims, and receipts (`AIF-002`, `AIF-002A`).

```text
SnapshotRef {
    snapshot_id
    role

    repository
    ref
    commit

    working_tree_state
    index_state

    captured_at

    content_digest
    metadata_digest
}
```

### Required Working-Tree & Index States
```text
CLEAN
DIRTY
PARTIAL
UNKNOWN
```

`commit` alone is insufficient because a working tree or index can differ from `HEAD`. Therefore:
```text
HEAD = abc123, working_tree_state = DIRTY
  ≢
HEAD = abc123, working_tree_state = CLEAN
```

---

## 3. Snapshot Taxonomy

A single overloaded `baseline` is forbidden. The five canonical snapshot roles are:

| Snapshot Role | Meaning |
|---|---|
| `comparison_base` | Reference snapshot/ref used for historical or diff comparison (`git merge-base`, target branch, or base tag). |
| `intake_snapshot` (`S0`) | Repository state observed when the task was admitted. |
| `execution_snapshot` (`S1`) | Repository state after the relevant agent execution. |
| `verification_snapshot` (`S2`) | Repository state actually subjected to verification/testing. |
| `current_snapshot` (`S3`) | Repository state observed when the receipt generator or completion gate runs. |

Separating these five roles eliminates silent cross-snapshot evidence transfer (`AIF-002A`, `AIF-014`).

---

## 4. `AuthorityEvent`

Authority is an event with explicit provenance and temporal bounds, not a boolean (`AIF-001`, `AIF-001A`).

```text
AuthorityEvent {
    event_id
    request_id

    actor
    authority_basis
    authority_status

    action_scope[]
    path_scope[]

    restrictions[]

    issued_at
    effective_from
    expires_at

    issuer
    evidence[]
}
```

### Authority Status
```text
AUTHORIZED
NOT_AUTHORIZED
UNKNOWN
EXPIRED
CONFLICTING
```

### Important Distinction: `authority_basis` vs. `evidence[]`
`authority_basis` answers *"Why is this action claimed to be authorized?"*  
Setting `authority_basis = "user request"` is **not** itself proof. The evidence for the authority event (e.g., prompt record, signed approval artifact, governance rule) must be separately represented in `evidence[]`.

---

## 5. `Request`

```text
Request {
    request_id

    actor

    repository
    target_ref

    requested_actions[]

    authority_events[]

    acceptance_expression

    constraints[]

    created_at
}
```

The `Request` is purely declarative: it defines what was asked and under what constraints, and does **not** establish admission or execution.

---

## 6. `AdmissionRecord`

Bridges authority (`AuthorityEvent[]`) and execution (`ExecutionRecord[]`).

```text
AdmissionRecord {
    request_id

    admission_status

    admitted_actions[]
    admitted_paths[]

    excluded_actions[]
    excluded_paths[]

    blockers[]
    clarifications[]

    authority_refs[]

    intake_snapshot
}
```

### Admission Status
```text
ADMITTED
INSPECT_ONLY
BLOCKED
REJECTED
```

### Key Invariant (`AIF-001`, `AIF-001A`)
```text
EXECUTION cannot legitimately precede ADMISSION
```
If an execution occurs prior to or outside `AdmissionRecord`, that execution is recorded as an explicit failure condition (`UNAUTHORIZED_ACTION` / `SCOPE_VIOLATION`) rather than being silently retroactively authorized.

---

## 7. `ExecutionRecord`

The canonical execution primitive (`AIF-004`, `AIF-004A`, `AIF-005`, `AIF-005A`).

```text
ExecutionRecord {
    execution_id
    request_id

    actor

    action
    command

    working_directory
    environment_digest

    tool
    tool_version

    started_at
    ended_at

    execution_state
    exit_code

    stdout_ref
    stderr_ref

    subject_snapshot
    resulting_snapshot

    process_result
    test_result
    semantic_result
}
```

### Execution State
```text
NOT_STARTED
STARTED
EXECUTED
FAILED
CANCELLED
INTERRUPTED
NOT_OBSERVABLE
```

This binds `command + context + time + actor + snapshot + result` instead of relying on textual claims, while preserving the distinction between `PROCESS_RESULT` (`exit_code == 0`), `TEST_RESULT` (`tests_executed > 0 ∧ tests_failed == 0`), and `SEMANTIC_RESULT` (`AIF-005A`).

---

## 8. `ChangeRecord`

Distinguishes state transition (`DIFF(S0, S1)`) from actor causality (`AIF-003`, `AIF-003A`).

```text
ChangeRecord {
    path

    change_type

    before_digest
    after_digest

    intake_state
    execution_state

    attribution
    attribution_basis

    generated
    generated_by
}
```

### Attribution Vocabulary
```text
PREEXISTING
AGENT_ATTRIBUTED
EXTERNAL_ATTRIBUTED
GENERATED
UNATTRIBUTED
UNKNOWN
```

`DIFF(S0, S1)` establishes that a state changed (`STATE_CHANGE`). It does **not** automatically establish `AGENT_ATTRIBUTED` (`AGENT_ATTRIBUTED_CHANGE` vs. `UNATTRIBUTED_CHANGE`) without `attribution_basis` linking the change to an agent `ExecutionRecord`.

---

## 9. `Claim`

A `Claim` is an explicit, bounded proposition that the assurance system is asked to evaluate (`AIF-006`, `AIF-006A`, `AIF-008`, `AIF-008A`).

```text
Claim {
    claim_id

    subject
    proposition

    required_evidence[]

    required_snapshot

    status
}
```

### Epistemic Claim Status
```text
VERIFIED
PARTIAL
UNVERIFIED
UNKNOWN
NOT_REQUESTED
NOT_CHECKED
NOT_OBSERVABLE
CONTRADICTED
STALE
MISMATCH
```

### Bounded Proposition Rule
Propositions must always use scope-bounded wording:
- Valid: `"TypeScript typecheck passes"` (`required_snapshot: execution_snapshot`, `required_evidence: [typecheck_execution]`)
- Valid: `"No HIGH severity dependency vulnerabilities were reported by the configured audit"` (`required_snapshot: verification_snapshot`, `required_evidence: [dependency_audit_result]`)
- Forbidden: `"dependencies are safe"` or `"repository contains no secrets"`

---

## 10. `EvidenceRef`

```text
EvidenceRef {
    evidence_id

    producer
    producer_version

    source_type
    source_locator

    captured_at

    subject_snapshot
    scope

    content_digest
    provenance[]

    claim_scope
    limitations[]
    snapshot_independent
}
```

### Canonical `source_type` Values
```text
COMMAND_OUTPUT
FILE_CONTENT
GIT_OBJECT
CI_RUN
CI_ARTIFACT
TEST_REPORT
SCANNER_RESULT
MANIFEST
LOCKFILE
HUMAN_AUTHORIZATION
SKILL_OUTPUT
EXTERNAL_RECORD
```

### Evidentiary Status of `SKILL_OUTPUT` (`AIF-018`)
`SKILL_OUTPUT` must **not** automatically qualify as strong execution evidence. Its evidentiary adequacy depends on the underlying `ExecutionRecord`, `COMMAND_OUTPUT`, `GIT_OBJECT`, or `SCANNER_RESULT` in its `provenance[]`.

---

## 11. `EvidenceCoverage`

The mathematical bridge between `EvidenceRef` (`E`) and `Claim` (`C`) (`AIF-007`, `AIF-014`, `AIF-014A`, `AIF-015`, `AIF-017`).

```text
EvidenceCoverage {
    evidence_id
    claim_id

    subject_match
    snapshot_match
    scope_match
    method_match
    freshness

    adequacy
    limitations[]
}
```

### Adequacy (`Coverage(E, C)`)
```text
SUFFICIENT
PARTIAL
IRRELEVANT
CONTRADICTORY
UNKNOWN
```

### Verification Condition
A single-evidence claim becomes verified only when:
```text
VERIFY(C)  ⇔  ∃ E: Coverage(E, C) = SUFFICIENT
```
For multi-evidence claims:
```text
VERIFY(C)  ⇔  ∀ required evidence predicate p ∈ C.required_evidence:
                  ∃ E_p: Coverage(E_p, p) = SUFFICIENT
                    ∧ ¬∃ E_c: Coverage(E_c, C) = CONTRADICTORY
```

---

## 12. `VerificationRecord`

Binds verification explicitly to a `claim_id`, `method`, `subject_snapshot`, `evidence_refs[]`, and `coverage[]` (`AIF-006A`).

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

### Verification Result
```text
VERIFIED
PARTIAL
UNVERIFIED
CONTRADICTED
STALE
MISMATCH
NOT_OBSERVABLE
```

This prevents `verification.status = VERIFIED` from existing without a specific `claim_id` and `EvidenceCoverage`.

---

## 13. `Finding`

Bounded detector/auditor observation record separating `severity` (impact if true) from `confidence` (evidentiary certainty) (`AIF-010`, `AIF-012`).

```text
Finding {
    finding_id

    category
    severity

    proposition

    subject
    snapshot

    evidence_refs[]

    confidence

    limitations[]
    remediation_authorized: false
}
```

### Severity vs. Confidence Separation
- `severity ∈ {CRITICAL, HIGH, MODERATE, LOW, INFO}`
- `confidence ∈ {CONFIRMED, HIGH, MEDIUM, LOW, HEURISTIC}`
- `severity = HIGH` with `confidence = LOW` is valid: a high-impact suspected finding is distinct from a verified high-impact finding.
- `remediation_authorized` is permanently `false` (`AIF-010`: audit findings never authorize remediation).

---

## 14. `AcceptanceExpression`

The algebraic logic layer over claims (`AIF-009`, `AIF-011`, `AIF-020`):

```text
AcceptanceExpression =
    ALL(expressions[])
  | ANY(expressions[])
  | AT_LEAST_N(n, expressions[])
  | OPTIONAL(expression)
  | CONDITIONAL(condition, then, else)
  | CLAIM(claim_id)
```

*(Note: `CRITERION` leaf nodes referencing `required_claim_id` are an alias for `CLAIM(claim_id)` with criterion metadata.)*

### Example
```text
ALL(
    CLAIM(scope_verified),
    CLAIM(implementation_verified),
    CLAIM(test_suite_verified),
    ANY(
        CLAIM(ci_current_head_verified),
        CLAIM(local_verification_explicitly_allowed)
    )
)
```

---

## 15. `CompletionResult`

The output of `arena-completion-gate` (`C-07`) (`AIF-013`, `AIF-019`, `AIF-020`).

```text
CompletionResult {
    request_id

    acceptance_expression

    status

    evaluated_claims[]

    satisfied_requirements[]
    unmet_requirements[]

    blockers[]
    unknowns[]

    evidence_refs[]

    evaluated_snapshot

    generated_at
}
```

### Completion Status
```text
COMPLETABLE
INCOMPLETE
BLOCKED
REJECTED
UNVERIFIED
```

---

## 16. `ArenaEvidenceReceipt`

The canonical output container uniting all Semantic Kernel objects (`schema_version: "aif/0.1"`).

```text
ArenaEvidenceReceipt {
    schema_version: "aif/0.1"
    receipt_id

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

    acceptance_expression
    completion_result

    generated_at
}
```

---

## 17. Receipt Immutability Rule

An `ArenaEvidenceReceipt` is an immutable historical evidence object:
```text
receipt R1 ──describes──► snapshot S
```
If the repository state changes (`S → S'`), `R1` must **never** be mutated in place to describe `S'`. Instead:
```text
R1 ──describes──► snapshot S
R2 ──describes──► snapshot S'
```
This guarantees historical evidence preservation, reproducibility, and auditability.

---

## 18. Claim-Scope-Dependent Evidence Invalidation (`AIF-014`, `AIF-014A`)

Not every repository mutation invalidates every claim. Define the intersection predicate:
```text
Intersects(Change, Claim)
```
Then:
```text
Evidence E becomes STALE for Claim C  ⇔
    E.subject_snapshot = S
    ∧ later change S → S'
    ∧ Intersects(Change(S, S'), C.subject / C.scope)
```
- **Example**: If `typecheck` evidence was captured at snapshot `S` and `README.md` is modified in `S → S'`, the `typecheck` evidence remains valid (`VALID_AT_SNAPSHOT` / non-intersecting) **if and only if** the `typecheck` claim scope explicitly excludes `README.md`. Meanwhile, any `docs-integrity-check` claim intersects `README.md` and becomes `STALE` (`INVALIDATED_BY_MUTATION`).

---

## 19. Contradiction Handling (`AIF-017`)

When two pieces of evidence disagree on the same claim:
```text
        ┌── E1 ── CLEAN (no vulnerability reported)
        │
CLAIM ──┤
        │
        └── E2 ── FINDING (vulnerability reported)
```
The resulting `Claim.status` and `VerificationRecord.result` must be:
```text
CONTRADICTED
```
never collapsed to `PASS` (optimistic erasure) and never silently overwritten without preserving both `E1` and `E2` in the receipt graph unless the `AcceptanceExpression` explicitly specifies contradiction resolution rules.

---

## 20. Evidence Normalization Rule (`AIF-016`)

Every producer adapter and `evidence-receipt-generator` (`C-06`) must obey:
```text
Normalize(E)  ≠  ExpandClaim(E)
```
- **Allowed structural normalization**: `secret-leak-scan` emits `"No matches in scanned paths"` → normalized to `finding_type = SECRET_PATTERN_MATCH, matches = 0, scope = scanned_paths`.
- **Forbidden semantic laundering**: Transforming `"No matches in scanned paths"` into `repository_has_no_secrets = true`.

---

## 21. Four Orthogonal State Machines

The four state families must **never** be collapsed into a single status enum:

### 21.1 Authority State Machine
```text
UNKNOWN
  ├──► AUTHORIZED ──► EXPIRED
  ├──► NOT_AUTHORIZED
  └──► CONFLICTING
```

### 21.2 Execution State Machine
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

### 21.3 Verification State Machine
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

### 21.4 Completion State Machine
```text
EVALUATING
    ├──► COMPLETABLE
    ├──► INCOMPLETE
    ├──► BLOCKED
    ├──► REJECTED
    └──► UNVERIFIED
```

---

## 22. Canonical Transition Theorem

The AIF v0.1 Semantic Kernel enforces four foundational implications:

1. **Authorized Execution (`AIF-001`, `AIF-001A`)**:
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
4. **No Hidden Epistemic Deficits (`AIF-008`, `AIF-008A`, `AIF-013`, `AIF-017`, `AIF-019`)**:
   ```text
   Evaluate(...) = TRUE  ⇒  no mandatory requirement is UNKNOWN, UNVERIFIED,
                            BLOCKED, MISMATCH, STALE, or CONTRADICTED
   ```
   *(unless the `AcceptanceExpression` explicitly permits that state via `OPTIONAL` / `ANY` / `CONDITIONAL`).*

---

## 23. Responsibility Boundaries of the Eight Assurance Skills (`C-01` – `C-08`)

| Skill | Contract | Produces (Kernel Objects) | Does Not Decide |
|---|---|---|---|
| `arena-intake-and-authority` | `C-01` | `Request`, `AuthorityEvent[]`, `AdmissionRecord` | Completion |
| `agent-change-scope-audit` | `C-02` | `SnapshotRef`, `ChangeRecord[]`, `Finding[]` | Authorization |
| `dependency-supply-chain-audit` | `C-03` | `Finding[]`, `EvidenceRef[]` | Completion |
| `ci-workflow-audit` | `C-04` | `ExecutionRecord[]`, `EvidenceRef[]`, `Finding[]` | Overall success |
| `test-execution-and-evidence-audit` | `C-05` | `ExecutionRecord[]`, `EvidenceRef[]`, `VerificationRecord[]` | Overall completion |
| `evidence-receipt-generator` | `C-06` | `EvidenceCoverage[]`, `ArenaEvidenceReceipt` | Missing evidence (never fabricates) |
| `arena-completion-gate` | `C-07` | `CompletionResult` | New evidence or remediation |
| `skill-evaluation-harness` | `C-08` | `SkillEvalReceipt` | Repository completion |

---

## 24. Existing Repository Skills as Kernel Producers

The 14 existing `.claude/skills/` plug into the Semantic Kernel as specialized producers without becoming a monolithic skill:

```text
secret-leak-scan                  ──► Finding[] + EvidenceRef[]
dependency-vulnerability-audit    ──► Finding[] + EvidenceRef[]
authorization-boundary-scan       ──► Finding[] + EvidenceRef[]
repo-onboarding-audit             ──► Finding[] + EvidenceRef[]
docs-integrity-check              ──► Finding[] + EvidenceRef[]
doc-symbol-audit                  ──► Finding[] + EvidenceRef[]
session-git-sync-check            ──► SnapshotRef + Finding[] + EvidenceRef[]
contract-implementation-sync      ──► VerificationRecord + EvidenceRef[]
contract-freeze-gate              ──► Claim[] + VerificationRecord[]
```

---

## 25. No Implicit Trust Hierarchy (`AIF-011`)

AIF v0.1 forbids hardcoding `CI evidence > local evidence` as a universal axiom. Instead:
```text
criterion  ──►  required evidence class
```
- `"CI passes on current HEAD"` requires `CI_RUN` / `CI_ARTIFACT` evidence at `current_snapshot`.
- `"TypeScript has no compiler errors"` may be satisfied by a reproducible local `COMMAND_OUTPUT` / `ExecutionRecord` at `verification_snapshot` if the `AcceptanceExpression` permits it.

This preserves **evidence adequacy** (`Coverage(E, C)`) rather than an arbitrary prestige hierarchy.

---

## 26. Canonical JSON Shape (`schema_version: "aif/0.1"`)

```json
{
  "schema_version": "aif/0.1",
  "receipt_id": "rcpt-20260929-001",
  "request": {
    "request_id": "req-001",
    "requested_actions": ["INSPECT", "MODIFY", "VERIFY"],
    "acceptance_expression": {
      "op": "ALL",
      "expressions": [
        { "op": "CLAIM", "claim_id": "claim-tests-verified" }
      ]
    }
  },
  "snapshots": [],
  "authority_events": [],
  "admission": {},
  "execution_records": [],
  "change_records": [],
  "claims": [],
  "evidence": [],
  "coverage": [],
  "verifications": [],
  "findings": [],
  "acceptance_expression": {},
  "completion_result": {},
  "generated_at": "2026-09-29T12:00:00Z"
}
```

---

## 27. Freeze Status Matrix & Kernel Topology

```text
                          STATUS
Semantic boundaries       VERIFIED
State families            VERIFIED
Snapshot taxonomy         VERIFIED
Authority model           PROVISIONAL → FREEZE CANDIDATE
Execution model           PROVISIONAL → FREEZE CANDIDATE
Evidence model            PROVISIONAL → FREEZE CANDIDATE
Claim model               PROVISIONAL → FREEZE CANDIDATE
Acceptance expressions    PROVISIONAL → FREEZE CANDIDATE
Receipt model             PROVISIONAL → FREEZE CANDIDATE
Completion model          PROVISIONAL → FREEZE CANDIDATE
```

```text
                 ┌─────────────────┐
                 │ Semantic Kernel │
                 │                 │
                 │ SnapshotRef     │
                 │ AuthorityEvent  │
                 │ AdmissionRecord │
                 │ ExecutionRecord │
                 │ ChangeRecord    │
                 │ Claim           │
                 │ EvidenceRef     │
                 │ EvidenceCoverage│
                 │ VerificationRec │
                 │ Finding         │
                 │ AcceptanceExpr  │
                 └────────┬────────┘
                          │
          ┌───────────────┼────────────────┐
          │               │                │
       detector        auditor          executor
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                  ArenaEvidenceReceipt
                          │
                          ▼
                   CompletionResult
```

### Complete Invariant Cross-Reference (`AIF-001` – `AIF-020` + `AIF-001A` – `AIF-014A`)

- Primary Invariants: `AIF-001`, `AIF-002`, `AIF-003`, `AIF-004`, `AIF-005`, `AIF-006`, `AIF-007`, `AIF-008`, `AIF-009`, `AIF-010`, `AIF-011`, `AIF-012`, `AIF-013`, `AIF-014`, `AIF-015`, `AIF-016`, `AIF-017`, `AIF-018`, `AIF-019`, `AIF-020`.
- Sub-Invariants: `AIF-001A`, `AIF-002A`, `AIF-003A`, `AIF-004A`, `AIF-005A`, `AIF-006A`, `AIF-008A`, `AIF-014A`.
