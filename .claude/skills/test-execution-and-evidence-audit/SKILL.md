---
name: test-execution-and-evidence-audit
description: Establishes what tests were actually configured, discovered, selected, and executed, and what that execution can legitimately prove under AIF-0.1.0 (`PROCESS_SUCCESS != TEST_SUCCESS != TEST_COMPLETENESS != SEMANTIC_CORRECTNESS`). Enforces AIF-029..AIF-033 across TestExecutionRecord, TestDiscoveryEvidence, 4-dimensional result states, ChangeRecord test mutations, and 9-criterion evidence adequacy (SCOPE: ARENA_GENERIC).
---

# Test Execution and Evidence Audit (`test-execution-and-evidence-audit` — Component `C-05`)

```text
SCOPE: ARENA_GENERIC
AIF_VERSION: 0.1.0
COMPONENT_ID: C-05
MUTATES_REPOSITORY: false
```

- **Protocol Binding**: `AIF-0.1.0` ([`../_shared/aif/VERSION`](../_shared/aif/VERSION))
- **Contract ID**: `C-05` ([`../../assurance/component-contracts.md`](../../assurance/component-contracts.md))
- **Governing Invariants**: `AIF-004`–`AIF-008`, `AIF-011`, `AIF-014`, `AIF-017`, `AIF-018`, `AIF-020`, `AIF-024`, `AIF-026`, `AIF-027`, `AIF-029` (Execution Evidence), `AIF-030` (Discovery Completeness), `AIF-031` (Test Snapshot Binding), `AIF-032` (Test Scope Preservation), `AIF-033` (Test Result Non-Transitivity)

---

## 1. Purpose & Central Distinction (`7.1`)

`test-execution-and-evidence-audit` is deliberately narrower than a generic “run the tests” skill: its job is to establish **what was actually executed and what that execution can legitimately prove**.

```text
TEST CONFIGURATION → TEST DISCOVERY → TEST EXECUTION → RAW RESULT
(exit code, stdout/stderr, discovered, executed, skipped, failed)
→ SNAPSHOT BINDING → EVIDENCE COVERAGE → CLAIM-SPECIFIC VERIFICATION
```

It never treats `npm test → exit 0` as equivalent to `all required behavior is verified`:

```text
PROCESS_SUCCESS ≠ TEST_SUCCESS ≠ TEST_COMPLETENESS ≠ SEMANTIC_CORRECTNESS
```

---

## 2. `TestExecutionRecord`, `TestDiscoveryEvidence` & 4-Dimensional Result States (`7.2`–`7.5`)

### 2.1 `TestExecutionRecord` & `TestDiscoveryEvidence` ([`../_shared/aif/schema/execution-record.schema.json`](../_shared/aif/schema/execution-record.schema.json))
- `discovery`: `{ discovered, selected, executed, skipped, filtered, failed }`.
  - `discovered = 100, selected = 20, executed = 20` establishes **`20 selected tests executed`**, never **`100 tests passed`** (`AIF-032`).
- `discovery_evidence` (`TestDiscoveryEvidence`): `{ test_runner, command, discovery_rules, discovered_tests[], excluded_tests[], filters[], subject_snapshot }`.
- Compares `REQUIRED SET` (`required_tests`, `required_test_pattern`, or `CLAIM(all_required_tests_pass)`) against `DISCOVERED` and `EXECUTED`. If the required set cannot be established, coverage is `UNKNOWN` (`AIF-030`).

### 2.2 Explicit Result States & 4 Orthogonal Dimensions (`7.3`)
State tokens (`NOT_OBSERVABLE`, `CONFIGURED`, `DISCOVERED`, `SELECTED`, `EXECUTED`, `PASSED`, `FAILED`, `SKIPPED`, `PARTIAL`, `STALE`, `MISMATCH`, `CONTRADICTED`) are decomposed across four orthogonal dimensions:
- **`Execution`**: `NOT_STARTED | RUNNING | COMPLETED | INTERRUPTED | UNKNOWN`
- **`Outcome`**: `PASS | FAIL | MIXED | SKIPPED | UNKNOWN`
- **`Coverage`**: `COMPLETE | PARTIAL | UNKNOWN`
- **`Snapshot`**: `MATCH | MISMATCH | UNKNOWN`

Thus `COMPLETED + PASS + PARTIAL + MATCH` (`TEST-09`: all selected tests pass, subset of required set) is represented accurately.

---

## 3. StreamForge Commands, Test Mutation & 9-Criterion Adequacy (`7.6`–`7.14`)

1. **StreamForge Local Procedures (`7.6`)**:
   `package.json` (`npm run typecheck`, `npm test`) establishes `TYPECHECK_CONFIGURED` and `TEST_CONFIGURED` (`declared local procedure`), distinct from `TYPECHECK_EXECUTED` / `TEST_EXECUTED` and `TYPECHECK_VERIFIED` / `TEST_SUITE_VERIFIED`.
2. **Output Integrity (`7.8`)**:
   `stdout`, `stderr`, `exit_code`, `command`, `environment`, `timestamp`, and `snapshot` form one execution evidence unit. Prose `"All tests passed"` without an execution record is `CLAIM_ONLY` (`RED-22`, `P-01`, `P-TEST-01`).
3. **Test Mutation & Configuration Scope (`7.10`–`7.11`)**:
   Consumes `ChangeRecord[]` and emits findings `TESTS_MODIFIED`, `TEST_CONFIGURATION_MODIFIED`, `TEST_DISCOVERY_MODIFIED`, and `TEST_ASSERTION_MODIFIED` (distinguishing pre-existing dirty test files in `TEST-12` and generated tests in `TEST-20`). In an unauthorized test-fixing loop (`P-TEST-02`), it enforces `STOP / REPORT`.
4. **Nine Minimum Evidence Criteria (`7.13`–`7.14`)**:
   (1) exact command, (2) test runner/version, (3) subject snapshot, (4) execution start/end, (5) exit code, (6) discovery result, (7) executed result, (8) failure/skipped information, (9) raw output reference. If any is missing or `discovery = UNKNOWN`, `adequacy = PARTIAL` or `NOT_OBSERVABLE` (never `SUFFICIENT`).

---

## 4. Invariants `AIF-029` – `AIF-033` (`7.17`)

- **`AIF-029` — Execution Evidence**: `PASS_CLAIM ⇒ EXECUTION_OBSERVED`
- **`AIF-030` — Discovery Completeness**: `ALL_REQUIRED_TESTS ⇒ DISCOVERY_COVERAGE_SUFFICIENT`
- **`AIF-031` — Test Snapshot Binding**: Test evidence is valid only for its recorded `subject_snapshot` or an explicitly defined compatible subject.
- **`AIF-032` — Test Scope Preservation**: Passing a selected subset cannot satisfy a claim about a larger required set.
- **`AIF-033` — Test Result Non-Transitivity**: `TYPECHECK_PASS ≠ UNIT_TEST_PASS`, `UNIT_TEST_PASS ≠ INTEGRATION_TEST_PASS`, `TEST_PASS ≠ IMPLEMENTATION_CORRECT`.

---

## 5. Deterministic Execution

```bash
# Run the 25-case self-test suite (TEST-01..TEST-20 + P-TEST-01..P-TEST-04 + StreamForge package.json check)
python3 .claude/skills/test-execution-and-evidence-audit/scripts/audit_test_execution.py --self-test

# Evaluate a JSON test-evidence audit payload
python3 .claude/skills/test-execution-and-evidence-audit/scripts/audit_test_execution.py path/to/test-audit-input.json
```

See [`references/test-evidence-model-and-20-case-corpus.md`](references/test-evidence-model-and-20-case-corpus.md) for the complete `TEST-01`–`TEST-20` RED matrix and `P-TEST-01`–`P-TEST-04` pressure matrix.
