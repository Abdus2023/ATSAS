# AIF-0.1 Executable Invariants (`AIF-001` – `AIF-020` + Sub-Invariants)

> **Protocol Version**: `0.1`  
> **Bridge**: `Invariant → Test → Skill Behavior → Evidence`  
> **Runner**: `tests/aif-v01-red-suite.py` and `bin/aif-verify`

---

## 1. Invariant Registry (`AIF-001` – `AIF-020` + `AIF-001A` – `AIF-014A`)

| Invariant ID | Normative Statement |
|---|---|
| `AIF-001` | **Authority precedes mutation.** `EXECUTION` cannot legitimately precede `ADMISSION`. |
| `AIF-001A` | **Authority is time- and action-scoped.** `EXECUTED(action, t) ⇒ ∃ E: action ∈ E.action_scope ∧ E.effective_from ≤ t < E.expires_at`. |
| `AIF-002` | **Scope is 5-snapshot-relative** (`comparison_base`, `intake_snapshot`, `execution_snapshot`, `verification_snapshot`, `current_snapshot`). |
| `AIF-002A` | **No evidence may transfer across snapshots without explicit justification** (`HEAD=abc123, DIRTY ≢ HEAD=abc123, CLEAN`). |
| `AIF-003` | **Agent changes require before/after provenance** (`DIFF(intake_snapshot, execution_snapshot)`). |
| `AIF-003A` | **State transition is not actor causality without attribution evidence** (`AGENT_ATTRIBUTED` requires `attribution_basis`). |
| `AIF-004` | **Declaration is not execution.** |
| `AIF-004A` | **Execution identity includes `command`, `working_directory`, `environment_digest`, `tool`, `tool_version`, `started_at`, `ended_at`, `subject_snapshot`, and `resulting_snapshot`.** |
| `AIF-005` | **Execution is not success.** |
| `AIF-005A` | **Process success (`PROCESS_RESULT`), test success (`TEST_RESULT`), and semantic sufficiency (`SEMANTIC_RESULT`) are distinct.** |
| `AIF-006` | **Success is not verification.** |
| `AIF-006A` | **Verification is always relative to an explicitly named `Claim` (`VerificationRecord.claim_id`).** |
| `AIF-007` | **Evidence is bound to `subject`, `scope`, `method`, `snapshot`, and `limitations` via `EvidenceCoverage(E, C)`.** |
| `AIF-008` | **Unknown remains unknown (`UNKNOWN ≠ PASS`, `NOT_OBSERVABLE ≠ CLEAN`).** |
| `AIF-008A` | **`NOT_REQUESTED ≠ NOT_CHECKED ≠ NOT_OBSERVABLE ≠ UNKNOWN ≠ PARTIAL ≠ CONTRADICTED`.** |
| `AIF-009` | **Acceptance is evaluated against an explicit `AcceptanceExpression` AST (`ALL`, `ANY`, `AT_LEAST_N`, `OPTIONAL`, `CONDITIONAL`, `CLAIM`).** |
| `AIF-010` | **Audit does not authorize remediation (`Finding.remediation_authorized == false`).** |
| `AIF-011` | **Completion requires satisfaction of each criterion's specific required evidence class (no implicit `CI > local` trust hierarchy).** |
| `AIF-012` | **Detectors produce `Finding[]` and `EvidenceRef[]`, never `CompletionResult`.** |
| `AIF-013` | **Completion gate consumes evidence and never manufactures it (`¬Evidence(C) ≠ Evidence(¬C)`).** |
| `AIF-014` | **Mutation after verification invalidates snapshot-dependent claims.** |
| `AIF-014A` | **Evidence invalidation is claim-scope-dependent (`Intersects(Change, Claim)`).** |
| `AIF-015` | **No evidence from one subject or snapshot may satisfy a claim about another.** |
| `AIF-016` | **Evidence normalization may not broaden semantic claim scope (`Normalize(E) ≠ ExpandClaim(E)`).** |
| `AIF-017` | **Contradictory evidence (`E1: CLEAN` vs `E2: FINDING`) yields `CONTRADICTED`, never `PASS` or `FAIL`.** |
| `AIF-018` | **Skill assertions (`verified=true` / `SKILL_OUTPUT`) are not strong execution evidence.** |
| `AIF-019` | **Missing evidence is an explicit epistemic state, not an implicit pass.** |
| `AIF-020` | **Every completion decision is deterministically reproducible from `Evaluate(AcceptanceExpression, Claims, VerificationRecords, Evidence, Snapshot)` alone.** |

---

## 2. Machine-Testable Invariant Specifications (`TEST AIF-001-01` – `TEST AIF-020-01`)

```text
TEST AIF-001-01
Given:
    execution_records is non-empty AND admission.admission_status == "BLOCKED"
Expected:
    invariant_violation = AIF-001
Forbidden:
    completion_result.status = COMPLETABLE

TEST AIF-001A-01
Given:
    ExecutionRecord.started_at >= AuthorityEvent.expires_at OR action not in AuthorityEvent.action_scope
Expected:
    invariant_violation = AIF-001A
Forbidden:
    authority_status = AUTHORIZED

TEST AIF-002-01
Given:
    SnapshotRef missing working_tree_state or role not in {comparison_base, intake_snapshot, execution_snapshot, verification_snapshot, current_snapshot}
Expected:
    schema_or_invariant_violation = AIF-002
Forbidden:
    valid = true

TEST AIF-002A-01
Given:
    verification_snapshot has commit="abc123", working_tree_state="CLEAN"
    current_snapshot has commit="abc123", working_tree_state="DIRTY"
Expected:
    invariant_violation = AIF-002A (snapshots are non-equivalent)
Forbidden:
    snapshot_match = true

TEST AIF-003-01
Given:
    ChangeRecord modifies a path outside AdmissionRecord.admitted_paths
Expected:
    invariant_violation = AIF-003
Forbidden:
    completion_result.status = COMPLETABLE

TEST AIF-003A-01
Given:
    ChangeRecord.attribution == "AGENT_ATTRIBUTED" AND attribution_basis is empty or "diff_only"
Expected:
    invariant_violation = AIF-003A
Forbidden:
    attribution = AGENT_ATTRIBUTED without execution provenance

TEST AIF-004-01
Given:
    command declared in Request or package.json but ExecutionRecord.execution_state == "NOT_STARTED"
Expected:
    invariant_violation = AIF-004 if claim marked VERIFIED
Forbidden:
    execution_state = EXECUTED

TEST AIF-004A-01
Given:
    command declared but not executed (stdout_ref empty, execution_state != EXECUTED)
Expected:
    execution_state != EXECUTED (invariant_violation = AIF-004A if cited as execution proof)
Forbidden:
    VerificationRecord.result = VERIFIED

TEST AIF-005-01
Given:
    ExecutionRecord.execution_state == "EXECUTED" AND exit_code == 1
Expected:
    invariant_violation = AIF-005 if VerificationRecord.result == "VERIFIED"
Forbidden:
    VerificationRecord.result = VERIFIED

TEST AIF-005A-01
Given:
    ExecutionRecord.exit_code == 0 AND test_result == "ZERO_TESTS_DISCOVERED"
Expected:
    invariant_violation = AIF-005A if test suite claim marked VERIFIED
Forbidden:
    test_result = TEST_PASSED

TEST AIF-006-01
Given:
    ExecutionRecord.exit_code == 0 for "npm run lint" used to verify "unit tests pass"
Expected:
    invariant_violation = AIF-006
Forbidden:
    Claim.status = VERIFIED

TEST AIF-006A-01
Given:
    VerificationRecord.result == "VERIFIED" with unknown or missing claim_id
Expected:
    invariant_violation = AIF-006A
Forbidden:
    valid = true

TEST AIF-007-01
Given:
    Claim.status == "VERIFIED" with no EvidenceCoverage having adequacy == "SUFFICIENT"
Expected:
    invariant_violation = AIF-007
Forbidden:
    Claim.status = VERIFIED

TEST AIF-008-01
Given:
    scanner unavailable (Claim.status = NOT_OBSERVABLE)
Expected:
    observation = NOT_OBSERVABLE (invariant_violation = AIF-008 if promoted to VERIFIED)
Forbidden:
    observation = CLEAN / VERIFIED

TEST AIF-008A-01
Given:
    mandatory Claim has status in {NOT_REQUESTED, NOT_CHECKED, NOT_OBSERVABLE, UNKNOWN, PARTIAL}
Expected:
    invariant_violation = AIF-008A if CompletionResult.status == "COMPLETABLE"
Forbidden:
    CompletionResult.status = COMPLETABLE

TEST AIF-009-01
Given:
    AcceptanceExpression = ALL(CLAIM(c1), CLAIM(c2)) where c1=VERIFIED and c2=UNVERIFIED
Expected:
    invariant_violation = AIF-009 if CompletionResult.status == "COMPLETABLE"
Forbidden:
    Evaluate(AcceptanceExpression) = SATISFIED

TEST AIF-010-01
Given:
    Finding.remediation_authorized == true
Expected:
    invariant_violation = AIF-010
Forbidden:
    remediation_authorized = true

TEST AIF-011-01
Given:
    Claim requires CI_RUN evidence but only local COMMAND_OUTPUT is provided (method_match == false)
Expected:
    invariant_violation = AIF-011 / AIF-015
Forbidden:
    EvidenceCoverage.adequacy = SUFFICIENT

TEST AIF-012-01
Given:
    detector skill emits CompletionResult directly without arena-completion-gate
Expected:
    invariant_violation = AIF-012
Forbidden:
    detector_produces_completion = true

TEST AIF-013-01
Given:
    Claim.status == "VERIFIED" with required_evidence = [] and coverage = []
Expected:
    invariant_violation = AIF-013
Forbidden:
    Claim.status = VERIFIED

TEST AIF-014-01
Given:
    EvidenceRef.subject_snapshot != current_snapshot AND Intersects(ChangeRecord, Claim) == true
Expected:
    invariant_violation = AIF-014 if EvidenceCoverage.freshness == "FRESH"
Forbidden:
    EvidenceCoverage.freshness = FRESH

TEST AIF-014A-01
Given:
    ChangeRecord modifies "src/auth.ts" after verification_snapshot AND Claim.subject covers "src/auth.ts"
Expected:
    invariant_violation = AIF-014A if Claim remains VERIFIED at current_snapshot
Forbidden:
    EvidenceCoverage.freshness = NON_INTERSECTING_CHANGE

TEST AIF-015-01
Given:
    EvidenceCoverage has subject_match=false OR snapshot_match=false OR scope_match=false OR method_match=false
Expected:
    invariant_violation = AIF-015 if adequacy == "SUFFICIENT"
Forbidden:
    EvidenceCoverage.adequacy = SUFFICIENT

TEST AIF-016-01
Given:
    EvidenceRef.claim_scope or Claim.proposition contains unbounded universal claim ("repository has no secrets" / "dependencies are safe")
Expected:
    invariant_violation = AIF-016
Forbidden:
    valid = true

TEST AIF-017-01
Given:
    Claim has both EvidenceCoverage(adequacy=SUFFICIENT) and EvidenceCoverage(adequacy=CONTRADICTORY)
Expected:
    invariant_violation = AIF-017 if Claim.status == "VERIFIED"
Forbidden:
    Claim.status = VERIFIED

TEST AIF-018-01
Given:
    EvidenceRef.source_type == "SKILL_OUTPUT" with empty provenance[] used as sole SUFFICIENT evidence for an execution claim
Expected:
    invariant_violation = AIF-018
Forbidden:
    EvidenceCoverage.adequacy = SUFFICIENT

TEST AIF-019-01
Given:
    Claim referenced in AcceptanceExpression is missing from claims[] or has no VerificationRecord
Expected:
    invariant_violation = AIF-019 if CompletionResult.status == "COMPLETABLE"
Forbidden:
    CompletionResult.status = COMPLETABLE

TEST AIF-020-01
Given:
    CompletionResult.status == "COMPLETABLE" while Evaluate(acceptance_expression, receipt) != "SATISFIED"
Expected:
    invariant_violation = AIF-020
Forbidden:
    CompletionResult.status = COMPLETABLE
```
