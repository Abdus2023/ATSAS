---
name: arena-intake-and-authority
description: Evaluates whether a requested agent action has sufficiently established authority and whether the requested action, path, actor, and temporal scope can be admitted under AIF-0.1.0 (`AUTHORIZED != ADMITTED != EXECUTED`). Use at the start of any agent task, before any repository mutation or command execution, when a mid-task scope expansion is requested, or when auditing whether a request is `ADMITTED`, `INSPECT_ONLY`, `BLOCKED`, or `REJECTED`. Never confuse this governance intake gate with `authorization-boundary-scan` (which scans application source code and dependencies).
---

# Arena Intake and Authority (`C-01`)

```text
SCOPE: ARENA_GENERIC
AIF_VERSION: 0.1.0
COMPONENT_ID: C-01
MUTATES_REPOSITORY: false
```

Determine whether a requested agent action has sufficiently established authority and whether the requested scope can be admitted under [`.claude/skills/_shared/aif/`](../_shared/aif/README.md).

**This skill does NOT execute the task, modify the repository, verify the implementation, or declare completion.**

```text
AUTHORIZED ≠ ADMITTED ≠ EXECUTED
```

- **Authority** says an action may be performed (`AUTHORIZED(action, path, actor, time)`).
- **Admission** says the specific request has been accepted into the workflow with a frozen scope (`AdmissionRecord`).
- **Execution** says a process or mutation actually occurred (`ExecutionRecord`).

---

## 1. Phase 3 Contract Boundary

| Attribute | Rule |
|---|---|
| **Consumes** | `Request`, `AuthorityEvent[]`, `SnapshotRef` (`intake_snapshot` `S0`), applicable repository policy |
| **Produces** | `AdmissionRecord`, per-action `authority_matrix`, authority `Finding[]`, `clarifications[]` |
| **May inspect** | Repository metadata/instructions (`AGENTS.md`, `CLAUDE.md`, `README.md`, `package.json`, `.git/`) |
| **May mutate** | `NO` (`mutates_repository: false` — reports invalid files, never repairs them) |
| **May execute task** | `NO` |
| **May verify implementation** | `NO` |
| **May declare completion** | `NO` |
| **Governing Invariants** | `AIF-001`, `AIF-001A`, `AIF-002`, `AIF-003`, `AIF-008`, `AIF-010`, `AIF-021`, `AIF-022` |

---

## 2. Four-Dimensional Authority Lattice & 12-Action Vocabulary

Never emit a coarse boolean `authorized = true`. Evaluate authority across four dimensions:

$$\text{AUTHORIZED}(\text{action}, \text{path}, \text{actor}, \text{time})$$

over the 12-action vocabulary:
- **Inspection**: `READ`, `LIST`, `SEARCH`
- **Process / Side Effect**: `EXECUTE` (e.g., `run_tests`, `npm install`)
- **Repository Mutation**: `CREATE`, `MODIFY`, `DELETE`, `RENAME`, `GENERATE`
- **History & External Side Effects**: `COMMIT`, `PUSH`, `RELEASE`

### Non-Transitivity (`AIF-022`) & No Retroactive Authorization (`AIF-021`)
1. **Actor non-transitivity (`AIF-022`)**: Authority granted to `Agent A` never authorizes `Agent B`.
2. **Action non-transitivity (`AIF-022`)**:
   - `READ`/`LIST`/`SEARCH` never implies `MODIFY`/`CREATE`/`DELETE`/`RENAME`.
   - `MODIFY` never implies `COMMIT`, `PUSH`, or `RELEASE`.
   - `EXECUTE` (`run_tests`) never implies permission to modify `test/**` files unless `test/**` modification is explicitly authorized.
3. **No retroactive authorization (`AIF-021`)**: Authorization created at $T_2$ cannot retroactively authorize an action executed at $T_1 < T_2$.

---

## 3. Four Fundamental Intake Outcomes

| Outcome | Meaning | Canonical Trigger |
|---|---|---|
| `ADMITTED` | Required authority and path/action/actor/time scope are established | `"Update src/resolver.ts and run the resolver tests"` with matching `AuthorityEvent` |
| `INSPECT_ONLY` | Inspection (`READ`, `LIST`, `SEARCH`) is authorized; mutation is not | `"Investigate why CI fails"` with no mutation authority |
| `BLOCKED` | Prerequisite authority or scope is unresolved, vague, expired, or conflicting | `"Fix whatever is wrong"`, missing approval, `EXPIRED` (`AIF-001A`), `CONFLICTING` authority, or mid-task scope expansion without a new `AuthorityEvent` |
| `REJECTED` | Requested action or target path explicitly conflicts with authority or policy | Request to modify `package.json` when `path_scope` is `src/**` and `package.json` is excluded |

---

## 4. Workflow Steps

1. Capture or receive the `intake_snapshot` (`S0`) `SnapshotRef` before any task execution begins.
2. Run the deterministic intake evaluator:
   ```bash
   python3 .claude/skills/arena-intake-and-authority/scripts/evaluate_intake.py <intake-input.json>
   ```
   Or run the 13-case adversarial self-test suite (`RED-01`..`RED-04`, `A-01`..`A-07`, `AIF-021`, `AIF-022`):
   ```bash
   python3 .claude/skills/arena-intake-and-authority/scripts/evaluate_intake.py --self-test
   ```
3. Inspect the emitted `AdmissionRecord`:
   - If `admission_status == "BLOCKED"` or `"REJECTED"`, halt all mutation/execution and surface `blockers` and `clarifications`.
   - If `admission_status == "INSPECT_ONLY"`, restrict downstream operations strictly to `READ`, `LIST`, `SEARCH`.
   - If `admission_status == "ADMITTED"`, freeze `admitted_actions`, `admitted_paths`, `excluded_actions`, and `excluded_paths`. Any later need to touch an excluded path requires a `NEW REQUEST -> NEW AUTHORITY EVENT -> NEW ADMISSION`.

See [`references/authority-lattice-and-adversarial-tests.md`](./references/authority-lattice-and-adversarial-tests.md) for the complete lattice specification and adversarial test table.
