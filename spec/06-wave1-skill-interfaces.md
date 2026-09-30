# 06 — v0.1 Normative Interface Contracts for the Eight Assurance Components (`PROVISIONALLY FROZEN`)

> **Canonical Design Artifact**: Synchronized with [`.claude/assurance/component-contracts.md`](../.claude/assurance/component-contracts.md) and [`.claude/assurance/capability-map.md`](../.claude/assurance/capability-map.md).
> **Status**: `PROVISIONALLY FROZEN — v0.1 Normative Interface Contract`
> **Rule**: Only after these eight component contracts are frozen may `skill-creator` (paired with `skill-evaluation-harness`) be used to generate the actual `SKILL.md` directories.

---

## 1. Post-Overlap-Audit Architectural Corrections

### 1.1 Detectors vs. Verifiers vs. Authorities vs. Evidence Infrastructure vs. Meta-Assurance

To prevent the failure mode where *the component that detects a condition also declares that the condition is sufficient for completion*, `.claude/skills/` is organized into four layers and five distinct functional roles:

```text
┌─────────────────────────────────────────────────────────┐
│                 DECISION / ASSURANCE                    │
│                                                         │
│  07 arena-completion-gate           [W8 authority]      │
│  06 evidence-receipt-generator      [W7 evidence]       │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                 VERIFICATION / AUDIT                    │
│                                                         │
│  02 agent-change-scope-audit        [W2 verifier]       │
│  04 ci-workflow-audit               [W5 verifier]       │
│  05 test-execution-and-evidence-audit [W6 verifier]     │
│  03 dependency-supply-chain-audit   [W4 verifier]       │
│                                                         │
│  secret-leak-scan                   [W3 existing detector]│
│  dependency-vulnerability-audit     [existing detector] │
│  authorization-boundary-scan        [existing detector] │
│  docs-integrity-check               [existing detector] │
│  contract-implementation-sync       [existing verifier] │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                    AUTHORITY                             │
│                                                         │
│  01 arena-intake-and-authority      [W1 authority]      │
│  repo-onboarding-audit              [existing context]  │
│  session-git-sync-check             [existing]          │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                    META / DEVELOPMENT                    │
│                                                         │
│  skill-creator                      [existing]          │
│  08 skill-evaluation-harness        [new meta]          │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Two Kinds of Authorization (Never Merge)

```text
                       AUTHORIZATION
                             │
              ┌──────────────┴──────────────┐
              │                             │
       DOMAIN AUTHORITY              AGENT AUTHORITY
              │                             │
     "Is this content/use            "May this agent
      permitted?"                     modify this?"
              │                             │
     authorization-                 arena-intake-
     boundary-scan                  and-authority
```

### 1.3 Secret Scanning & Vulnerability Scanning: Reuse Existing Detectors

- **Secret scanning (`Secret skill needed = NO`)**: `secret-leak-scan` is already a well-bounded working-tree detector (`HIGH`, `LOW`, `placeholder`, `clean`). `06 evidence-receipt-generator` adapts its output into a snapshot-bound `SCANNER_NO_MATCH` (`PARTIAL_COVERAGE`) receipt (`W3` / `W7`), and `07 arena-completion-gate` decides whether that scoped claim satisfies the acceptance criterion.
- **Vulnerability scanning (`New vulnerability scanner needed = NO`)**: `dependency-vulnerability-audit` remains the advisory detector and is consumed as one evidence source inside `03 dependency-supply-chain-audit` (`W4`).

### 1.4 Three-Snapshot Provenance Model (`S0`, `S1`, `S2`)

```text
BASELINE → S0 (intake_snapshot) → S1 (execution_snapshot) → S2 (verification_snapshot)
```

- `AGENT_CHANGE = DIFF(S0, S1)` (never `DIFF(remote, S1)`, which would conflate `PREEXISTING = DIFF(comparison_base, S0)` with agent actions).
- Five distinct ref fields in `ArenaEvidenceReceipt.subject`: `comparison_base`, `intake_snapshot` (`S0`), `execution_snapshot` (`S1`), `verification_snapshot` (`S2`), and `head_commit` (`HEAD`).
- Enforced by **`AAI-011` — Verification Immutability**: `VERIFIED(C, S2)` does not certify any later mutable state `S' != S2`.

---

## 2. Normative v0.1 Component Contracts (`01` – `08` / `W1` – `W8`)

### `01` (`W1`) — `arena-intake-and-authority`
- **Layer / Role**: `AUTHORITY` / `Authority & Decision Component`
- **Owns**: `WHO | WHAT | WHERE | WHICH ACTION | UNDER WHICH AUTHORITY | WITH WHICH CONSTRAINTS` + capturing `S0 = intake_snapshot`. Does not determine technical correctness or Domain Authority (`authorization-boundary-scan`).
- **Input**: `Request`, `Repository`, `Branch`, `comparison_base`, `intake_snapshot (S0)`, `Requester authority`, `Requested actions`, `Target paths/resources`, `Repo governance policy`, `Acceptance criteria`.
- **Output**: `IntakeAuthorityRecord { request_id, subject { repository, branch, comparison_base, intake_snapshot }, authority { authority_basis, authority_status, mutation_permitted, authorized_scope[], forbidden_scope[] }, states, blockers[], required_clarifications[] }`.
- **States**: `PROPOSED → AUTHORIZED → ADMITTED`, `INSPECT_ONLY`, `BLOCKED`, `REJECTED`.
- **Invariants & Tests**: `AAI-001`, `AAI-002`, `AAI-008`, `AAI-010`; Test IDs `AAI-001`..`AAI-004`, `P-005`, `P-008`.
- **Required Evidence**: Original request prompt, repository governance policy, and `S0` snapshot descriptor.
- **Forbidden Inferences**: `capable ⇒ authorized`; `"fix everything" ⇒ broad authorization`; `"investigate CI" ⇒ modify files`; `authorized(path A) ⇒ authorized(neighboring path B)`; `user intent ⇒ overrides repo policy`; `prior scope receipt ⇒ silent mid-task scope expansion`.

---

### `02` (`W2`) — `agent-change-scope-audit`
- **Layer / Role**: `VERIFICATION / AUDIT` / `Verifier (Change Provenance)`
- **Owns**: `WHAT ACTUALLY CHANGED` via `AGENT_CHANGE = DIFF(S0, S1)`, classifying paths as `authorized (IN_SCOPE)`, `pre-existing (PREEXISTING = DIFF(comparison_base, S0))`, `generated (GENERATED)`, `unexpected (OUT_OF_SCOPE)`, and `deleted / modified / added`. Does not determine whether changes are technically good, and must never mutate files to pass its own audit (`AAI-010`).
- **Input**: `AUTHORIZED_SCOPE` (from `01`), `comparison_base`, `intake_snapshot (S0)`, `execution_snapshot (S1)`, `build_generated_patterns`, `generated_artifact_policy`.
- **Output**: `ScopeAuditRecord { subject { comparison_base, intake_snapshot, execution_snapshot }, diffs { preexisting_paths[], agent_changed_paths[] }, classifications { in_scope[], out_of_scope[], deleted_out_of_scope[], generated[], preexisting[] }, scope_status, states, failure_codes[] }`.
- **States**: `IN_SCOPE`, `OUT_OF_SCOPE`, `GENERATED`, `PREEXISTING`, `MIXED`, `UNDETERMINED` (never collapsed into `IN_SCOPE`).
- **Invariants & Tests**: `AAI-001`, `AAI-002`, `AAI-003`, `AAI-010`; Test IDs `AAI-005`..`AAI-008`, `AAI-032`, `P-002`, `P-008`.
- **Required Evidence**: `S0` and `S1` tree hashes and diff manifests (`git diff --name-status`), plus pre/post-audit tree hash equality (`P-002`).
- **Forbidden Inferences**: `DIFF(remote, S1) ⇒ AGENT_CHANGE`; `README edit ⇒ harmless`; `generated(path) ⇒ authorized(path)`; `deletion ⇒ cleanup`; `audit found out-of-scope file ⇒ agent may delete/revert it during audit`.

---

### `03` (`W4`) — `dependency-supply-chain-audit`
- **Layer / Role**: `VERIFICATION / AUDIT` / `Verifier (Supply-Chain Orchestrator)`
- **Owns**: `dependency declaration → resolution → lock → integrity → registry → lifecycle → vulnerability → provenance`. Consumes the existing `dependency-vulnerability-audit` detector rather than replacing it.
- **Input**: `project_dir`, `verification_snapshot (S2)`, `allowed_registries[]`, `vulnerability_detector_output` (from `dependency-vulnerability-audit`).
- **Output**: `SupplyChainAuditRecord { verification_snapshot, manifests_detected[], lockfiles_detected[], graph_observability, manifest_lock_status, integrity_status, registry_status, lifecycle_scripts, vulnerability_summary, overall_classification, states, failure_codes[] }`.
- **States**: `SUPPLY_CHAIN_VERIFIED`, `PARTIALLY_OBSERVABLE`, `DRIFT`, `FINDING`, `LIFECYCLE_SCRIPT`, `REGISTRY_VARIANCE`, `PARTIAL_COVERAGE`, `NOT_OBSERVABLE`.
- **Invariants & Tests**: `AAI-003`, `AAI-007`, `AAI-008`, `AAI-010`, `AAI-011`; Test IDs `AAI-013`..`AAI-017`, `P-006`.
- **Required Evidence**: Manifest & lockfile hashes at `S2`, `.npmrc`/`pip.conf`/`.cargo/config.toml` resolution configs, lifecycle hooks, and raw `dependency-vulnerability-audit` output.
- **Forbidden Inferences**: `manifest exists ⇒ resolved graph`; `manifest ≠ lockfile ⇒ either is automatically authoritative`; `direct deps clean ⇒ transitive graph clean`; `postinstall exists ⇒ malicious`; `alternate registry ⇒ compromised`; `scanner SKIP / exit 0 ⇒ 0 vulnerabilities`.

---

### `04` (`W5`) — `ci-workflow-audit`
- **Layer / Role**: `VERIFICATION / AUDIT` / `Verifier (CI Configuration vs. Execution)`
- **Owns**: Separate classification of `WHAT CI IS CONFIGURED TO DO` (`CI_CONFIGURATION`) and `WHAT CI ACTUALLY EXECUTED` (`CI_EXECUTION`).
- **Input**: `workflow_dir`, `verification_snapshot (S2)`, `head_commit`, `observed_ci_runs[]`, `ci_api_reachable`.
- **Output**: `CIWorkflowAuditRecord { verification_snapshot, head_commit, ci_configuration { status, workflow_files[], declared_jobs[], permission_findings[] }, ci_execution { status, matching_head_runs[], stale_runs[] }, ci_pass, overall_classification, states, failure_codes[] }`.
- **States**:
  - `CI_CONFIGURATION`: `CI_CONFIGURED`, `NOT_OBSERVED`, `PERMISSION_FINDING`
  - `CI_EXECUTION`: `EXECUTED_AT_HEAD`, `STALE_EXECUTION`, `NOT_EXECUTED`, `UNKNOWN`, `NOT_OBSERVABLE`
  - `CI_PASS`: `PASSED`, `FAILED`, `UNKNOWN`, `NOT_APPLICABLE`
- **Invariants & Tests**: `AAI-003`, `AAI-004`, `AAI-005`, `AAI-008`, `AAI-011`; Test IDs `AAI-019`..`AAI-021`, `P-007`.
- **Required Evidence**: Workflow YAML files (or directory proof of absence) and CI run records (`run_id`, `head_sha`, `status`, `conclusion`).
- **Forbidden Inferences**: `workflow file exists ⇒ CI executed or passed`; `workflow file absent ⇒ CI = FAIL or CI = PASS`; `old commit CI green ⇒ current HEAD CI green`; `broad workflow permission ⇒ compromise`; `local tests pass ⇒ CI passed`.

---

### `05` (`W6`) — `test-execution-and-evidence-audit`
- **Layer / Role**: `VERIFICATION / AUDIT` / `Verifier (Test Execution Lifecycle & Evidence)`
- **Owns**: `WHAT TEST WAS REQUESTED | WHAT TEST WAS EXECUTED | ON WHICH SNAPSHOT (S2 vs S1) | WITH WHAT COMMAND | WITH WHAT EXIT STATUS | WITH WHAT RESULT`. Consumes `repo-onboarding-audit` (`detect_manifests()`) for `TEST_DECLARED` (`AAI-018`). Does not decide overall task completion.
- **Input**: `execution_snapshot (S1)`, `verification_snapshot (S2)`, `agent_changed_paths[]`, `declared_scripts`, `discovered_test_files[]`, `execution_records[]`, `agent_prose_claims[]`.
- **Output**: `TestExecutionAuditRecord { snapshots { execution_snapshot, verification_snapshot, snapshot_match }, progression_stage, test_surface_integrity, suite_coverage, overall_classification, states, failure_codes[] }`.
- **States & Progression Ladder**:
  ```text
  TEST_DECLARED / TEST_AVAILABLE → TEST_STARTED → TEST_EXECUTED → TEST_PASSED → TEST_EVIDENCED
  ```
  Plus failure/partial classifications: `CLAIM_ONLY`, `STALE_EVIDENCE`, `PARTIAL_EXECUTION`, `PARTIALLY_EVIDENCED`, `TEST_SURFACE_CHANGED`, `NOT_OBSERVABLE`, `TEST_FAILED`.
- **Invariants & Tests**: `AAI-003`..`AAI-008`, `AAI-011`; Test IDs `AAI-018`, `AAI-022`..`AAI-026`, `P-001`, `P-003`.
- **Required Evidence**: `declared_command`, `executed_command`, observed integer `exit_code`, `stdout`/`stderr` digests, timestamps, `S1`/`S2` snapshots, and discovered vs. modified test file lists.
- **Forbidden Inferences**: `script in package.json ⇒ executed`; `"tests pass" in prose ⇒ executed`; `pre-edit test output ⇒ valid after edit`; `1 test file passed ⇒ suite passed`; `stdout without exit code ⇒ passed`; `modified tests pass ⇒ independent verification`; `runner unavailable ⇒ pass`.

---

### `06` (`W7` / `W3` Adapter) — `evidence-receipt-generator`
- **Layer / Role**: `DECISION / ASSURANCE` / `Evidence Infrastructure & Detector Adapter`
- **Owns**: `claim → evidence requirement → actual evidence → 3-snapshot binding (S0, S1, S2) → provenance → ArenaEvidenceReceipt`. Adapts existing detector outputs (`secret-leak-scan`, `docs-integrity-check`, `authorization-boundary-scan`) into scoped evidence records. Must **never** manufacture missing evidence.
- **Input**: `subject { repository, branch, comparison_base, intake_snapshot, execution_snapshot, verification_snapshot, head_commit }`, `request`, verifier records (`01`..`05`), `detector_runs[]` (including `secret-leak-scan`), and `candidate_claims[]`.
- **Output**: `ArenaEvidenceReceipt` (`schemas/aif-evidence-receipt.schema.json`).
- **States**:
  - `verification.snapshot_binding`: `STABLE_MATCH` (`S1 == S2 == head_commit`), `VERIFICATION_STALE` (`S1 != S2`), `EVIDENCE_MISMATCH` (`S2 != head_commit`), `UNBOUND`
  - Scoped claim classifications: `NOT_SECRET_CONFIRMED`, `SUSPECTED`, `HISTORICAL_EXPOSURE`, `PARTIAL_COVERAGE`, `SCANNER_NO_MATCH`, `TYPECHECK_VERIFIED`, `UNVERIFIED`, `EVIDENCE_MISMATCH`
- **Invariants & Tests**: `AAI-003`, `AAI-006`, `AAI-007`, `AAI-008`, `AAI-011`; Test IDs `AAI-009`..`AAI-012`, `AAI-027`..`AAI-030`, `P-004`, `P-006`.
- **Required Evidence**: Non-empty `evidence.commands`, `evidence.exit_codes`, `evidence.timestamps`, `evidence.provenance`, and 3-snapshot binding (`S0`, `S1`, `S2`, `head_commit`).
- **Forbidden Inferences**: `receipt assertion ⇒ evidence`; `nearby commit SHA ⇒ same state`; `typecheck pass ⇒ repository correctness`; `secret-leak-scan 0 hits ⇒ universal absence of secrets`.

---

### `07` (`W8`) — `arena-completion-gate`
- **Layer / Role**: `DECISION / ASSURANCE` / `Terminal Authority & Decision Component`
- **Owns ONLY**: *"Given all available evidence (`ArenaEvidenceReceipt`), are the mandatory acceptance criteria sufficiently evidenced at the current snapshot?"* Does not execute remediation.
- **Input**: `current_head_commit`, `current_tree_hash`, `mandatory_acceptance_criteria[]`, `evidence_receipts[]` (`ArenaEvidenceReceipt`), optional `user_completion_override_prompt`.
- **Output**: `CompletionGateDecision { evaluated_at_commit, claim_matrix[], gate_status, states, blockers[], unmet_criteria[] }`.
- **States**: `COMPLETABLE`, `INCOMPLETE`, `BLOCKED`, `REJECTED`, `SPLIT_EVIDENCE`, `UNVERIFIED`.
- **Invariants & Tests**: `AAI-001`..`AAI-011`; Test IDs `AAI-031`..`AAI-034`, `P-001`, `P-005`, `P-007`.
- **Required Evidence**: Validated `ArenaEvidenceReceipt` instances covering 100% of mandatory acceptance criteria at `S1 == S2 == current_head_commit` with `authority_status == ADMITTED` and `scope_status == IN_SCOPE`.
- **Forbidden Inferences**: `code exists ⇒ done`; `tests pass ⇒ scope violation repaired`; `choose convenient snapshot when CI and local disagree`; `majority of criteria evidenced ⇒ complete`; `user says "just mark it complete" ⇒ complete`.

---

### `08` — `skill-evaluation-harness`
- **Layer / Role**: `META / DEVELOPMENT` / `Meta-Assurance Behavioral Evaluator`
- **Owns**: `skill quality | trigger precision | behavioral correctness | pressure resistance | regression stability`. Evaluates the skills themselves and emits `SkillEvalReceipt` (`schemas/aif-skill-eval-receipt.schema.json`).
- **Input**: `skill_id`, `skill_dir`, `skill_revision`, `test_cases[]` (`AAI-001`..`034`, `P-001`..`008`).
- **Output**: `SkillEvalReceipt` (`baseline { skill_enabled: false }`, `treatment { skill_enabled: true }`, `pressure { mutation_attempt, observed_response }`, `assertions { expected[], observed[], passed[], failed[], unknown[] }`, `evidence`, `conclusion { status, dimensions }`).
- **States**: `PASS`, `FAIL`, `UNKNOWN`, `NOT_APPLICABLE`, `NOT_OBSERVABLE`.

---

## 3. Canonical Failure Cause Taxonomy (15 Codes)

| Failure Code | Meaning |
| :--- | :--- |
| `AUTHORITY_MISSING` | No usable authority evidence |
| `SCOPE_UNDEFINED` | Target/action boundary insufficient |
| `SCOPE_VIOLATION` | Actual changes (`DIFF(S0, S1)`) exceed authorized scope |
| `NOT_EXECUTED` | Required command/action never ran |
| `WRONG_HEAD` | Evidence belongs to another commit (`S2 != head_commit`) |
| `STALE_EVIDENCE` | Evidence predates relevant changes (`S1 != S2`) |
| `CI_NOT_CONFIGURED` | No applicable CI automation found |
| `CI_NOT_EXECUTED` | Workflow exists but execution not evidenced |
| `TEST_NOT_EXECUTED` | Required test was not actually run |
| `TEST_FAILED` | Test execution failed (`exit_code != 0`) |
| `SECRET_UNVERIFIED` | Suspicious material or history cannot be conclusively classified |
| `DEPENDENCY_UNRESOLVED` | Dependency graph cannot be established |
| `EVIDENCE_INCOMPLETE` | Claim lacks required evidence |
| `ARTIFACT_MISMATCH` | Artifact does not correspond to claimed source |
| `RECEIPT_INVALID` | Evidence receipt itself fails schema/integrity requirements |

---

## 4. Shared Evidence Identity (`EvidenceRef`), Adequacy Rule & Ten Forbidden Transitions

### 4.1 `EvidenceRef` (`schemas/aif-evidence-ref.schema.json`)

```text
EvidenceRef {
    evidence_id
    repository
    snapshot
    source_type
    source_locator
    captured_at
    producer
    producer_version
    claim_scope
}
```

### 4.2 Evidence Adequacy Rule

```text
RESULT ≠ EVIDENCE ≠ DECISION
evidence adequacy = claim requirements ∩ evidence coverage
```

### 4.3 Ten Forbidden Transitions (`FT-01` – `FT-10`)

1. `CLAIMED → VERIFIED`
2. `DECLARED → EXECUTED`
3. `EXECUTED → PASSED`
4. `CI_CONFIGURED → CI_PASSED`
5. `SCANNER_CLEAN → REPOSITORY_SAFE`
6. `CODE_PRESENT → IMPLEMENTED`
7. `IMPLEMENTED → VERIFIED`
8. `VERIFIED@A → VERIFIED@B`
9. `AUDIT_FINDING → REMEDIATED`
10. `UNKNOWN → PASS`

---

## 5. Arena Assurance Interface Freeze v0.1 (`AIF-001` – `AIF-014`) & Contract Index (`C-01` – `C-08`)

| Contract ID | Component | Freeze Rules Bound |
| :--- | :--- | :--- |
| `C-01` (`W1`) | `arena-intake-and-authority` (`IntakeRequest` → `IntakeResult`) | `AIF-001`, `AIF-002`, `AIF-009`, `AIF-010` |
| `C-02` (`W2`) | `agent-change-scope-audit` (`ScopeAuditRequest` → `ScopeAudit`) | `AIF-001`, `AIF-002`, `AIF-003`, `AIF-010`, `AIF-014` |
| `C-03` (`W4`) | `dependency-supply-chain-audit` (`SupplyChainRequest` → `DependencyAudit`) | `AIF-004`, `AIF-007`, `AIF-008`, `AIF-009`, `AIF-012` |
| `C-04` (`W5`) | `ci-workflow-audit` (`CIAuditRequest` → `CIAudit`) | `AIF-004`, `AIF-005`, `AIF-007`, `AIF-009`, `AIF-014` |
| `C-05` (`W6`) | `test-execution-and-evidence-audit` (`TestEvidenceRequest` → `TestEvidence`) | `AIF-004`, `AIF-005`, `AIF-006`, `AIF-007`, `AIF-009`, `AIF-014` |
| `C-06` (`W7`) | `evidence-receipt-generator` (`ReceiptInput` → `ArenaEvidenceReceipt`) | `AIF-003`, `AIF-007`, `AIF-008`, `AIF-009`, `AIF-012`, `AIF-013`, `AIF-014` |
| `C-07` (`W8`) | `arena-completion-gate` (`CompletionRequest` → `CompletionResult`) | `AIF-001`..`AIF-014` |
| `C-08` | `skill-evaluation-harness` (`SkillEvalCase` → `SkillEvalReceipt`) | `AIF-001`..`AIF-014` (`RED`, `GREEN`, `PRESSURE`, `REGRESSION`) |

### The 14 Interface Freeze Invariants (`AIF-001` – `AIF-014`)
- `AIF-001`: Authority precedes mutation
- `AIF-002`: Scope is snapshot-relative
- `AIF-003`: Agent changes require before/after provenance
- `AIF-004`: Declaration is not execution
- `AIF-005`: Execution is not success
- `AIF-006`: Success is not verification
- `AIF-007`: Verification is snapshot-bound
- `AIF-008`: Evidence has bounded claim scope
- `AIF-009`: Unknown remains unknown
- `AIF-010`: Audit does not authorize remediation
- `AIF-011`: Completion is conjunctive over mandatory criteria
- `AIF-012`: Existing detectors produce evidence; they do not decide completion
- `AIF-013`: Completion gate consumes evidence; it does not manufacture evidence
- `AIF-014`: A changed verification snapshot invalidates prior certification

