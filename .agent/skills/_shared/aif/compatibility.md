# AIF-0.1 Versioning, Compatibility & Skill Contract Declarations

> **Protocol Version**: `0.1` ([`VERSION`](./VERSION))  
> **Core Rule**: **A semantic change is a breaking change even if the JSON Schema remains technically compatible.**

---

## 1. Strict Semantic Versioning Rules (`AIF_VERSION = 0.1`)

| Change Type | Version Bump |
|---|---|
| Typo / documentation clarification only | `PATCH` (`0.1.x`) |
| Add optional field | `MINOR` (`0.2.0`) |
| Add new non-breaking state | `MINOR` (`0.2.0`) |
| Add optional evidence source (`source_type`) | `MINOR` (`0.2.0`) |
| Change meaning of existing state (e.g., `UNKNOWN` → `FAILED`) | **`MAJOR` (`1.0.0`)** |
| Rename state | **`MAJOR` (`1.0.0`)** |
| Remove field | **`MAJOR` (`1.0.0`)** |
| Change invariant (`AIF-001`..`AIF-020`) | **`MAJOR` (`1.0.0`)** |
| Change acceptance expression semantics | **`MAJOR` (`1.0.0`)** |
| Change snapshot taxonomy or equivalence semantics | **`MAJOR` (`1.0.0`)** |

---

## 2. Normative Compatibility Contract

```text
A skill declaring:

    aif_version = 0.1

MUST interpret AIF-0.1 states and invariants according to
the frozen AIF-0.1 contract in .claude/skills/_shared/aif/.

A skill MUST NOT:

    reinterpret UNKNOWN as FAILURE or PASS
    reinterpret CLAIMED as VERIFIED
    reinterpret EXECUTED as SUCCESS
    reinterpret CLEAN as VERIFIED (or unbounded REPOSITORY_SAFE)
    reinterpret configured CI as executed CI
    reinterpret detector output as completion
```

---

## 3. Mechanical Skill Contract Declaration (`aif:` Block)

Every Wave-1 assurance skill must declare its AIF contract in YAML frontmatter or structured metadata so the skill graph is mechanically inspectable:

```yaml
aif:
  version: "0.1"
  consumes:
    - SnapshotRef
    - Request
  produces:
    - EvidenceRef
    - Finding
  mutates_repository: false
```

### Canonical Skill Graph Declarations (`C-01` – `C-08`)

| Skill | `aif.version` | `aif.consumes` | `aif.produces` | `aif.mutates_repository` |
|---|---|---|---|---|
| `arena-intake-and-authority` (`C-01`) | `"0.1"` | `SnapshotRef` | `Request`, `AuthorityEvent`, `AdmissionRecord`, `AcceptanceExpression` | `false` |
| `agent-change-scope-audit` (`C-02`) | `"0.1"` | `AdmissionRecord`, `SnapshotRef`, `ExecutionRecord` | `SnapshotRef`, `ChangeRecord`, `Finding`, `EvidenceRef` | `false` |
| `dependency-supply-chain-audit` (`C-03`) | `"0.1"` | `SnapshotRef`, `Request` | `Finding`, `EvidenceRef` | `false` |
| `ci-workflow-audit` (`C-04`) | `"0.1"` | `SnapshotRef`, `Request` | `ExecutionRecord`, `Finding`, `EvidenceRef`, `VerificationRecord` | `false` |
| `test-execution-and-evidence-audit` (`C-05`) | `"0.1"` | `SnapshotRef`, `Request`, `Claim` | `ExecutionRecord`, `EvidenceRef`, `VerificationRecord` | `false` |
| `evidence-receipt-generator` (`C-06`) | `"0.1"` | `Request`, `AdmissionRecord`, `SnapshotRef`, `AuthorityEvent`, `ExecutionRecord`, `ChangeRecord`, `Claim`, `EvidenceRef`, `VerificationRecord`, `Finding`, `AcceptanceExpression` | `EvidenceCoverage`, `ArenaEvidenceReceipt` | `false` |
| `arena-completion-gate` (`C-07`) | `"0.1"` | `Request`, `AdmissionRecord`, `ChangeRecord`, `Claim`, `EvidenceRef`, `EvidenceCoverage`, `VerificationRecord`, `AcceptanceExpression`, `ArenaEvidenceReceipt` | `CompletionResult` | `false` |
| `skill-evaluation-harness` (`C-08`) | `"0.1"` | `SnapshotRef`, `Request` | `SkillEvalReceipt` | `false` |
