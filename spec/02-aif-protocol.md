# 02 — AIF Protocol Specification (Agent Assurance Interface)

## 1. Canonical Definition

**AIF (Agent Assurance Interface)** is a repository-governed assurance protocol for agent-driven software work. It defines a common semantic interface for **authority, admission, execution, change attribution, observation, verification, evidence, acceptance, and completion**.

> **Tagline:** *AIF — Evidence-bound assurance for agent-driven software work.*

### 1.1 Core Principle

> **No claim is verified without sufficient, scope-bounded, snapshot-bound evidence. No task is complete without evidence satisfying every mandatory acceptance criterion.**

### 1.2 Architectural Separation

```text
AIF does not make the work happen.
AIF determines what may be claimed about what happened.
```

AIF preserves the repository's standing non-conflation discipline across all eleven foundational concepts:

```text
representation ≠ semantics ≠ evidence ≠ truth ≠ authority ≠ authorization ≠ admission ≠ execution ≠ success ≠ canonicality ≠ durability
```

At the operational boundary, an Arena Agent progresses through five distinct assurance questions:

```text
             ARENA AGENT
                  │
                  ▼
        ┌─────────────────────┐
        │ Authorization       │
        │ What may I do?      │
        └──────────┬──────────┘
                   ▼
        ┌─────────────────────┐
        │ Admission           │
        │ What is allowed now?│
        └──────────┬──────────┘
                   ▼
        ┌─────────────────────┐
        │ Execution           │
        │ What actually ran?  │
        └──────────┬──────────┘
                   ▼
        ┌─────────────────────┐
        │ Verification        │
        │ What did it prove?  │
        └──────────┬──────────┘
                   ▼
        ┌─────────────────────┐
        │ Evidence            │
        │ Can we reproduce it?│
        └─────────────────────┘
```

---

## 2. The AIF Assurance Pipeline

AIF structures assurance as a directed semantic pipeline:

```text
AUTHORITY
    ↓
ADMISSION
    ↓
EXECUTION
    ↓
OBSERVATION
    ↓
VERIFICATION
    ↓
EVIDENCE
    ↓
ACCEPTANCE
    ↓
COMPLETION
```

Across this pipeline, AIF separates concerns explicitly so that no stage can impersonate a downstream stage:

| Concern | Authority / Semantic Layer | Normative Question Answered |
| :--- | :--- | :--- |
| May this operation occur? | **Authority / Admission** | Is the agent authorized, and does the operation satisfy scope and policy preconditions? |
| Did an operation actually execute? | **Execution evidence** | Was the tool or command invoked, with what parameters, and in what execution context? |
| What changed? | **Change attribution** | Which repository files and snapshots (`pre_snapshot` → `post_snapshot`) were modified? |
| What was observable? | **Observation** | What outputs, exit codes, logs, diffs, or runtime signals were actually captured? |
| Does observation satisfy the claim? | **Verification** | When evaluated against the claim predicate and scope, what epistemic state results? |
| What proves the verification? | **Evidence** | Which immutable, snapshot-bound, scope-bounded artifact record backs the verification? |
| Does evidence satisfy the contract? | **Acceptance** | Are all mandatory acceptance criteria for the task backed by valid `VERIFIED` evidence? |
| May the task be declared complete? | **Completion** | Do all mandatory acceptance criteria hold at the final repository snapshot without contradiction or staleness? |

---

## 3. Specification of Semantic Stages

### 3.1 Authority

**Authority** defines the ceiling of permissible actions granted to an agent session by the host environment, user, and repository governance policy.

* **Inputs**: Session identity, branch binding (e.g., locked working branch), repository governance policy (`atsas-governance.schema.json`), user grants.
* **Semantics**: Determines whether a class of operation (e.g., mutating workspace files, running subprocesses, pushing to a branch) is within the agent's delegated authority.

### 3.2 Admission

**Admission** evaluates a specific proposed operation against active **Authority**, task scope, and repository preconditions prior to execution.

* **Inputs**: Proposed tool/command invocation, target paths, current repository snapshot, authority context.
* **Outcomes**:
  * `ADMITTED` — Operation is permitted to execute.
  * `REJECTED` — Operation violates authority or governance policy (e.g., modifying `.git` internals, switching off a bound session branch).
  * `ESCALATED` — Operation requires explicit user confirmation before execution.

### 3.3 Execution

**Execution** records the concrete occurrence of an admitted operation.

* **Properties**:
  * `execution_id`: Unique identifier for the execution event.
  * `tool_id` & `invocation`: Exact tool and parameters or command executed.
  * `pre_snapshot_id`: Repository snapshot immediately prior to execution.
  * `post_snapshot_id`: Repository snapshot immediately following execution.
  * `started_at`, `completed_at`, `duration_ms`.
* **Constraint**: Execution proves only that an action was attempted and finished; **execution is not verification, and execution is not completion**.

### 3.4 Change Attribution

**Change Attribution** binds workspace modifications to the execution events and repository snapshots that produced them.

* **Repository Snapshot (`aif-snapshot.schema.json`)**:
  * `snapshot_id`: Unique identifier for the state of the workspace.
  * `git_head_sha`: Base commit SHA.
  * `tree_hash`: Cryptographic digest of the tracked and relevant working-tree state (e.g., `git write-tree` or manifest digest).
  * `modified_paths`: Explicit list of added, modified, deleted, or renamed paths relative to `git_head_sha`.
* **Semantics**: Any mutation advances the workspace to a new `snapshot_id` and `tree_hash`. Evidence collected against an earlier `tree_hash` whose covered scope intersects subsequent changes automatically transitions to `STALE`.

### 3.5 Observation

**Observation** captures what was empirically visible from an execution event or workspace inspection, along with explicit boundaries on what could **not** be observed.

* **Properties**:
  * `observation_id`: Unique identifier.
  * `execution_id`: Reference to the execution that produced the observation.
  * `snapshot_id`: The repository snapshot under which the observation was recorded.
  * `observability_status`: `FULL`, `PARTIAL`, or `NOT_OBSERVABLE`.
  * `signals`: Structured outputs (`exit_code`, `stdout_digest`, `stderr_digest`, `excerpt`, `parsed_metrics`).
  * `unobserved_dimensions`: Explicit declaration of aspects that were not observable (e.g., external production database state, unexecuted code paths, truncated logs).

### 3.6 Verification

**Verification** evaluates one or more **Observations** against an explicit **Claim** predicate within a declared **Scope** and **Snapshot**.

* **Inputs**: Claim statement, target scope (files, modules, behavioral surface), target `snapshot_id`, observation records, evaluation predicate.
* **Output**: An epistemic state from the AIF State Model (`VERIFIED`, `UNKNOWN`, `NOT_OBSERVABLE`, `PARTIAL`, `STALE`, `MISMATCH`, `CONTRADICTED`).

### 3.7 Evidence

**Evidence** is the immutable, auditable binding that proves a verification result (`aif-evidence.schema.json`).

Every valid AIF Evidence record **must** bind six elements:
1. **Scope (`scope`)**: The exact files, components, or interfaces covered by the evidence.
2. **Snapshot (`snapshot_id` & `tree_hash`)**: The exact repository state at which the evidence was produced.
3. **Execution Context (`execution_id`)**: The admitted execution event that generated the underlying observation.
4. **Observation Reference (`observation_id`)**: The empirical observation(s) evaluated.
5. **Provenance (`provenance`)**: Verifier identity, timestamp, and content digest (`sha256`).
6. **Supported Claims (`supports_claims`)**: The claim IDs this evidence substantiates.

### 3.8 Acceptance

**Acceptance** evaluates the task's **Acceptance Criteria Contract** against the set of current Claims and their bound Evidence.

* Each **Acceptance Criterion** (`criterion_id`, `description`, `mandatory`, `required_scope`, `required_claims`) is evaluated:
  * A criterion is `ACCEPTED` if and only if all of its `required_claims` are in state `VERIFIED`, bound to the **final repository snapshot**, and their evidence scope covers the criterion's `required_scope`.
  * Otherwise, the criterion retains the limiting epistemic state (`PARTIAL`, `STALE`, `NOT_OBSERVABLE`, `MISMATCH`, `CONTRADICTED`, or `UNKNOWN`).

### 3.9 Completion

**Completion** is the terminal assurance verdict for the task (`aif-completion-manifest.schema.json`).

* A task may be declared `COMPLETE` **if and only if**:
  1. Every mandatory acceptance criterion has status `ACCEPTED` (backed by `VERIFIED` claims).
  2. Every supporting evidence record is bound to the final repository snapshot (`final_snapshot_id`), or its covered scope is provably disjoint from any subsequent change (`STALE` check).
  3. No mandatory claim or criterion is in state `UNKNOWN`, `NOT_OBSERVABLE`, `PARTIAL`, `STALE`, `MISMATCH`, or `CONTRADICTED`.
* If any mandatory criterion is not `ACCEPTED`, the task completion status **must** reflect the true status (`INCOMPLETE`, `PARTIAL_COMPLETION`, or `BLOCKED`) and surface the exact blocking epistemic states.

---

## 4. Canonical Arena Completion State Machine

To prevent the shortcut `agent says "done" → DONE`, AIF defines an explicit 7-stage completion state machine with deterministic failure branches at every gate:

```text
                    ┌──────────────┐
                    │    INTAKE    │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  AUTHORIZED  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   ADMITTED   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   EXECUTED   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   VERIFIED   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  EVIDENCED   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ COMPLETABLE  │
                    └──────────────┘
```

### 4.1 Failure Branches

```text
AUTHORIZED
    │
    ├── NO → BLOCKED
    │
    ▼
ADMITTED
    │
    ├── NO → REJECTED
    │
    ▼
EXECUTED
    │
    ├── NO → NOT_EXECUTED
    │
    ▼
VERIFIED
    │
    ├── NO → UNVERIFIED
    │
    ▼
EVIDENCED
    │
    ├── NO → EVIDENCE_INCOMPLETE
    │
    ▼
COMPLETABLE
```

### 4.2 Example: Formalizing `"CI passes"`

Under the AIF completion state machine, a claim such as `"CI passes"` requires five distinct evidence components:

```text
Claim: "CI passes"

Required evidence:
    CI workflow exists
    +
    CI execution occurred
    +
    execution identifies commit SHA
    +
    relevant job completed
    +
    exit/result is recorded

Therefore:
    CI_CONFIGURED ≠ CI_EXECUTED ≠ CI_PASSED ≠ RELEASE_VERIFIED
```
