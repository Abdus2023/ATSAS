# Arena Assurance Interface v0.1 — Semantic Kernel Layout, Ownership & Versioning Freeze Specification

```text
Document Class: HISTORICAL
Protocol: AIF-0.1.0
Evaluated Snapshot: 15f7fa01778f06821d1c5c9c285bb0d666e04f8b
Currentness: HISTORICAL — NOT CURRENT BRANCH EVIDENCE (Normative authority is .claude/skills/_shared/aif/)
```

> **Status**: `_shared/aif` Layout `FREEZE CANDIDATE` · Phase 0/1 `AIF-0.1` Contract & RED Suite `IMPLEMENTED & VERIFIED` · Wave-1 `SKILL.md` Authoring `NOT STARTED`  
> **Scope**: `ARENA_GENERIC`  
> **Companion Artifacts**: [`.claude/skills/_shared/aif/README.md`](../skills/_shared/aif/README.md), [`.claude/assurance/canonical-data-model.md`](./canonical-data-model.md), [`.claude/assurance/component-contracts.md`](./component-contracts.md), [`tests/aif-v01-red-suite.py`](../../tests/aif-v01-red-suite.py)

---

## 1. Key Architectural Decision

> **Do not make the semantic kernel a skill. Make it a versioned protocol/contract consumed by skills.**

AIF defines the vocabulary, schemas, state machines, evidence rules, and invariants; individual skills provide observations, execution records, findings, and verification evidence.

---

## 2. Canonical Repository Layout (`.claude/skills/_shared/aif/`)

```text
.claude/
└── skills/
    ├── _shared/
    │   └── aif/
    │       ├── README.md
    │       ├── schema/
    │       │   ├── snapshot.schema.json
    │       │   ├── authority-event.schema.json
    │       │   ├── request.schema.json
    │       │   ├── admission.schema.json
    │       │   ├── execution-record.schema.json
    │       │   ├── change-record.schema.json
    │       │   ├── claim.schema.json
    │       │   ├── evidence-ref.schema.json
    │       │   ├── evidence-coverage.schema.json
    │       │   ├── verification-record.schema.json
    │       │   ├── finding.schema.json
    │       │   ├── acceptance-expression.schema.json
    │       │   └── completion-result.schema.json
    │       │
    │       ├── invariants.md
    │       ├── states.md
    │       ├── evidence-rules.md
    │       ├── compatibility.md
    │       └── VERSION
    │
    ├── <14 existing skills>/
    └── <8 Wave-1 assurance skills (to be authored after Phase 0/1)>:
        ├── arena-intake-and-authority/
        ├── agent-change-scope-audit/
        ├── dependency-supply-chain-audit/
        ├── ci-workflow-audit/
        ├── test-execution-and-evidence-audit/
        ├── evidence-receipt-generator/
        ├── arena-completion-gate/
        └── skill-evaluation-harness/
```

### Why `.claude/skills/_shared/aif/` Is Preferable to a `skills/aif/` Skill

- **A skill** means: *"When this task/context occurs, perform this procedure."*
- **A protocol** means: *"These are the semantics that all participating procedures must obey."*
- If `skills/aif/` were an ordinary skill, an agent could invoke it selectively or interpret it differently across skills, causing semantic drift (`Skill A` vs. `Skill B` vs. `Completion Gate`).
- Instead, `.claude/skills/_shared/aif/` is a **non-executable protocol dependency of the skills** (`validate_skill.py --all .claude/skills` explicitly ignores `_`-prefixed shared dependency directories while `tests/aif-v01-red-suite.py` validates every schema and invariant in `_shared/aif/`).

---

## 3. Three Separated Authorities

```text
SEMANTIC AUTHORITY
        │
        │ defines what terms mean
        ▼
     AIF CORE (.claude/skills/_shared/aif/)
        │
        │ consumed by
        ▼
PROCEDURAL AUTHORITY
        │
        │ defines how a skill performs its task
        ▼
      SKILLS (.claude/skills/<skill-name>/)
        │
        │ produces evidence
        ▼
DECISION AUTHORITY
        │
        │ evaluates acceptance expression
        ▼
 COMPLETION GATE (arena-completion-gate)
```

- `arena-completion-gate` does **not** define what `VERIFIED` means — it consumes the AIF definition of `VERIFIED`.
- `ci-workflow-audit` does **not** define what evidence is — it produces CI evidence according to AIF.

---

## 4. Critical Dependency Rule

> **Skills may depend on AIF semantics. AIF must not depend on skills.**

```text
            AIF (.claude/skills/_shared/aif/)
          /   |   \
         /    |    \
        ▼     ▼     ▼
     Intake  CI   Tests
       │      │      │
       └──────┼──────┘
              ▼
          Evidence
              │
              ▼
        Completion Gate
```

---

## 5. Two-Layer Protocol Split: `AIF-CORE` and `AIF-PROFILES`

### `AIF-CORE` (Answers: *"What does `VERIFIED` mean?"*)
- `identity` (`request_id`, `actor`, `repository`, `snapshot`)
- `snapshots` (`SnapshotRef`)
- `authority` (`AuthorityEvent`)
- `admission` (`AdmissionRecord`)
- `execution` (`ExecutionRecord`)
- `changes` (`ChangeRecord`)
- `claims` (`Claim`)
- `evidence` (`EvidenceRef`, `EvidenceCoverage`)
- `verification` (`VerificationRecord`)
- `acceptance` (`AcceptanceExpression`)
- `completion` (`CompletionResult`, `ArenaEvidenceReceipt`)

### `AIF-PROFILES` (Answers: *"What evidence is sufficient to verify this particular class of claim?"*)
- `repository-change`
- `security-audit`
- `CI-verification`
- `test-verification`
- `dependency-assurance`
- `skill-evaluation`

---

## 6. Mechanical Skill Contract Declarations (`C-01` – `C-08`)

Every Wave-1 skill declares its `aif` contract (`version`, `consumes`, `produces`, `mutates_repository`) so the skill graph is mechanically inspectable:

| Contract ID | Skill | `aif.version` | `aif.consumes` | `aif.produces` | `aif.mutates_repository` |
|---|---|---|---|---|---|
| `C-01` | `arena-intake-and-authority` | `"0.1"` | `SnapshotRef` | `Request`, `AuthorityEvent`, `AdmissionRecord`, `AcceptanceExpression` | `false` |
| `C-02` | `agent-change-scope-audit` | `"0.1"` | `AdmissionRecord`, `SnapshotRef`, `ExecutionRecord` | `SnapshotRef`, `ChangeRecord`, `Finding`, `EvidenceRef` | `false` |
| `C-03` | `dependency-supply-chain-audit` | `"0.1"` | `SnapshotRef`, `Request` | `Finding`, `EvidenceRef` | `false` |
| `C-04` | `ci-workflow-audit` | `"0.1"` | `SnapshotRef`, `Request` | `ExecutionRecord`, `Finding`, `EvidenceRef`, `VerificationRecord` | `false` |
| `C-05` | `test-execution-and-evidence-audit` | `"0.1"` | `SnapshotRef`, `Request`, `Claim` | `ExecutionRecord`, `EvidenceRef`, `VerificationRecord` | `false` |
| `C-06` | `evidence-receipt-generator` | `"0.1"` | `Request`, `AdmissionRecord`, `SnapshotRef`, `AuthorityEvent`, `ExecutionRecord`, `ChangeRecord`, `Claim`, `EvidenceRef`, `VerificationRecord`, `Finding`, `AcceptanceExpression` | `EvidenceCoverage`, `ArenaEvidenceReceipt` | `false` |
| `C-07` | `arena-completion-gate` | `"0.1"` | `Request`, `AdmissionRecord`, `ChangeRecord`, `Claim`, `EvidenceRef`, `EvidenceCoverage`, `VerificationRecord`, `AcceptanceExpression`, `ArenaEvidenceReceipt` | `CompletionResult` | `false` |
| `C-08` | `skill-evaluation-harness` | `"0.1"` | `SnapshotRef`, `Request` | `SkillEvalReceipt` | `false` |

---

## 7. Pure Completion Evaluation Rule (`AIF-013`, `AIF-020`)

The completion gate is a pure decision function:
```text
CompletionResult =
    Evaluate(
        AcceptanceExpression,
        Claims,
        VerificationRecords,
        Evidence,
        Snapshot
    )
```
It is **never** an autonomous repair loop (`inspect → fix → rerun → modify → declare done`).

---

## 7. Freeze Candidate Status Matrix

| Component | Status |
|---|---|
| Semantic boundaries | **VERIFIED** |
| Snapshot taxonomy | **VERIFIED** |
| State families | **VERIFIED** |
| Authority model | **FREEZE CANDIDATE** |
| Evidence model | **FREEZE CANDIDATE** |
| Claim/verification model | **FREEZE CANDIDATE** |
| Acceptance expression | **FREEZE CANDIDATE** |
| Receipt | **FREEZE CANDIDATE** |
| `_shared/aif` layout | **FREEZE CANDIDATE** |
| Phase 0/1 `AIF-0.1` contract & RED test suite (`tests/aif-v01-red-suite.py`) | **VERIFIED (`28/28` RED invariant tests + `13/13` modular schemas passing)** |
| Wave-1 `SKILL.md` implementation | **NOT STARTED** |
| Behavioral skill evaluation | **NOT STARTED** |
