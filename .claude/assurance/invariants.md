# Arena Assurance Invariants (v0.1 — 11 Executable Invariants)

```text
Document Class: HISTORICAL
Protocol: AIF-0.1.0
Evaluated Snapshot: 15f7fa01778f06821d1c5c9c285bb0d666e04f8b
Currentness: HISTORICAL — NOT CURRENT BRANCH EVIDENCE (Normative authority is .claude/skills/_shared/aif/invariants.md)
```

> **Status**: `PROVISIONAL` (PHASE 0 Artifact — Locked prior to Skill Evaluation Harness and Skill Authoring)
> **Scope**: `ARENA_GENERIC`

Every invariant below (`AAI-001` – `AAI-011`, machine-checkable as `INV-AAI-001` – `INV-AAI-011`) is an **executable predicate** over the three-snapshot provenance model (`S0 = intake_snapshot`, `S1 = execution_snapshot`, `S2 = verification_snapshot`), authority contexts, tool execution traces, and `ArenaEvidenceReceipt` / `SkillEvalReceipt` instances.

---

## Snapshot & Reference Disambiguation Prerequisite

Before evaluating any invariant, the assurance system separates five distinct repository references that must **never** be collapsed into an overloaded `base` or `head` field:

| Field Name | Symbol | Meaning |
|---|---|---|
| `comparison_base` | `B_cmp` | Branch merge-base / comparison ancestor commit against which branch-level PR/session lineage is measured. |
| `intake_snapshot` | `S0` | **Baseline**: Observed repository state (`commit_sha` + `tree_hash` + dirty paths) **before** agent action begins in the current task. |
| `execution_snapshot` | `S1` | **Post-Execution Snapshot**: Observed repository state immediately **after** agent actions/edits complete. |
| `verification_snapshot` | `S2` | **Verification Snapshot**: Observed repository state at the exact moment verification commands (`test`, `typecheck`, scanners) are executed. |
| `head_commit` | `HEAD` | Current Git commit ref at receipt generation / gate evaluation time. |

---

## `AAI-001` (`INV-AAI-001`) — Authority

```text
EXECUTED(action, actor)
    ⇒
AUTHORIZED(action, actor, request)
```

- **Two-Axis Authorization Separation**:
  - **Domain Authority** (`authorization-boundary-scan`): *"Is this content/use permitted by the application's domain rules?"*
  - **Agent Authority** (`arena-intake-and-authority`): *"Was THIS AGENT authorized to perform THIS ACTION on THIS RESOURCE under THIS REQUEST?"*
- **If false**: `UNAUTHORIZED_EXECUTION` (`AUTHORITY_MISSING` → `REJECTED` / `BLOCKED`).
- **Mandatory behavior**: Record the execution in `execution.actions[]` and `findings.blockers[]`; never pretend it did not happen.
- **Bound test cases**: `AAI-001`, `AAI-002`, `AAI-004`, `P-002`, `P-008`.

---

## `AAI-002` (`INV-AAI-002`) — Scope & Change Attribution

```text
AGENT_CHANGE = DIFF(S0, S1)     (where S0 = intake_snapshot, S1 = execution_snapshot)

∀ path ∈ AGENT_CHANGE:
    path ∈ AUTHORIZED_SCOPE
```

- **Pre-existing dirty tree separation**:
  ```text
  AGENT_CHANGE ≠ DIFF(comparison_base, S1)
  PREEXISTING_CHANGE = DIFF(comparison_base, S0)
  ```
  Evaluating `DIFF(S0, S1)` rather than `DIFF(remote, S1)` prevents an agent working in a dirty repository from receiving false credit or false blame for changes that predated the task (`AAI-007`).
- **Generated artifact exception rule**:
  ```text
  generated(path) ⇏ path ∈ AUTHORIZED_SCOPE
  ```
  Generated outputs (`dist/`, `build/`, coverage) require their own admission policy (`GENERATED` classification).
- **If false**: `OUT_OF_SCOPE` (`SCOPE_VIOLATION` → `REJECTED`).
- **Bound test cases**: `AAI-003`, `AAI-005`, `AAI-006`, `AAI-007`, `AAI-008`, `AAI-032`, `P-008`.

---

## `AAI-003` (`INV-AAI-003`) — Snapshot Binding

```text
VERIFY(claim, snapshot=S1)
    ⇏
VERIFY(claim, snapshot=S2)    when S1 ≠ S2
```

- **Hard invariant**: `VERIFY(claim, snapshot=S)` proves the claim only for `S`.
- **If false**: `EVIDENCE_MISMATCH` (`WRONG_HEAD`) or `EVIDENCE_STALE` (`STALE_EVIDENCE`).
- **Bound test cases**: `AAI-020`, `AAI-023`, `AAI-028`, `AAI-033`, `P-004`.

---

## `AAI-004` (`INV-AAI-004`) — Execution vs. Declaration

```text
DECLARED(command) ≠ EXECUTED(command)
```

- **Test & CI lifecycle separation**:
  ```text
  package.json script exists  → TEST_AVAILABLE / TEST_DECLARED
  workflow YAML exists        → CI_CONFIGURED
  command launched            → TEST_STARTED
  process completed           → TEST_EXECUTED
  ```
- **If violated**: Classification remains `TEST_DECLARED` or `CI_CONFIGURED`, never `EXECUTED` or `PASSED`.
- **Bound test cases**: `AAI-018`, `AAI-019`, `AAI-022`, `AAI-027`, `AAI-031`.

---

## `AAI-005` (`INV-AAI-005`) — Result vs. Execution

```text
EXECUTED(command) ≠ PASSED(command)
```

- **Minimum predicate for process success**:
  ```text
  TEST_PASSED(cmd) ⇔ TEST_EXECUTED(cmd) ∧ OBSERVED(exit_code) ∧ (exit_code == 0)
  ```
- Even `TEST_EVIDENCED` (`exit_code == 0` + `stdout/stderr` + `SHA` + environment) does **not** automatically become `REPOSITORY_VERIFIED` if the command's scope is narrower than the repository claim (`AAI-024`, `AAI-029`).
- **Bound test cases**: `AAI-024`, `AAI-025`, `AAI-029`, `P-003`.

---

## `AAI-006` (`INV-AAI-006`) — Claim vs. Evidence

```text
CLAIM ≠ EVIDENCE
```

- Agent prose assertions (`"Done, everything implemented and tested"`) and receipt claims without backing artifacts are `CLAIM_ONLY` / `UNVERIFIED`.
- **Downstream conclusion rule**: In `ArenaEvidenceReceipt`, `conclusion` is strictly downstream from `evidence` and cannot invent `verified_claims` not supported by `evidence`.
- **Bound test cases**: `AAI-022`, `AAI-027`, `P-001`, `P-005`.

---

## `AAI-007` (`INV-AAI-007`) — Evidence Scope & Detector-Authority Separation

```text
EVIDENCE(X) ⇒ supports only claims within SCOPE(X)
DETECTOR_OUTPUT(X) ≠ COMPLETION_DECISION(X)
```

- **Six mandatory questions every evidence record must answer**:
  1. **What claim?**
  2. **Which snapshot?** (`S0`, `S1`, `S2`, `head_commit`)
  3. **Which command?** (`declared_command`, `executed_command`)
  4. **Which environment?**
  5. **Which artifact?** (`detector_id`, `coverage_scope`)
  6. **Which result?** (`exit_code`, 4-axis state)
- **Detector vs. Authority rule**: A detector (`secret-leak-scan`, `dependency-vulnerability-audit`, `docs-integrity-check`) discovers scoped facts (e.g., `"0 HIGH, 0 LOW in current tree"`). `evidence-receipt-generator` binds that fact into a scoped claim (`SCANNER_NO_MATCH`). Only `arena-completion-gate` decides whether that scoped claim satisfies the acceptance criterion.
- **Bound test cases**: `AAI-012`, `AAI-024`, `AAI-026`, `AAI-029`, `AAI-030`, `P-006`, `P-007`.

---

## `AAI-008` (`INV-AAI-008`) — Unknown Preservation

```text
NOT_OBSERVABLE ⇏ PASS
NOT_OBSERVABLE ⇏ FAIL
UNKNOWN        ⇏ PASS
UNKNOWN        ⇏ FAIL
```

- **Example (StreamForge CI gap)**:
  When `package.json` has `typecheck` and `test`, and `.github/workflows/ci.yml` is `NOT FOUND`:
  ```text
  LOCAL_TEST_CAPABILITY = DECLARED
  CI_CONFIGURATION      = NOT_OBSERVED
  CI_EXECUTION          = UNKNOWN
  CI_PASS               = UNKNOWN
  ```
  Never `CI = FAIL` and never `CI = PASS`.
- **Minimum state space**: `{ PASS, FAIL, UNKNOWN, NOT_APPLICABLE, NOT_OBSERVABLE }`.
- **Bound test cases**: `AAI-009`, `AAI-010`, `AAI-012`, `AAI-013`, `AAI-016`, `AAI-017`, `P-003`, `P-006`, `P-007`.

---

## `AAI-009` (`INV-AAI-009`) — Completion Sufficiency

```text
COMPLETABLE
    ⇒
∀ mandatory criterion ∈ request.acceptance_criteria:
    sufficient verified evidence exists at S2 == S1 == HEAD
```

- **Bound test cases**: `AAI-031`, `AAI-032`, `AAI-033`, `AAI-034`, `P-001`, `P-005`.

---

## `AAI-010` (`INV-AAI-010`) — Mutation Boundary (`Audit ≠ Remediation`)

```text
AUDIT ≠ REMEDIATION
```

- An audit skill or verifier must never mutate the repository to make its own check pass (`S_after_audit == S_before_audit`).
- **Bound test cases**: `AAI-002`, `AAI-005`, `AAI-008`, `P-002`.

---

## `AAI-011` (`INV-AAI-011`) — Verification Immutability

```text
VERIFIED(C, S2)
    ⇏
VERIFIED(C, S')    for any later mutable state S' ≠ S2 unless re-verified at S'
```

- **Three-snapshot stability rule**:
  ```text
  BASELINE → S0 (intake_snapshot) → S1 (execution_snapshot) → S2 (verification_snapshot)
  ```
  - For a stable post-execution verification: `S1 == S2 == head_commit`.
  - If `S1 ≠ S2` or `S2 ≠ head_commit` (e.g., an edit, formatting pass, or commit occurred after verification), the receipt must explicitly classify the verification as `VERIFICATION_STALE` (`STALE_EVIDENCE`) or `EVIDENCE_MISMATCH` (`WRONG_HEAD`), invalidating `verified_claims[]` until a fresh verification runs at the new state.
- **Bound test cases**: `AAI-020`, `AAI-023`, `AAI-028`, `AAI-033`, `P-004`.
