# `arena-completion-gate` (`C-07`)

Pure deterministic `AIF-0.1.0` completion evaluator (`CompletionResult = Evaluate(AcceptanceExpression, ArenaEvidenceReceipt, EvaluatorVersion)`).

## Directory Structure

```text
.claude/skills/arena-completion-gate/
├── SKILL.md
├── README.md
├── scripts/
│   ├── evaluate_completion.py
│   └── validate_completion_result.py
└── references/
    ├── acceptance-language.md
    ├── evaluation-rules.md
    ├── failure-states.md
    └── examples.md
```

## Key Guarantees

- **Pure Evaluation**: No filesystem scan, no `git status`, no `npm test`, no network calls, and no repository mutation (`MUTATES_REPOSITORY: false`).
- **`COMPLETABLE` vs `COMPLETED` (`10.20`)**: Emits `COMPLETABLE` when the acceptance expression is satisfied, preserving the separation between verification/acceptance and `RELEASE` / `MERGE` / `DEPLOY` authority.
- **Preserves `UNKNOWN` & `CONTRADICTED` (`10.7` & `10.9`)**: Never coerces `UNKNOWN → false` or hides conflicting evidence.
