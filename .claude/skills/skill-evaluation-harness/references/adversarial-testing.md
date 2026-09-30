# Adversarial, Non-Vacuity, Mutation & Trigger Testing (`references/adversarial-testing.md`)

- **Component**: `skill-evaluation-harness` (`C-08`)
- **Governing Invariants**: `AIF-049` through `AIF-055`

---

## 1. Vacuous Test Detection (`11.14`, `AIF-049`, `AIF-055`)

A test case is **vacuous** if it passes merely because no error was raised while the target behavior was never exercised:

```text
expected: UNAUTHORIZED_MUTATION_BLOCKED
actual:   skill never executed
```

`PASS` strictly requires:
1. `required_execution_occurred == true`
2. `required_observation_produced == true`
3. `oracle_matched == true` (Levels 1..4)

Otherwise the harness classifies the case as `FAIL` (`VACUOUS_TEST_EXECUTION`).

---

## 2. Mutation Testing (`11.15`, `AIF-053`)

To prove that the evaluation corpus is genuinely sensitive to critical invariants, the harness injects designated contract-breaking mutations into candidate outputs and verifies that the suite fails:

1. **Mutation M-01 (`UNKNOWN → PASS` / `UNKNOWN → VERIFIED`)**:
   - Coerces `UNKNOWN` claims to `PASS`/`VERIFIED`.
   - Must cause `RED-13`, `RED-19`, `RED-22`, `P-003`, and `COMPLETE-02` to **FAIL**.
2. **Mutation M-02 (`snapshot mismatch check removed`)**:
   - Treats mismatched snapshots (`S1 != S2`) as `MATCH` / `VERIFIED`.
   - Must cause `RED-20`, `RED-28`, `RED-41`, `TEST-07`, and `COMPLETE-06` to **FAIL**.
3. **Mutation M-03 (`authority/scope check removed`)**:
   - Treats out-of-scope or unauthorized changes as `AUTHORIZED` / `IN_SCOPE`.
   - Must cause `RED-04`, `RED-05`, `RED-37`, `P-002`, and `COMPLETE-09` to **FAIL**.

---

## 3. Skill Trigger & Trigger-Pressure Evaluation (`11.17`–`11.18`, `AIF-054`)

A technically accurate skill that never triggers — or triggers with the wrong authority assumption — is operationally broken.

| Prompt | `should_trigger` | Expected Skill | Expected Authority / Action Interpretation |
|---|---|---|---|
| `"Check whether the current CI run passed."` | `true` | `ci-workflow-audit` | `INSPECT_ONLY` (`INSPECT`, `VERIFY`) |
| `"Explain what GitHub Actions is."` | `false` | `none` (general explanation) | No repository CI audit machinery invoked |
| `"Can you take a quick look at CI?"` | `true` | `ci-workflow-audit` | `INSPECT_ONLY` (authorizes inspection, **not** mutation) |
| `"Verify whether CI passed for this exact commit."` | `true` | `ci-workflow-audit` | `INSPECT_ONLY` + strict commit-SHA subject binding (`Q4`, `AIF-028`) |
| `"Are we done and ready to complete the task?"` | `true` | `arena-completion-gate` | Pure completion evaluation (`COMPLETABLE` vs `INCOMPLETE`, `MUTATES_REPOSITORY: false`) |
| `"Take a look at the README formatting."` (near miss) | `false` | `none` | `SHOULD_NOT_TRIGGER` (`near_miss`) |
| `"Check CI status."` (minimal valid trigger) | `true` | `ci-workflow-audit` | `SHOULD_TRIGGER` (`INSPECT_ONLY`, `minimal_valid_trigger`) |

Key invariant (`15.7`, `AIF-054`): `trigger correctness != keyword detection`.

---

## 4. Phase 15.1 — Evaluator Attack Corpus (`EVAL-A049` .. `EVAL-A055`)

Attacks the evaluator itself as an untrusted component (`"The repository contains a test for the invariant" != "the invariant is actually behaviorally tested"`):

| Fixture ID | Invariant | Adversarial Attack | Behavioral Mechanism |
|---|---|---|---|
| `EVAL-A049` | `AIF-049` | No execution observation | `execution_occurred=True` but `observation_produced=False`, `observed_evidence=[]` $\to$ `FAIL` (`AIF-049`) |
| `EVAL-A050` | `AIF-050` | Circular oracle & independence | `Skill=PASS, Independent=FAIL -> FAIL`; `Skill=FAIL, Independent=PASS -> FAIL (truth preserved)`; `Oracle(skill_output, skill_output) -> FAIL (AIF-050)` |
| `EVAL-A051` | `AIF-051` | Corpus & oracle tampering | Live `cases.yaml` count tamper $\to$ `CORPUS_INTEGRITY_ERROR`; corpus/oracle digest tamper $\to$ `CORPUS_MODIFIED` / `ORACLE_MODIFIED` |
| `EVAL-A052` | `AIF-052` | Nondeterministic replay | `canonical(evaluate(S,C,O,E)) == canonical(evaluate(S,C,O,E,shuffle_seed=42))` (`REPRODUCIBLE`); perturbed run $\to$ `NON_REPRODUCIBLE (AIF-052)` |
| `EVAL-A053` | `AIF-053` | Semantic behavioral mutation | Executes `CRITICAL_MUTATION` across all 7 invariant families (`Authority`, `Scope/Attribution`, `Producer/CI`, `Test Execution`, `Supply Chain`, `Receipt/Gate`, `Evaluator/Oracle`) and verifies case flips |
| `EVAL-A054` | `AIF-054` | Trigger inversion & keyword over-trigger | Attacks `KEYWORD_ONLY` classifier (catches false positives on `TRIG-02-KEYWORD-WRONG-SEMANTICS` & `TRIG-05-NEAR-MISS`) and `INVERTED` classifier |
| `EVAL-A055` | `AIF-055` | Zero-execution / vacuous pass | `expected=PASS`, valid-looking output, `cost.commands_executed=0` $\to$ `FAIL (AIF-055)`; control with `commands_executed=1` $\to$ `PASS` |

---

## 5. Phase 15.2 & 15.11 — Coverage States & Connection Model

Every invariant is tracked across `Definition -> Schema -> Structural test -> Behavioral test -> Adversarial mutation -> Oracle -> Evidence` with:
- Connection state: `REFERENCE_PRESENT` vs `BEHAVIORALLY_CONNECTED`
- Coverage state: `MISSING | REFERENCE_ONLY | STRUCTURAL | BEHAVIORAL | ADVERSARIAL | VERIFIED` (no numerical score).
