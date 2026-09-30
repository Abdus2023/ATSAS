---
name: aif-component-contract-designer
description: Designs and validates the 8 normative AIF component contracts (`C-01`..`C-08`), the universal execution envelope (`SkillInput -> Observation -> SkillResult -> EvidenceRef[] -> State`), and the 13-phase implementation order (`PHASE 0`..`PHASE 12`) before authoring `SKILL.md` files. Use whenever defining inputs, outputs, state transitions, required evidence, or non-authority boundaries ("Produces vs. Does Not Decide") for assurance skills (`arena-intake-and-authority`, `agent-change-scope-audit`, `dependency-supply-chain-audit`, `ci-workflow-audit`, `test-execution-and-evidence-audit`, `evidence-receipt-generator`, `arena-completion-gate`, `skill-evaluation-harness`).
---

# AIF Component Contract Designer (`C-01` – `C-08`)

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
    - Claim
    - VerificationRecord
  mutates_repository: false
```

Defines the normative interface contracts (`C-01`..`C-08`) and responsibility boundaries for the eight assurance components before any `SKILL.md` implementation begins.

## Workflow

### Step 1 — Enforce the Universal Execution Envelope & Non-Authority Boundaries

Read `references/eight-component-contracts.md` before drafting or modifying any component contract. Every component must obey:

```text
SkillInput -> Observation/execution -> SkillResult -> EvidenceRef[] -> State classification
```
where `RESULT != EVIDENCE != DECISION`.

Each component contract must explicitly state:
1. **Produces (Kernel Objects)**: Which of the 14 `AIF-0.1` Semantic Kernel objects it emits.
2. **Does Not Decide**: Which decisions are strictly outside its authority (e.g., detectors never decide `CompletionResult`; `arena-completion-gate` never fabricates missing `EvidenceRef`).

### Step 2 — Author Contracts Using the Canonical Template

Use `assets/component-contract-template.md` when adding or updating contracts in `.claude/assurance/component-contracts.md` and `spec/06-wave1-skill-interfaces.md`.

### Step 3 — Run Deterministic Component Contract Validation

Execute `scripts/validate_component_contracts.py` to verify that all 8 contracts (`C-01`..`C-08`), all 8 skill identifiers, all 12 phases (`PHASE 0`..`PHASE 12`), and all 15 failure taxonomy codes are defined:

```bash
python3 .agent/skills/aif-component-contract-designer/scripts/validate_component_contracts.py
```
