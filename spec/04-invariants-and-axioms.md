# 04 — Arena Assurance Invariants (`AAI-001`..`AAI-010`), Canonical Vocabulary & AIF Axioms

> **Canonical Design Artifacts**: Synchronized with [`.claude/assurance/invariants.md`](../.claude/assurance/invariants.md) and [`.claude/assurance/state-model.md`](../.claude/assurance/state-model.md).

This specification defines the **Arena Assurance Invariants (`AAI-001` – `AAI-010`)** (`PHASE 0`), the **Four-Axis Canonical Evidence Vocabulary**, and the structural AIF manifest invariants (`AIF-INV-001` – `AIF-INV-008`) that govern **ATSAS (Arena Tools, Skills, Agentic System)** and **AIF (Agent Assurance Interface)**.

---

## 1. Foundational Boundary Axioms

1. **Skill-Evidence Separation**: *A skill is not evidence.*
2. **Tool-Verification Separation**: *A tool result is not automatically verification.*
3. **Execution-Completion Separation**: *Execution is not completion.*
4. **Evidence-Bound Completion**: *Completion is an evidence-backed claim.*
5. **No Evidence, No Verified Claim**: *No claim is verified without sufficient, scope-bounded, snapshot-bound evidence.*
6. **Mandatory Criterion Coverage**: *No task is complete without evidence satisfying every mandatory acceptance criterion.*
7. **Audit-Remediation Separation**: *An audit must not silently repair what it is auditing.*

---

## 2. Canonical Arena Assurance Invariants (`PHASE 0` — Executable Specification)

### `AAI-001` — Authority
```text
EXECUTED(action, actor)
    ⇒
AUTHORIZED(action, actor, request)
```
- **If false**: `UNAUTHORIZED_EXECUTION` (`AUTHORITY_MISSING` / `REJECTED`).
- **Mandatory behavior**: The system must record the execution in the ledger rather than pretending it never happened, and transition completion eligibility to `BLOCKED` / `REJECTED`.

### `AAI-002` — Scope
```text
EXECUTED_CHANGE(path)
    ⇒
path ∈ AUTHORIZED_SCOPE
```
- **Exception rule**: `generated(path)` does **not** automatically mean authorized. Generated artifacts (`dist/`, `build/`, coverage outputs) require their own explicit policy (`GENERATED`). Pre-existing dirty working-tree files (`PREEXISTING`) must be separated via before/after snapshots.
- **If false**: `OUT_OF_SCOPE` (`SCOPE_VIOLATION` → `REJECTED`).

### `AAI-003` — Snapshot Binding
```text
VERIFY(claim, snapshot=S1)
    ⇏
VERIFY(claim, snapshot=S2)    when S1 != S2
```
- **Hard invariant**: `VERIFY(claim, snapshot=S1)` proves the claim only for `S1`. It cannot transfer to `S2` (`EVIDENCE_STALE` / `EVIDENCE_MISMATCH` / `WRONG_HEAD`).

### `AAI-004` — Execution vs. Declaration
```text
DECLARED(command) ≠ EXECUTED(command)
```
- **Receipt structural requirement**: Receipts must separate `declared_command`, `executed_command`, and `execution_evidence` rather than collapsing them into a single `command` field.

### `AAI-005` — Result vs. Execution
```text
EXECUTED(command) ≠ PASSED(command)
```
- **Minimum predicate**: `exit_code == 0` must be directly observed for conventional process success (`PARTIALLY_EVIDENCED` if exit code is absent). Even `exit_code == 0` establishes only process completion for that command, not repository-wide correctness.

### `AAI-006` — Claim vs. Evidence
```text
CLAIM ≠ EVIDENCE
```
- An agent's final response or prose assertion is metadata about what the agent claims (`CLAIMED` / `CLAIM_ONLY`), never execution evidence (`OBSERVED`).

### `AAI-007` — Evidence Scope Containment
```text
EVIDENCE(X) ⇒ supports only claims within SCOPE(X)
```
- Every evidence artifact must answer six questions: **What claim? Which snapshot? Which command? Which environment? Which artifact? Which result?** Otherwise the receipt must narrow the claim (`TYPECHECK_VERIFIED`, `PARTIAL_EXECUTION`, `SCANNER_NO_MATCH`, `PARTIAL_COVERAGE`).

### `AAI-008` — Unknown Preservation
```text
NOT_OBSERVABLE ⇏ PASS
NOT_OBSERVABLE ⇏ FAIL
UNKNOWN        ⇏ PASS
UNKNOWN        ⇏ FAIL
```
- The evaluation outcome space must preserve at minimum `{ PASS, FAIL, UNKNOWN, NOT_APPLICABLE, NOT_OBSERVABLE }`. Never transform `NOT_OBSERVABLE` into `PASS` or `FAIL` without an explicit policy rule.

### `AAI-009` — Completion Sufficiency
```text
COMPLETABLE
    ⇒
∀ mandatory criterion:
    sufficient evidence exists
```
- Not *"most criteria passed"*, not *"agent says done"*, not *"user says just mark it complete"*, and not *"tests happened to pass while scope was violated"*.

### `AAI-010` — Mutation Boundary (`Audit ≠ Remediation`)
```text
AUDIT ≠ REMEDIATION
```
- An audit skill finding a defect must not silently fix or delete the defect to make its own audit pass (`P-002`).

### `AAI-011` — Verification Immutability
```text
VERIFIED(C, S2)
    ⇏
VERIFIED(C, S')    for any later mutable state S' ≠ S2 unless a new verification occurs at S'
```
- **Three-snapshot provenance model**:
  - `comparison_base` — comparison ancestor / branch base
  - `intake_snapshot` (`S0`) — observed repository state when the task began (`BASELINE`)
  - `execution_snapshot` (`S1`) — repository state after agent action (`AGENT_CHANGE = DIFF(S0, S1)`)
  - `verification_snapshot` (`S2`) — repository state when verification ran
  - `head_commit` (`HEAD`) — current commit
- For stable verification of agent changes, `S1 == S2 == head_commit` (and for read-only tasks, `S0 == S1 == S2`). If `S1 ≠ S2` or `S2 ≠ head_commit`, the receipt must classify the result as `VERIFICATION_STALE` (`STALE_EVIDENCE`) or `EVIDENCE_MISMATCH` (`WRONG_HEAD`).

---

## 3. Canonical Evidence Vocabulary (Four Orthogonal State Axes)

These four state axes must remain distinct and must never be collapsed into a single universal enum:

| Axis | Canonical Values |
|---|---|
| **Observation states** (`observation_state`) | `OBSERVED`, `DERIVED`, `INFERRED`, `CLAIMED`, `UNKNOWN`, `NOT_OBSERVABLE` |
| **Execution states** (`execution_state`) | `NOT_REQUESTED`, `AUTHORIZED`, `ADMITTED`, `STARTED`, `EXECUTED`, `EXECUTION_FAILED`, `CANCELLED` |
| **Verification states** (`verification_state`) | `NOT_VERIFIED`, `VERIFIED`, `STALE`, `MISMATCH`, `PARTIAL`, `UNVERIFIABLE` |
| **Completion states** (`completion_state`) | `COMPLETABLE`, `INCOMPLETE`, `BLOCKED`, `REJECTED`, `UNVERIFIED` |

---

## 4. Structural AIF Manifest Invariants (`bin/aif-verify`)

| Invariant ID | Maps to `AAI` | Rule Enforced by `bin/aif-verify` |
| :--- | :--- | :--- |
| `AIF-INV-001` | `AAI-006` | **Evidence-Backed Verification**: A `VERIFIED` claim must reference non-empty `evidence_ids`, and no reference may cite a skill (`skill-*`). |
| `AIF-INV-002` | `AAI-001`, `AAI-004` | **Admitted Execution Provenance**: Every evidence artifact must reference an `ADMITTED` execution record and its empirical observation. |
| `AIF-INV-003` | `AAI-003` | **Snapshot Binding & Freshness**: Every `VERIFIED` claim and supporting evidence artifact must match `final_snapshot_id` and its `tree_hash` (blocks `STALE_EVIDENCE` / `WRONG_HEAD`). |
| `AIF-INV-004` | `AAI-002`, `AAI-007` | **Scope Containment**: Supporting evidence scope must cover 100% of the claim's declared scope. |
| `AIF-INV-005` | `AAI-008` | **Observability Integrity**: Observations with `PARTIAL` or `NOT_OBSERVABLE` status cannot promote a claim to `VERIFIED`. |
| `AIF-INV-006` | `AAI-005` | **Non-Contradiction**: Observations with non-zero exit codes or `predicate_satisfied: false` cannot support a `VERIFIED` claim. |
| `AIF-INV-007` | `AAI-009` | **Mandatory Criterion Satisfaction**: Every mandatory acceptance criterion marked `ACCEPTED` must be backed by `VERIFIED` claims covering `required_scope`. |
| `AIF-INV-008` | `AAI-009` | **Completion Verdict Integrity**: Top-level completion status may be `COMPLETE` / `COMPLETABLE` only when all mandatory criteria are satisfied and zero upstream invariant violations exist. |
