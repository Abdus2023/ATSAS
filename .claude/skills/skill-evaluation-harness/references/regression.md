# Regression Snapshots & Baselines (`references/regression.md`)

- **Component**: `skill-evaluation-harness` (`C-08`)
- **Governing Invariants**: `AIF-051`, `AIF-052`

---

## 1. `EvaluationSuiteResult` & Raw Reporting (`11.10`)

```text
EvaluationSuiteResult {
    suite_id
    suite_version
    skill
    skill_version
    cases[]
    passed
    failed
    errors
    blocked
    not_observable
    regression_status
    generated_at
}
```

- `total_cases ≠ quality_score`
- The harness never fabricates a single `"skill quality = 93%"` percentage. Instead, it reports raw counts by category:
  ```text
  41 RED:      41 PASS 0 FAIL
   8 PRESSURE:  8 PASS 0 FAIL
  12 RECEIPT:  12 PASS 0 FAIL
  10 COMPLETE: 10 PASS 0 FAIL
   1 GREEN:     1 PASS 0 FAIL
  ```

---

## 2. `EvaluationBaseline` Identity (`11.11`–`11.12`)

```text
EvaluationBaseline {
    baseline_id
    suite_version
    skill_commit
    case_corpus_digest
    oracle_digest
    evaluator_version
    generated_at
}
```

```text
baseline = skill snapshot + case corpus + oracle + evaluator
```

When a skill changes from `v0.1` to `v0.2`:
- If `case_corpus_digest` changed $\to$ `CORPUS_MODIFIED` (`AIF-051`).
- If `oracle_digest` changed $\to$ `ORACLE_MODIFIED` (`AIF-051`).
- If a previously passing case now fails $\to$ `NEW_FAILURE` (`11.11`).
- If identical inputs are rerun $\to$ identical `EvaluationSuiteResult` (`AIF-052`).
