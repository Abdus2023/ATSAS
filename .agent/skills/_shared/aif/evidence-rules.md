# AIF-0.1 Evidence Rules & Assurance Profiles (`AIF-CORE` + `AIF-PROFILES`)

> **Protocol Version**: `0.1`  
> **Core Principle**: **NO EVIDENCE → NO VERIFIED CLAIM.** Claims and evidence are separate objects.

---

## 1. Evidence Adequacy & `EvidenceCoverage(E, C)` (`AIF-007`, `AIF-015`)

```text
EvidenceCoverage {
    evidence_id
    claim_id

    subject_match
    snapshot_match
    scope_match
    method_match
    freshness

    adequacy
    limitations[]
}
```

A claim `C` is verified at snapshot `S` if and only if:
```text
VERIFY(C, S)  ⇔  ∀ required evidence predicate p ∈ C.required_evidence:
                     ∃ E_p: EvidenceCoverage(E_p, C, S).adequacy == SUFFICIENT
                       ∧ ¬∃ E_c: EvidenceCoverage(E_c, C, S).adequacy == CONTRADICTORY
```

### `SKILL_OUTPUT` Restriction (`AIF-018`)
`EvidenceRef.source_type == "SKILL_OUTPUT"` must **not** qualify as `SUFFICIENT` execution or verification evidence unless backed by non-empty `provenance[]` referencing an `ExecutionRecord`, `COMMAND_OUTPUT`, `GIT_OBJECT`, `TEST_REPORT`, or `SCANNER_RESULT`.

---

## 2. Claim-Scope-Dependent Invalidation (`Intersects(Change, Claim)`) (`AIF-014`, `AIF-014A`)

Not every mutation invalidates every claim:
```text
Evidence E becomes STALE for Claim C  ⇔
    E.subject_snapshot = S
    ∧ later change S → S'
    ∧ Intersects(Change(S, S'), C.subject)
```
- If `Intersects(Change(S, S'), C.subject) == false`, `EvidenceCoverage.freshness` may be recorded as `NON_INTERSECTING_CHANGE` (or `SNAPSHOT_INDEPENDENT` for authority/intake evidence).
- If `Intersects(Change(S, S'), C.subject) == true`, `EvidenceCoverage.freshness` becomes `STALE` and `Claim.status` becomes `STALE`.

---

## 3. Contradiction Preservation (`AIF-017`)

When `E1` reports `CLEAN` and `E2` reports `FINDING` on the same claim `C`:
```text
        ┌── E1 ── CLEAN
        │
CLAIM ──┤
        │
        └── E2 ── FINDING
```
- `Claim.status` MUST be `CONTRADICTED` (never `VERIFIED` and never silently collapsed to `PASS` or `FAIL` without preserving both edges in the evidence graph).

---

## 4. Evidence Normalization Rule (`AIF-016`)

Every producer adapter and `evidence-receipt-generator` must obey:
```text
Normalize(E)  ≠  ExpandClaim(E)
```
- **Valid normalization**: `secret-leak-scan` `"No matches in scanned paths"` → `finding_type = SECRET_PATTERN_MATCH, matches = 0`.
- **Forbidden semantic laundering**: Transforming `"No matches in scanned paths"` into `"repository_has_no_secrets = true"` or `"dependencies are safe"`.

---

## 5. Receipt Immutability Rule

An `ArenaEvidenceReceipt` is a historical evidence object:
```text
R1 ──describes──► snapshot S
R2 ──describes──► snapshot S'
```
Never mutate `R1` in place after `S → S'`.

---

## 6. No Implicit Trust Hierarchy (`AIF-011`)

AIF-0.1 does **not** define `CI evidence > local evidence` as a universal rule. Instead:
```text
criterion  ──►  required evidence class
```
- `"CI passes on current HEAD"` requires `CI_RUN` / `CI_ARTIFACT` evidence at `current_snapshot`.
- `"TypeScript has no compiler errors"` may be satisfied by reproducible local `COMMAND_OUTPUT` evidence if permitted by the `AcceptanceExpression`.

---

## 7. `AIF-PROFILES` (Domain-Class Evidence Sufficiency Rules)

While `AIF-CORE` defines what `VERIFIED` means, `AIF-PROFILES` define what evidence is sufficient for each class of claim:

| Profile ID | Target Claim Class | Required `EvidenceRef.source_type` | Required `SnapshotRef.role` |
|---|---|---|---|
| `repository-change` | Change scope & attribution (`DIFF(S0,S1) ⊆ admitted_paths`) | `GIT_OBJECT` + `ChangeRecord[]` with `attribution_basis` | `intake_snapshot` + `execution_snapshot` |
| `security-audit` | Bounded secret / authz / hygiene scan | `SCANNER_RESULT` with explicit `scope` and `limitations` | `verification_snapshot == current_snapshot` |
| `CI-verification` | Workflow configuration vs. remote run outcome | `FILE_CONTENT` (for config) + `CI_RUN` / `CI_ARTIFACT` (for execution) | `verification_snapshot == current_snapshot` |
| `test-verification` | Test discovery, execution, and pass/fail count | `COMMAND_OUTPUT` / `TEST_REPORT` + `ExecutionRecord` (`exit_code == 0`, `test_result == TEST_PASSED`) | `verification_snapshot == current_snapshot` |
| `dependency-assurance` | Lockfile parity, registry resolution & vulnerability audit | `LOCKFILE` + `MANIFEST` + `SCANNER_RESULT` | `verification_snapshot == current_snapshot` |
| `skill-evaluation` | `RED / GREEN / PRESSURE / REGRESSION` behavioral evaluation | `SkillEvalReceipt` (`baseline`, `treatment`, `pressure`, `assertions`) | Fixture `SnapshotRef` |
