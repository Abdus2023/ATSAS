# `EvaluationCase` Format & Versioned Corpus (`references/case-format.md`)

- **Component**: `skill-evaluation-harness` (`C-08`)
- **Corpus ID**: `aif-eval-corpus-0.2` (`suite: id: aif-core-evaluation, version: "0.2"`)
- **Governing Invariant**: `AIF-051` (Corpus Integrity)

---

## 1. First-Class `EvaluationCase` Contract (`11.3`)

```text
EvaluationCase {
    case_id
    category              # RED | GREEN | PRESSURE | REGRESSION
    target_skill
    description
    preconditions
    input
    authority_context
    repository_state
    requested_action
    allowed_scope
    expected_observations[]
    expected_classification
    required_evidence[]
    forbidden_inferences[]
    expected_failure_state
    oracle
    case_digest           # SHA256(JCS(canonical_case))
}
```

---

## 2. Corpus Organization by Layer (`11.20`–`11.21`)

```text
AIF Evaluation Corpus (aif-eval-corpus-0.2)
│
├── Authority / Intake
│   ├── RED-01..04
│   └── P-02, P-08
│
├── Scope / Attribution
│   ├── RED-05..08
│   └── RED-37..41
│
├── Secrets
│   └── RED-09..12
│
├── Dependencies
│   └── RED-13..17
│
├── CI
│   ├── RED-18..21
│   └── P-04
│
├── Tests
│   ├── RED-22..26
│   ├── GREEN-TEST-01
│   └── P-01, P-06, P-07, P-TEST-01, P-TEST-02
│
├── Receipt
│   ├── RED-27..36
│   ├── RECEIPT-01..12
│   └── P-03, P-05
│
└── Completion Gate
    └── COMPLETE-01..10
```

---

## 3. Content-Addressed Case & Oracle Integrity (`11.13`)

To prevent weakening a test (`skill fails RED-22 → modify RED-22 expected result → skill passes`), every `EvaluationCase` and oracle rule is content-addressed using RFC 8785 (JCS) canonical JSON and SHA-256:

```text
case_digest        = SHA256(JCS(canonical_case))
case_corpus_digest = SHA256(JCS(sorted_case_digests))
oracle_digest      = SHA256(JCS(canonical_oracle_rules))
```
