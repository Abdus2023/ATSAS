# Phase 15 — Adversarial Gap Review & Phase 15.1 Evaluator Attack Corpus (`EVAL-A049`..`EVAL-A055`)

```text
Document Class: HISTORICAL / EVIDENCE
Protocol: AIF-0.1.0
Evaluated Branch: arena/01a0ecca-atsas
Prior Baseline Commit: 059856dfba9bebee291c360e1d18f1621b3f724a
Currentness: CURRENT BRANCH EVIDENCE (Phase 15 Adversarial Gap Review & Phase 15.1 Evaluator Attack Corpus)
```

---

## 1. Purpose of Phase 15 — Attacking the Evaluator as an Untrusted Component

Phase 13 (Normalization) and Phase 14 (Execution) established that the 63 normative rules (`55` primary invariants `AIF-001..AIF-055` + `8` explicitly enumerated sub-invariants `AIF-001A, 002A, 003A, 004A, 005A, 006A, 008A, 014A`) are present, cross-referenced, and executed.

Phase 15 attacks the deeper adversarial boundary:

```text
"The repository contains a test for the invariant"
                        ≠
"The invariant is actually behaviorally tested."
```

Specifically: **Does the evaluator fail when the evaluator itself is wrong?**

---

## 2. Resolution of Phase 15 Findings A–J (`15.1`–`15.10`)

### 2.1 Finding A (`15.1`) — `AIF-049..055` Behavioral Upgrade & Phase 15.1 Attack Corpus (`EVAL-A049`..`EVAL-A055`)

Previously, `mut_aif_034`..`mut_aif_055` in [`tests/aif-v01-red-suite.py`](../../tests/aif-v01-red-suite.py) injected textual violation phrases into `claim_scope`, proving that [`bin/aif-verify`](../../bin/aif-verify) recognized constructed violation markers rather than proving that the evaluation system detects the real underlying failure when `claim_scope` is clean.

**Remediation**:
1. Built the **7 executable adversarial fixtures `EVAL-A049` .. `EVAL-A055`** in [`.claude/skills/skill-evaluation-harness/scripts/run_suite.py`](../skills/skill-evaluation-harness/scripts/run_suite.py) (`run_evaluator_attack_corpus()`) and [`.claude/skills/skill-evaluation-harness/scripts/compare_result.py`](../skills/skill-evaluation-harness/scripts/compare_result.py).
2. Upgraded [`bin/aif-verify`](../../bin/aif-verify) (`validate_canonical_data_model_bundle`) and [`tests/aif-v01-red-suite.py`](../../tests/aif-v01-red-suite.py) (`mut_aif_034`..`mut_aif_055`) so every mutator mutates structured behavioral state (`supply_chain_state`, `receipt_state`, `evaluation_harness_state`) without touching `claim_scope`.

| Fixture ID | Invariant | Known-Good Baseline (`15.1.1`) | Controlled Defect Attack (`15.1.3`–`15.1.9`) $\to$ Observed Failure $\to$ Oracle Classification | Assurance Profile (`15.1.12`) | Status |
|---|---|---|---|---|---|
| **`EVAL-A049`** | `AIF-049` | `expected=PASS, execution=COMPLETED, observation=present -> PASS` | **Stage 2A (Fake execution, `15.1.3`)**: `expected=PASS, execution=NOT_STARTED, observation=present` (output still looks correct) $\to$ `status=FAIL != PASS`, `AIF-049 (NO_EXECUTION_EVIDENCE)`. **Stage 2B (Missing observation)**: `observation_produced=False, observed_evidence=[]` $\to$ `status=FAIL`, `AIF-049` | `BEHAVIORAL + ADVERSARIAL` | `VERIFIED` |
| **`EVAL-A050`** | `AIF-050` | **Fixture B1**: `skill_output=NOT_VERIFIED, independent_expected=NOT_VERIFIED (RED-22) -> oracle=PASS` | **Fixture A (`15.1.4`)**: `skill_output=PASS, independent_expected=FAIL -> oracle=FAIL`. **Fixture B2**: `skill_output=FAIL, independent_expected=PASS -> oracle=FAIL` (expected truth preserved). **Circular Attack**: `Oracle(skill_output, skill_output)` $\to$ `FAIL` (`AIF-050 ORACLE_INDEPENDENCE_VIOLATION`) | `BEHAVIORAL + ADVERSARIAL` | `VERIFIED` |
| **`EVAL-A051`** | `AIF-051` | `D1, O1, V1, S1 -> BASELINE_MATCH` | **All 4 Baseline Binding Attacks (`15.1.5`)**: 1) Case modified `D1 -> D2` $\to$ `CORPUS_MODIFIED`; 2) `O1 -> O2` $\to$ `ORACLE_MODIFIED`; 3) `V1 -> V2` $\to$ `EVALUATOR_MODIFIED`; 4) `S1 -> S2` $\to$ `SKILL_SNAPSHOT_MODIFIED`; 5) `cases.yaml` count tamper $\to$ `CORPUS_INTEGRITY_ERROR` | `BEHAVIORAL + ADVERSARIAL` | `VERIFIED` |
| **`EVAL-A052`** | `AIF-052` | `R1 = evaluate(S,C,O,V)` vs `R2 = evaluate(S,C,O,V, shuffle_seed=42, generated_at=different)` $\to$ `canonical(R1) == canonical(R2)` (`REPRODUCIBLE`, timestamp excluded per `15.1.6`) | **Controlled Defect**: Perturb semantic case result in `R2` $\to$ `verify_replay_determinism` reports `NON_REPRODUCIBLE` (`AIF-052`) | `BEHAVIORAL + ADVERSARIAL` | `VERIFIED` |
| **`EVAL-A053`** | `AIF-053` | Original implementation $\to$ `79/79` protected cases `PASS` | **Real Behavioral Mutations (`15.1.7`)** across all 7 invariant families in `run_case.py` (`UNKNOWN -> VERIFIED`, `snapshot mismatch -> MATCH`, etc.): `CRITICAL_MUT_AUTHORITY` (`4` flipped), `CRITICAL_MUT_SCOPE_ATTRIBUTION` (`12` flipped), `CRITICAL_MUT_PRODUCER_CI` (`6` flipped), `CRITICAL_MUT_TEST_EXEC` (`63` flipped), `CRITICAL_MUT_SUPPLY_CHAIN` (`3` flipped), `CRITICAL_MUT_RECEIPT_GATE` (`21` flipped), `CRITICAL_MUT_EVALUATOR_ORACLE` (`4` flipped) | `BEHAVIORAL + MUTATION` | `VERIFIED` (`7/7` families) |
| **`EVAL-A054`** | `AIF-054` | `T1 SHOULD_TRIGGER -> PASS`, `T2 SHOULD_NOT_TRIGGER -> PASS`, `near_miss -> SHOULD_NOT_TRIGGER PASS` (`7/7 PASS`) | **Trigger Inversion & Keyword Attacks (`15.1.8`)**: `INVERTED` classifier (`T1 -> FAIL`, `T2 -> FAIL`, `7/7` fail) & `KEYWORD_ONLY` classifier (`near_miss` `TRIG-05` & `TRIG-02` $\to$ false-positive `FAIL`) | `BEHAVIORAL + ADVERSARIAL` | `VERIFIED` |
| **`EVAL-A055`** | `AIF-055` | `execution_count=1, raw_observation=present, oracle=matching -> PASS` | **Strongest Zero-Execution Fake (`15.1.9`)**: `expected_observation=correct, observed_output=correct, oracle=matching, execution_count=0` $\to$ `FAIL` (`AIF-055 VACUOUS_TEST: execution_count=0`) | `BEHAVIORAL + ADVERSARIAL` | `VERIFIED` |

### 2.1.1 Corpus Versioning Discipline (`15.1.11`)

In accordance with Section `15.1.11`, `aif-eval-corpus-0.2` (`case_corpus_digest = sha256:b288f19ff6ccb633cda544b602aadd7fb01bb1cfffeec169b0ade639d618dc5c`) is preserved unchanged, and `EVAL-A049`..`EVAL-A055` are registered as the additive `ADVERSARIAL` layer (`aif-evaluator-attack-corpus-v1`) in `skill-evaluation-harness` (`C-08`).

### 2.1.2 Release-Gate Consequence (`15.1.12`)

```text
AIF-049 (EVAL-A049)  BEHAVIORAL + ADVERSARIAL   VERIFIED
AIF-050 (EVAL-A050)  BEHAVIORAL + ADVERSARIAL   VERIFIED
AIF-051 (EVAL-A051)  BEHAVIORAL + ADVERSARIAL   VERIFIED
AIF-052 (EVAL-A052)  BEHAVIORAL + ADVERSARIAL   VERIFIED
AIF-053 (EVAL-A053)  BEHAVIORAL + MUTATION      VERIFIED
AIF-054 (EVAL-A054)  BEHAVIORAL + ADVERSARIAL   VERIFIED
AIF-055 (EVAL-A055)  BEHAVIORAL + ADVERSARIAL   VERIFIED
```

---

### 2.2 Finding B (`15.2`) & Section `15.11` — Reference-vs-Behavior Traceability & Coverage State Model

`compute_invariant_coverage()` in [`.claude/skills/skill-evaluation-harness/scripts/run_suite.py`](../skills/skill-evaluation-harness/scripts/run_suite.py) now tracks all **63 normative rules** (`55` primary + `8` sub-invariants) across the 7-layer chain:

```text
Invariant
   ├── Definition
   ├── Schema
   ├── Structural test
   ├── Behavioral test
   ├── Adversarial mutation
   ├── Oracle
   └── Evidence
```

with explicit non-numerical states:
- **Connection Status**: `REFERENCE_PRESENT` vs `BEHAVIORALLY_CONNECTED` (or `MISSING`)
- **Coverage State**: `MISSING | REFERENCE_ONLY | STRUCTURAL | BEHAVIORAL | ADVERSARIAL | VERIFIED` (no numerical score).

Furthermore, `EVAL-11` in `run_suite.py --self-test` verifies both:
1. All `63/63` rules are `BEHAVIORALLY_CONNECTED` and `VERIFIED`, and
2. Simulating a disconnected behavioral mutator (`simulated_disconnected_invariants={"AIF-049"}`) while leaving all textual ID references intact immediately downgrades `AIF-049` from `BEHAVIORALLY_CONNECTED` (`VERIFIED`) to `REFERENCE_PRESENT` (`REFERENCE_ONLY`).

---

### 2.3 Findings C & D (`15.3`–`15.4`) — Executable Index Chain & Mutation Class Taxonomy

Explicit mutation classes defined and enforced in [`run_case.py`](../skills/skill-evaluation-harness/scripts/run_case.py) and [`run_suite.py`](../skills/skill-evaluation-harness/scripts/run_suite.py):
- `STRUCTURAL_MUTATION`: changes representation without altering semantics.
- `BEHAVIORAL_MUTATION`: changes executable semantics.
- `CRITICAL_MUTATION`: targets a behavior that the evaluator claims to protect across all 7 invariant families (`CRITICAL_MUT_AUTHORITY`, `CRITICAL_MUT_SCOPE_ATTRIBUTION`, `CRITICAL_MUT_PRODUCER_CI`, `CRITICAL_MUT_TEST_EXEC`, `CRITICAL_MUT_SUPPLY_CHAIN`, `CRITICAL_MUT_RECEIPT_GATE`, `CRITICAL_MUT_EVALUATOR_ORACLE`).

---

### 2.4 Findings I & J (`15.9`–`15.10`) — Non-Collapsed Runner Categories & Runner Self-Integrity Attack

[`tests/run-tests.sh`](../../tests/run-tests.sh) separates checks into three distinct categories (`total_checks != quality_score`) and includes an adversarial self-integrity attack (Section `7`) that feeds tampered inputs into the integrity verifier and confirms rejection:

```text
Category Breakdown (total_checks != quality_score):
  INTEGRITY CHECKS   (internal connection)     : 93 passed
  EXECUTION CHECKS   (behavioral conformance)  : 18 passed
  ADVERSARIAL CHECKS (assumption violation)    : 10 passed
----------------------------------------------
Summary: 121 passed, 0 failed
Note: Declared check counts provide evidence for their declared properties only (not a synthetic quality percentage).
```

---

## 3. Complete 63-Rule Reference-vs-Behavior & 7-Layer Coverage Matrix (`15.2` & `15.11`)

Every one of the **63 normative rules** (`55` primary invariants + `8` sub-invariants) is verified across all 7 layers:

| Rule ID | Family | Behavioral Corpus Cases | Structured Adversarial Mutation (`tests/aif-v01-red-suite.py` / `run_suite.py`) | Oracle Failure Code (`oracle.md` / `bin/aif-verify`) | Connection Status | Coverage State |
|---|---|---|---|---|---|---|
| `AIF-001` | Authority | `RED-001`, `P-01` | `mut_aif_001` (spoofed `granted_by=agent-self`) | `AIF-001` (`AUTHORITY_VIOLATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-001A` | Authority | `RED-002` | `mut_aif_001a` (missing authority grant for mutating request) | `AIF-001A` (`AUTHORITY_VIOLATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-002` | Authority | `RED-002` | `mut_aif_002` (`authorized=True` with empty `authority_refs`) | `AIF-002` (`AUTHORITY_VIOLATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-002A` | Authority | `RED-002`, `P-04` | `mut_aif_002a` (unreferenced ambient authority claim) | `AIF-002A` (`AUTHORITY_VIOLATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-003` | Authority | `RED-003`, `P-05` | `mut_aif_003` (`ADMITTED` while `authorized=False`) | `AIF-003` (`ADMISSION_WITHOUT_AUTHORITY`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-003A` | Authority | `RED-003`, `RED-029` | `mut_aif_003a` (`EXECUTED` while admission `REJECTED`) | `AIF-003A` (`EXECUTION_WITHOUT_ADMISSION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-004` | Authority | `RED-004`, `P-02` | `mut_aif_004` (`changed_paths` outside `allowed_paths`) | `AIF-004` (`SCOPE_VIOLATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-004A` | Authority | `RED-004`, `P-08` | `mut_aif_004a` (`INSPECT_ONLY` request performs `WRITE`) | `AIF-004A` (`ACTION_MODE_VIOLATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-005` | Snapshots | `RED-005`, `RED-037` | `mut_aif_005` (ambient workspace diff attributed to agent) | `AIF-005` (`ATTRIBUTION_AMBIGUOUS`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-005A` | Snapshots | `RED-005`, `RED-039` | `mut_aif_005a` (`AGENT_AUTHORED` without `execution_ref`) | `AIF-005A` (`PROVENANCE_UNBOUND`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-006` | Snapshots | `RED-006`, `RED-038` | `mut_aif_006` (`pre_snapshot == post_snapshot` on non-empty diff) | `AIF-006` (`SNAPSHOT_TRANSITION_INVALID`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-006A` | Snapshots | `RED-006`, `RED-040` | `mut_aif_006a` (missing `pre_snapshot` on change record) | `AIF-006A` (`SNAPSHOT_MISSING`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-007` | Snapshots | `RED-007` | `mut_aif_007` (`worktree_clean=True` with dirty index) | `AIF-007` (`SNAPSHOT_DIRTY_MISMATCH`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-008` | Snapshots | `RED-008`, `RED-028`, `RED-041` | `mut_aif_008` (`evidence.snapshot_ref != current_snapshot`) | `AIF-008` (`STALE_EVIDENCE`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-008A` | Snapshots | `RED-028`, `COMPLETE-06` | `mut_aif_008a` (cross-commit evidence promotion) | `AIF-008A` (`CROSS_SNAPSHOT_PROMOTION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-009` | Snapshots | `RED-007` | `mut_aif_009` (malformed SHA-256 digest in `SnapshotRef`) | `AIF-009` (`DIGEST_FORMAT_INVALID`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-010` | Evidence | `RED-009`, `P-01` | `mut_aif_010` (`VERIFIED` claim with empty `evidence_refs`) | `AIF-010` (`UNSUPPORTED_CLAIM`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-011` | Evidence | `RED-010`, `P-01` | `mut_aif_011` (self-asserted prose `source_kind=agent_prose`) | `AIF-011` (`PROSE_NOT_EVIDENCE`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-012` | Evidence | `RED-011` | `mut_aif_012` (`VERIFIED` claim backed only by `HYPOTHESIS`) | `AIF-012` (`EPISTEMIC_ESCALATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-013` | Evidence | `RED-012` | `mut_aif_013` (dangling `evidence_ref` ID) | `AIF-013` (`DANGLING_EVIDENCE_REF`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-014` | Verification | `RED-013`, `P-03` | `mut_aif_014` (`UNKNOWN` coerced to `VERIFIED`) | `AIF-014` (`UNKNOWN_COERCION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-014A` | Verification | `RED-013`, `RED-024` | `mut_aif_014a` (`SKIPPED` check reported as `VERIFIED`) | `AIF-014A` (`SKIPPED_NOT_PASS`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-015` | Verification | `RED-014`, `P-06` | `mut_aif_015` (partial path scan promoted to repo-wide `VERIFIED`) | `AIF-015` (`PARTIAL_SCOPE_OVERCLAIM`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-016` | Verification | `RED-015` | `mut_aif_016` (contradictory evidence collapsed to `VERIFIED`) | `AIF-016` (`CONTRADICTION_SUPPRESSED`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-017` | Verification | `RED-016`, `RED-017` | `mut_aif_017` (`claim_scope` broader than `evidence_scope`) | `AIF-017` (`CLAIM_EXCEEDS_EVIDENCE`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-018` | Verification | `RED-026`, `RED-027` | `mut_aif_018` (verifier mutates repository state) | `AIF-018` (`VERIFIER_SIDE_EFFECT`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-019` | Execution | `RED-018`, `RED-022` | `mut_aif_019` (claimed command execution without `ExecutionRecord`) | `AIF-019` (`UNRECORDED_EXECUTION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-020` | Completion | `RED-031`..`034`, `COMPLETE-01`..`10` | `mut_aif_020` (`COMPLETABLE` while mandatory claim `UNVERIFIED`) | `AIF-020` (`PREMATURE_COMPLETION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-021` | Intake (`C-01`) | `RED-001`..`004`, `P-04`, `P-05`, `P-08` | `mut_aif_021` (authority 4-tuple missing `actor`/`time` binding) | `AIF-021` (`AUTHORITY_TUPLE_INCOMPLETE`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-022` | Intake (`C-01`) | `RED-003`, `P-05` | `mut_aif_022` (`arena-intake-and-authority` sets `mutated_repository=True`) | `AIF-022` (`INTAKE_MUTATION_FORBIDDEN`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-023` | Scope (`C-02`) | `RED-005`, `RED-037`, `RED-039` | `mut_aif_023` (dirty baseline blamed on agent without `ExecutionRecord`) | `AIF-023` (`UNATTRIBUTED_DIFF_BLAME`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-024` | Scope (`C-02`) | `RED-004`, `RED-038`, `P-02` | `mut_aif_024` (undeclared side-effect path marked `IN_SCOPE`) | `AIF-024` (`UNDECLARED_PATH_CHANGE`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-025` | Scope (`C-02`) | `RED-040`, `RED-041` | `mut_aif_025` (`agent-change-scope-audit` mutates working tree) | `AIF-025` (`AUDIT_MUTATION_FORBIDDEN`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-026` | Producers | `RED-014`, `RED-016`, `P-06` | `mut_aif_026` (adapter widens producer proposition scope) | `AIF-026` (`EVIDENCE_MONOTONICITY_VIOLATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-027` | Producers | `RED-030`, `P-01` | `mut_aif_027` (producer emits `CompletionResult` directly) | `AIF-027` (`PRODUCER_INDEPENDENCE_VIOLATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-028` | CI (`C-04`) | `RED-019`, `RED-020`, `RED-035` | `mut_aif_028` (CI Q1..Q6 collapsed or `workflow_sha != head_sha`) | `AIF-028` (`CI_COMMIT_MISMATCH`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-029` | Tests (`C-05`) | `RED-022`, `P-TEST-01` | `mut_aif_029` (`exit_code=0` with `executed_count=0` marked `PASS`) | `AIF-029` (`ZERO_TESTS_EXECUTED`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-030` | Tests (`C-05`) | `RED-023` | `mut_aif_030` (filtered test subset claimed as full suite `COMPLETE`) | `AIF-030` (`FILTERED_SUITE_OVERCLAIM`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-031` | Tests (`C-05`) | `RED-024`, `P-03` | `mut_aif_031` (`skipped > 0` collapsed into full coverage `PASS`) | `AIF-031` (`SKIPPED_TESTS_HIDDEN`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-032` | Tests (`C-05`) | `RED-025` | `mut_aif_032` (weak/assertion-free test claimed as `SEMANTIC_CORRECTNESS`) | `AIF-032` (`SEMANTIC_CORRECTNESS_OVERCLAIM`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-033` | Tests (`C-05`) | `RED-028`, `TEST-07` | `mut_aif_033` (test report bound to stale snapshot `S1 != S2`) | `AIF-033` (`STALE_TEST_EVIDENCE`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-034` | Supply Chain (`C-03`) | `RED-021` | `mut_aif_034` (`supply_chain_state`: manifest without lockfile marked `PINNED_LOCKED`) | `AIF-034` (`UNLOCKED_MANIFEST_PIN_CLAIM`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-035` | Supply Chain (`C-03`) | `RED-021` | `mut_aif_035` (`supply_chain_state`: `lockfile_ drifted=True` marked `CONSISTENT`) | `AIF-035` (`MANIFEST_LOCKFILE_DRIFT`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-036` | Supply Chain (`C-03`) | `RED-017` | `mut_aif_036` (`supply_chain_state`: `install_scripts_inspected=False` marked `SAFE`) | `AIF-036` (`UNINSPECTED_INSTALL_SCRIPTS`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-037` | Supply Chain (`C-03`) | `RED-016` | `mut_aif_037` (`supply_chain_state`: `vulnerability_free` claimed by supply-chain skill) | `AIF-037` (`VULN_CONFLATED_WITH_SUPPLY_CHAIN`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-038` | Supply Chain (`C-03`) | `RED-021` | `mut_aif_038` (`supply_chain_state`: unpinned `git+https`/tarball marked `PINNED`) | `AIF-038` (`UNPINNED_PROVENANCE_SOURCE`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-039` | Supply Chain (`C-03`) | `RED-014` | `mut_aif_039` (`supply_chain_state`: offline/unobserved registry marked `VERIFIED`) | `AIF-039` (`UNOBSERVED_REGISTRY_VERIFIED`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-040` | Supply Chain (`C-03`) | `RED-026`, `P-TEST-02` | `mut_aif_040` (`supply_chain_state`: `mutated_repository=True`) | `AIF-040` (`SUPPLY_CHAIN_MUTATION_FORBIDDEN`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-041` | Receipts (`C-06`) | `RED-036`, `RECEIPT-01` | `mut_aif_041` (`receipt_state`: `receipt_id != sha256(JCS(payload))`) | `AIF-041` (`RECEIPT_DIGEST_MISMATCH`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-042` | Receipts (`C-06`) | `RED-028`, `RECEIPT-03` | `mut_aif_042` (`receipt_state`: mixed snapshots collapsed into single receipt) | `AIF-042` (`RECEIPT_SNAPSHOT_MIXING`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-043` | Receipts (`C-06`) | `RECEIPT-05` | `mut_aif_043` (`receipt_state`: `in_place_mutated=True` instead of `R1 -> R2`) | `AIF-043` (`RECEIPT_IMMUTABILITY_VIOLATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-044` | Receipts (`C-06`) | `RED-015`, `RECEIPT-07` | `mut_aif_044` (`receipt_state`: `CONTRADICTED` evidence dropped from receipt) | `AIF-044` (`RECEIPT_CONTRADICTION_DROPPED`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-045` | Receipts (`C-06`) | `RED-031`, `RECEIPT-09` | `mut_aif_045` (`receipt_state`: `receipt_valid=True` promoted to `all_claims_verified=True`) | `AIF-045` (`RECEIPT_VALID_NOT_CLAIMS_VERIFIED`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-046` | Receipts (`C-06`) | `RECEIPT-10` | `mut_aif_046` (`receipt_state`: `emits_completion_verdict=True`) | `AIF-046` (`RECEIPT_EMITS_COMPLETION_FORBIDDEN`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-047` | Receipts (`C-06`) | `RED-032`, `COMPLETE-04` | `mut_aif_047` (`receipt_state`: `gate_mutated_evidence=True`) | `AIF-047` (`COMPLETION_GATE_IMPURE`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-048` | Receipts (`C-06`) | `RED-033`, `COMPLETE-08` | `mut_aif_048` (`receipt_state`: `remaining_blockers` omitted on `INCOMPLETE`) | `AIF-048` (`COMPLETION_BLOCKERS_OMITTED`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-049` | Evaluation (`C-08`) | `RED-022`, `EVAL-06`, **`EVAL-A049`** | `mut_aif_049` & `EVAL-A049` (`observation_produced=False, observed_evidence=[]`) | `AIF-049` (`MISSING_OBSERVATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-050` | Evaluation (`C-08`) | `RED-022`, `EVAL-07`, **`EVAL-A050`** | `mut_aif_050` & `EVAL-A050` (`Oracle(skill_output, skill_output)` / `derive_oracle_from_self=True`) | `AIF-050` (`ORACLE_INDEPENDENCE_VIOLATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-051` | Evaluation (`C-08`) | `RED-036`, `EVAL-09`, **`EVAL-A051`** | `mut_aif_051` & `EVAL-A051` (`cases.yaml` count tamper & corpus/oracle digest mismatch) | `AIF-051` (`CORPUS_INTEGRITY_ERROR`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-052` | Evaluation (`C-08`) | `RED-036`, `EVAL-09`, **`EVAL-A052`** | `mut_aif_052` & `EVAL-A052` (shuffled replay vs nondeterministic perturbation) | `AIF-052` (`NON_REPRODUCIBLE`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-053` | Evaluation (`C-08`) | `EVAL-10`, **`EVAL-A053`** | `mut_aif_053` & `EVAL-A053` (`7` `CRITICAL_MUTATION` modes across all 7 families) | `AIF-053` (`MUTATION_INSENSITIVE`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-054` | Evaluation (`C-08`) | `RED-001`, `EVAL-12`, **`EVAL-A054`** | `mut_aif_054` & `EVAL-A054` (`KEYWORD_ONLY` over-trigger & `INVERTED` trigger attacks) | `AIF-054` (`TRIGGER_MISCLASSIFICATION`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |
| `AIF-055` | Evaluation (`C-08`) | `RED-013`, `EVAL-06`, **`EVAL-A055`** | `mut_aif_055` & `EVAL-A055` (`expected=PASS`, valid output, `commands_executed=0`) | `AIF-055` (`VACUOUS_TEST`) | `BEHAVIORALLY_CONNECTED` | `VERIFIED` |

---

## 4. Phase 15.12 Priority Matrix — Final Resolution

| Area | Pre-Phase-15 Status | Post-Phase-15.1 Status | Priority |
|---|---|---|---|
| **55 invariant definitions** | `PRESENT` | `VERIFIED` (`BEHAVIORALLY_CONNECTED`) | — |
| **8 sub-invariants (`001A..006A, 008A, 014A`)** | `PRESENT` | `VERIFIED` (`BEHAVIORALLY_CONNECTED`) | — |
| **13 schemas / 14 semantic types** | `PRESENT` | `VERIFIED` (`BEHAVIORALLY_CONNECTED`) | — |
| **49-case corpus (`cases.yaml`)** | `PRESENT` | `VERIFIED` (`BEHAVIORALLY_CONNECTED`) | — |
| **63-rule references** | `PRESENT` | `VERIFIED` (`BEHAVIORALLY_CONNECTED`) | — |
| **Oracle table (`oracle.md`)** | `PRESENT` | `VERIFIED` (`BEHAVIORALLY_CONNECTED`) | — |
| **Fresh execution** | `VERIFIED` | `VERIFIED` | — |
| **Historical snapshot separation** | `PRESENT` | `VERIFIED` | — |
| **`AIF-049` behavioral execution (`EVAL-A049`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `P0` (**CLOSED**) |
| **`AIF-050` oracle independence experiment (`EVAL-A050`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `P0` (**CLOSED**) |
| **`AIF-051` corpus tamper experiment (`EVAL-A051`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `P0` (**CLOSED**) |
| **`AIF-052` deterministic replay experiment (`EVAL-A052`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `P0` (**CLOSED**) |
| **`AIF-053` semantic mutation testing (`EVAL-A053`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `P0` (**CLOSED**) |
| **`AIF-054` positive/negative trigger tests (`EVAL-A054`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `P1` (**CLOSED**) |
| **`AIF-055` zero-execution attack (`EVAL-A055`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `P0` (**CLOSED**) |
| **Reference-vs-behavior traceability (`63` rules)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `P1` (**CLOSED**) |
| **Runner self-integrity attack (`tests/run-tests.sh`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `P1` (**CLOSED**) |

---

## 5. Gate Status Summary

```text
Phase 13    NORMALIZATION            VERIFIED
Phase 14    EXECUTION                VERIFIED
Phase 15.1  ATTACK CORPUS DESIGN     DEFINED  (EVAL-A049..EVAL-A055)
Phase 15.2  ATTACK IMPLEMENTATION    VERIFIED (Known-good -> PASS -> Controlled defect -> DETECTED)
Phase 15.3  FRESH EXECUTION          VERIFIED (7/7 evaluator attacks detected; 153/153 kernel & RED suite; 121/121 runner checks)
Phase 15.4  GAP REASSESSMENT         VERIFIED (63/63 rules BEHAVIORALLY_CONNECTED & VERIFIED)
Phase 16    RELEASE GATE             READY FOR EVALUATION
```
