---
name: aif-semantic-kernel-engineer
description: Engineers, packages, and verifies the AIF-0.1 Semantic Kernel (`_shared/aif/`), its 14 canonical object types (`Request`, `SnapshotRef`, `AuthorityEvent`, `AdmissionRecord`, `ExecutionRecord`, `ChangeRecord`, `Claim`, `EvidenceRef`, `EvidenceCoverage`, `VerificationRecord`, `Finding`, `AcceptanceExpression`, `CompletionResult`, `ArenaEvidenceReceipt`), its 4 orthogonal state machines, and its Phase 0/1 28-case RED invariant test suite. Use whenever evolving the shared AIF protocol contract, validating `_shared/aif/` schemas, or verifying that the Semantic Kernel remains a versioned protocol dependency rather than a "god skill".
---

# AIF Semantic Kernel Engineer (`_shared/aif/` & Phase 0/1 RED Suite)

```text
SCOPE: ARENA_GENERIC
```

```yaml
aif:
  version: "0.1"
  consumes:
    - Request
    - SnapshotRef
  produces:
    - VerificationRecord
    - EvidenceRef
  mutates_repository: false
```

Maintains the **AIF-0.1 Semantic Kernel** as a small, versioned protocol contract (`_shared/aif/`) consumed by specialized producer skills and evaluated by `arena-completion-gate`, preventing "god skill" bloat and semantic drift.

## Workflow

### Step 1 — Enforce the Three-Authority & Dependency Boundaries

Read `references/kernel-object-graph.md` before modifying any Semantic Kernel schema or rule:

1. **Do not make the semantic kernel a skill.** Keep it as a versioned protocol/contract under `_shared/aif/`.
2. **Skills may depend on AIF semantics. AIF must not depend on skills.**
3. **Separate the three authorities**:
   - **Semantic Authority (`AIF CORE`)**: Defines what states and kernel objects mean.
   - **Procedural Authority (`SKILLS`)**: Defines how each skill performs its task and emits evidence.
   - **Decision Authority (`COMPLETION GATE`)**: Pure evaluation `CompletionResult = Evaluate(AcceptanceExpression, Claims, VerificationRecords, Evidence, Snapshot)`.

### Step 2 — Declare Mechanical `aif:` Contracts on Skills

Use `assets/skill-aif-contract-snippet.yaml` when annotating any skill so the skill graph (`version`, `consumes`, `produces`, `mutates_repository`) is mechanically inspectable and obeys strict semantic versioning (`compatibility.md`).

### Step 3 — Run the Phase 0/1 Semantic Kernel & RED Invariant Suite

Execute `scripts/verify_semantic_kernel.py` to verify:
1. Both `.claude/skills/_shared/aif/` and `.agent/skills/_shared/aif/` are synchronized and contain `VERSION`, `README.md`, `invariants.md`, `states.md`, `evidence-rules.md`, `compatibility.md`, and all 13 modular Draft 2020-12 JSON Schemas in `schema/`.
2. All 28 executable RED invariant tests (`TEST AIF-001-01` .. `TEST AIF-020-01`) in `tests/aif-v01-red-suite.py` pass with 0 failures:

```bash
python3 .agent/skills/aif-semantic-kernel-engineer/scripts/verify_semantic_kernel.py
```
