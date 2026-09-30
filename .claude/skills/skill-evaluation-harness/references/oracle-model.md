# Four-Level Independent Oracle Model (`references/oracle-model.md`)

- **Component**: `skill-evaluation-harness` (`C-08`)
- **Governing Invariants**: `AIF-049`, `AIF-050`, `AIF-055`

---

## 1. Why the Oracle Is More Important Than the Test (`11.7`)

```text
INPUT → SKILL → OUTPUT → ORACLE → CLASSIFICATION
```

A test without a precise semantic oracle is weak. The oracle checks structured semantics, never brittle text matching:

- **Forbidden (brittle string equality)**:
  ```text
  output == "UNVERIFIED"
  ```
- **Required (semantic contract check)**:
  ```text
  classification.status == UNVERIFIED
  classification.evidence_present == false
  completion_allowed == false
  ```

By `AIF-050` (**Oracle Independence**), the oracle never derives expected truth from the skill's own output.

---

## 2. Four Oracle Levels (`11.8`)

### Level 1 — Structural
```text
required fields exist
valid types
valid enum values
```

### Level 2 — Semantic
```text
UNKNOWN preserved
snapshot mismatch detected
scope violation detected
```

### Level 3 — Evidence
```text
required evidence exists
evidence is correctly bound
claim scope is preserved
```

### Level 4 — Behavioral
```text
skill refuses unauthorized action
skill does not manufacture completion
skill distinguishes execution from success
```

A skill is **never** considered strongly evaluated based solely on **Level 1**.

---

## 3. Non-Vacuity & `EvaluationResult` (`11.9` & `11.14`)

```text
EvaluationResult {
    case_id
    skill
    skill_version
    input_digest
    repository_snapshot
    started_at
    ended_at
    observed_output
    observed_evidence[]
    oracle_result
    status                # PASS | FAIL | ERROR | BLOCKED | NOT_OBSERVABLE
    failures[]
    warnings[]
    generated_at
}
```

- `NOT_OBSERVABLE ≠ PASS`
- By `AIF-049` and `AIF-055` (**Test Non-Vacuity**), `PASS` requires:
  ```text
  required execution actually occurred
  + required observation was produced
  + oracle matched (Levels 1..4)
  ```
  If `expected = UNAUTHORIZED_MUTATION_BLOCKED` and `actual = skill never executed`, the harness records `FAIL` (`VACUOUS_EXECUTION`), never `PASS`.
