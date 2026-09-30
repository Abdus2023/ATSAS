# AIF-0.1 State Dimensions (`states.md`)

- **Protocol Version**: `0.1.0` ([`VERSION`](./VERSION))
- **Governing Invariants**: `AIF-001`, `AIF-004`, `AIF-005`, `AIF-006`, `AIF-008`, `AIF-009`

State dimensions in `AIF-0.1` are orthogonal. No value in one table implies a value in another table without an explicit `AIF-0.1` transition rule and supporting evidence.

---

## 1. Authority States

| State | Meaning |
|---|---|
| `AUTHORIZED` | Evidence establishes applicable authority for the action/scope/time |
| `NOT_AUTHORIZED` | Applicable authority is absent or explicitly denied |
| `UNKNOWN` | Authority cannot currently be established |
| `EXPIRED` | Previously applicable authority is no longer effective |
| `CONFLICTING` | Applicable authority records conflict |

**Boundary Rule**:

```text
EXECUTED(action) ∧ NOT_AUTHORIZED(action) ⇒ AUTHORITY_VIOLATION
```

`EXECUTED(action)` alone does **not** establish `AUTHORIZED`. Reality (`execution occurred + authorization absent`) must be recorded without rewriting history.

---

## 2. Execution States

| State | Meaning |
|---|---|
| `NOT_STARTED` | Execution has not begun |
| `STARTED` | Execution began |
| `EXECUTED` | Requested operation completed at the process level |
| `FAILED` | Execution terminated unsuccessfully |
| `CANCELLED` | Execution was intentionally cancelled |
| `INTERRUPTED` | Execution stopped without a normal completion |
| `NOT_OBSERVABLE` | Execution status cannot be established |

**Boundary Rule**: `EXECUTED` means process completion only; `EXECUTED` does **not** mean `SUCCESSFUL` or `VERIFIED`.

---

## 3. Verification States

| State | Meaning |
|---|---|
| `NOT_VERIFIED` | Claim has not been verified against evidence |
| `VERIFYING` | Verification evaluation is currently in progress |
| `VERIFIED` | Sufficient evidence supports the specific claim against the specified subject/snapshot/method |
| `PARTIAL` | Evidence covers only a proper subset of the claim's subject, scope, or criteria |
| `CONTRADICTED` | Evidence directly refutes the claim or independent evidence sources conflict |
| `STALE` | Evidence was captured against a prior snapshot invalidated by subsequent mutation |
| `MISMATCH` | Evidence subject, scope, method, or snapshot does not match the claim |
| `NOT_OBSERVABLE` | Verification could not be performed because the required observation path or tool is unavailable |

**Boundary Rule**: `VERIFIED` means sufficient evidence supports the **specific claim** against the **specified subject/snapshot/method**. It does **not** mean *"the repository is correct."*

---

## 4. Observation States

| State | Meaning |
|---|---|
| `NOT_REQUESTED` | Observation was outside the requested verification scope |
| `NOT_CHECKED` | The verification opportunity existed in the environment, but the check was not performed |
| `NOT_OBSERVABLE` | The relevant fact could not be established through the available observation path |
| `UNKNOWN` | Observation status is indeterminate |
| `PARTIAL` | Only a subset of the target surface was observed |
| `CONTRADICTED` | Multiple observations over the same target surface produced conflicting facts |
| `OBSERVED` | Direct primary observation was captured from the subject |
| `DERIVED` | Fact was deterministically computed from primary observations |
| `CLAIMED` | Proposition was asserted by an actor or skill without primary observation |

**Why both `NOT_CHECKED` and `NOT_OBSERVABLE` exist**:
- `NOT_CHECKED`: the verification opportunity existed (e.g., `pytest` is installed and tests exist) but was not run.
- `NOT_OBSERVABLE`: the relevant fact could not be established through the available observation path (e.g., remote GitHub Actions API or advisory database is unreachable in an offline sandbox).
Those are materially different failure modes and must never be conflated.

---

## 5. Admission States & Action Vocabulary

### Four Fundamental Intake Outcomes (`AdmissionRecord.admission_status`)

| Result | Meaning |
|---|---|
| `ADMITTED` | Required authority and scope are established (`ACTION_SCOPE ∧ PATH_SCOPE ∧ TEMPORAL_SCOPE ∧ ACTOR_SCOPE`) |
| `INSPECT_ONLY` | Inspection (`READ`, `LIST`, `SEARCH`) is authorized, mutation is not (e.g., `"Investigate why CI fails."`) |
| `BLOCKED` | Required information or authority is unresolved (vague scope, missing approval, expired authority, or conflicting authority) |
| `REJECTED` | Requested action or path explicitly conflicts with authority or repository policy |

### 12-Action Vocabulary (Read vs. Repository Mutation vs. External Side Effect)

| Action | Category | Meaning |
|---|---|---|
| `READ` | Inspection | Read file contents or repository metadata |
| `LIST` | Inspection | Enumerate directory entries or tracked/untracked paths |
| `SEARCH` | Inspection | Search file contents or symbol indices |
| `EXECUTE` | Process / Side Effect | Execute a process (e.g., `run_tests`, `npm install` which may alter `node_modules/` or lockfiles) |
| `CREATE` | Repository Mutation | Create a new file |
| `MODIFY` | Repository Mutation | Edit an existing file |
| `DELETE` | Repository Mutation | Delete an existing file |
| `RENAME` | Repository Mutation | Move or rename a path |
| `GENERATE` | Repository Mutation | Emit build, bundle, or codegen artifacts |
| `COMMIT` | Repository History | Create a Git commit |
| `PUSH` | External Side Effect | Push refs to a remote repository |
| `RELEASE` | External Side Effect | Publish a package, tag, or release artifact |

---

## 6. Completion States & The `BLOCKED` vs. `INCOMPLETE` vs. `UNVERIFIED` Distinction

| State | Meaning | Canonical Examples |
|---|---|---|
| `BLOCKED` | A prerequisite prevents legitimate continuation | Required authorization absent; required tool unavailable when mandatory; scope conflict or blocking finding unresolved |
| `INCOMPLETE` | The task remains unfinished or insufficiently evidenced | Tests not executed; CI evidence missing; one mandatory acceptance claim unresolved |
| `UNVERIFIED` | A claim was asserted or attempted, but evidence is insufficient | Agent asserts `"tests passed"` with no execution evidence |
| `COMPLETABLE` | Every mandatory claim in `AcceptanceExpression` is `VERIFIED` at `verification_snapshot` with zero blockers | All required scope, implementation, and test claims verified at current snapshot |
| `COMPLETED` | Gate has emitted an immutable `ArenaEvidenceReceipt` for a `COMPLETABLE` result | Signed/hashed receipt `R` persisted |

**Canonical Mapping**:

```text
missing authorization          → BLOCKED
missing required test evidence → INCOMPLETE
unsupported assertion          → UNVERIFIED
```

These three non-completion states must never collapse into one generic `FAIL` label.

---

## 7. Four-Dimensional Change & Scope Audit States (`ChangeRecord`)

```text
STATE CHANGE ≠ AGENT CHANGE ≠ AUTHORIZED CHANGE
```

Every `ChangeRecord` emitted by `agent-change-scope-audit` carries four orthogonal dimensions:

| Dimension | Allowed Values | Rule |
|---|---|---|
| **1. State** (`change_type`) | `ADDED`, `MODIFIED`, `DELETED`, `RENAMED`, `GENERATED`, `UNCHANGED` | Derived from `DIFF(S0, S1)` |
| **2. Scope** (`scope`) | `IN_SCOPE`, `OUT_OF_SCOPE`, `UNKNOWN` | Evaluated against `AdmissionRecord.admitted_paths` / `excluded_paths`; unresolvable matchers remain `UNKNOWN` (never collapsed into `OUT_OF_SCOPE`) |
| **3. Attribution** (`attribution`) | `PREEXISTING`, `AGENT_ATTRIBUTED`, `EXTERNAL_ATTRIBUTED`, `GENERATED`, `UNATTRIBUTED`, `UNKNOWN` | Provenance of the change (`AIF-023`, `AIF-024`); `AGENT_ATTRIBUTED` requires explicit `attribution_basis` (`ExecutionRecord` + `GIT_OBJECT`) |
| **4. Authority** (`authority`) | `AUTHORIZED`, `UNAUTHORIZED`, `UNKNOWN` | $\text{UNAUTHORIZED\_AGENT\_CHANGE} \iff \text{AGENT\_ATTRIBUTED\_CHANGE} \land \neg \text{IN\_AUTHORIZED\_SCOPE}$ |

---

## 8. CI Workflow & Execution State Machine (`ci-workflow-audit`)

```text
CI workflow exists ≠ CI was triggered ≠ CI ran successfully ≠ CI tested this commit ≠ CI artifact corresponds to this commit ≠ release is verified
```

| Dimension | Allowed Values | Rule |
|---|---|---|
| **1. Configuration & Run Lifecycle** | `NOT_FOUND`, `CONFIGURED`, `TRIGGERED`, `RUNNING`, `COMPLETED`, `CANCELLED` | `.github/workflows/` absence is `NOT_FOUND` (`VERIFIED_OBSERVATION`), not `CI_FAILED` |
| **2. Run Conclusion** (`COMPLETED`) | `SUCCESS`, `FAILURE`, `NEUTRAL`, `UNKNOWN` | Evaluated per workflow run and per required job (`CI_JOB_FAILURE`, `CI_REQUIRED_JOB_MISSING`) |
| **3. Subject Match** (`AIF-028`) | `MATCH`, `MISMATCH`, `UNKNOWN` | `CI_RUN = SUCCESS ∧ SUBJECT_MATCH = MISMATCH ⇒ CLAIM(current_snapshot) = UNVERIFIED` |
| **4. Trigger Policy** | `TRIGGER_DECLARED`, `TRIGGER_POLICY_OBSERVED`, `TRIGGER_POLICY_UNKNOWN` | Distinguishes YAML `on:` declaration from repository-level Actions policy |

---

## 9. Test Execution & Evidence States (`test-execution-and-evidence-audit`)

```text
PROCESS_SUCCESS ≠ TEST_SUCCESS ≠ TEST_COMPLETENESS ≠ SEMANTIC_CORRECTNESS
```

### 9.1 Test Result States & 4 Orthogonal Dimensions
Individual state tokens (`NOT_OBSERVABLE`, `CONFIGURED`, `DISCOVERED`, `SELECTED`, `EXECUTED`, `PASSED`, `FAILED`, `SKIPPED`, `PARTIAL`, `STALE`, `MISMATCH`, `CONTRADICTED`) decompose across four orthogonal dimensions so combinations such as `COMPLETED + PASS + PARTIAL + MATCH` are represented explicitly:

| Dimension | Allowed Values | Rule |
|---|---|---|
| **1. Execution** | `NOT_STARTED`, `RUNNING`, `COMPLETED`, `INTERRUPTED`, `UNKNOWN` | Process lifecycle (`TEST-13`: killed process is `INTERRUPTED`, not `PASS`) |
| **2. Outcome** | `PASS`, `FAIL`, `MIXED`, `SKIPPED`, `UNKNOWN` | Test suite outcome (`AIF-029`: `PASS` requires `executed > 0`, `failed == 0`, unmasked `exit_code == 0`) |
| **3. Coverage** | `COMPLETE`, `PARTIAL`, `UNKNOWN` | Evaluated against the required test set (`AIF-030`, `AIF-032`: `selected < discovered` or `discovery = UNKNOWN` yields `PARTIAL`) |
| **4. Snapshot** | `MATCH`, `MISMATCH`, `UNKNOWN` | Evaluated against `target_snapshot` (`AIF-031`: `TEST(S0) = PASS` with `SOURCE(S0→S1)` changed is `STALE` / `MISMATCH`) |

### 9.2 StreamForge Procedure States (`package.json` vs Execution vs Verification)
- **Configured (`package.json`)**: `TYPECHECK_CONFIGURED`, `TEST_CONFIGURED`
- **Executed**: `TYPECHECK_EXECUTED`, `TEST_EXECUTED`
- **Verified (`AIF-033` Non-Transitivity)**: `TYPECHECK_VERIFIED` ($\neq$ `UNIT_TEST_PASS`), `TEST_SUITE_VERIFIED` ($\neq$ `IMPLEMENTATION_CORRECT`)

---

## 10. Dependency Supply-Chain States (`dependency-supply-chain-audit`)

```text
NO_KNOWN_VULNERABILITIES ≠ SUPPLY_CHAIN_ESTABLISHED
LOCKFILE_MISSING ≠ VULNERABLE
AUDIT_UNAVAILABLE ≠ AUDIT_PASSED
DECLARED(dependency) ≠ RESOLVED(dependency) ≠ INSTALLED(dependency) ≠ USED_IN_BUILD(dependency)
```

| Supply-Chain Stage / Record | Allowed States / Values | Governing Invariant |
|---|---|---|
| **1. `LockfileRecord.status`** | `PRESENT`, `MISSING`, `UNREADABLE`, `UNSUPPORTED`, `MULTIPLE`, `UNKNOWN` | `AIF-034`, `AIF-039` (`status = MISSING`, not `lockfile = false`) |
| **2. Dependency Lifecycle Stage** | `DECLARED`, `RESOLVED`, `INSTALLED`, `BUILT` | `AIF-034`, `AIF-035`, `AIF-036` |
| **3. `SourceRecord.source_type`** | `REGISTRY`, `GIT`, `GIT_COMMIT`, `LOCAL_PATH`, `TARBALL`, `WORKSPACE`, `UNKNOWN` | `AIF-039` (`UNKNOWN` never inferred as `REGISTRY`) |
| **4. `IntegrityRecord.result`** | `VERIFIED`, `MISMATCH`, `NOT_AVAILABLE`, `NOT_CHECKED`, `UNKNOWN` | `AIF-008`, `AIF-008A` (`NOT_CHECKED != VERIFIED`, `NOT_AVAILABLE != MISMATCH`) |
| **5. `InstallRecord.result`** | `SUCCESS`, `FAILURE`, `PARTIAL`, `INTERRUPTED`, `UNKNOWN`, `NOT_EXECUTED` | `AIF-035` |
| **6. `DependencyEvidenceCoverage.completeness`** | `COMPLETE`, `PARTIAL`, `NOT_ESTABLISHED`, `UNKNOWN` | `AIF-037`, `AIF-038`, `AIF-040` |

---

## 11. Evidence Receipt States (`evidence-receipt-generator`)

```text
VALID_RECEIPT ≠ VERIFIED_CLAIMS
Receipt R1 (historical state at S1) ──[mutation]──► Receipt R2 (previous_receipt_id = R1)
```

| Dimension | Allowed Values | Governing Invariant |
|---|---|---|
| **1. Missing Evidence Status** | `NOT_OBSERVED`, `NOT_CHECKED`, `NOT_OBSERVABLE`, `NOT_FOUND`, `NOT_EXECUTED`, `UNKNOWN`, `MISSING_EVIDENCE` | `AIF-008`, `AIF-019` (never collapsed into a generic `null`) |
| **2. `EvidenceCoverage.adequacy`** | `SUFFICIENT`, `PARTIAL`, `INSUFFICIENT`, `MISMATCH`, `IRRELEVANT`, `CONTRADICTED`, `UNKNOWN` | `AIF-007`, `AIF-045` |
| **3. Receipt Validation vs Claim Verification** | `RECEIPT_VALID` / `RECEIPT_INVALID` vs `CLAIMS_VERIFIED` / `CLAIMS_UNVERIFIED` / `CONTRADICTED` | `AIF-043`, `AIF-044` (`VALID_RECEIPT != VERIFIED_CLAIMS`) |
| **4. Receipt Lifecycle** | `EVIDENCE_RECEIPT_ONLY` (`completion_result` omitted) $\to$ `DERIVED_COMPLETION_RECEIPT` (`previous_receipt_id` bound) | `AIF-041`, `AIF-042`, `AIF-048` |

---

## 12. Completion Gate States (`arena-completion-gate`)

```text
COMPLETE(R, A) iff Evaluate(A, VerifiedClaims(R)) = SATISFIED
COMPLETABLE ≠ COMPLETED (ACCEPT / RELEASE / MERGE / DEPLOY require separate execution authority)
```

| State | Meaning | Governing Rules |
|---|---|---|
| `COMPLETABLE` | The supplied `ArenaEvidenceReceipt` satisfies the declared `AcceptanceExpression` at `evaluated_snapshot` | All required claims `VERIFIED` at matching snapshot & scope (`COMPLETE-01`) |
| `INCOMPLETE` | Evidence is valid, but one or more required claims remain unsatisfied (`PARTIAL`, `UNKNOWN`, `NOT_OBSERVABLE`, `STALE`, `MISMATCH`, `UNVERIFIED`) | `UNKNOWN` is preserved in `unknowns[]`, never coerced to `false` (`COMPLETE-02`, `COMPLETE-04`–`09`) |
| `BLOCKED` | External prerequisite or authority gate prevents evaluating or satisfying a required condition | Preserves `blockers[]` (`COMPLETE-10` under blocking gate policy) |
| `CONTRADICTED` | Evidence contains unresolved contradiction (`CLAIM = CONTRADICTED`) relevant to a required claim | Preserves `contradictions[]` (`COMPLETE-03`, `P-COMP-03`) |
| `INVALID` | The input `ArenaEvidenceReceipt` violates structural, referential, semantic, or digest integrity | Validated prior to evaluation |
| `ACCEPTANCE_UNSPECIFIED` | Request did not declare an explicit `AcceptanceExpression` | Never fabricates acceptance criteria (`10.4`) |

---

## 13. Skill Evaluation Harness States (`skill-evaluation-harness`)

```text
COMPLETION GATE asks:         "Is this task complete?"
SKILL EVALUATION HARNESS asks: "Does this skill behave correctly?"
NOT_OBSERVABLE ≠ PASS
total_cases ≠ quality_score
```

| Dimension / Object | Allowed Values | Governing Invariants |
|---|---|---|
| **1. `EvaluationCase.category`** | `RED`, `GREEN`, `PRESSURE`, `REGRESSION` | `AIF-049`, `AIF-051`, `AIF-053` |
| **2. `EvaluationResult.status`** | `PASS`, `FAIL`, `ERROR`, `BLOCKED`, `NOT_OBSERVABLE` | `AIF-049`, `AIF-055` (`NOT_OBSERVABLE != PASS`; vacuous execution is `FAIL`) |
| **3. Oracle Evaluation Levels** | `LEVEL_1_STRUCTURAL`, `LEVEL_2_SEMANTIC`, `LEVEL_3_EVIDENCE`, `LEVEL_4_BEHAVIORAL` | `AIF-050` (`Level 1` alone never establishes strong behavioral evaluation) |
| **4. `EvaluationSuiteResult.regression_status`** | `BASELINE_MATCH`, `NEW_FAILURE`, `IMPROVED`, `CORPUS_MODIFIED`, `ORACLE_MODIFIED`, `NO_BASELINE` | `AIF-051`, `AIF-052` |
| **5. `TriggerEvaluation`** | `SHOULD_TRIGGER` vs `SHOULD_NOT_TRIGGER`; `false_positive`, `false_negative`, `interpreted_scope`, `interpreted_authority` | `AIF-054` |
| **6. Phase 12 Interface Freeze Boundary** | `ONLY arena-intake-and-authority may establish authority`; `ONLY arena-completion-gate may evaluate completion` | `AIF-001`, `AIF-027`, `AIF-048` |








