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

## 2. Phase 15.1 — The Seven Executable Evaluator Attack Fixtures (`EVAL-A049` .. `EVAL-A055`)

All 7 adversarial evaluator fixtures are implemented in [`.claude/skills/skill-evaluation-harness/scripts/run_suite.py`](../skills/skill-evaluation-harness/scripts/run_suite.py) (`run_evaluator_attack_corpus()`), enforced by [`.claude/skills/skill-evaluation-harness/scripts/compare_result.py`](../skills/skill-evaluation-harness/scripts/compare_result.py), and executed by both [`tests/aif-v01-red-suite.py`](../../tests/aif-v01-red-suite.py) and [`tests/run-tests.sh`](../../tests/run-tests.sh) without injecting violation phrases into `claim_scope`:

| Fixture ID | Invariant | Adversarial Attack | Behavioral Mechanism Executed | Observed Result |
|---|---|---|---|---|
| **`EVAL-A049`** | `AIF-049` | **No execution observation** | Feeds `GREEN-TEST-01` expected `PASS` classification with `execution_occurred=True`, `commands_executed=1`, **but `observation_produced=False` and `observed_evidence=[]`**. | `status = FAIL`, `matched = False`, `AIF-049 (MISSING_OBSERVATION)` (`DETECTED`) |
| **`EVAL-A050`** | `AIF-050` | **Circular oracle & independence attack** | 1) `Skill=PASS` vs `Independent=NOT_VERIFIED` (`RED-22`) $\to$ `FAIL`; 2) `Skill=BLOCKED` vs `Independent=VERIFIED` (`GREEN-TEST-01`) $\to$ `FAIL` & independent expected status preserved; 3) Circular `Oracle(skill_output, skill_output)` (`expected_classification is observed.classification`) $\to$ rejected with `AIF-050 (ORACLE_INDEPENDENCE_VIOLATION)`. | All 3 anti-circularity sub-attacks rejected (`DETECTED`) |
| **`EVAL-A051`** | `AIF-051` | **Corpus & oracle tampering** | 1) In-memory tamper of `cases.yaml` (`red_cases: 40` vs `41` actual) $\to$ `CORPUS_INTEGRITY_ERROR`; 2) Tamper of `case_corpus_digest` against baseline $\to$ `CORPUS_MODIFIED` (`corpus_integrity_valid=False`); 3) Tamper of `oracle_digest` $\to$ `ORACLE_MODIFIED` (`oracle_integrity_valid=False`). | All 3 tamper modes rejected (`DETECTED`) |
| **`EVAL-A052`** | `AIF-052` | **Nondeterministic replay experiment** | 1) Executes `R1 = evaluate(S, C, O, E)` and `R2 = evaluate(S, C, O, E, shuffle_seed=42)` (shuffled discovery order) and verifies `canonical_suite_digest(R1) == canonical_suite_digest(R2)` (`REPRODUCIBLE`); 2) Injects nondeterministic perturbation in `R2` and verifies `NON_REPRODUCIBLE` (`AIF-052`). | `clean=REPRODUCIBLE`, `perturbed=NON_REPRODUCIBLE (AIF-052)` (`DETECTED`) |
| **`EVAL-A053`** | `AIF-053` | **Strong behavioral mutation across all 7 families** | Executes `baseline -> CRITICAL_MUTATION -> re-evaluation -> flip detection` across all 7 families: `CRITICAL_MUT_AUTHORITY` (`4` flipped), `CRITICAL_MUT_SCOPE_ATTRIBUTION` (`12` flipped), `CRITICAL_MUT_PRODUCER_CI` (`6` flipped), `CRITICAL_MUT_TEST_EXEC` (`63` flipped), `CRITICAL_MUT_SUPPLY_CHAIN` (`3` flipped), `CRITICAL_MUT_RECEIPT_GATE` (`21` flipped), `CRITICAL_MUT_EVALUATOR_ORACLE` (`4` flipped). | `7/7` critical family behavioral mutations killed (`DETECTED`) |
| **`EVAL-A054`** | `AIF-054` | **Positive/negative trigger matrix & trigger inversion** | Evaluates 7-fixture matrix (`clear_trigger`, `keyword_wrong_semantics`, `adversarial_wording`, `minimal_valid_trigger`, `near_miss`, `unrelated_request`, `completion_gate`). Attacks `KEYWORD_ONLY` classifier (catches false positives on `TRIG-02-KEYWORD-WRONG-SEMANTICS` & `TRIG-05-NEAR-MISS`) and `INVERTED` classifier (`7/7` fail). | `trigger correctness != keyword detection` proven (`DETECTED`) |
| **`EVAL-A055`** | `AIF-055` | **Zero-execution / vacuous pass attack** | 1) Attack: `expected=PASS` (`GREEN-TEST-01`), valid-looking classification & evidence list, `execution_occurred=True`, **but `cost.commands_executed = 0`** $\to$ rejected with `AIF-055 (VACUOUS_TEST: execution_count=0)`; 2) Control: `commands_executed = 1` + raw observation + oracle match $\to$ `PASS`. | `zero_exec=FAIL (AIF-055)`, `control=PASS` (`DETECTED`) |

---

## 3. Upgrade of `bin/aif-verify` & `tests/aif-v01-red-suite.py` (`AIF-034`..`AIF-055`)

In addition to `EVAL-A049`..`EVAL-A055`, the mutators `mut_aif_034`..`mut_aif_055` in [`tests/aif-v01-red-suite.py`](../../tests/aif-v01-red-suite.py) and validators in [`bin/aif-verify`](../../bin/aif-verify) were upgraded from textual `claim_scope` violation markers to **structured behavioral state mutations** over `supply_chain_state`, `receipt_state`, and `evaluation_harness_state`.

---

## 4. Non-Collapsed Check Categories & Runner Self-Integrity Attack (`15.9` & `15.10`)

[`tests/run-tests.sh`](../../tests/run-tests.sh) now separates its checks into three explicit categories rather than a single undifferentiated score:

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

## 5. Phase 15.11 & 15.12 — Coverage State Model & Priority Matrix Resolution

Coverage states (`MISSING | REFERENCE_ONLY | STRUCTURAL | BEHAVIORAL | ADVERSARIAL | VERIFIED`, distinguishing `REFERENCE_PRESENT` vs `BEHAVIORALLY_CONNECTED`):

| Area / Invariant Surface | Pre-Phase-15 Status | Post-Phase-15.1 Status | Connection State | Priority |
|---|---|---|---|---|
| **55 primary invariant definitions (`AIF-001..055`)** | `PRESENT` | `VERIFIED` | `BEHAVIORALLY_CONNECTED` | — |
| **8 enumerated sub-invariants (`001A..006A, 008A, 014A`)** | `PRESENT` | `VERIFIED` | `BEHAVIORALLY_CONNECTED` | — |
| **13 modular schemas / 14 core types** | `PRESENT` | `VERIFIED` | `BEHAVIORALLY_CONNECTED` | — |
| **49-case behavioral corpus (`cases.yaml`)** | `PRESENT` | `VERIFIED` | `BEHAVIORALLY_CONNECTED` | — |
| **`AIF-049` behavioral execution (`EVAL-A049`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `BEHAVIORALLY_CONNECTED` | `P0 (CLOSED)` |
| **`AIF-050` oracle independence experiment (`EVAL-A050`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `BEHAVIORALLY_CONNECTED` | `P0 (CLOSED)` |
| **`AIF-051` corpus tamper experiment (`EVAL-A051`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `BEHAVIORALLY_CONNECTED` | `P0 (CLOSED)` |
| **`AIF-052` deterministic replay experiment (`EVAL-A052`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `BEHAVIORALLY_CONNECTED` | `P0 (CLOSED)` |
| **`AIF-053` semantic mutation testing (`EVAL-A053`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `BEHAVIORALLY_CONNECTED` | `P0 (CLOSED)` |
| **`AIF-054` positive/negative trigger tests (`EVAL-A054`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `BEHAVIORALLY_CONNECTED` | `P1 (CLOSED)` |
| **`AIF-055` zero-execution attack (`EVAL-A055`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `BEHAVIORALLY_CONNECTED` | `P0 (CLOSED)` |
| **Reference-vs-behavior traceability (`63` rules)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `BEHAVIORALLY_CONNECTED` | `P1 (CLOSED)` |
| **Runner self-integrity attack (`tests/run-tests.sh`)** | `PARTIAL` | `ADVERSARIAL / VERIFIED` | `BEHAVIORALLY_CONNECTED` | `P1 (CLOSED)` |

---

## 6. Gate Status Summary

```text
Phase 13  NORMALIZATION        VERIFIED
Phase 14  EXECUTION            VERIFIED
Phase 15  ADVERSARIAL REVIEW   VERIFIED (EVAL-A049..EVAL-A055 7/7 DETECTED)
Phase 16  RELEASE GATE         READY FOR EVALUATION
```
