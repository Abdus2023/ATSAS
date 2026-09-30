# AIF-0.1 Protocol Compatibility & Skill Contract (`compatibility.md`)

- **Protocol Family**: `AIF-0.1`
- **Concrete Frozen Version**: `0.1.0` ([`VERSION`](./VERSION))
- **Status**: `FROZEN AIF-0.1.0 KERNEL CONTRACT`

---

## 1. Protocol Family (`AIF-0.1`) vs Concrete Frozen Version (`0.1.0`)

To avoid unnecessary naming migrations across documentation and schemas, ATSAS distinguishes:

```text
AIF-0.1
  protocol family (human-readable specification & architecture family)

AIF-0.1.0 (VERSION = 0.1.0)
  concrete frozen semantic version
```

`.claude/skills/_shared/aif/VERSION` (and `.agent/skills/_shared/aif/VERSION`) contains the exact semantic version string:

```text
0.1.0
```

No `v` prefix, no date, and no git hash are embedded in `VERSION`; git commit and `SnapshotRef` supply repository provenance.

---

## 2. Semantic Versioning Rules

- **Patch (`0.1.x`)**: Clarifications, examples, or additional RED/pressure test cases in `tests/cases.yaml` that do not alter schema validation or invariant semantics.
- **Minor (`0.x.0`)**: Additive optional fields or new invariants that preserve backward compatibility with `0.1.0` receipts.
- **Major (`x.0.0`)**: Any breaking change to state tables (`states.md`), `SnapshotRef` (`snapshots.md`), `EvidenceRef` (`evidence.md`), `invariants.md`, or the 13 schemas in `schema/`.

---

## 3. Consumer Skill Contract

Any skill that consumes `AIF-0.1` must:
1. Reference `.claude/skills/_shared/aif/` (`VERSION = 0.1.0`) rather than redefining authority, execution, verification, observation, or completion states.
2. Produce and consume only objects conforming to the 13 JSON Schemas in [`schema/`](./schema/).
3. Respect the division of responsibilities in [`README.md`](./README.md):
   - `AIF`: defines
   - `Skills`: perform
   - `Evidence producers`: observe/report
   - `Completion gate`: evaluate
