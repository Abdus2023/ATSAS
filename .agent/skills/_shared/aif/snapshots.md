# AIF-0.1 Snapshot Semantics & Change Attribution Rules (`snapshots.md`)

> **Protocol Version**: `0.1`  
> **Core Rules**:  
> - Snapshot names are **roles**, not necessarily distinct git commits (`AIF-002`, `AIF-002A`).  
> - `DIFF(S0, S1)` proves **state change**, not **actor causality** (`AIF-003`, `AIF-003A`).

---

## 1. Five Canonical Snapshot Roles

```text
comparison_base
        │
        │ diff reference
        ▼
intake_snapshot
        │
        │ agent activity
        ▼
execution_snapshot
        │
        │ verification command
        ▼
verification_snapshot
        │
        │ current observation
        ▼
current_snapshot
```

### Roles Are Not Necessarily Commits

A repository can transition through working-tree states without creating a new git commit, or share the same snapshot across multiple roles:

```text
S0 = commit abc + dirty working tree
S1 = commit abc + modified working tree
S2 = commit def + clean working tree
```

produces:
```text
intake_snapshot       = S0
execution_snapshot    = S1
verification_snapshot = S2
current_snapshot      = S2
```

Therefore:
```text
HEAD = abc123, working_tree_state = DIRTY
  !=
HEAD = abc123, working_tree_state = CLEAN
```

Every `SnapshotRef` must record `commit`, `working_tree_state`, `index_state`, `content_digest`, and `metadata_digest`.

---

## 2. Crucial Distinction: State Change vs. Actor Attribution (`AIF-003`, `AIF-003A`)

Observing `DIFF(S0, S1)` establishes only:
> **The repository state changed.**

It does **not** establish:
> **The agent caused every observed change.**

### Required `ChangeRecord.attribution` Values
```text
PREEXISTING
AGENT_ATTRIBUTED
EXTERNAL_ATTRIBUTED
GENERATED
UNATTRIBUTED
UNKNOWN
```

### Prohibited Implementation Shortcut
```text
all changes after agent start = AGENT_ATTRIBUTED   (FORBIDDEN)
```
Assigning `attribution = AGENT_ATTRIBUTED` requires an explicit `attribution_basis` linking the modified path to an admitted agent action or `ExecutionRecord`. Without attribution evidence, a change observed in `DIFF(S0, S1)` must be classified as `UNATTRIBUTED` or `UNKNOWN`.
