---
name: assurance-test-matrix-designer
description: Designs, expands, and validates the 18-Domain Repository Assurance Matrix, the 11 Core Arena Assurance Invariants (`AAI-001`..`AAI-011`), and the 42-Case Behavioral & Pressure Test Matrix (`AAI-001`..`AAI-034`, `P-001`..`P-008`) BEFORE any `SKILL.md` implementation. Use whenever applying TDD (`RED -> GREEN -> PRESSURE -> REGRESSION`) to agent skills, authoring behavioral or adversarial pressure test cases, or verifying that an assurance test matrix satisfies the 11-column canonical schema.
---

# Assurance Test Matrix Designer (RED & Pressure TDD for Skills)

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

Applies Test-Driven Development (`RED -> GREEN -> PRESSURE -> REGRESSION`) to Agent Skills by specifying behavioral failure modes, required evidence, forbidden inferences, and adversarial pressure scenarios **before** authoring `SKILL.md` files.

## Workflow

### Step 1 — Map the 18 Repository Assurance Domains & 11 Core Invariants

Read `references/matrix-schema-and-domains.md` for the full 18-domain taxonomy, the 11 core Arena Assurance Invariants (`AAI-001`..`AAI-011`), and the 11-column test matrix schema. Never author a new assurance skill without first defining the RED behavioral cases and adversarial pressure cases (`P-001`..`P-008`) it must pass.

### Step 2 — Author Test Cases Using the 11-Column Canonical Schema

Use `assets/test-matrix-row-template.md` to add or update rows in `.claude/assurance/test-matrix.md` and `ARENA_ASSURANCE_TEST_MATRIX.md`. Every row must specify all 11 columns:

1. `TEST_ID` (`AAI-001`..`AAI-034` with `RED-01`..`RED-34` cross-reference, or `P-001`..`P-008`)
2. `TRIGGER`
3. `PRECONDITION`
4. `AUTHORIZED_SCOPE`
5. `AGENT_ACTION`
6. `EXPECTED_OBSERVATION`
7. `EXPECTED_CLASSIFICATION`
8. `REQUIRED_EVIDENCE`
9. `FORBIDDEN_INFERENCE`
10. `FAILURE_STATE`
11. `TARGET_SKILL`

### Step 3 — Run Deterministic Test Matrix Validation

Execute `scripts/validate_test_matrix.py` to verify that all 11 columns, all 34 behavioral cases (`AAI-001`..`AAI-034`), and all 8 pressure cases (`P-001`..`P-008`) are present and structurally complete:

```bash
python3 .agent/skills/assurance-test-matrix-designer/scripts/validate_test_matrix.py .claude/assurance/test-matrix.md ARENA_ASSURANCE_TEST_MATRIX.md
```
