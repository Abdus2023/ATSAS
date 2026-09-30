# Normative Interface Contracts (`C-01` – `C-08`), Shared `EvidenceRef` & AIF v0.1 Freeze Specification

```text
Document Class: HISTORICAL
Protocol: AIF-0.1.0
Evaluated Snapshot: 15f7fa01778f06821d1c5c9c285bb0d666e04f8b
Currentness: HISTORICAL — NOT CURRENT BRANCH EVIDENCE (Normative authority is .claude/skills/_shared/aif/)
```

> **Status**: `AIF v0.1 FREEZE CANDIDATE — Hardened via Adversarial Freeze Review`
> **Scope**: `ARENA_GENERIC`
> **Core Rule**: `RESULT ≠ EVIDENCE ≠ DECISION` — Every assurance component exposes the same conceptual envelope (`SkillInput → Observation / execution → SkillResult → Evidence references → State classification`), and **only `C-07 arena-completion-gate` makes the final completion decision**.

---

## 1. Normative Contract Envelope & Architecture Theorem

### 1.1 Universal Skill Envelope

```text
SkillInput
    ↓
Observation / execution
    ↓
SkillResult
    ↓
Evidence references (EvidenceRef[])
    ↓
State classification
```

The critical separation:
```text
RESULT ≠ EVIDENCE ≠ DECISION
```
- **Detector example (`secret-leak-scan`)**:
  - `RESULT`: `0 matching patterns`
  - `EVIDENCE`: `scanner=secret-leak-scan, version=0.1.0, snapshot=abc123:tree_hash, paths=src,test, timestamp=T`
  - `DECISION`: `"secret criterion satisfied"` — **Only `C-07 arena-completion-gate` may make this decision.**

### 1.2 The Architecture Theorem

```text
                AUTHORITY
                    │
                    ▼
                ADMISSION
                    │
                    ▼
                EXECUTION
                    │
                    ▼
               OBSERVATION
                    │
                    ▼
               VERIFICATION
                    │
                    ▼
                 EVIDENCE
                    │
                    ▼
                ACCEPTANCE
```

> **Central Rule**: **Each arrow requires its own evidence.** No state may be inferred merely because the preceding state exists.

---

## 2. Shared Evidence Contract (`EvidenceRef`) & Evidence Adequacy

### 2.1 Minimal Evidence Identity (`EvidenceRef`)

All eight components (`C-01` – `C-08`) and all existing detector adapters use the same minimal evidence identity (`schemas/aif-evidence-ref.schema.json`):

```text
EvidenceRef {
    evidence_id

    repository
    snapshot          // Composite digest: <commit_sha>:<staged_tree_sha>:<worktree_diff_sha256>

    source_type       // "PROCESS_EXECUTION" | "DETECTOR_SCAN" | "GIT_DIFF" | "STATIC_INSPECTION" | "CI_RUN" | "POLICY_DOC"
    source_locator    // Artifact path, command log ref, or commit/blob ref

    captured_at

    producer
    producer_version

    claim_scope       // Explicit, bounded statement of what this evidence actually covers
}
```

**Bounded `claim_scope` rule**:
- Valid: `"No HIGH-severity matches produced by secret-leak-scan against current working-tree source/config paths."`
- Invalid (broader than evidence): `"Repository contains no secrets."`

### 2.2 Evidence Strength Hierarchy & Adequacy Formula

```text
                 STRONGER
                    ▲
                    │
             independent execution
                    │
             raw execution artifact
                    │
             reproducible command
                    │
             tool-generated result
                    │
             static inspection
                    │
             agent observation
                    │
             agent assertion
                    ▼
                 WEAKER
```

Because static inspection is the appropriate evidence for some claims (e.g., workflow configuration or manifest declaration), strength alone is not sufficiency:

```text
evidence adequacy = claim requirements ∩ evidence coverage
```
Never infer: `stronger-looking evidence ⇒ automatically sufficient`.

---

## 3. Ten Forbidden State Transitions

Every one of these ten transitions is strictly forbidden across all contracts and is tested behaviorally in `C-08`:

| # | Forbidden Transition | Invariant Violated | Why It Is Forbidden |
|---|---|---|---|
| `FT-01` | `CLAIMED → VERIFIED` | `AIF-006`, `AAI-006` | Agent prose or assertion is a claim, not execution evidence. |
| `FT-02` | `DECLARED → EXECUTED` | `AIF-004`, `AAI-004` | A script in `package.json` or `Makefile` does not mean it ran. |
| `FT-03` | `EXECUTED → PASSED` | `AIF-005`, `AAI-005` | Running a command without observing unmasked `exit_code == 0` and non-vacuous test execution does not mean it passed. |
| `FT-04` | `CI_CONFIGURED → CI_PASSED` | `AIF-004`, `AIF-005` | Presence of `.github/workflows/*.yml` does not mean CI ran or succeeded. |
| `FT-05` | `SCANNER_CLEAN → REPOSITORY_SAFE` | `AIF-008`, `AIF-012` | A clean detector result is bounded by detector rules, version, and inspected paths (`claim_scope`). |
| `FT-06` | `CODE_PRESENT → IMPLEMENTED` | `AIF-006` | Unverified files on disk do not establish contract-conformant implementation. |
| `FT-07` | `IMPLEMENTED → VERIFIED` | `AIF-006` | Code matching a contract shape has not been runtime/test verified until executed and evidenced. |
| `FT-08` | `VERIFIED@A → VERIFIED@B` | `AIF-007`, `AIF-014` | Verification at snapshot `A` never certifies a mutated snapshot `B`. |
| `FT-09` | `AUDIT_FINDING → REMEDIATED` | `AIF-010`, `AAI-010` | Discovering a defect during an audit does not authorize the audit to mutate the repository. |
| `FT-10` | `UNKNOWN → PASS` | `AIF-009`, `AAI-008` | Unobservable or skipped checks (`NOT_OBSERVABLE`, `UNKNOWN`) must never collapse into `PASS`. |

---

## 4. Normative Component Contracts (`C-01` – `C-08`)

---

### Contract `C-01` — `arena-intake-and-authority`

#### Purpose
Establish whether a requested action is sufficiently specified and authorized before mutation, and anchor the baseline `intake_snapshot` (`S0`).

#### Input
```text
IntakeRequest {
    request_id
    actor
    repository
    branch_or_ref

    requested_actions[]
    target_paths[]
    constraints[]

    acceptance_criteria[]
    authority_basis
}
```

#### Output
```text
IntakeResult {
    request_id

    authority_status
    scope_status
    admission_status

    requested_actions[]
    admitted_actions[]

    target_paths[]
    forbidden_paths[]

    blockers[]
    clarifications[]

    intake_snapshot
}
```

#### State Vocabulary
- **Authority States**: `AUTHORITY_CONFIRMED`, `AUTHORITY_UNKNOWN`, `AUTHORITY_CONFLICT`, `AUTHORIZATION_EXPIRED`
- **Scope States**: `SCOPE_DEFINED`, `SCOPE_UNDEFINED`, `SCOPE_CONFLICT`
- **Admission States**: `ADMITTED`, `BLOCKED`, `REJECTED`, `INSPECT_ONLY`

#### Hard Invariants
- `I-01`: `EXECUTED(action) ⇒ action ∈ admitted_actions` (and `intake_snapshot.captured_at <= action.start_time` per `PATCH-001`)
- `I-02`: `missing authority ≠ authorization`
- `I-03`: `inspection authorization ≠ mutation authorization`
- `I-04`: `vague request ≠ broad authorization`

#### Forbidden Inference
- `user asked "investigate" ⇒ user authorized modification`
- `user owns repository ⇒ every possible repository action is authorized`
- `skill was invoked ⇒ skill is authorized to mutate`

#### Mutation Policy
Read-only by default. Any mutation must be independently authorized.

---

### Contract `C-02` — `agent-change-scope-audit`

#### Purpose
Determine what changed during the authorized execution interval (`DIFF(intake_snapshot, execution_snapshot)`).

#### Input
```text
ScopeAuditRequest {
    request_id

    comparison_base
    intake_snapshot
    execution_snapshot

    authorized_paths[]
    authorized_actions[]

    generated_artifact_policy
}
```

#### Output
```text
ScopeAudit {
    request_id

    comparison_base
    intake_snapshot
    execution_snapshot

    changed_paths[]

    authorized_changes[]
    unauthorized_changes[]

    preexisting_changes[]
    generated_changes[]

    additions[]
    modifications[]
    deletions[]

    scope_status
    evidence[]
}
```

#### States
`IN_SCOPE`, `OUT_OF_SCOPE`, `MIXED`, `PREEXISTING_ONLY`, `GENERATED_ONLY`, `UNDETERMINED`.

#### Core Invariant
```text
AGENT_CHANGE = DIFF(intake_snapshot, execution_snapshot)
```
(computed over per-path content/mode/index blob hashes so that agent edits to a file that was *already* dirty in `intake_snapshot` are still detected as `AGENT_CHANGE` per `PATCH-003`).
Never `DIFF(remote_base, execution_snapshot)`.

#### Forbidden Inference
- `file appears in final diff ⇒ agent changed file` (until `intake_snapshot` establishes that)
- `file was dirty in intake_snapshot ⇒ subsequent agent edits to that file are preexisting` (`PATCH-003`)
- `generated artifact ⇒ authorized artifact`

---

### Contract `C-03` — `dependency-supply-chain-audit`

#### Purpose
Evaluate dependency declarations, lockfiles, resolutions, registries, integrity hashes, lifecycle hooks, provenance, and vulnerability results by composing the existing `dependency-vulnerability-audit` detector.

#### Input
```text
SupplyChainRequest {
    repository
    snapshot

    manifests[]
    lockfiles[]

    registry_policy
    lifecycle_policy
    provenance_policy

    vulnerability_audit_policy
}
```

#### Output
```text
DependencyAudit {
    snapshot

    manifests[]
    lockfiles[]

    declared_dependencies[]
    resolved_dependencies[]
    transitive_dependencies[]

    registry_configuration[]
    integrity_records[]

    lifecycle_scripts[]
    provenance_findings[]

    vulnerability_results[]

    drift_findings[]
    observability_gaps[]

    status
    evidence[]
}
```

#### Independent State Distinctions
`DECLARED`, `RESOLVED`, `LOCKED`, `INTEGRITY_OBSERVED`, `REGISTRY_OBSERVED`, `LIFECYCLE_OBSERVED`, `VULNERABILITY_CHECKED`, `PROVENANCE_OBSERVED` (plus `PARTIALLY_OBSERVABLE`, `DRIFT`, `FINDING`, `LIFECYCLE_SCRIPT`, `REGISTRY_VARIANCE`, `PARTIAL_COVERAGE`).
- `DECLARED ≠ RESOLVED`
- `RESOLVED ≠ INTEGRITY_VERIFIED`
- `INTEGRITY_VERIFIED ≠ TRUSTED`
- `VULNERABILITY_CHECKED ≠ SAFE`

#### Existing Skill Composition
```text
dependency-supply-chain-audit
             │
             ├── manifest inspection
             ├── lockfile inspection
             ├── registry inspection
             ├── lifecycle inspection
             └── dependency-vulnerability-audit [existing detector]
                         │
                         ▼
                  vulnerability result
```

---

### Contract `C-04` — `ci-workflow-audit`

#### Purpose
Explicitly model CI configuration and CI execution as multi-state observations rather than a single boolean.

#### Input
```text
CIAuditRequest {
    repository
    target_snapshot

    workflow_paths[]
    required_checks[]

    expected_commands[]
    required_permissions[]
}
```

#### Output
```text
CIAudit {
    snapshot

    workflow_files[]
    triggers[]
    jobs[]
    permissions[]

    commands[]
    environments[]
    secrets[]
    artifacts[]

    configured_checks[]
    execution_records[]

    configuration_status
    execution_status

    findings[]
    evidence[]
}
```

#### State Machine
```text
CI_NOT_CONFIGURED
        │
        ▼
CI_CONFIGURED
        │
        ▼
CI_EXECUTED
        │
   ┌────┴────┐
   ▼         ▼
CI_PASSED  CI_FAILED
```
With independent states: `CI_NOT_OBSERVABLE`, `CI_CANCELLED`, `CI_STALE` (`STALE_EXECUTION`), `PERMISSION_FINDING`.

#### Critical Invariant
`CI_PASSED(commit=A)` does **not** imply `CI_PASSED(commit=B)`.

#### Forbidden Inference
- `package.json has "test" ⇒ CI runs test`
- `workflow exists ⇒ workflow executed`
- `workflow executed ⇒ workflow passed`

---

### Contract `C-05` — `test-execution-and-evidence-audit`

#### Purpose
Establish what test evidence actually exists at `target_snapshot` (whereas `C-04` answers what the automation system does).

#### Input
```text
TestEvidenceRequest {
    repository
    target_snapshot

    required_tests[]
    commands[]

    environment_requirements
    coverage_requirements
}
```

#### Output
```text
TestEvidence {
    target_snapshot

    declared_commands[]
    executed_commands[]

    environment

    start_time
    end_time

    exit_codes[]

    stdout_references[]
    stderr_references[]

    tests_discovered
    tests_executed
    tests_passed
    tests_failed
    tests_skipped

    coverage_scope

    status
    evidence[]
}
```

#### States
`TEST_DECLARED`, `TEST_AVAILABLE`, `TEST_STARTED`, `TEST_EXECUTED`, `TEST_PASSED`, `TEST_FAILED`, `TEST_PARTIAL` (`PARTIAL_EXECUTION` / `PARTIALLY_EVIDENCED` / `TEST_SURFACE_CHANGED`), `TEST_STALE` (`STALE_EVIDENCE`), `TEST_UNOBSERVABLE` (`NOT_OBSERVABLE`), `TEST_EVIDENCED`, `CLAIM_ONLY`.

#### Critical Invariant
`TEST_PASSED` requires actual execution evidence with unmasked `exit_code == 0`, `tests_executed > 0`, and `tests_failed == 0` (`PATCH-004`, `PATCH-005`). A textual statement such as `"all tests passed"` is only `CLAIMED` (`CLAIM_ONLY`).

---

### Contract `C-06` — `evidence-receipt-generator`

#### Purpose
Central evidence normalization layer that binds claims, required evidence, actual `EvidenceRef` artifacts, and 3-snapshot provenance into `ArenaEvidenceReceipt` without manufacturing missing evidence.

#### Input
```text
ReceiptInput {
    request
    authority_result

    scope_result
    audit_results[]

    execution_records[]
    verification_results[]

    artifacts[]
}
```

#### Output
```text
ArenaEvidenceReceipt {
    schema_version
    receipt_id

    subject {
        repository
        branch
        comparison_base
        intake_snapshot
        execution_snapshot
        verification_snapshot
        head_commit
    }

    request {
        request_id
        requested_actions[]
        acceptance_criteria[]
    }

    authority {
        actor
        authority_basis
        authority_status
        scope[]
    }

    execution {
        status
        actions[]
        commands[]
        changed_paths[]
    }

    verification {
        checks[]
        snapshot_binding
        result
    }

    evidence {
        artifacts[]
        commands[]
        outputs[]
        exit_codes[]
        timestamps[]
        provenance[]
    }

    findings {
        facts[]
        blockers[]
        unknowns[]
        stale_evidence[]
        mismatches[]
    }

    conclusion {
        status
        verified_claims[]
        unverified_claims[]
        unmet_criteria[]
    }
}
```

#### Core Receipt Chain Rule
Every verified claim must be representable as:
```text
CLAIM
  ↓
REQUIRED EVIDENCE
  ↓
ACTUAL EVIDENCE (EvidenceRef)
  ↓
SNAPSHOT (S1 == S2 == head_commit)
  ↓
PROVENANCE
```
If any link in the chain breaks: `UNVERIFIED`, never `PASS`.

---

### Contract `C-07` — `arena-completion-gate`

#### Purpose
The **only** component allowed to answer: *"Is the requested task completable according to its acceptance contract?"*

#### Input
```text
CompletionRequest {
    request_id

    acceptance_criteria[]

    intake_result
    scope_result

    audit_results[]
    test_results[]
    ci_results[]

    evidence_receipt
}
```

#### Output
```text
CompletionResult {
    request_id

    status

    blocking_conditions[]
    unmet_requirements[]
    evidence_gaps[]

    verified_claims[]
    unverified_claims[]

    supporting_evidence[]
}
```

#### Terminal States
`COMPLETABLE`, `INCOMPLETE`, `BLOCKED`, `REJECTED`, `UNVERIFIED` (with `SPLIT_EVIDENCE` reported in `blocking_conditions[]` / `evidence_gaps[]`).

#### Conjunction & Non-Remediation Rules
1. **Conjunction rule**:
   ```text
   COMPLETABLE  ⇔  ∀ mandatory criterion ∈ IntakeRequest.acceptance_criteria:
                       criterion has sufficient, snapshot-matched evidence
   ```
2. **Forbidden autonomous remediation loop**:
   `C-07` must **never** trigger `completion-gate → automatically fix failures → rerun → completion`. Instead:
   ```text
   completion-gate
       ↓
   BLOCKED / INCOMPLETE
       ↓
   human / authorized next action (new C-01 / execution authority)
       ↓
   new execution (new S1)
       ↓
   new evidence (new S2 & C-06 receipt)
       ↓
   new gate evaluation
   ```

---

### Contract `C-08` — `skill-evaluation-harness`

#### Purpose
Meta-assurance infrastructure that behaviorally tests skills across `RED`, `GREEN`, `PRESSURE`, and `REGRESSION` modes.

#### Input
```text
SkillEvalCase {
    test_id
    skill_id

    prompt
    repository_fixture

    authority_context
    expected_behavior

    pressure_conditions[]
}
```

#### Output
```text
SkillEvalReceipt {
    kind: "SkillEvalReceipt"
    schema_version
    skill_id
    skill_revision
    test_id

    fixture_snapshot

    baseline {
        enabled: false
        observed_behavior
    }

    treatment {
        enabled: true
        observed_behavior
    }

    pressure {
        observed_behavior
    }

    assertions {
        passed[]
        failed[]
        unknown[]
    }

    evidence[]

    status
}
```

#### Required Evaluation Modes
- **`RED`**: Skill absent (`baseline.enabled = false`) — expected failure or weak rationalization demonstrated.
- **`GREEN`**: Skill present (`treatment.enabled = true`) — expected behavior achieved.
- **`PRESSURE`**: Adversarial prompt / conflicting instruction / tempting shortcut (`P-001`..`P-008`) — boundary holds.
- **`REGRESSION`**: Previously passing cases re-run at new `skill_revision`.

---

## 5. Frozen 13-Phase Implementation Order (`PHASE 0` – `PHASE 12`)

```text
PHASE 0   11 Assurance Invariants (AAI-001..AAI-011), 20+8 Interface Invariants (AIF-001..AIF-020), & 9 Canonical Types
    │
PHASE 1   42-case Behavioral Matrix (AAI-001..AAI-034, P-001..P-008)
    │
PHASE 2   Canonical Data Model Schema (aif-canonical-data-model.schema.json) + EvidenceRef + ArenaEvidenceReceipt
    │
PHASE 3   Skill Evaluation Harness (C-08)
    │
PHASE 4   arena-intake-and-authority (C-01)
    │
PHASE 5   agent-change-scope-audit (C-02)
    │
PHASE 6   ci-workflow-audit (C-04)
    │
PHASE 7   test-execution-and-evidence-audit (C-05)
    │
PHASE 8   dependency-supply-chain-audit (C-03)
    │
PHASE 9   arena-completion-gate (C-07) + evidence-receipt-generator (C-06)
    │
PHASE 10  RED / GREEN / PRESSURE evaluation runs
    │
PHASE 11  Real StreamForge repository trial
    │
PHASE 12  Interface freeze
```

---

## 6. Canonical Data Model (14-Type Semantic Kernel) & Expanded Invariants (`AIF-001` – `AIF-020`)

All eight contracts (`C-01`..`C-08`) share the 14-type Semantic Kernel specified in `.claude/assurance/canonical-data-model.md`, `.claude/assurance/semantic-kernel-layout-review.md`, and `schemas/aif-canonical-data-model.schema.json`:

1. `Request` (`request_id`, `actor`, `repository`, `target_ref`, `requested_actions[]`, `authority_events[]`, `acceptance_expression`, `constraints[]`, `created_at`)
2. `SnapshotRef` (`snapshot_id`, `role` ∈ `{comparison_base, intake_snapshot, execution_snapshot, verification_snapshot, current_snapshot}`, `repository`, `ref`, `commit`, `working_tree_state`, `index_state`, `captured_at`, `content_digest`, `metadata_digest`)
3. `AuthorityEvent` (`event_id`, `request_id`, `actor`, `authority_basis`, `authority_status`, `action_scope[]`, `path_scope[]`, `restrictions[]`, `issued_at`, `effective_from`, `expires_at`, `issuer`, `evidence[]`)
4. `AdmissionRecord` (`request_id`, `admission_status`, `admitted_actions[]`, `admitted_paths[]`, `excluded_actions[]`, `excluded_paths[]`, `blockers[]`, `clarifications[]`, `authority_refs[]`, `intake_snapshot`)
5. `ExecutionRecord` (`execution_id`, `request_id`, `actor`, `action`, `command`, `working_directory`, `environment_digest`, `tool`, `tool_version`, `started_at`, `ended_at`, `execution_state`, `exit_code`, `stdout_ref`, `stderr_ref`, `subject_snapshot`, `resulting_snapshot` + 3-layer results `PROCESS_RESULT`, `TEST_RESULT`, `SEMANTIC_RESULT`)
6. `ChangeRecord` (`path`, `change_type`, `before_digest`, `after_digest`, `intake_state`, `execution_state`, `attribution`, `attribution_basis`, `generated`, `generated_by`)
7. `Claim` (`claim_id`, `subject`, `proposition`, `required_evidence[]`, `required_snapshot`, `status`)
8. `EvidenceRef` (`evidence_id`, `producer`, `producer_version`, `source_type`, `source_locator`, `captured_at`, `subject_snapshot`, `scope`, `content_digest`, `provenance[]`, `claim_scope`, `limitations[]`, `snapshot_independent`)
9. `EvidenceCoverage` (`evidence_id`, `claim_id`, `subject_match`, `snapshot_match`, `scope_match`, `method_match`, `freshness`, `adequacy`, `limitations[]`)
10. `VerificationRecord` (`verification_id`, `claim_id`, `method`, `subject_snapshot`, `evidence_refs[]`, `coverage[]`, `result`, `verified_at`, `verifier`)
11. `Finding` (`finding_id`, `category`, `severity`, `proposition`, `subject`, `snapshot`, `evidence_refs[]`, `confidence`, `limitations[]`, `remediation_authorized: false`)
12. `AcceptanceExpression` (`ALL`, `ANY`, `AT_LEAST_N`, `OPTIONAL`, `CONDITIONAL`, and leaf `CLAIM(claim_id)` / `CRITERION`)
13. `CompletionResult` (`request_id`, `acceptance_expression`, `status`, `evaluated_claims[]`, `satisfied_requirements[]`, `unmet_requirements[]`, `blockers[]`, `unknowns[]`, `evidence_refs[]`, `evaluated_snapshot`, `generated_at`)
14. `ArenaEvidenceReceipt` (`schema_version: "aif/0.1"`, uniting all Semantic Kernel objects; `CompletionGate = Evaluate(AcceptanceExpression, ArenaEvidenceReceipt)`)

### Expanded Invariant Set (`AIF-001` – `AIF-020` + Sub-Invariants `AIF-001A` – `AIF-014A`)

| Invariant ID | Formal Statement | Canonical Type / Contract Binding |
|---|---|---|
| `AIF-001` | **Authority precedes mutation.** | `AuthorityEvent`, `C-01`, `C-02`, `C-07` |
| `AIF-001A` | **Authority is time- and action-scoped** (`EXECUTED(action, t) ⇒ ∃ E: action ∈ E.action_scope ∧ E.effective_from ≤ t < E.expires_at`). | `AuthorityEvent`, `ExecutionRecord` |
| `AIF-002` | **Scope is 4-snapshot-relative** (`S0 = intake`, `S1 = execution`, `S2 = verification`, `S3 = current/head` + `comparison_base`). | `SnapshotRef`, `C-01`, `C-02` |
| `AIF-002A` | **No evidence may transfer across snapshots without explicit justification** (`snapshot_independent == true`). | `SnapshotRef`, `EvidenceRef`, `EvidenceCoverage` |
| `AIF-003` | **Agent changes require before/after provenance** (`DIFF(S0, S1)`). | `SnapshotRef`, `PathTransition`, `C-02` |
| `AIF-003A` | **State transition is not actor causality without attribution evidence** (`STATE_CHANGE` vs `AGENT_ATTRIBUTED_CHANGE` vs `UNATTRIBUTED_CHANGE`). | `PathTransition`, `ExecutionRecord`, `C-02` |
| `AIF-004` | **Declaration is not execution.** | `ExecutionRecord`, `C-04`, `C-05` |
| `AIF-004A` | **Execution identity includes command, environment, working directory, tool version, timestamps, and subject snapshot.** | `ExecutionRecord`, `C-04`, `C-05` |
| `AIF-005` | **Execution is not success.** | `ExecutionRecord`, `C-04`, `C-05` |
| `AIF-005A` | **Process success (`PROCESS_RESULT`), test success (`TEST_RESULT`), and semantic sufficiency (`SEMANTIC_RESULT`) are distinct.** | `ExecutionRecord`, `C-05` |
| `AIF-006` | **Success is not verification.** | `Claim`, `EvidenceCoverage`, `C-05`..`C-07` |
| `AIF-006A` | **Verification is always relative to an explicitly named claim** (`VERIFY(claim, evidence, verification_method, snapshot)`). | `Claim`, `EvidenceCoverage`, `C-06`, `C-07` |
| `AIF-007` | **Evidence is bound to `subject`, `scope`, `method`, `snapshot`, and `limitations` via `Coverage(E, C)`.** | `EvidenceRef`, `EvidenceCoverage` |
| `AIF-008` | **Unknown remains unknown (`UNKNOWN ≠ PASS`).** | `Claim`, `Finding`, `C-01`..`C-08` |
| `AIF-008A` | **`NOT_REQUESTED ≠ NOT_CHECKED ≠ NOT_OBSERVABLE ≠ UNKNOWN ≠ PARTIAL ≠ CONTRADICTED`.** | `Claim`, `Finding`, `C-06`, `C-07` |
| `AIF-009` | **Acceptance is evaluated against an explicit `AcceptanceExpression` AST (`ALL`, `ANY`, `AT_LEAST_N`, `OPTIONAL`, `CONDITIONAL`, `CRITERION`).** | `AcceptanceExpression`, `C-01`, `C-06`, `C-07` |
| `AIF-010` | **Audit does not authorize remediation (`remediation_authorized == false`).** | `Finding`, `AuthorityEvent`, `C-02`..`C-07` |
| `AIF-011` | **Completion requires satisfaction of each criterion's specific `EvidenceRequirement`.** | `AcceptanceExpression`, `EvidenceCoverage`, `C-07` |
| `AIF-012` | **Detectors produce findings and `EvidenceRef` artifacts, not completion decisions.** | `Finding`, `EvidenceRef`, Detectors |
| `AIF-013` | **Completion gate consumes evidence and never manufactures it (`¬Evidence(C) ≠ Evidence(¬C)`).** | `Claim`, `ArenaEvidenceReceipt`, `C-06`, `C-07` |
| `AIF-014` | **Mutation after verification invalidates snapshot-dependent claims.** | `SnapshotRef`, `EvidenceCoverage`, `C-02`, `C-07` |
| `AIF-014A` | **Evidence invalidation is claim-scope-dependent (`VALID_AT_SNAPSHOT`, `INVALIDATED_BY_MUTATION`, `INVALIDATED_BY_DEPENDENCY_CHANGE`, `SNAPSHOT_INDEPENDENT_VALID`).** | `EvidenceRef`, `EvidenceCoverage`, `C-06`, `C-07` |
| `AIF-015` | **No evidence from one subject or snapshot may satisfy a claim about another.** | `Claim`, `EvidenceCoverage`, `C-06`, `C-07` |
| `AIF-016` | **Evidence normalization (`C-06`) may not broaden semantic `claim_scope`.** | `EvidenceRef`, `ArenaEvidenceReceipt`, `C-06` |
| `AIF-017` | **Contradictory evidence (`CLEAN` vs `FOUND`) must remain `CONTRADICTED / CONFLICT`, never collapsed to `PASS`.** | `Claim`, `EvidenceCoverage`, `Finding`, `C-06`, `C-07` |
| `AIF-018` | **Skill assertions (`verified=true`) are not execution evidence (`source_type ≠ SKILL_ASSERTION`).** | `EvidenceRef`, `ExecutionRecord`, `C-06`, `C-08` |
| `AIF-019` | **Missing evidence is an explicit epistemic state, not an implicit pass.** | `Claim`, `AcceptanceExpression`, `C-06`, `C-07` |
| `AIF-020` | **Every completion decision must be deterministically reproducible from `Evaluate(AcceptanceExpression, ArenaEvidenceReceipt)` alone.** | `AcceptanceExpression`, `ArenaEvidenceReceipt`, `C-06`, `C-07` |

### Freeze Assessment

- **`SKILL.md` implementation**: **`NOT YET`**
- **Interface freeze**: **`NOT YET`** (Canonical Data Model v0.1 and `AIF-001`..`AIF-020` are now specified in `.claude/assurance/canonical-data-model.md` and `schemas/aif-canonical-data-model.schema.json` to serve as the shared foundation before `SKILL.md` authoring)
- **Architecture**: **`STRONG / PROVISIONAL`**

