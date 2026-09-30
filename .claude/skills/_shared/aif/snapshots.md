# AIF-0.1 Snapshot & Attribution Contract (`snapshots.md`)

- **Protocol Version**: `0.1.0` ([`VERSION`](./VERSION))
- **Governing Invariants**: `AIF-002`, `AIF-002A`, `AIF-003`, `AIF-003A`, `AIF-014`, `AIF-015`
- **Canonical Schema**: [`schema/snapshot-ref.schema.json`](./schema/snapshot-ref.schema.json)

---

## 1. `SnapshotRef` Contract

A commit hash identifies repository history; **it does not necessarily identify the complete working state**. During agent execution, `HEAD = abc123` frequently coexists with `working_tree_state = DIRTY` and `index_state = DIRTY`. An evidence receipt that records only `HEAD` is insufficient for working-tree claims.

```text
SnapshotRef {
    snapshot_id
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

| Field | Type | Semantics |
|---|---|---|
| `snapshot_id` | `string` | Unique identifier for this snapshot instance within a receipt bundle |
| `role` | `enum` (optional) | `comparison_base \| intake_snapshot \| execution_snapshot \| verification_snapshot \| current_snapshot` |
| `repository` | `string` | Repository identifier (e.g., `Abdus2023/ATSAS`) |
| `ref` | `string` | Symbolic git reference (e.g., `refs/heads/arena/01a0ecca-atsas`) |
| `commit` | `string` | 40-character hexadecimal Git `HEAD` commit SHA |
| `working_tree_state` | `CLEAN \| DIRTY` | Whether tracked/untracked working-tree files differ from `HEAD` |
| `index_state` | `CLEAN \| DIRTY` | Whether the git index (staging area) differs from `HEAD` |
| `captured_at` | `string (date-time)` | ISO-8601 UTC timestamp when the snapshot was captured |
| `content_digest` | `sha256:<hex>` | Digest over the working-tree content state (including dirty/untracked state) |
| `metadata_digest` | `sha256:<hex>` | Digest over path list, file modes, and git status metadata |

---

## 2. Five Snapshot Roles

| Role | Meaning |
|---|---|
| `comparison_base` | Baseline reference (`main` or merge-base) against which overall branch scope is compared |
| `intake_snapshot` (`S0`) | Exact working-tree and index state captured before agent execution begins |
| `execution_snapshot` (`S1`) | State against which a command or mutation was executed |
| `verification_snapshot` (`S2`) | Exact state bound to a `VerificationRecord` |
| `current_snapshot` | Present working-tree and index state at completion evaluation |

Two snapshots `S_a` and `S_b` represent the same workspace state if and only if:

$$\text{commit}(S_a) = \text{commit}(S_b) \land \text{working\_tree\_state}(S_a) = \text{working\_tree\_state}(S_b) \land \text{index\_state}(S_a) = \text{index\_state}(S_b) \land \text{content\_digest}(S_a) = \text{content\_digest}(S_b)$$

---

## 3. State Change (`DIFF(S0, S1)`) vs. Actor Attribution

`DIFF(S0, S1)` proves **state change** between two snapshots; it does **not** by itself prove **actor attribution** (`AIF-003A`). The inference:

```text
all changes after agent start = agent changes
```

is **prohibited**. Every `ChangeRecord` ([`schema/change-record.schema.json`](./schema/change-record.schema.json)) must classify each changed path using an explicit attribution value and `attribution_basis`:

| Attribution | Meaning |
|---|---|
| `PREEXISTING` | Path was already dirty or untracked in `intake_snapshot` (`S0`) with identical `after_digest` |
| `AGENT_ATTRIBUTED` | Change is linked to an explicit agent `ExecutionRecord` or write operation |
| `EXTERNAL_ATTRIBUTED` | Change was produced by an external process or user action outside agent execution |
| `GENERATED` | Path was emitted as a build/test artifact by an executed tool (`generated: true`) |
| `UNATTRIBUTED` | Path changed between `S0` and `S1`, but no execution record establishes the actor |
| `UNKNOWN` | Attribution cannot be determined because `intake_snapshot` (`S0`) was not captured |

---

## 4. Admission Scope Enforcement (`OUT_OF_SCOPE CHANGE`)

`AdmissionRecord` freezes `admitted_paths` and `excluded_paths` before execution begins. Any path in `DIFF(intake_snapshot, current_snapshot)` (or `AGENT_ATTRIBUTED` / `GENERATED`) that matches `excluded_paths` or falls outside `admitted_paths` is not merely `"a diff"` — it is classified as an `OUT_OF_SCOPE CHANGE` (`SCOPE_VIOLATION`), which transitions Completion to `BLOCKED`.
