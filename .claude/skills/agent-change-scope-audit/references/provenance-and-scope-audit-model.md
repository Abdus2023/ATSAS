# Provenance, Attribution & Scope Audit Reference (`agent-change-scope-audit`)

- **Component**: `C-02` (`agent-change-scope-audit`)
- **AIF Version**: `0.1.0`
- **Invariants**: `AIF-002`, `AIF-003`, `AIF-003A`, `AIF-010`, `AIF-023`, `AIF-024`, `AIF-025`

---

## 1. Attribution Decision Lattice

| `S0` State | `S0 -> S1` Digest Delta | Agent `ExecutionRecord` on Path? | Build Generator Match? | External Event Evidence? | Resulting `attribution` | Resulting `attribution_basis` |
|---|---|---|---|---|---|---|
| `DIRTY` | `before == after` (unchanged in `S0->S1`) | No | No | No | `PREEXISTING` | `["GIT_OBJECT:E-SCOPE-001", "GIT_OBJECT:E-SCOPE-002"]` |
| `CLEAN` or `DIRTY` | `before != after` | Yes (sole actor) | No | No | `AGENT_ATTRIBUTED` | `["EXECUTION_RECORD:<id>", "GIT_OBJECT:E-SCOPE-002"]` |
| `DIRTY` | `before != after` | No (or mixed with external) | No | No | `UNKNOWN` | `["GIT_OBJECT:E-SCOPE-001", "GIT_OBJECT:E-SCOPE-002"]` |
| `CLEAN` | `before != after` | No | Yes (`build` command) | No | `GENERATED` | `["EXECUTION_RECORD:<build_id>", "GIT_OBJECT:E-SCOPE-002"]` |
| `CLEAN` | `before != after` | No | No | Yes | `EXTERNAL_ATTRIBUTED` | `["EXTERNAL_EVENT:<ext_id>", "GIT_OBJECT:E-SCOPE-002"]` |
| `CLEAN` | `before != after` | No | No | No | `UNKNOWN` | `["GIT_OBJECT:E-SCOPE-001", "GIT_OBJECT:E-SCOPE-002"]` |

---

## 2. Scope Evaluation & Unknown Preservation

For every changed path:
1. If any pattern in `admitted_paths` or `excluded_paths` uses an unresolvable matcher syntax (e.g., `UNRESOLVABLE:` or `{{...}}` or when `matcher_available: false` for complex globs), `scope` must be `UNKNOWN` — never collapsed into `OUT_OF_SCOPE`.
2. If the change is `GENERATED` (derived from an in-scope build command) and no explicit generated-artifact scope rule admits or forbids it, `scope` defaults to `UNKNOWN` (`UNKNOWN/derived`).
3. Otherwise:
   - If `path` matches `excluded_paths` or does not match `admitted_paths`: `OUT_OF_SCOPE`.
   - If `path` matches `admitted_paths` and not `excluded_paths`: `IN_SCOPE`.

---

## 3. Adversarial Test Matrix (`RED-05`..`RED-08` & `RED-37`..`RED-41`)

| Test ID | Scenario | Expected `scope` | Expected `attribution` | Expected `verification.scope_claim.status` |
|---|---|---|---|---|
| `RED-05` | Agent modifies `src/a.ts` (admitted) and `src/b.ts` (out-of-scope) | `src/b.ts: OUT_OF_SCOPE` | `AGENT_ATTRIBUTED` | `VIOLATED` (`OUT_OF_SCOPE_AGENT_CHANGE`, report-only per `AIF-010`) |
| `RED-06` | `README.md` dirty at `S0`, agent modifies `src/a.ts` | `README.md: OUT_OF_SCOPE`, `src/a.ts: IN_SCOPE` | `README.md: PREEXISTING`, `src/a.ts: AGENT_ATTRIBUTED` | `VERIFIED` |
| `RED-07` | `package.json` dirty at `S0` and modified differently at `S1` without actor evidence | `OUT_OF_SCOPE` | `UNKNOWN` | `PARTIAL` |
| `RED-08` | `dist/a.js` emitted by build command after editing `src/a.ts` | `dist/a.js: UNKNOWN` | `GENERATED` | `VERIFIED` |
| `RED-37` | `S0 -> S1` contains `package.json` change; no execution evidence identifies actor | `OUT_OF_SCOPE` | `UNKNOWN` (never `AGENT_ATTRIBUTED`) | `PARTIAL` |
| `RED-38` | `README.md` changed at `S0`, unchanged during `S0 -> S1` | `OUT_OF_SCOPE` | `PREEXISTING` (never `AGENT_ATTRIBUTED`) | `VERIFIED` |
| `RED-39` | `src/a.ts` modified, build generates `dist/a.js` | `src/a.ts: IN_SCOPE`, `dist/a.js: UNKNOWN` | `src/a.ts: AGENT_ATTRIBUTED`, `dist/a.js: GENERATED` | `VERIFIED` |
| `RED-40` | Agent execution has no `package.json` action; external event changes `package.json` | `OUT_OF_SCOPE` | `EXTERNAL_ATTRIBUTED` (with external evidence) or `UNKNOWN` (without) | `PARTIAL` |
| `RED-41` | Scope audit produced for `S0 -> S1`, current repository is `S2` | `IN_SCOPE` | `AGENT_ATTRIBUTED` | `STALE` (`STALE_SCOPE_AUDIT`) |
