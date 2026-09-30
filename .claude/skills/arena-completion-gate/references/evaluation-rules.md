# Completion Gate Evaluation Rules (`evaluation-rules.md`)

- **Component**: `C-07` (`arena-completion-gate`)
- **Governing Invariants**: `AIF-002`, `AIF-003`, `AIF-006`–`AIF-020`, `AIF-023`–`AIF-028`, `AIF-031`, `AIF-041`–`AIF-048`

---

## 1. Claim Verification State Mapping (`10.6`)

| Verification / Coverage State | Gate Evaluation | Trace Bucket |
|---|---|---|
| `VERIFIED` (`snapshot_match=MATCH`, `scope_match=MATCH`) | `SATISFIED` | `satisfied_requirements[]` |
| `PARTIAL` | `UNSATISFIED` | `unmet_requirements[]` |
| `UNVERIFIED` | `UNSATISFIED` | `unmet_requirements[]` |
| `STALE` | `UNSATISFIED` | `unmet_requirements[]` |
| `MISMATCH` | `UNSATISFIED` | `unmet_requirements[]` |
| `NOT_OBSERVABLE` | `UNSATISFIED` | `unmet_requirements[]`, `unknowns[]` |
| `UNKNOWN` | `UNSATISFIED` | `unmet_requirements[]`, `unknowns[]` |
| `CONTRADICTED` | `CONTRADICTED` | `unmet_requirements[]`, `contradictions[]` |

---

## 2. Non-Transitivity & Scope Rules (`10.10` – `10.14`)

1. **No Retroactive Repair (`10.10`)**: Fixing a finding mutates repository state and requires a new snapshot and new receipt (`R1 → R2`) before re-evaluating completion.
2. **Snapshot Rule (`10.11`)**: Evidence captured at `S1` with `snapshot_match = MISMATCH` or `STALE` for `evaluated_snapshot = S2` is `UNSATISFIED`.
3. **Scope Rule (`10.12`)**: Any unauthorized out-of-scope change (`ChangeRecord` with `scope = OUT_OF_SCOPE` or `authority = UNAUTHORIZED`) causes `scope-compliant` to be `UNSATISFIED`.
4. **Agent Prose Ignored (`10.13`)**: `AGENT_ASSERTION ≠ EXECUTION_RECORD ≠ EVIDENCE ≠ VERIFICATION`.
5. **Detector Scope Enforced (`10.14`)**: `secret-leak-scan = VERIFIED_NO_MATCH` satisfies `CLAIM("no-secret-patterns-in-scanned-paths")`, never `CLAIM("repository-is-secure")`.
