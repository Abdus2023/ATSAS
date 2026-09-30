# AIF-0.1 Normative Invariants (`invariants.md`)

- **Document Class**: `NORMATIVE`
- **Protocol Family**: `AIF-0.1`
- **Concrete Frozen Version**: `0.1.0` ([`VERSION`](./VERSION))
- **Status**: `FROZEN AIF-0.1.0 KERNEL CONTRACT`

```text
Primary invariants:
    AIF-001 .. AIF-055

Sub-invariants:
    explicitly enumerated A-suffixed identifiers
    currently:
      AIF-001A
      AIF-002A
      AIF-003A
      AIF-004A
      AIF-005A
      AIF-006A
      AIF-008A
      AIF-014A
```

---

## 1. The 7 Invariant Families (`AIF-001` .. `AIF-055`)

| Family | IDs | Purpose |
|---|---|---|
| **Core** | `001–020` | Fundamental AIF semantics (reality, authority, snapshot, execution, evidence, verification, completion) |
| **Authority / attribution** | `021–025` | Who may act and what can be attributed (`arena-intake-and-authority`, `agent-change-scope-audit`) |
| **Evidence producers** | `026–028` | Producer monotonicity, independence, and CI subject binding (`ci-workflow-audit`, adapters) |
| **Test execution** | `029–033` | What test execution can establish (`test-execution-and-evidence-audit`) |
| **Supply chain** | `034–040` | Dependency provenance and uncertainty (`dependency-supply-chain-audit`) |
| **Receipts** | `041–048` | Durable evidence and completion separation (`evidence-receipt-generator`, `arena-completion-gate`) |
| **Evaluation** | `049–055` | Assurance of the evaluator itself (`skill-evaluation-harness`) |

---

## 2. Normative Invariant Definitions (`AIF-001` .. `AIF-055` + Enumerated Sub-Invariants)

### `AIF-001` — Authority Precedes Mutation (Reality-Preserving Rule)
- **Rule**: Legitimate mutation requires prior `ADMITTED` status in `AdmissionRecord` backed by an `AUTHORIZED` `AuthorityEvent`. Because unauthorized execution can occur in reality, `EXECUTED(action)` never implies `AUTHORIZED(action)`:
  $$\text{EXECUTED}(\text{action}) \land \text{NOT\_AUTHORIZED}(\text{action}) \implies \text{AUTHORITY\_VIOLATION}$$
  The evidence model must record `execution occurred + authorization absent` as a violation (`BLOCKED`) without rewriting history.
- **Sub-Invariant `AIF-001A` (Temporal Authority Validity)**: Every `ExecutionRecord` must fall within `[effective_from, expires_at]` of its governing `AuthorityEvent`; expired or revoked authority yields `EXPIRED` / `BLOCKED`.
- **Behavioral Tests**: `RED-001`, `RED-002`, `RED-004`, `P-08`, `TEST AIF-001-01`, `TEST AIF-001A-01`.

### `AIF-002` — Snapshot Identity Is Mandatory
- **Rule**: Every `ExecutionRecord`, `EvidenceRef`, `VerificationRecord`, and `Finding` must bind to an explicit `SnapshotRef` (`commit`, `working_tree_state`, `index_state`, `content_digest`, `metadata_digest`).
- **Sub-Invariant `AIF-002A` (Working-Tree & Index State Identity)**: Two snapshots with the same `commit` but different `working_tree_state`, `index_state`, or `content_digest` are distinct states; `snapshot_match = true` across them is forbidden.
- **Behavioral Tests**: `RED-005`, `RED-006`, `RED-008`, `P-02`, `P-04`, `TEST AIF-002-01`, `TEST AIF-002A-01`.

### `AIF-003` — Scope & Provenance Confinement
- **Rule**: `AdmissionRecord` freezes `admitted_actions`, `admitted_paths`, and `excluded_paths`. Any modified, added, deleted, or generated path outside `admitted_paths` or matching `excluded_paths` is an `OUT_OF_SCOPE CHANGE` (`SCOPE_VIOLATION` -> `BLOCKED`).
- **Sub-Invariant `AIF-003A` (State Change != Actor Attribution)**: `DIFF(S0, S1)` proves state change, not actor attribution. Attributing a change as `AGENT_ATTRIBUTED` with `attribution_basis = "diff_only"` is forbidden.
- **Behavioral Tests**: `RED-003`, `RED-005`, `RED-006`, `RED-007`, `RED-008`, `RED-032`, `P-04`, `P-08`, `TEST AIF-003-01`, `TEST AIF-003A-01`.

### `AIF-004` — Declaration != Execution
- **Rule**: The existence of a workflow file, test script, or configuration file (`STATIC_CONFIG`) never establishes `ExecutionState = EXECUTED` or `VerificationState = VERIFIED`.
- **Sub-Invariant `AIF-004A` (Process Launch Requires Output Provenance)**: `ExecutionState = EXECUTED` requires valid process result and output reference (`stdout_ref` or `stderr_ref`).
- **Behavioral Tests**: `RED-002`, `RED-018`, `RED-019`, `P-03`, `TEST AIF-004-01`, `TEST AIF-004A-01`.

### `AIF-005` — Execution != Success
- **Rule**: Process completion (`EXECUTED`), timeout (`INTERRUPTED`), or non-zero exit (`FAILED`, `exit_code != 0`) must never be classified as `TEST_PASSED` or `VERIFIED`.
- **Sub-Invariant `AIF-005A` (Zero-Test Vacuous Pass Prohibition)**: `exit_code == 0` with `ZERO_TESTS_DISCOVERED` is vacuous and cannot verify a test-execution claim.
- **Behavioral Tests**: `RED-024`, `RED-025`, `P-03`, `TEST AIF-005-01`, `TEST AIF-005A-01`.

### `AIF-006` — Success != Verification
- **Rule**: A successful process exit (`EXITED_ZERO`) whose `semantic_result` is `IRRELEVANT_TO_CLAIM` or `PARTIAL` cannot produce `VerificationState = VERIFIED`.
- **Sub-Invariant `AIF-006A` (Relational Verification Binding)**: Every `VerificationRecord` must reference an existing `claim_id` and `subject_snapshot` (`VERIFY(C1, S1)`).
- **Behavioral Tests**: `RED-022`, `RED-026`, `RED-029`, `P-01`, `TEST AIF-006-01`, `TEST AIF-006A-01`.

### `AIF-007` — Evidence Is Bounded by Subject, Scope, Snapshot, and Method
- **Rule**: A claim can be `VERIFIED` only if covered by `SUFFICIENT` `EvidenceCoverage` matching `subject_match`, `snapshot_match`, `scope_match`, and `method_match`.
- **Behavioral Tests**: `RED-009`, `RED-010`, `RED-016`, `RED-017`, `RED-021`, `RED-027`, `RED-030`, `P-06`, `TEST AIF-007-01`.

### `AIF-008` — Unknown & Unobservable Preservation (`UNKNOWN != PASS`)
- **Rule**: `UNKNOWN`, `NOT_CHECKED`, and `NOT_OBSERVABLE` must be preserved explicitly and never coerced into `VERIFIED` or `COMPLETABLE`.
- **Sub-Invariant `AIF-008A` (Detector Skip / Unavailability)**: When a scanner or verifier is unavailable or skips targets, coverage is incomplete (`PARTIAL` / `NOT_OBSERVABLE`), never `"0 findings"` or `"VERIFIED"`.
- **Behavioral Tests**: `RED-013`, `RED-019`, `P-03`, `P-06`, `TEST AIF-008-01`, `TEST AIF-008A-01`.

### `AIF-009` — Declarative Acceptance Expression Evaluation
- **Rule**: `CompletionResult.status = COMPLETABLE` is permitted if and only if `AcceptanceExpression` (`ALL`, `ANY`, `AT_LEAST_N`, `OPTIONAL`, `CONDITIONAL`, `CLAIM`) evaluates to satisfied over current `VerificationRecord`s.
- **Behavioral Tests**: `RED-031`, `RED-034`, `P-05`, `TEST AIF-009-01`.

### `AIF-010` — Audit != Remediation
- **Rule**: An audit or detector skill operating under read-only authority must follow `AUDIT FINDING -> REPORT -> STOP / NEW REQUEST`. Autonomous self-remediation (`remediation_authorized = true` without a new mutation `AuthorityEvent`) is forbidden.
- **Behavioral Tests**: `P-02`, `TEST AIF-010-01`.

### `AIF-011` — Independent Criterion Evidence
- **Rule**: Evidence satisfying one criterion (e.g., local unit tests) cannot substitute for an independent required criterion with a different `method` (e.g., remote CI execution).
- **Behavioral Tests**: `RED-034`, `P-07`, `TEST AIF-011-01`.

### `AIF-012` — Detector Finding != Completion Judgment
- **Rule**: Detectors emit `Finding` and `EvidenceRef` records; a detector may never emit a completion judgment (`COMPLETABLE` / `COMPLETED`) as a finding category.
- **Behavioral Tests**: `RED-030`, `P-06`, `TEST AIF-012-01`.

### `AIF-013` — Completion Gate Cannot Manufacture Evidence
- **Rule**: A `VERIFIED` claim requires non-empty `required_evidence` and `EvidenceCoverage`. The completion gate cannot mark a claim `VERIFIED` with empty evidence.
- **Behavioral Tests**: `RED-022`, `RED-027`, `P-01`, `TEST AIF-013-01`.

### `AIF-014` — Mutation Invalidates Intersecting Evidence
- **Rule**: Any mutation between `S1` and `S2` invalidates (`STALE`) prior snapshot-dependent evidence unless non-intersection is proven.
- **Sub-Invariant `AIF-014A` (Non-Intersection Proof Requirement)**: `freshness = NON_INTERSECTING_CHANGE` is forbidden when any `ChangeRecord` path intersects the claim's subject or scope.
- **Behavioral Tests**: `RED-020`, `RED-023`, `RED-028`, `RED-033`, `P-04`, `TEST AIF-014-01`, `TEST AIF-014A-01`.

### `AIF-015` — Subject & Snapshot Compatibility
- **Rule**: `EvidenceCoverage` with `subject_match = false` or `snapshot_match = false` cannot support a `VERIFIED` claim.
- **Behavioral Tests**: `RED-011`, `RED-028`, `P-04`, `TEST AIF-015-01`.

### `AIF-016` — Normalization Cannot Broaden Claims
- **Rule**: Receipt normalization must preserve detector scope and limitations; broadening a pattern scan into universal absence (`"The repository contains no secrets"`) is forbidden.
- **Behavioral Tests**: `RED-012`, `RED-030`, `P-06`, `TEST AIF-016-01`.

### `AIF-017` — Contradiction Preservation (`RED-035`)
- **Rule**: When evidence `E1` reports `CLEAN` and independent evidence `E2` reports `FINDING` (`CONTRADICTORY`) on the same subject, snapshot, and claim scope, both `EvidenceRef`s must be retained and verification must be `CONTRADICTED` (never `VERIFIED`).
- **Behavioral Tests**: `RED-014`, `RED-015`, `RED-035`, `TEST AIF-017-01`.

### `AIF-018` — Skill Assertions != Evidence
- **Rule**: An `EvidenceRef` with `source_type = "SKILL_OUTPUT"` and empty primary `provenance[]` is invalid.
- **Behavioral Tests**: `RED-022`, `P-01`, `TEST AIF-018-01`.

### `AIF-019` — Missing Evidence Remains Explicit
- **Rule**: Every claim referenced by `AcceptanceExpression` must exist in `claims[]`, and any unmet requirement or unknown must be explicitly listed in `CompletionResult.unmet_requirements` / `unknowns`.
- **Behavioral Tests**: `RED-034`, `P-03`, `P-05`, `TEST AIF-019-01`.

### `AIF-020` — Receipt Reproducibility (`RED-036`)
- **Rule**: Given receipt `R`, acceptance expression `A`, evidence `E`, and claims `C`, completion evaluation is a pure deterministic function:
  $$\text{Evaluate}(R) = \text{Evaluate}(R)$$
  A result that changes without an input change is a `REPRODUCIBILITY VIOLATION`.
- **Behavioral Tests**: `RED-036`, `P-04`, `P-05`, `P-07`, `TEST AIF-020-01`.

### `AIF-021` — No Retroactive Authorization
- **Rule**: Authorization created at $T_2$ cannot retroactively authorize an action executed at $T_1$:
  $$\text{EXECUTED}(a, T_1) \land \text{AUTHORIZED}(a, T_2) \land T_2 > T_1 \implies \text{the } T_2 \text{ authority does not authorize the } T_1 \text{ execution}$$
  If an `ExecutionRecord` has `started_at < AuthorityEvent.issued_at` (or `< AuthorityEvent.effective_from`), the execution remains unauthorized (`AUTHORITY_VIOLATION` / `BLOCKED`) and the receipt must preserve the temporal distinction.
- **Behavioral Tests**: `A-01`, `TEST AIF-021-01`.

### `AIF-022` — Authority Is Non-Transitive by Default
- **Rule**: Authority is evaluated over the 4-dimensional lattice $\text{AUTHORIZED}(\text{action}, \text{path}, \text{actor}, \text{time})$ and is non-transitive by default across both actors and actions:
  - **Actor non-transitivity**: If `Agent A` is authorized to `MODIFY src/**`, that does not authorize `Agent B` to perform the same action.
  - **Action non-transitivity**: `READ` / `LIST` / `SEARCH` (`inspect`) does not imply `MODIFY` / `CREATE` / `DELETE` / `RENAME`; `MODIFY` does not imply `COMMIT`, `PUSH`, or `RELEASE`; `EXECUTE` (`run_tests`) does not imply authority to modify `test/**` files unless explicitly granted.
- **Behavioral Tests**: `RED-002`, `A-04`, `A-06`, `A-07`, `TEST AIF-022-01`.

### `AIF-023` — Attribution Is Evidence-Dependent
- **Rule**: `AGENT_ATTRIBUTED(change)` requires attribution evidence sufficient for that claim (such as an `ExecutionRecord` targeting the path plus snapshot diff `DIFF(S0, S1)`). A state transition `DIFF(S0, S1)` alone establishes `STATE_CHANGE` (`OBSERVED`), never `AGENT_ATTRIBUTED_CHANGE`:
  $$\text{STATE\_CHANGE} \neq \text{AGENT\_CHANGE} \neq \text{AUTHORIZED\_CHANGE}$$
  $$\text{UNAUTHORIZED\_AGENT\_CHANGE} \iff \text{AGENT\_ATTRIBUTED\_CHANGE} \land \neg \text{IN\_AUTHORIZED\_SCOPE}$$
- **Behavioral Tests**: `RED-006`, `RED-007`, `RED-037`, `RED-039`, `RED-040`, `TEST AIF-023-01`.

### `AIF-024` — Pre-Existing State Must Not Become Agent Responsibility
- **Rule**: If a file modification or untracked state exists at `intake_snapshot` (`S0`) and is unchanged during `S0 -> S1` (or lacks evidence of subsequent agent modification), the scope audit must preserve `attribution = PREEXISTING` and must never classify the pre-existing state as `AGENT_ATTRIBUTED` or `UNAUTHORIZED_AGENT_CHANGE`.
- **Behavioral Tests**: `RED-006`, `RED-038`, `P-04`, `TEST AIF-024-01`.

### `AIF-025` — Scope Audit Is Snapshot-Relative
- **Rule**: Every scope audit and `ChangeRecord` must explicitly identify its snapshot comparison (`S0 -> S1`). A later transition (`S1 -> S2`) is a distinct observation; a scope audit produced against `S1` is `STALE` when the current repository is at `S2` and must never be used to verify `S2`.
- **Behavioral Tests**: `RED-020`, `RED-028`, `RED-041`, `P-04`, `TEST AIF-025-01`.

### `AIF-026` — Evidence Monotonicity
- **Rule**: An evidence producer adapter MUST NOT produce or verify a claim stronger than the claim supported by its source evidence:
  $$\text{Strength}(\text{Adapter}(E)) \le \text{Strength}(E)$$
  For example, `"No matches in scanned files"` may support `"No configured secret-pattern matches exist in the scanned paths"` (`VERIFIED`), but must never verify `"No secrets exist anywhere in the repository"` (`UNVERIFIED`), and `"npm run typecheck exited 0"` must never verify `"The implementation is correct"`.
- **Behavioral Tests**: `RED-012`, `RED-030`, `ADP-01`, `ADP-10`, `ADP-11`, `ADP-14`, `TEST AIF-026-01`.

### `AIF-027` — Producer Independence
- **Rule**: An evidence producer must never declare itself sufficient for a task completion criterion or emit a completion decision (`authority: false`, `admission: false`, `completion: false`):
  $$\text{Producer} \to \text{Evidence} \to \text{Claim Coverage} \to \text{AcceptanceExpression} \to \text{Completion Gate}$$
  Never $\text{Producer} \to \text{PASS} \to \text{DONE}$.
- **Behavioral Tests**: `RED-022`, `RED-030`, `ADP-12`, `TEST AIF-027-01`.

### `AIF-028` — CI Subject Binding
- **Rule**: A CI execution result may satisfy a claim only when the execution subject (`commit_sha` / `subject_snapshot` and artifact `run_id`) matches the claim's required snapshot, or an explicitly defined equivalent subject relation is proven:
  $$\text{VERIFY}(C, \text{CI\_E}) \implies \text{Subject}(C) \equiv \text{Subject}(\text{CI\_E})$$
  `CI_RUN = SUCCESS` on commit `A` while current `HEAD = B` yields `CLAIM(B) = UNVERIFIED` (`CI_SNAPSHOT_MISMATCH` / `STALE`), never `CI = PASS`.
- **Behavioral Tests**: `RED-020`, `CI-04`, `CI-05`, `CI-12`, `CI-13`, `CI-19`, `CI-20`, `TEST AIF-028-01`.

### `AIF-029` — Execution Evidence
- **Rule**: A test-pass claim requires evidence (`TestExecutionRecord` + output provenance) that the relevant tests actually executed (`PASS_CLAIM ⇒ EXECUTION_OBSERVED`). Process exit code `0` alone (`PROCESS_SUCCESS`), masked commands (`|| true`), or zero-test runs (`discovered == 0` / `executed == 0`) never establish `TEST_SUCCESS`.
- **Behavioral Tests**: `RED-022`, `RED-024`, `RED-025`, `TEST-01`, `TEST-05`, `P-TEST-01`, `P-TEST-03`, `TEST AIF-029-01`.

### `AIF-030` — Discovery Completeness
- **Rule**: A complete test-set claim requires evidence (`TestDiscoveryEvidence` / `discovery.discovered` vs required set) sufficient to establish the required test set (`ALL_REQUIRED_TESTS ⇒ DISCOVERY_COVERAGE_SUFFICIENT`). If discovery is `UNKNOWN` or required tests are absent/excluded, adequacy is `PARTIAL` or `INCOMPLETE`, never `SUFFICIENT`.
- **Behavioral Tests**: `TEST-02`, `TEST-03`, `TEST-08`, `TEST-19`, `TEST AIF-030-01`.

### `AIF-031` — Test Snapshot Binding
- **Rule**: Test evidence is valid only for its recorded `subject_snapshot` or an explicitly defined compatible subject (`TEST(S0) = PASS ∧ SOURCE(S0→S1) = changed ⇒ TEST(S1) = UNVERIFIED / STALE`).
- **Behavioral Tests**: `RED-027`, `TEST-06`, `TEST-07`, `P-TEST-04`, `TEST AIF-031-01`.

### `AIF-032` — Test Scope Preservation
- **Rule**: Passing a selected subset (`discovered = 100, selected = 20, executed = 20` or filtered `include = test/changed-feature.test.ts`) establishes a selected-set claim only (`COMPLETED + PASS + PARTIAL + MATCH`) and cannot satisfy a claim about a larger required test set.
- **Behavioral Tests**: `RED-026`, `TEST-02`, `TEST-08`, `TEST-09`, `TEST-10`, `TEST AIF-032-01`.

### `AIF-033` — Test Result Non-Transitivity
- **Rule**: Distinct verification levels are non-transitive (`TYPECHECK_PASS ≠ UNIT_TEST_PASS`, `UNIT_TEST_PASS ≠ INTEGRATION_TEST_PASS`, `TEST_PASS ≠ IMPLEMENTATION_CORRECT`). Each requires its own bounded claim and corresponding evidence.
- **Behavioral Tests**: `RED-030`, `TEST-18`, `TEST-19`, `TEST AIF-033-01`.

### `AIF-034` — Declaration/Resolution Separation
- **Rule**: Declaring a dependency in a manifest does not establish how or whether it was resolved (`DECLARED(dependency) ≠ RESOLVED(dependency)`).
- **Behavioral Tests**: `DEP-SC-01`, `DEP-SC-03`, `P-DEP-05`, `TEST AIF-034-01`.

### `AIF-035` — Resolution/Installation Separation
- **Rule**: Resolving a dependency in a lockfile does not establish that an installation command actually executed (`RESOLVED(dependency) ≠ INSTALLED(dependency)`).
- **Behavioral Tests**: `DEP-SC-02`, `TEST AIF-035-01`.

### `AIF-036` — Installation/Build Separation
- **Rule**: Installing dependencies does not establish that a build executed or consumed those dependencies (`INSTALLED(dependency) ≠ USED_IN_BUILD(dependency)`).
- **Behavioral Tests**: `DEP-SC-02`, `DEP-SC-10`, `TEST AIF-036-01`.

### `AIF-037` — Artifact Provenance
- **Rule**: Any claim concerning build provenance or artifact origin requires proven build origin (`ARTIFACT_CLAIM requires PROVEN_BUILD_ORIGIN` via `ArtifactRecord` $\to$ `BuildRecord` $\to$ `ResolutionRecord` $\to$ `LockfileRecord` $\to$ `DependencyManifestRecord`). Observing `dist/app.js` alone establishes `ARTIFACT_OBSERVED` with `BUILD_PROVENANCE = UNKNOWN`.
- **Behavioral Tests**: `DEP-SC-09`, `DEP-SC-10`, `TEST AIF-037-01`.

### `AIF-038` — Vulnerability Scope
- **Rule**: A vulnerability audit result (`VULNERABILITY_AUDIT_RESULT`) may satisfy only claims within its declared vulnerability-audit scope; it cannot satisfy a general supply-chain-trust claim (`NO_KNOWN_VULNERABILITIES ≠ SUPPLY_CHAIN_ESTABLISHED`, `LOCKFILE_MISSING ≠ VULNERABLE`, `AUDIT_UNAVAILABLE ≠ AUDIT_PASSED`).
- **Behavioral Tests**: `DEP-SC-01`, `DEP-SC-04`, `DEP-SC-05`, `P-DEP-01`, `TEST AIF-038-01`.

### `AIF-039` — Supply-Chain Unknown Preservation
- **Rule**: Any unobservable supply-chain stage must remain `UNKNOWN` (`UNOBSERVABLE(stage) ⇒ UNKNOWN(stage)`) unless independent evidence establishes the state (e.g., `source_type = UNKNOWN` must never be inferred as `REGISTRY` / `PUBLIC_REGISTRY`).
- **Behavioral Tests**: `DEP-SC-05`, `DEP-SC-06`, `DEP-SC-09`, `TEST AIF-039-01`.

### `AIF-040` — Resolution Snapshot Binding
- **Rule**: A dependency-resolution result may satisfy a claim only when its manifest/lockfile subject matches the required snapshot (`S1` resolution cannot silently certify an `S2` build after dependency mutation).
- **Behavioral Tests**: `DEP-SC-10`, `P-DEP-04`, `TEST AIF-040-01`.

### `AIF-041` — Receipt Immutability
- **Rule**: A receipt describes a historical evidence state (`Receipt R1`) and must not be mutated in place to represent a later repository state; new observations or mutations require generating a new receipt (`Receipt R2` with `previous_receipt_id = R1.receipt_id`).
- **Behavioral Tests**: `RECEIPT-10`, `P-REC-07`, `TEST AIF-041-01`.

### `AIF-042` — Receipt Determinism
- **Rule**: Equivalent canonical inputs must produce an identical `receipt_id` via RFC 8785 (JCS) canonicalization and SHA-256 (`Generate(R_inputs) == Generate(R_inputs)`).
- **Behavioral Tests**: `RED-036`, `RECEIPT-05`, `P-REC-07`, `TEST AIF-042-01`.

### `AIF-043` — Evidence Referential Integrity
- **Rule**: Every `evidence_id`, `claim_id`, `snapshot_id`, and `execution_id` referenced by a `VerificationRecord` or `EvidenceCoverage` entry in a receipt must resolve to an identifiable object with a non-empty `source_locator` and matching `content_digest`.
- **Behavioral Tests**: `RECEIPT-01`, `RECEIPT-07`, `RECEIPT-08`, `TEST AIF-043-01`.

### `AIF-044` — Receipt Validation Non-Transitivity
- **Rule**: Structural, referential, and hash validity of a receipt does not imply that its claims are verified (`VALID_RECEIPT ≠ VERIFIED_CLAIMS`).
- **Behavioral Tests**: `RECEIPT-09`, `RECEIPT-12`, `P-REC-01`, `TEST AIF-044-01`.

### `AIF-045` — Normalization Non-Expansion
- **Rule**: Normalized evidence propositions in a receipt cannot possess broader semantic scope than their source observation (`SOURCE CLAIM → NORMALIZED CLAIM` must preserve or narrow scope).
- **Behavioral Tests**: `RED-012`, `RECEIPT-03`, `RECEIPT-11`, `P-REC-02`, `P-REC-06`, `TEST AIF-045-01`.

### `AIF-046` — Contradiction Preservation
- **Rule**: Conflicting evidence items (`E1`, `E2`, `E3`) cannot be silently discarded or overwritten in a receipt merely to obtain a clean verification result; all conflicting `evidence_refs` must be retained with `result = CONTRADICTED`.
- **Behavioral Tests**: `RED-014`, `RED-035`, `RECEIPT-04`, `P-REC-05`, `TEST AIF-046-01`.

### `AIF-047` — Historical Snapshot Preservation
- **Rule**: Every `EvidenceRef` in a receipt retains the historical `subject_snapshot` against which it was actually captured; old evidence must never be rebound to a newer snapshot ID.
- **Behavioral Tests**: `RECEIPT-02`, `RECEIPT-10`, `P-REC-04`, `TEST AIF-047-01`.

### `AIF-048` — Completion Separation
- **Rule**: Receipt generation (`evidence-receipt-generator`) assembles, normalizes, and links evidence and coverage; it cannot itself authorize, admit, or complete a request (`completion_result` is optional at the receipt layer and produced only by `arena-completion-gate`).
- **Behavioral Tests**: `RECEIPT-06`, `P-REC-03`, `TEST AIF-048-01`.

### `AIF-049` — Test Execution Evidence
- **Rule**: An evaluation case (`EvaluationCase`) cannot pass (`status = PASS`) merely because the expected output was assumed; required execution and raw observation must actually be observed.
- **Behavioral Tests**: `RED-022`, `P-TEST-01`, `EVAL-01`, `TEST AIF-049-01`.

### `AIF-050` — Oracle Independence
- **Rule**: The evaluation oracle (`compare_result.py`) must evaluate structured semantics against an independent case oracle contract and must never derive expected truth from the skill's own output.
- **Behavioral Tests**: `EVAL-02`, `TEST AIF-050-01`.

### `AIF-051` — Corpus Integrity
- **Rule**: Evaluation results and baselines (`EvaluationBaseline`) are cryptographically bound to the exact content-addressed case corpus (`case_corpus_digest = sha256(JCS(corpus))`) and oracle (`oracle_digest`) used; modifying a test case's expected result to make a failing skill pass invalidates the baseline.
- **Behavioral Tests**: `EVAL-03`, `TEST AIF-051-01`.

### `AIF-052` — Regression Reproducibility
- **Rule**: Identical skill snapshot + identical `case_corpus_digest` + identical `oracle_digest` + identical `evaluator_version` must produce equivalent `EvaluationSuiteResult` classifications (`EvaluateSuite(B) == EvaluateSuite(B)`).
- **Behavioral Tests**: `EVAL-04`, `TEST AIF-052-01`.

### `AIF-053` — Mutation Sensitivity
- **Rule**: Critical invariant test suites must detect designated contract-breaking mutations (such as coercing `UNKNOWN -> PASS` or removing snapshot mismatch checks).
- **Behavioral Tests**: `EVAL-05`, `RED-020`, `RED-028`, `RED-041`, `TEST-07`, `COMPLETE-06`, `TEST AIF-053-01`.

### `AIF-054` — Trigger Correctness
- **Rule**: Skill evaluation (`TriggerEvaluation`) must distinguish appropriate activation (`SHOULD TRIGGER`) from inappropriate activation (`SHOULD NOT TRIGGER`) as well as trigger pressure (`INSPECT_ONLY` vs verification/mutation authority).
- **Behavioral Tests**: `EVAL-06`, `TEST AIF-054-01`.

### `AIF-055` — Test Non-Vacuity
- **Rule**: A test case cannot pass (`PASS`) when its required behavior was never exercised or observed (`PASS` requires `required_execution_occurred AND required_observation_produced AND oracle_matched`; `NOT_OBSERVABLE ≠ PASS`).
- **Behavioral Tests**: `EVAL-07`, `TEST AIF-055-01`.









