---
name: atsas-aif-architecture-bootstrap
description: Bootstraps and verifies the ATSAS (Arena Tools, Skills, Agentic System) and AIF (Agent Assurance Interface) two-layer repository architecture, 9-concern assurance pipeline, and non-binary epistemic state model. Use whenever initializing a repository-governed agent assurance framework, separating capability/execution (ATSAS) from claim/evidence verification (AIF), authoring foundational boundary specifications, or auditing whether a repository enforces "NO EVIDENCE -> NO VERIFIED CLAIM".
---

# ATSAS & AIF Architecture Bootstrap

```text
SCOPE: ARENA_GENERIC
```

```yaml
aif:
  version: "0.1"
  consumes:
    - SnapshotRef
  produces:
    - EvidenceRef
    - Finding
  mutates_repository: false
```

Establishes and verifies the foundational separation between **ATSAS** (capability and behavior architecture: what an agent can use and how its agentic system operates) and **AIF** (assurance and claim architecture: what can legitimately be claimed about the resulting work).

## Workflow

### Step 1 — Enforce the ATSAS vs. AIF Boundary Axioms

Read `references/boundary-axioms.md` before creating or reviewing architectural specifications. Every design artifact must preserve four non-negotiable axioms:

1. **A skill is not evidence.**
2. **A tool result is not automatically verification.**
3. **Execution is not completion.**
4. **Completion is an evidence-backed claim (`NO EVIDENCE -> NO VERIFIED CLAIM`).**

Always write the acronym `ATSAS` in all-caps (`ATSAS`, never `ATSAs`).

### Step 2 — Structure the 9-Concern AIF Pipeline & Non-Binary Epistemic Lattice

Use `assets/aif-overview-template.md` when scaffolding a new repository overview or `spec/` tree. Ensure the specification explicitly separates:

1. **The 9-Concern Pipeline**:
   ```text
   AUTHORITY -> ADMISSION -> EXECUTION -> CHANGE ATTRIBUTION -> OBSERVATION -> VERIFICATION -> EVIDENCE -> ACCEPTANCE -> COMPLETION
   ```
2. **The 7 Core Non-Binary Epistemic States**:
   - `VERIFIED`: Sufficient, fresh, scope-bounded, snapshot-bound evidence satisfies the claim.
   - `UNKNOWN`: Claim has not yet been evaluated or observation is indeterminate.
   - `NOT_OBSERVABLE`: The execution environment or tool surface cannot observe the target property.
   - `PARTIAL`: Evidence covers only a subset of the declared scope or acceptance criteria.
   - `STALE`: Evidence is bound to an older repository snapshot that was subsequently modified.
   - `MISMATCH`: Observed snapshot, scope, or output diverges from the claimed target or value.
   - `CONTRADICTED`: Direct counter-evidence refutes the claim or violates an acceptance criterion.

### Step 3 — Run Deterministic Architecture Verification

Execute `scripts/verify_architecture_layout.py` against the repository root to verify that all required specification files, schemas, boundary axioms, and epistemic states are present and unmodified by acronym or boolean-collapse drift:

```bash
python3 .agent/skills/atsas-aif-architecture-bootstrap/scripts/verify_architecture_layout.py .
```

Fix any reported missing files, missing epistemic states, or casing violations before proceeding to test-matrix or skill design.
