---
name: aif-assurance-workflow-orchestrator
description: Orchestrates the complete end-to-end ATSAS & AIF assurance engineering pipeline from architecture bootstrap (`atsas-aif-architecture-bootstrap`), cross-repo skill portability import (`cross-repo-skill-portability-import`), 42-case RED/pressure test matrix design (`assurance-test-matrix-designer`), capability overlap audit (`skill-capability-overlap-audit`), component contract specification (`aif-component-contract-designer`), adversarial freeze review (`aif-adversarial-freeze-review`), and Semantic Kernel engineering (`aif-semantic-kernel-engineer`) to Phase 0/1 RED suite execution and receipt evaluation. Use whenever running a full repository assurance pass or onboarding a new repository to ATSAS/AIF.
---

# AIF End-to-End Assurance Workflow Orchestrator

```text
SCOPE: ARENA_GENERIC
```

```yaml
aif:
  version: "0.1"
  consumes:
    - Request
    - AdmissionRecord
    - SnapshotRef
    - ExecutionRecord
    - ChangeRecord
    - Claim
    - EvidenceRef
    - EvidenceCoverage
    - VerificationRecord
    - Finding
    - AcceptanceExpression
  produces:
    - ArenaEvidenceReceipt
    - CompletionResult
  mutates_repository: false
```

Executes the complete 7-stage ATSAS & AIF assurance engineering methodology in strict causal order without skipping pre-implementation verification gates.

## Workflow

### Step 1 — Follow the 7-Stage Pre-Implementation & Assurance Order

Read `references/end-to-end-pipeline.md` before starting a repository assurance pass:

1. **Stage 1 (`atsas-aif-architecture-bootstrap`)**: Establish ATSAS vs. AIF separation, 9-concern pipeline, and 7 non-binary epistemic states.
2. **Stage 2 (`cross-repo-skill-portability-import`)**: Audit imported/bundled skills for `"Location is not scope"` (`SCOPE: ARENA_GENERIC` / `STREAMFORGE_REPO` + `ADAPTATION:` tags).
3. **Stage 3 (`assurance-test-matrix-designer`)**: Define the 18 assurance domains, 11 `AAI-001`..`AAI-011` invariants, and 42-case `AAI-001`..`AAI-034` + `P-001`..`P-008` RED/Pressure test matrix before authoring `SKILL.md` files.
4. **Stage 4 (`skill-capability-overlap-audit`)**: Map existing skills against the 42 cases, use `EvidenceRef` adapters instead of duplicating detectors, and separate app-security authz from task authority.
5. **Stage 5 (`aif-component-contract-designer`)**: Specify the 8 normative component contracts (`C-01`..`C-08`), universal execution envelope, and `PHASE 0`..`PHASE 12` order.
6. **Stage 6 (`aif-adversarial-freeze-review`)**: Red-team the contracts against `ADV-001`..`ADV-014`, apply `PATCH-001`..`PATCH-014`, and enforce `FT-01`..`FT-10` and `AIF-001`..`AIF-020` (`+A`).
7. **Stage 7 (`aif-semantic-kernel-engineer`)**: Freeze the 14-type `AIF-0.1` Semantic Kernel under `_shared/aif/` and run the 28-case Phase 0/1 RED invariant test suite.

### Step 2 — Assemble & Evaluate Canonical Evidence Bundles

Use `assets/receipt-bundle-template.json` when constructing an `AIFCanonicalDataModelBundle` (`schema_version: "aif/0.1"`), and evaluate it with `.agent/tools/aif-verify` and `.agent/tools/aif-completion-eval`.

### Step 3 — Execute the Full Deterministic Pipeline Script

Run `scripts/run_assurance_pipeline.py` to execute all 7 stage verifiers, all `.agent/tools/` contract checks, and the 28-case Phase 0/1 RED test suite in one deterministic pass:

```bash
python3 .agent/skills/aif-assurance-workflow-orchestrator/scripts/run_assurance_pipeline.py
```
