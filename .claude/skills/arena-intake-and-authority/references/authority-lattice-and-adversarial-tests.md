# Authority Lattice & Adversarial Test Suite (`arena-intake-and-authority`)

- **Component**: `C-01` (`arena-intake-and-authority`)
- **Consumed Kernel**: [`.claude/skills/_shared/aif/`](../../_shared/aif/README.md) (`VERSION = 0.1.0`)
- **Executable Evaluator**: [`../scripts/evaluate_intake.py`](../scripts/evaluate_intake.py)

---

## 1. Resulting Authority Lattice

```text
                    AUTHORITY
                        │
             ┌──────────┴──────────┐
             │                     │
          ACTION                 ACTOR
             │                     │
      ┌──────┼──────┐              │
      ▼      ▼      ▼              │
     READ  MODIFY  EXECUTE         │
             │                     │
             ▼                     │
           PATH                    │
             │                     │
             ▼                     │
           TIME                    │
             │                     │
             └──────────┬──────────┘
                        ▼
                     ADMISSION
```

Admission requires conjunction across all four dimensions:

$$\text{AUTHORIZED}(\text{action}, \text{path}, \text{actor}, \text{time}) = \text{ACTION\_SCOPE} \land \text{PATH\_SCOPE} \land \text{TEMPORAL\_SCOPE} \land \text{ACTOR\_SCOPE}$$

---

## 2. Adversarial Test Matrix (`--self-test`)

| Test ID | Input Scenario | Expected Outcome | Governing Invariant |
|---|---|---|---|
| `RED-01` | Vague mutation request (`"Fix whatever is wrong."`) | `BLOCKED` + `clarifications` + `admitted_actions: [READ, LIST, SEARCH]` | `AIF-001` |
| `RED-02` | CI investigation only (`"Investigate why CI fails."`) | `INSPECT_ONLY` | `AIF-001`, `AIF-022` |
| `RED-03` | Explicit narrow file scope (`"Update src/resolver.ts and run the resolver tests."`) | `ADMITTED` with exact scope (`test/resolver/**` not auto-added unless authorized) | `AIF-003`, `AIF-022` |
| `RED-04` | Required approval absent for protected surface | `BLOCKED` (`AUTHORITY_MISSING`) | `AIF-001` |
| `A-01` | Expired authority (`expires_at: 19:00`, evaluated at `19:05`) | `EXPIRED` -> `BLOCKED` | `AIF-001A` |
| `A-02` | Conflicting authority (`AUTH-001: modify src/**` vs `AUTH-002: do not modify src/auth/**`) | `CONFLICTING` -> `BLOCKED` | `AIF-001` |
| `A-03` | Action authorized (`MODIFY src/**`), requested path excluded (`package.json`) | `REJECTED` | `AIF-003` |
| `A-04` | Read authorized, write unauthorized | `INSPECT_ONLY` | `AIF-022` |
| `A-05` | Mid-task scope expansion (`A1` excludes `package.json`) without new `AuthorityEvent` | `BLOCKED` (`NEW_AUTHORITY_EVENT_REQUIRED`) | `AIF-001`, `AIF-003` |
| `A-06` | `PUSH` unauthorized | `PUSH` remains in `excluded_actions` (`UNKNOWN`) | `AIF-022` |
| `A-07` | `RELEASE` unauthorized | `RELEASE` remains in `excluded_actions` (`NOT_AUTHORIZED`) | `AIF-022` |
| `AIF-021` | Retroactive authorization ($T_2 > T_1$) | `BLOCKED` (`RETROACTIVE_AUTHORIZATION_FORBIDDEN`) | `AIF-021` |
| `AIF-022` | Non-transitive actor authority (`agent-A` authority used by `agent-B`) | `BLOCKED` (`ACTOR_NOT_AUTHORIZED`) | `AIF-022` |
