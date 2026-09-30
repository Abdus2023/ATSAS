# Phase 13 & Phase 14 — Consistency / Normalization Audit & Execution Verification

- **Protocol Version**: `AIF-0.1.0` ([`../skills/_shared/aif/VERSION`](../skills/_shared/aif/VERSION))
- **Canonical Test Entrypoint**: `./tests/run-tests.sh`

---

## 1. Phase 13 — Resolution of the 6 Specification Drift Findings

| # | Drift Finding Identified | Root Cause | Resolution Applied & Verified |
|---|---|---|---|
| **1** | **Phase-12 audit had a stale `HEAD = 15f7fa0` header** | Line 4 of `phase12-interface-freeze-audit.md` still referenced `15f7fa0` after `ea23125` was committed | Updated [`.claude/assurance/phase12-interface-freeze-audit.md`](./phase12-interface-freeze-audit.md) to record the full commit progression (`S0 = 15f7fa0 → S1 = ea23125 → S2 = b9a9ce5 → Phase 13/14`). |
| **2** | **AIF invariant count evolved to `AIF-001..AIF-055` (`63` rules with `8` `*A` sub-invariants), while comments still said `20` or `28`** | `tests/aif-v01-red-suite.py`, `_shared/aif/README.md`, and `_shared/aif/tests/README.md` retained Phase 2 headings | Normalized `tests/aif-v01-red-suite.py`, `_shared/aif/README.md`, and `_shared/aif/tests/README.md` (adding `AIF-049..AIF-055` rows to the 55-invariant coverage table). |
| **3** | **Behavioral corpus count in `cases.yaml` is `49` (`41 RED + 8 PRESSURE`), while headers still said `44` (`36 RED + 8 PRESSURE`)** | `RED-037..RED-041` were added in Phase 4 without updating the file headers in `cases.yaml`, `oracle.md`, `tests/README.md`, and `tests/aif-v01-red-suite.py` | Normalized all references to `49` behavioral cases (`41 RED + 8 PRESSURE`) in `cases.yaml`, `oracle.md`, `_shared/aif/tests/README.md`, `_shared/aif/README.md`, `tests/aif-v01-red-suite.py`, and `tests/run-tests.sh`. |
| **4** | **`.agent/tools/aif-red-suite` expected old `VERSION == 0.1` and `28` tests** | `.agent/` was packaged during Phase 1 before `VERSION` became `0.1.0` and invariants expanded to `AIF-055` | Upgraded `.agent/skills/_shared/aif/VERSION` to `0.1.0` and upgraded `.agent/tools/aif-red-suite` to verify `VERSION == 0.1.0` and delegate directly to the canonical `tests/aif-v01-red-suite.py`. |
| **5** | **`tests/run-tests.sh` printed `"All 14 imported Agent Skills"` while validating all `22` skills** | Output string was not updated when Wave-1 skills `C-01..C-08` were added to `.claude/skills/` | Updated `tests/run-tests.sh` output to `"All 22 Agent Skills in .claude/skills/ (14 imported + 8 Wave-1 AIF skills)"` and updated `README.md` and `.claude/skills/README.md` to index all `22` skills. |
| **6** | **No `.github/workflows/` on `ATSAS` branch** | `ATSAS` has local test suites (`./tests/run-tests.sh`) but no `.github/workflows/` directory | Explicitly recorded in `phase12-interface-freeze-audit.md`: `CI_CONFIGURED = NOT_OBSERVED`, `CI_EXECUTED = NOT_OBSERVED`, `CI_PASSED = NOT_OBSERVED` (distinguishing unconfigured remote CI from local test execution per `AIF-004`, `AIF-008`, `AIF-028`). |

---

## 2. Schema & Layer Reconciliations (`Phase 13`)

### 2.1 Reconciliation of `13` Modular JSON Schemas vs `14` Core Semantic Kernel Types (`+ 3` Evaluation Types)
- **14 Core Repository Assurance Types**: `SnapshotRef`, `AuthorityEvent`, `Request`, `AdmissionRecord`, `ExecutionRecord`, `ChangeRecord`, `Claim`, `EvidenceRef`, `EvidenceCoverage`, `VerificationRecord`, `Finding`, `AcceptanceExpression`, `CompletionResult`, `ArenaEvidenceReceipt`.
- **Why `.claude/skills/_shared/aif/schema/` contains `13` JSON Schema files**:
  - `common.schema.json` defines shared primitives **plus** `$defs/EvidenceCoverage` and `$defs/Finding` (`2` core types).
  - The remaining `12` files (`snapshot-ref.schema.json`, `request.schema.json`, `authority-event.schema.json`, `admission-record.schema.json`, `execution-record.schema.json`, `change-record.schema.json`, `claim.schema.json`, `evidence-ref.schema.json`, `verification-record.schema.json`, `acceptance-expression.schema.json`, `completion-result.schema.json`, `evidence-receipt.schema.json`) each define `1` primary core type (`2 + 12 = 14` core conceptual types across `13` modular schema files).
- **Phase 11 Meta-Assurance Types (`12.19`)**: `EvaluationCase`, `EvaluationResult`, and `EvaluationSuiteResult` (plus `EvaluationBaseline`).

### 2.2 Reconciliation of `.claude/` vs `.agent/` Responsibilities
- **`.claude/skills/` + `.claude/assurance/`**: The **canonical `AIF-0.1.0` implementation layer** (`22` active skills + non-skill semantic kernel `.claude/skills/_shared/aif/`).
- **`.agent/`**: The **Phase 0/1 bootstrap process archive & CLI wrapper toolkit** (`9` meta-engineering process skills + `7` CLI wrappers). `.agent/tools/aif-red-suite` delegates directly to `tests/aif-v01-red-suite.py`.
- **Single Canonical Test Entrypoint**: `./tests/run-tests.sh`.

---

## 3. Phase 14 — Execution Verification Matrix

| Verification Target | Command | Observed Result |
|---|---|---|
| **1. AIF-0.1.0 Kernel & 49-Case RED/Pressure Suite** | `python3 tests/aif-v01-red-suite.py` | `145 passed, 0 failed` (`13` schemas, `63` invariant mutators `AIF-001..055`, `49` behavioral cases in `cases.yaml`, `15` adapter cases) |
| **2. Legacy `.agent/tools/aif-red-suite` Wrapper** | `./.agent/tools/aif-red-suite` | `145 passed, 0 failed` (verifies `VERSION == 0.1.0` in both `.claude` & `.agent` and delegates to `tests/aif-v01-red-suite.py`) |
| **3. Wave-1 Component Self-Tests (`C-01`..`C-08`)** | `evaluate_intake.py` (`14/14`), `audit_change_scope.py` (`9/9`), `audit_supply_chain.py` (`16/16`), `audit_ci_workflow.py` (`21/21`), `audit_test_execution.py` (`27/27`), `generate_receipt.py` (`19/19`), `evaluate_completion.py` (`22/22`), `run_suite.py` (`13/13`) | `141/141` component self-test assertions `PASS` |
| **4. 22-Skill Structural & `SCOPE:` Validation** | `python3 .claude/skills/skill-creator/scripts/validate_skill.py --all .claude/skills` | `22 skill(s) checked, 0 error(s)` |
| **5. `aif-eval-corpus-0.2` Harness Suite** | `python3 .claude/skills/skill-evaluation-harness/scripts/generate_report.py` | `79 PASS, 0 FAIL, 0 NOT_OBSERVABLE` (`65 RED`, `11 PRESSURE`, `3 GREEN`) |
| **6. Canonical Full Repository Test Entrypoint** | `./tests/run-tests.sh` | `118 passed, 0 failed` (`exit_code = 0`) |
