---
name: arena-completion-gate
description: Pure deterministic completion evaluator that evaluates a declarative AcceptanceExpression (ALL, ANY, AT_LEAST_N, OPTIONAL, CONDITIONAL, CLAIM) over an immutable ArenaEvidenceReceipt under AIF-0.1.0 without inspecting the repository, running commands, or mutating state (`COMPLETE(R, A) iff Evaluate(A, VerifiedClaims(R)) = SATISFIED`, `COMPLETABLE != COMPLETED`). Use whenever deciding whether an agent task is COMPLETABLE, INCOMPLETE, BLOCKED, CONTRADICTED, or INVALID (SCOPE: ARENA_GENERIC).
---

# Arena Completion Gate (`arena-completion-gate` — Component `C-07`)

```text
SCOPE: ARENA_GENERIC
AIF_VERSION: 0.1.0
COMPONENT_ID: C-07
MUTATES_REPOSITORY: false
```

- **Protocol Binding**: `AIF-0.1.0` ([`../_shared/aif/VERSION`](../_shared/aif/VERSION))
- **Contract ID**: `C-07` ([`../../assurance/component-contracts.md`](../../assurance/component-contracts.md))
- **Governing Invariants**: `AIF-002`, `AIF-003`, `AIF-006`–`AIF-020`, `AIF-023`–`AIF-028`, `AIF-031`, `AIF-041`–`AIF-048`

---

## 1. Fundamental Equation & Pure Function Model (`10.1` & `10.17`)

`arena-completion-gate` is the smallest possible decision mechanism in the architecture: it does not inspect the repository, run tests, run scanners, modify files, or trust the agent's final message.

```text
COMPLETE(R, A) iff Evaluate(A, VerifiedClaims(R)) = SATISFIED
CompletionResult = Evaluate(AcceptanceExpression, ArenaEvidenceReceipt, EvaluatorVersion)
```

```text
same receipt + same acceptance expression + same evaluator version ──► same CompletionResult
```

---

## 2. Acceptance Expression Language & Explicit Acceptance (`10.3` & `10.4`)

```text
AcceptanceExpression =
    ALL(expressions[])
  | ANY(expressions[])
  | AT_LEAST_N(n, expressions[])
  | OPTIONAL(expression)
  | CONDITIONAL(condition, then, else)
  | CLAIM(claim_id)
```

If a request omits acceptance criteria (`"Fix the bug."`), the gate never silently invents requirements; it returns `ACCEPTANCE_UNSPECIFIED`.

---

## 3. Completion States, Claim Semantics & `COMPLETABLE` vs `COMPLETED` (`10.5`–`10.7`, `10.20`)

### 3.1 Gate Outcomes
- **`COMPLETABLE`**: All required claims in `AcceptanceExpression` are `VERIFIED` at `evaluated_snapshot` with matching scope (`COMPLETABLE ≠ COMPLETED`; `ACCEPT`, `RELEASE`, `MERGE`, and `DEPLOY` require separate execution authority).
- **`INCOMPLETE`**: Receipt is valid, but one or more required claims remain unsatisfied (`PARTIAL`, `UNKNOWN`, `NOT_OBSERVABLE`, `STALE`, `MISMATCH`, `UNVERIFIED`).
- **`BLOCKED`**: An external prerequisite or unauthorized scope violation blocks evaluation/completion.
- **`CONTRADICTED`**: Required claim has `result = CONTRADICTED` (`contradictions[]` preserved).
- **`INVALID`**: The input `ArenaEvidenceReceipt` fails structural, referential, semantic, or digest validation.

### 3.2 The Crucial `UNKNOWN` Rule (`10.7`)
`UNKNOWN` is never coerced to `false` inside the evidence model. It is preserved in `CompletionResult.unknowns[]` while evaluating the requirement as unsatisfied (`INCOMPLETE`).

---

## 4. Deterministic Execution

```bash
# Run the 19-case Phase 10 completion gate self-test suite (COMPLETE-01..10 + P-COMP-01..08 + 10.21 output check)
python3 .claude/skills/arena-completion-gate/scripts/evaluate_completion.py --self-test

# Evaluate an ArenaEvidenceReceipt against an AcceptanceExpression
python3 .claude/skills/arena-completion-gate/scripts/evaluate_completion.py path/to/gate-input.json

# Validate a CompletionResult object against completion-result.schema.json
python3 .claude/skills/arena-completion-gate/scripts/validate_completion_result.py path/to/completion-result.json
```

See [`README.md`](README.md), [`references/acceptance-language.md`](references/acceptance-language.md), [`references/evaluation-rules.md`](references/evaluation-rules.md), [`references/failure-states.md`](references/failure-states.md), and [`references/examples.md`](references/examples.md).
