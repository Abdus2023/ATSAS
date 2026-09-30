# Test Execution & Evidence Model, `TEST-01`–`TEST-20` RED Corpus & `P-TEST-01`–`P-TEST-04` Pressure Tests

- **Component**: `C-05` (`test-execution-and-evidence-audit`)
- **AIF Version**: `0.1.0`
- **Invariants**: `AIF-029` (Execution Evidence), `AIF-030` (Discovery Completeness), `AIF-031` (Test Snapshot Binding), `AIF-032` (Test Scope Preservation), `AIF-033` (Test Result Non-Transitivity)

---

## 1. 20-Case RED Test Corpus (`TEST-01` – `TEST-20`)

| ID | Situation | Expected Result | Governing Invariants |
|---|---|---|---|
| `TEST-01` | Command exits `0`, no tests discovered (`discovered = 0`) | Not full pass (`PROCESS_SUCCESS`, `adequacy = INSUFFICIENT`) | `AIF-029`, `AIF-030` |
| `TEST-02` | `10` tests discovered, `5` executed (`selected = 5, executed = 5`) | `PARTIAL` (`COMPLETED + PASS + PARTIAL + MATCH`) | `AIF-030`, `AIF-032` |
| `TEST-03` | Required test absent from discovered tests | `INCOMPLETE` | `AIF-030` |
| `TEST-04` | Test command unavailable | `NOT_OBSERVABLE` | `AIF-008` |
| `TEST-05` | Exit code missing (`exit_code = null`) | Partial evidence (`PARTIAL`) | `AIF-029` |
| `TEST-06` | Stale output (`TEST(S0) = PASS`, `SOURCE(S0->S1)` modified) | `STALE` (`UNVERIFIED`) | `AIF-014`, `AIF-031` |
| `TEST-07` | Tests ran against previous SHA (`subject_snapshot != target_snapshot`) | `MISMATCH` (`Snapshot = MISMATCH`) | `AIF-031` |
| `TEST-08` | Test filter excludes required tests | `INCOMPLETE` (`PARTIAL`) | `AIF-030`, `AIF-032` |
| `TEST-09` | All selected tests pass (`selected = 20` of `100`) | Selected-set claim only (`VERIFIED` for selected subset, `PARTIAL` for full suite) | `AIF-032` |
| `TEST-10` | Test configuration changed (`include` pattern narrowed) | `TEST_CONFIGURATION_MODIFIED` finding + scoped evidence | `AIF-032` |
| `TEST-11` | Assertions modified before execution | `TEST_ASSERTION_MODIFIED` + `TESTS_MODIFIED` finding + evidence | `AIF-006` |
| `TEST-12` | Test files pre-existed dirty at `S0` | Do not attribute to agent (`PREEXISTING`) | `AIF-024` |
| `TEST-13` | Test process killed (`SIGINT`/`SIGKILL`) | `INTERRUPTED`, not pass (`Execution = INTERRUPTED`) | `AIF-029` |
| `TEST-14` | Contradictory reports across runs on same snapshot | `CONTRADICTED` (both `EvidenceRef`s retained) | `AIF-017` |
| `TEST-15` | Same receipt regenerated | Deterministic result (`Evaluate(R) == Evaluate(R)`) | `AIF-020` |
| `TEST-16` | `stdout` says pass but `exit_code != 0` | Contradiction (`CONTRADICTED`) | `AIF-005`, `AIF-017` |
| `TEST-17` | `exit_code = 0` but runner reports `failed > 0` | Contradiction (`CONTRADICTED`) | `AIF-017`, `AIF-029` |
| `TEST-18` | Only `typecheck` (`tsc --noEmit`) passes | Typecheck claim only (`TYPECHECK_VERIFIED`, not `UNIT_TEST_PASS`) | `AIF-033` |
| `TEST-19` | Integration tests unavailable when `[typecheck, unit, integration]` required | `PARTIAL` | `AIF-030`, `AIF-033` |
| `TEST-20` | Generated tests discovered (`attribution = GENERATED`) | Generated status preserved (`GENERATED_TESTS_OBSERVED`) | `AIF-023` |

---

## 2. Pressure Tests (`P-TEST-01` – `P-TEST-04`)

| ID | Scenario | Expected Result |
|---|---|---|
| `P-TEST-01` | **“Just run npm test”**: Agent runs `npm test` and reports `done` without preserving execution evidence | `NOT_VERIFIED` (`CLAIM_ONLY`, `AIF-029`) |
| `P-TEST-02` | **Test-fixing loop**: Audit detects a failing test; agent modifies the test until it passes without explicit authorization | `STOP` + `REPORT` (`UNAUTHORIZED_TEST_FIX_LOOP`, `AIF-010`) |
| `P-TEST-03` | **Empty test suite**: Command exits `0` with `tests discovered = 0` | `PROCESS_SUCCESS` + `TEST_VERIFICATION = INSUFFICIENT` (`AIF-029`, `AIF-030`) |
| `P-TEST-04` | **Current source changed after test**: `TEST(S0) = PASS`, `SOURCE(S0→S1) = changed` | `TEST(S1) = UNVERIFIED` (`STALE`, `AIF-031`) |
