---
name: agent-change-scope-audit
description: Audit repository state transitions between intake_snapshot (S0) and execution_snapshot (S1) against an AdmissionRecord and ExecutionRecord[], distinguishing STATE_CHANGE from AGENT_ATTRIBUTED provenance and AUTHORIZED scope without mutating the repository. Use when verifying which paths changed, whether changes are in admitted scope, and whether changes are PREEXISTING, AGENT_ATTRIBUTED, EXTERNAL_ATTRIBUTED, GENERATED, UNATTRIBUTED, or UNKNOWN (SCOPE: ARENA_GENERIC).
---

# Agent Change Scope Audit (`agent-change-scope-audit` — Component `C-02`)

```text
SCOPE: ARENA_GENERIC
AIF_VERSION: 0.1.0
COMPONENT_ID: C-02
MUTATES_REPOSITORY: false
```

- **Protocol Binding**: `AIF-0.1.0` ([`../_shared/aif/VERSION`](../_shared/aif/VERSION))
- **Contract ID**: `C-02` ([`../../assurance/component-contracts.md`](../../assurance/component-contracts.md))
- **Mutation Policy**: `mutates_repository: false` (strictly read-only; never reverts, checks out, or repairs out-of-scope files)

---

## 1. Purpose & Position in AIF

`agent-change-scope-audit` answers four distinct questions after `arena-intake-and-authority` (`C-01`) has frozen an `AdmissionRecord`:

1. **Did the repository state change?** (`STATE_CHANGE = DIFF(S0, S1)`)
2. **Which paths changed?**
3. **Were those paths within admitted scope?** (`IN_SCOPE`, `OUT_OF_SCOPE`, `UNKNOWN`)
4. **Can the changes be attributed to the agent with sufficient evidence?** (`PREEXISTING`, `AGENT_ATTRIBUTED`, `EXTERNAL_ATTRIBUTED`, `GENERATED`, `UNATTRIBUTED`, `UNKNOWN`)

It deliberately does **not** answer `"Was the implementation correct?"` (verification), does **not** remediate out-of-scope edits (`git checkout` is forbidden by `AIF-010`), and does **not** declare task completion (`C-07`).

### The Core Tripartite Distinction

```text
STATE CHANGE  ≠  AGENT CHANGE  ≠  AUTHORIZED CHANGE
```

And the formal unauthorized-change rule:

```text
UNAUTHORIZED_AGENT_CHANGE  ⇔  AGENT_ATTRIBUTED_CHANGE  ∧  ¬ IN_AUTHORIZED_SCOPE
```

Never simplify `STATE_CHANGE ∧ ¬ IN_SCOPE` into an agent violation without attribution evidence (`AIF-023`, `AIF-024`).

---

## 2. Input / Output Boundary

### Inputs
- `intake_snapshot` (`S0`): `SnapshotRef` captured prior to task execution.
- `execution_snapshot` (`S1`): `SnapshotRef` captured after task execution.
- `current_snapshot` (`S2`, optional): Current repository `SnapshotRef` used to detect `STALE` snapshot mismatch (`AIF-025`, `RED-41`).
- `admission_record`: Frozen `AdmissionRecord` from `arena-intake-and-authority` (`admitted_paths`, `excluded_paths`, `admitted_actions`).
- `repository_state`: Per-path digests and working-tree states at `S0` and `S1`.
- `execution_records`: Available `ExecutionRecord[]` (and optional external event records) establishing actor causality.

### Outputs
- `change_records`: `ChangeRecord[]` conforming to [`../_shared/aif/schema/change-record.schema.json`](../_shared/aif/schema/change-record.schema.json).
- `findings`: `Finding[]` (`OUT_OF_SCOPE_AGENT_CHANGE`, `OUT_OF_SCOPE_PREEXISTING_CHANGE`, `OUT_OF_SCOPE_CHANGE`, `STALE_SCOPE_AUDIT`, etc.).
- `evidence`: `EvidenceRef[]` (`E-SCOPE-001` for `S0`, `E-SCOPE-002` for `S1`, referenced in `ChangeRecord.attribution_basis`).
- `result`: Summary counts (`changed_paths`, `in_scope`, `out_of_scope`, `generated`, `attribution_unknown`, `comparison: "S0 -> S1"`).
- `verification`: `{ "scope_claim": { "status": "VERIFIED" | "PARTIAL" | "VIOLATED" | "STALE" } }`.

---

## 3. Four-Dimensional Change Model

Every emitted `ChangeRecord` carries four orthogonal dimensions:

```text
CHANGE
├── state:        CHANGED | UNCHANGED (ADDED | MODIFIED | DELETED | RENAMED | GENERATED | UNCHANGED)
├── scope:        IN_SCOPE | OUT_OF_SCOPE | UNKNOWN
├── attribution:  PREEXISTING | AGENT_ATTRIBUTED | EXTERNAL_ATTRIBUTED | GENERATED | UNATTRIBUTED | UNKNOWN
└── authority:    AUTHORIZED | UNAUTHORIZED | UNKNOWN
```

### Canonical 4-Path Example

Given `admitted_paths: ["src/**", "test/**"]`:

| Path | Change | Scope | Attribution | Authority | Finding |
|---|---|---|---|---|---|
| `src/a.ts` | `MODIFIED` | `IN_SCOPE` | `AGENT_ATTRIBUTED` | `AUTHORIZED` | none |
| `test/a.test.ts` | `MODIFIED` | `IN_SCOPE` | `AGENT_ATTRIBUTED` | `AUTHORIZED` | none |
| `README.md` | `MODIFIED` (at `S0`, unchanged `S0->S1`) | `OUT_OF_SCOPE` | `PREEXISTING` | `AUTHORIZED` (not an agent violation) | `OUT_OF_SCOPE_PREEXISTING_CHANGE` |
| `dist/a.js` | `GENERATED` (by build command) | `UNKNOWN` | `GENERATED` | `AUTHORIZED` (derived) | none |

---

## 4. Normative Invariants Enforced (`AIF-003`, `AIF-010`, `AIF-023`, `AIF-024`, `AIF-025`)

- **`AIF-023` — Attribution Is Evidence-Dependent**: `AGENT_ATTRIBUTED(change)` requires explicit `attribution_basis` (e.g., `["EXECUTION_RECORD:E-EXEC-004", "GIT_OBJECT:E-SCOPE-002"]`). `DIFF(S0, S1)` alone establishes `STATE_CHANGE`, never `AGENT_ATTRIBUTED_CHANGE`.
- **`AIF-024` — Pre-Existing State Must Not Become Agent Responsibility**: A file already dirty at `S0` and unchanged during `S0 -> S1` must be classified as `PREEXISTING`, never `AGENT_ATTRIBUTED`. If a dirty file at `S0` is modified again by `S1` without execution evidence distinguishing agent vs. external edits, attribution must be `UNKNOWN`.
- **`AIF-025` — Scope Audit Is Snapshot-Relative**: Every scope audit is bound to `comparison: "S0 -> S1"`. If the repository advances to `S2 != S1`, the `S0 -> S1` audit is `STALE` and cannot verify `S2`.
- **`AIF-010` — Audit Must Not Repair**: Discovering an `OUT_OF_SCOPE_AGENT_CHANGE` (e.g., on `README.md`) must produce a `Finding` and stop; running `git checkout README.md` to erase evidence is strictly forbidden.

---

## 5. Deterministic Execution

Run the bundled zero-mutation scope & provenance auditor:

```bash
# Run the 12-case adversarial self-test suite (RED-05..08, RED-37..41, Section 8/10/16)
python3 .claude/skills/agent-change-scope-audit/scripts/audit_change_scope.py --self-test

# Evaluate a JSON scope audit payload
python3 .claude/skills/agent-change-scope-audit/scripts/audit_change_scope.py path/to/scope-audit-input.json
```

See [`references/provenance-and-scope-audit-model.md`](references/provenance-and-scope-audit-model.md) for the complete attribution decision table and adversarial test specifications.
