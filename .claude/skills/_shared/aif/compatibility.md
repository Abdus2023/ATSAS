# AIF-0.1 Protocol Compatibility & Authority Hierarchy (`compatibility.md`)

- **Document Class**: `NORMATIVE`
- **Protocol Family**: `AIF-0.1`
- **Concrete Frozen Version**: `0.1.0` ([`VERSION`](./VERSION))
- **Status**: `FROZEN AIF-0.1.0 KERNEL CONTRACT`

---

## 1. Canonical Authority Hierarchy & Document Classes

```text
AIF-0.1.0 (NORMATIVE: VERSION, schema/, invariants.md, states.md, snapshots.md, evidence.md, compatibility.md)
   │
   ▼
Test Oracle (EXECUTABLE-CONFORMANCE: tests/oracle.md)
   │
   ▼
Corpus (EXECUTABLE-CONFORMANCE: tests/cases.yaml)
   │
   ▼
Executable Validators (EXECUTABLE-CONFORMANCE: bin/aif-verify, tests/aif-v01-red-suite.py, tests/run-tests.sh)
   │
   ▼
Skills (CONSUMERS: .claude/skills/*)
   │
   ▼
Assurance / Reports (HISTORICAL / EVIDENCE: .claude/assurance/*, receipts, audit reports)
```

- **A report can provide evidence about the specification; it cannot redefine the specification.**
- **A test can demonstrate an invariant; it cannot silently create a new invariant.**
- **A skill can consume AIF semantics; it cannot define competing semantics.**

Every AIF-related artifact belongs to exactly one class:
1. **`NORMATIVE`**: Defines what AIF means (`VERSION`, `schema/`, `invariants.md`, `states.md`, `snapshots.md`, `evidence.md`, `compatibility.md`).
2. **`EXECUTABLE-CONFORMANCE`**: Tests whether an artifact or skill conforms to the normative definition (`bin/aif-verify`, `tests/aif-v01-red-suite.py`, `tests/cases.yaml`, `tests/oracle.md`, `tests/run-tests.sh`, skill self-tests).
3. **`HISTORICAL / EVIDENCE`**: Records what happened at a specific repository snapshot (`.claude/assurance/phase12-interface-freeze-audit.md`, `.claude/assurance/aif-v01-freeze-review.md`, execution reports, receipts).

---

## 2. Protocol Family (`AIF-0.1`) vs Concrete Frozen Version (`0.1.0`)

```text
AIF-0.1
  protocol family (human-readable specification & architecture family)

AIF-0.1.0 (VERSION = 0.1.0)
  concrete frozen semantic version
```

`.claude/skills/_shared/aif/VERSION` contains the exact semantic version string `0.1.0`. No `v` prefix, no date, and no git hash are embedded in `VERSION`; git commit and `SnapshotRef` supply repository provenance.

---

## 3. Development Evolution vs Frozen-Version Migration

`development evolution ≠ frozen-version migration`:

- **Before Freeze (`Draft AIF-0.1.0`)**: Invariant refinement, additional invariants (`AIF-001..AIF-055`), schema refinement, and corpus expansion (`49` cases) occur during development prior to freezing `AIF-0.1.0`.
- **Once Frozen (`AIF-0.1.0`)**:
  - **Patch (`0.1.x`)**: Clarification or example that does not alter schema validation or invariant semantics.
  - **Minor (`0.2.0`)**: Compatible additive contract (e.g., incorporating `PROPOSED` invariants or optional fields).
  - **Major (`1.0.0`)**: Incompatible semantic or schema change.

---

## 4. Consumer Skill Contract

Any skill that consumes `AIF-0.1` (`0.1.0`) must:
1. Reference `.claude/skills/_shared/aif/` (`VERSION = 0.1.0`) rather than redefining authority, execution, verification, observation, or completion states.
2. Produce and consume only objects conforming to the 13 JSON Schemas in [`schema/`](./schema/).
3. Respect the division of responsibilities in [`README.md`](./README.md):
   - `AIF`: defines
   - `Skills`: perform
   - `Evidence producers`: observe/report
   - `Completion gate`: evaluate

