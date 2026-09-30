# Arena Invariant Framework (`AIF-0.1`) — Shared Semantic Kernel

**AIF defines the semantics and evidence boundaries used by repository-governed agent workflows; it does not authorize agents, execute commands, modify repositories, or declare work complete by itself.**

---

## 1. Division of Responsibilities

```text
AIF:
  defines

Skills:
  perform

Evidence producers:
  observe/report

Completion gate:
  evaluate
```

- **AIF** defines the formal vocabulary, state dimensions, snapshot contracts, claim/evidence bounds, and completion invariants. It contains no runtime execution framework and never mutates a repository.
- **Skills** perform scoped tasks as consumers of `AIF-0.1`. Skills do not invent private definitions of authority, evidence, verification, or completion.
- **Evidence producers** (commands, scanners, git object inspectors, CI probes) observe repository or process state and report structured `EvidenceRef` and `Finding` records bound to an explicit `SnapshotRef`.
- **Completion gate** evaluates a declarative `AcceptanceExpression` against `VerificationRecord`s, `Finding`s, and `AdmissionRecord`s to emit a deterministic, reproducible `CompletionResult` and immutable `ArenaEvidenceReceipt`.

---

## 2. Minimal `AIF-0.1` Kernel Layout

```text
.claude/skills/_shared/aif/
├── VERSION                                    # 0.1.0
├── README.md                                  # Kernel boundary & division of responsibilities
├── invariants.md                              # 55 primary invariants (AIF-001 .. AIF-055) + 8 sub-invariants (63 rules)
├── states.md                                  # Orthogonal state dimensions (Authority, Admission, Execution, Evidence, Verification, Completion)
├── snapshots.md                               # 5-snapshot contract (comparison_base, intake, execution, verification, current) & dirty-tree attribution
├── evidence.md                                # EvidenceRef, narrow Claim, AcceptanceExpression & Receipt immutability
├── compatibility.md                           # SemVer rules & skill compatibility contract
│
├── producers/                                 # 10 declarative EvidenceProducerOutput adapter contracts + README.md
│
├── schema/                                    # 13 modular Draft 2020-12 JSON Schemas (encoding the 14 core Semantic Kernel types;
│   │                                          #   common.schema.json defines $defs/EvidenceCoverage & $defs/Finding + 12 type schemas)
│   ├── common.schema.json
│   ├── request.schema.json
│   ├── authority-event.schema.json
│   ├── admission-record.schema.json
│   ├── snapshot-ref.schema.json
│   ├── execution-record.schema.json
│   ├── change-record.schema.json
│   ├── claim.schema.json
│   ├── evidence-ref.schema.json
│   ├── verification-record.schema.json
│   ├── acceptance-expression.schema.json
│   ├── completion-result.schema.json
│   └── evidence-receipt.schema.json
│
└── tests/                                     # 49-case (41 RED + 8 PRESSURE) behavioral specification & deterministic test oracle
    ├── cases.yaml
    ├── oracle.md
    └── README.md
```

---

## 3. Admission & Reality-Preserving Authority Boundary

The state transition for repository-governed work is:

```text
REQUEST
   │
   ▼
AUTHORITY EVALUATION
   │
   ▼
ADMISSION
   │
   ▼
EXECUTION
```

Never:

```text
REQUEST -> EXECUTION -> "we were authorized because it worked"
```

Because unauthorized execution can occur in reality, `AIF-0.1` records reality without rewriting history:

$$\text{EXECUTED}(\text{action}) \land \text{NOT\_AUTHORIZED}(\text{action}) \implies \text{AUTHORITY\_VIOLATION}$$

`EXECUTED(action)` alone never establishes `AUTHORIZED(action)`.

---

## 4. First RED Gate

Before any assurance skill is implemented, the `AIF-0.1` kernel rejects the canonical unsafe workflow:

```text
Request:
    "Fix whatever is wrong."

Agent:
    modifies README
    modifies package.json
    modifies src/

Agent:
    "Done."
```

**Required `AIF-0.1` Interpretation**:
- **Authority**: `UNKNOWN` (insufficiently specified)
- **Admission**: `BLOCKED`
- **Changes**: `UNAUTHORIZED` / `UNATTRIBUTED` (`OUT_OF_SCOPE CHANGE`)
- **Verification**: `NOT_VERIFIED`
- **Completion**: `BLOCKED` or `INCOMPLETE` (never `COMPLETABLE` merely because the agent claims `"Done."`)
