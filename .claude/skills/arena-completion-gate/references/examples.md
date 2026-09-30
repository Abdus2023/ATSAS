# Completion Gate Examples & Human-Readable Output (`examples.md`)

## 1. Canonical Evaluation Trace (`10.8`)

Acceptance:
```text
ALL(
    CLAIM("tests-pass"),
    CLAIM("scope-compliant"),
    CLAIM("ci-pass")
)
```

Receipt claim states:
- `tests-pass = VERIFIED`
- `scope-compliant = VERIFIED`
- `ci-pass = UNKNOWN`

Result:
```json
{
  "request_id": "R-104",
  "status": "INCOMPLETE",
  "evaluated_claims": ["tests-pass", "scope-compliant", "ci-pass"],
  "satisfied_requirements": ["tests-pass", "scope-compliant"],
  "unmet_requirements": ["ci-pass"],
  "unknowns": ["ci-pass"],
  "contradictions": [],
  "blockers": [],
  "evaluated_snapshot": "S-27",
  "evaluator": "arena-completion-gate",
  "evaluator_version": "0.1.0"
}
```

---

## 2. Human-Readable Gate Output (`10.21`)

```text
AIF COMPLETION EVALUATION
─────────────────────────
Request: R-104
Snapshot: S-27
Acceptance: ALL(5 claims)

SATISFIED
  ✓ implementation-present
  ✓ typecheck-pass
  ✓ tests-pass
  ✓ scope-compliant

UNSATISFIED
  ! ci-pass — UNKNOWN
    No execution evidence for required snapshot.

RESULT
  INCOMPLETE

No repository mutation performed.
```
