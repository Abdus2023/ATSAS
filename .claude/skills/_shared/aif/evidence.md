# AIF-0.1 Evidence, Claim, Acceptance & Receipt Contract (`evidence.md`)

- **Protocol Version**: `0.1.0` ([`VERSION`](./VERSION))
- **Governing Invariants**: `AIF-006` .. `AIF-020`

---

## 1. Evidence Contract (`EvidenceRef`)

```text
Evidence
    ↓ supports
    ↓ Claim
```

Never:

```text
Evidence
    ↓ proves everything
```

Every `EvidenceRef` ([`schema/evidence-ref.schema.json`](./schema/evidence-ref.schema.json)) must answer eight mandatory questions:

1. **WHO produced it?** (`producer`, `producer_version`)
2. **WHAT was observed?** (`content_digest`, `claim_scope`)
3. **WHERE did it come from?** (`source_type`, `source_locator`, `provenance[]`)
4. **WHEN was it captured?** (`captured_at`)
5. **AGAINST WHICH snapshot?** (`subject_snapshot`)
6. **USING WHICH method/tool?** (`producer`, `source_type`)
7. **WHAT claim does it support?** (`claim_scope`, `scope`)
8. **WHAT are its limitations?** (`limitations[]`)

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
}
```

**Skill Output Rule (`AIF-018`)**: A skill's prose output (`source_type: "SKILL_OUTPUT"`) is never primary evidence unless backed by non-empty primary `provenance[]` (`COMMAND_OUTPUT`, `GIT_OBJECT`, `SCANNER_REPORT`, `CI_RUN_ARTIFACT`, `LOCKFILE_PARSE`, or `HUMAN_AUTHORIZATION`).

---

## 2. Claim Contract (`Claim`)

A claim must be narrow enough to falsify and verify mechanically ([`schema/claim.schema.json`](./schema/claim.schema.json)).

- **Invalid (unbounded)**: `"The implementation is correct."` or `"The repository contains no secrets."`
- **Valid (bounded)**: `"TypeScript compilation produced no reported compiler errors against snapshot S1 using TypeScript 5.6."`

```yaml
claim_id: implementation-typescript-compile
subject:
  repository: streamforge-stremio
  snapshot: S1
proposition:
  type: compiler_report
  result: no_reported_errors
required_evidence:
  - COMMAND_OUTPUT
status: VERIFIED
```

---

## 3. Declarative Acceptance Expressions (`AcceptanceExpression`)

Completion logic is never embedded inside individual verification skills. It is declared as a composable boolean expression ([`schema/acceptance-expression.schema.json`](./schema/acceptance-expression.schema.json)) using six operators:

- `ALL`: Every child expression must evaluate to satisfied (`VERIFIED`).
- `ANY`: At least one child expression must evaluate to satisfied (`VERIFIED`).
- `AT_LEAST_N`: At least `n` child expressions must evaluate to satisfied.
- `OPTIONAL`: Non-blocking optional claim; if unverified, recorded in `unknowns` without blocking completion.
- `CONDITIONAL`: `if_claim` implies `then_expression`.
- `CLAIM`: Leaf reference to a specific `claim_id`.

```yaml
op: ALL
expressions:
  - op: CLAIM
    claim_id: scope_verified
  - op: CLAIM
    claim_id: implementation_verified
  - op: CLAIM
    claim_id: tests_verified
  - op: ANY
    expressions:
      - op: CLAIM
        claim_id: ci_current_head_verified
      - op: CLAIM
        claim_id: local_verification_authorized
```

---

## 4. Explanatory Completion Result (`CompletionResult`)

`CompletionResult` ([`schema/completion-result.schema.json`](./schema/completion-result.schema.json)) explains **why** completion has its state rather than collapsing outcomes into a generic `FAIL` that destroys the distinction between `false`, `unknown`, `not checked`, `not observable`, and `contradicted`:

```yaml
status: INCOMPLETE
evaluated_claims:
  - scope_verified
  - implementation_verified
  - tests_verified
  - ci_current_head_verified
satisfied_requirements:
  - scope_verified
  - implementation_verified
  - tests_verified
unmet_requirements:
  - ci_current_head_verified
unknowns:
  - ci_current_head_verified
blockers: []
```

---

## 5. Receipt Immutability (`ArenaEvidenceReceipt`)

An `ArenaEvidenceReceipt` ([`schema/evidence-receipt.schema.json`](./schema/evidence-receipt.schema.json)) is an immutable historical record, **not** a mutable `current_status.json`:

```text
R1
├── snapshot S1
├── evidence E1
└── completion = INCOMPLETE

  (repository changes: S1 -> S2)

R2
├── snapshot S2
├── evidence E2
└── completion = COMPLETABLE
```

`R1` is never mutated into `R2`. Audit history is a sequence of immutable receipts $(R_1, R_2, \dots, R_n)$.

---

## 6. Existing Detector & Documentation Skills as AIF Evidence Producers (Phase 5 Adapter Contract)

Rather than duplicating existing detectors, `AIF-0.1` adapts existing skills (`secret-leak-scan`, `dependency-vulnerability-audit`, `authorization-boundary-scan`, `docs-integrity-check`, `doc-symbol-audit`, `contract-implementation-sync`, `contract-freeze-gate`) via a shared producer contract ([`producers/`](./producers/README.md)) governed by `AIF-007`, `AIF-008`, `AIF-012`, `AIF-016`, `AIF-026` (Evidence Monotonicity), and `AIF-027` (Producer Independence).

### 6.1 Shared Execution Context & Producer Output

```text
SkillExecutionContext {
    request_id
    execution_id
    actor
    repository
    subject_snapshot
    tool
    tool_version
    started_at
    ended_at
}

EvidenceProducerOutput {
    producer
    producer_version
    aif_version
    execution_context
    evidence[]
    findings[]
    verifications[]
    limitations[]
    coverage
}
```

### 6.2 Three Output Levels (`Observation -> Finding -> Verification`)

1. **Level 1 — Observation (`OBSERVED`)**: Raw factual observation (e.g., `package-lock.json is absent`).
2. **Level 2 — Finding (`FINDING`)**: Bounded proposition supported by the observation (e.g., `"Dependency audit cannot establish lockfile-resolved dependency coverage."`).
3. **Level 3 — Verification (`VERIFIED` / `UNVERIFIED` / `PARTIAL` / `STALE` / `MISMATCH` / `NOT_OBSERVABLE` / `CONTRADICTED`)**: Claim-specific evaluation enforcing `Strength(Adapter(E)) <= Strength(E)` (`AIF-026`). Never `Observation -> Completion` (`AIF-027`).

| Existing Skill | `producer` | Bounded `claim_scope` (Valid) | Forbidden Broadening (`AIF-016`, `AIF-026`) | Mandatory `limitations[]` & Unknown Preservation (`AIF-008`) |
|---|---|---|---|---|
| `secret-leak-scan` | `secret-leak-scan` | `"No configured secret-pattern matches exist in the scanned paths."` | `"The repository contains no secrets."` | `SECRET_PATTERN_MATCH`, `SECRET_SCAN_COVERAGE_LIMITED`; working-tree & regex-pattern bounded |
| `dependency-vulnerability-audit` | `dependency-vulnerability-audit` | `"Ecosystem audit tool reported 0 high/critical advisories for lockfiles [L] at snapshot S."` | `"All dependencies are safe."` or `AUDIT_SKIPPED -> AUDIT_PASSED` | Preserves `VULNERABILITIES_FOUND`, `NO_MATCHES`, `AUDIT_SKIPPED`, `LOCKFILE_MISSING`, `LOCKFILE_DRIFT`, `TOOL_UNAVAILABLE`, `PARTIAL_COVERAGE` |
| `authorization-boundary-scan` | `authorization-boundary-scan` | `"No obvious unauthorized-distribution/access-control-bypass mechanism was detected by this scan."` | `"Agent is authorized to modify repository X"` (`C-01` domain) | `category: AUTHORIZATION_BOUNDARY` (content/security domain, never agent task authority) |
| `docs-integrity-check` | `docs-integrity-check` | `"Required documentation references resolve for snapshot S."` | `"Documentation is complete and accurate."` | Link/fence resolution only |
| `contract-implementation-sync` | `contract-implementation-sync` | `"Exported symbols in implementation match declared contract surface at snapshot S."` | `"The implementation is correct."` | Structural surface alignment only |
| `contract-freeze-gate` | `contract-freeze-gate` | `"The documentation contract satisfies the documentation freeze criteria."` | `"The implementation is correct."` | Contract-freeze criteria only unless implementation evidence is explicitly supplied |


