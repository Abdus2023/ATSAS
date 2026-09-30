# Arena Assurance Interface (AIF) v0.1 — Adversarial Freeze Review

> **Status**: `AIF v0.1 FREEZE REVIEW COMPLETE — 14 Invariants Stress-Tested, 14 Loopholes Closed`
> **Scope**: `ARENA_GENERIC`
> **Evaluated Surface**: Interface Invariants `AIF-001` – `AIF-014`, Component Contracts `C-01` – `C-08`, Shared `EvidenceRef`, `ArenaEvidenceReceipt`, and Forbidden Transitions `FT-01` – `FT-10`.

---

## 1. Purpose of the Adversarial Freeze Review

Before generating any `SKILL.md` files or scripts via `skill-creator`, we attempt to **break** the 14 candidate interface invariants (`AIF-001` – `AIF-014`) and the 8 component contracts (`C-01` – `C-08`) using adversarial agent behaviors, edge-case repository states, and cross-contract seam exploits.

For every invariant `AIF-001` through `AIF-014`, this review records:
1. **The Adversarial Break Attempt (`ADV-001` – `ADV-014`)** — how an agent or malformed pipeline could satisfy the literal surface of the draft contract while violating the intended assurance property.
2. **The Ambiguity or Loophole Exposed** — the exact underspecified field, comparison, or seam in the unhardened v0.1 draft.
3. **The Normative Contract Patch (`PATCH-001` – `PATCH-014`)** — the exact deterministic rule added to `C-01` – `C-08`, `EvidenceRef`, and `ArenaEvidenceReceipt` to close the loophole permanently before implementation.

---

## 2. Adversarial Break Matrix (`AIF-001` – `AIF-014`)

### `AIF-001` — Authority precedes mutation

- **Target Contract**: `C-01` (`arena-intake-and-authority`: `IntakeRequest → IntakeResult`)
- **Adversarial Case (`ADV-001` — Retroactive / Post-Mutation Intake)**:
  An agent edits `src/server.ts` first (mutating the repository from `S_real_0` to `S_mutated`), and *only afterwards* invokes `C-01`. Because `C-01` captures `intake_snapshot` when invoked, `intake_snapshot` is recorded as `S_mutated`. Subsequently, `C-02` computes `DIFF(intake_snapshot, execution_snapshot) = DIFF(S_mutated, S_mutated) = ∅`, hiding the unauthorized mutation completely.
- **Ambiguity / Loophole Exposed**:
  `C-01` states `EXECUTED(action) ⇒ action ∈ admitted_actions` (`I-01`), but did not specify a temporal ordering constraint between `intake_snapshot.captured_at` and the session's first mutating tool call, nor how pre-intake mutations are detected.
- **Normative Closure (`PATCH-001` — Temporal & Pre-Flight Anchoring)**:
  1. `IntakeResult.intake_snapshot` must be captured at turn/task initialization **prior to any mutating tool call** (`write_file`, `edit_file`, or non-read-only `bash`).
  2. `intake_snapshot.captured_at <= min(execution_records[].start_time)` is a mandatory predicate.
  3. If any workspace mutation occurred in the current session prior to `intake_snapshot.captured_at` without a prior `ADMITTED` `IntakeResult`, `C-01` must set `authority_status = AUTHORITY_CONFLICT` and `admission_status = REJECTED`.

---

### `AIF-002` — Scope is snapshot-relative

- **Target Contracts**: `C-01` (`arena-intake-and-authority`), `C-02` (`agent-change-scope-audit`)
- **Adversarial Case (`ADV-002` — Symlink Traversal & Mid-Task Ref Switch)**:
  - *Variant A (Symlink escape)*: `target_paths = ["src/allowed/**"]`. The agent creates a symlink `src/allowed/link.json -> ../../config/prod-secrets.json` and modifies the target through the in-scope path string.
  - *Variant B (Branch/Ref switch)*: The agent runs `git checkout other-branch` or `git reset --hard <old_sha>` mid-task, then edits `src/allowed/index.ts`. The path string `"src/allowed/index.ts"` matches `target_paths`, even though the underlying snapshot lineage (`branch_or_ref` / `comparison_base`) was switched without authorization.
- **Ambiguity / Loophole Exposed**:
  `target_paths[]` and `authorized_paths[]` were modeled as bare path strings rather than `(snapshot_lineage, canonical_repo_realpath)` tuples.
- **Normative Closure (`PATCH-002` — Canonical Realpath & Ref-Lineage Binding)**:
  1. Path scope admission in `C-01` and `C-02` applies to **both** the lexical path and the resolved canonical `realpath` relative to repository root at `intake_snapshot` and `execution_snapshot`. Any symlink target resolving outside `authorized_paths[]` or outside the repository root is classified `OUT_OF_SCOPE`.
  2. `branch_or_ref` and `comparison_base` are part of the scope identity. Any change to `branch_or_ref` or `comparison_base` between `intake_snapshot` and `execution_snapshot` not explicitly listed in `admitted_actions[]` forces `scope_status = OUT_OF_SCOPE`.

---

### `AIF-003` — Agent changes require before/after provenance

- **Target Contract**: `C-02` (`agent-change-scope-audit`: `ScopeAuditRequest → ScopeAudit`)
- **Adversarial Case (`ADV-003` — Piggybacking on a Pre-Existing Dirty File)**:
  Suppose `README.md` already has uncommitted modifications at `intake_snapshot` (`S0`), so `README.md ∈ preexisting_changes`. `README.md` is **not** in `authorized_paths[]`. During execution (`S0 → S1`), the agent *also* appends lines to `README.md`. If `C-02` computes `DIFF(S0, S1)` using filename set subtraction (`dirty_files(S1) - dirty_files(S0)`), `README.md` is falsely classified as `PREEXISTING_ONLY` and the agent's unauthorized edit to `README.md` escapes detection!
- **Ambiguity / Loophole Exposed**:
  Representing `intake_snapshot` and `execution_snapshot` only by commit SHA + list of dirty filenames cannot distinguish a pre-existing dirty file left untouched by the agent from a pre-existing dirty file *further modified or reverted* by the agent.
- **Normative Closure (`PATCH-003` — Per-File Content & Index Blob Hash Provenance)**:
  1. `intake_snapshot` and `execution_snapshot` must record a per-path state map:
     `path -> (head_blob_sha, index_blob_sha, worktree_sha256, file_mode)` for every tracked and untracked file.
  2. `path ∈ changed_paths` (i.e. `DIFF(intake_snapshot, execution_snapshot)`) **iff** `(index_blob_sha, worktree_sha256, file_mode)` at `execution_snapshot` differs from `intake_snapshot`.
  3. If a path was dirty at `intake_snapshot` (`worktree_sha256(S0) != head_blob_sha(S0)`) **and** was further mutated at `execution_snapshot` (`worktree_sha256(S1) != worktree_sha256(S0)`), it must appear in **both** `preexisting_changes[]` and `changed_paths[]` (and if not in `authorized_paths[]`, in `unauthorized_changes[]` → `OUT_OF_SCOPE`).

---

### `AIF-004` — Declaration is not execution

- **Target Contracts**: `C-04` (`ci-workflow-audit`), `C-05` (`test-execution-and-evidence-audit`)
- **Adversarial Case (`ADV-004` — No-Op / Dry-Run / Collect-Only Masquerade)**:
  `package.json` declares `"test": "pytest"`. The agent executes `pytest --collect-only` or `npm test -- --help` or `true && echo "pytest"`, which launches a process and exits `0` without executing a single test body.
- **Ambiguity / Loophole Exposed**:
  `C-05` separates `declared_commands[]` from `executed_commands[]`, but did not define when an `executed_command` actually executes the declared test contract vs. a dry-run/list-only flag.
- **Normative Closure (`PATCH-004` — Non-Vacuous Command Execution Semantics)**:
  1. Commands containing dry-run or inspection-only flags (`--collect-only`, `--dry-run`, `--list`, `--version`, `--help`) classify at most as `TEST_AVAILABLE`, never `TEST_EXECUTED` or `TEST_PASSED`.
  2. In `C-05`, transitioning from `TEST_STARTED` to `TEST_EXECUTED` requires `tests_executed > 0` (unless `required_tests[]` is explicitly empty). If `tests_discovered > 0` and `tests_executed == 0`, status is `TEST_DECLARED` / `TEST_PARTIAL`.

---

### `AIF-005` — Execution is not success

- **Target Contracts**: `C-04` (`ci-workflow-audit`), `C-05` (`test-execution-and-evidence-audit`)
- **Adversarial Case (`ADV-005` — Pipeline Exit-Code Masking `| tail` / `|| true`)**:
  The agent runs `npm test 2>&1 | tail -n 50` in a shell without `set -o pipefail`, or runs `npm test || true`. The test runner exits `1` (failing), but the outer shell pipeline returns `exit_code = 0`.
- **Ambiguity / Loophole Exposed**:
  `C-05` checks `exit_codes[]`, which in a naive shell wrapper captures the exit code of the last pipeline stage (`tail` or `true`) rather than the test runner process itself.
- **Normative Closure (`PATCH-005` — Unmasked Runner Exit Status & Failure Count Reconciliation)**:
  1. `C-05` must reject shell commands that mask exit status (`|| true`, `; true`, or un-`pipefail`ed pipes) as `TEST_PARTIAL` (`PARTIALLY_EVIDENCED`) unless `PIPESTATUS[0]` / direct runner `exit_code` is captured.
  2. `TEST_PASSED` requires the conjunction:
     `runner_exit_code == 0 ∧ tests_executed > 0 ∧ tests_failed == 0`.
     If `runner_exit_code == 0` is reported alongside `tests_failed > 0` in parsed output, `C-05` must classify the run as `TEST_FAILED` (`CONTRADICTED`).

---

### `AIF-006` — Success is not verification

- **Target Contracts**: `C-05` (`test-execution-and-evidence-audit`), `C-06` (`evidence-receipt-generator`), `C-07` (`arena-completion-gate`)
- **Adversarial Case (`ADV-006` — Test Surface Weakening / `.skip` Injection / Typecheck-as-Test)**:
  - *Variant A*: The agent runs `npm test` and gets `exit_code = 0` (`TEST_PASSED`), but achieved this by editing `tests/auth.test.ts` to add `.skip` to the failing test or deleting an assertion (`AAI-026`).
  - *Variant B*: The agent runs `npm run typecheck` (`exit_code = 0`) and maps that success to the acceptance criterion `"Verify runtime parser behavior"` (`AAI-029`).
- **Ambiguity / Loophole Exposed**:
  `C-05` outputs `tests_skipped` and `coverage_scope`, and `C-02` outputs `modifications[]`, but `C-05` lacked an explicit `test_surface_integrity` field linking `C-02`'s diff on test paths to `C-05`'s verification status.
- **Normative Closure (`PATCH-006` — Test Surface Integrity & Adequacy Intersection)**:
  1. `C-05` (`TestEvidence`) must cross-reference `C-02` (`ScopeAudit.modifications` and `deletions`): if any existing test file was modified or deleted without explicit test-refactoring authority, or if `tests_skipped > baseline_tests_skipped`, `C-05` sets `status = TEST_PARTIAL` (`TEST_SURFACE_CHANGED`), preventing `TEST_EVIDENCED` from certifying independent regression verification.
  2. In `C-06` and `C-07`, `evidence adequacy = claim requirements ∩ evidence coverage`: a `TYPECHECK_VERIFIED` result covers static type soundness only and cannot satisfy a behavioral/runtime test criterion.

---

### `AIF-007` — Verification is snapshot-bound

- **Target Contracts**: `C-03`..`C-07`, `EvidenceRef`
- **Adversarial Case (`ADV-007` — Uncommitted Working-Tree Edit Under Identical Git `HEAD` SHA)**:
  The repository's `HEAD` commit SHA is `15f7fa0`. The agent edits `src/index.ts` (uncommitted), runs `npm test` (passes), and then makes *another* uncommitted edit to `src/index.ts` without committing. Throughout the entire sequence, `git rev-parse HEAD` remains `15f7fa0`! If `snapshot` is just `git rev-parse HEAD`, `execution_snapshot == verification_snapshot == "15f7fa0"`, masking the post-test uncommitted edit!
- **Ambiguity / Loophole Exposed**:
  Using a 40-char Git commit SHA alone as `snapshot` fails whenever the working tree or git index is dirty.
- **Normative Closure (`PATCH-007` — Composite Snapshot Digest)**:
  Every snapshot field (`intake_snapshot`, `execution_snapshot`, `verification_snapshot`, `target_snapshot`, and `EvidenceRef.snapshot`) is defined as a **composite digest**:
  ```text
  snapshot_id = "<head_commit_sha>:<index_tree_sha>:<worktree_status_and_diff_sha256>"
  ```
  A clean working tree at commit `C` with tree `T` has `<C>:<T>:clean`. Any single-byte modification to any tracked or untracked file in the working tree changes `worktree_status_and_diff_sha256`, immediately distinguishing `S1` from `S2` even when `head_commit` is unchanged.

---

### `AIF-008` — Evidence has bounded claim scope

- **Target Contracts**: `EvidenceRef`, `C-06` (`evidence-receipt-generator`), `C-07` (`arena-completion-gate`)
- **Adversarial Case (`ADV-008` — Claim Scope Laundering Between `EvidenceRef` and `verified_claims[]`)**:
  `secret-leak-scan` produces an `EvidenceRef` with `claim_scope = "No HIGH-severity regex matches in current working tree."` When `C-06` builds `ArenaEvidenceReceipt`, the agent populates `conclusion.verified_claims = ["Repository has zero leaked secrets in code or git history"]`, citing `evref-secret-scan-001`.
- **Ambiguity / Loophole Exposed**:
  `EvidenceRef.claim_scope` was bounded, but `ArenaEvidenceReceipt.conclusion.verified_claims[]` allowed free-text strings that could silently widen `EvidenceRef.claim_scope`.
- **Normative Closure (`PATCH-008` — Strict Claim-Scope Subsumption)**:
  1. Every entry in `ArenaEvidenceReceipt.conclusion.verified_claims[]` and `CompletionResult.verified_claims[]` must never exceed the union of `claim_scope` of its cited `EvidenceRef`s:
     ```text
     ∀ c ∈ verified_claims:  scope(c) ⊆ ⋃_{e ∈ supporting_evidence(c)} e.claim_scope
     ```
  2. Detector-backed claims must preserve the detector identity and scope qualifier verbatim in `verified_claims[]` (e.g. `"SCANNER_NO_MATCH[secret-leak-scan@0.1.0, scope=working_tree]: 0 HIGH matches"`).

---

### `AIF-009` — Unknown remains unknown

- **Target Contracts**: `C-01`..`C-08`, ` dependency-vulnerability-audit` adapter
- **Adversarial Case (`ADV-009` — Empty-Array / Zero-Exit-Code Collapse of `UNKNOWN` into `PASS`)**:
  - *Variant A*: `dependency-vulnerability-audit/scripts/run_dependency_audit.sh` runs in an offline sandbox or where `pip-audit`/`cargo-audit` is not installed. The script prints `SKIP: ...`, returns `0`, and exits `0` with `vulnerability_results = []`.
  - *Variant B*: `.github/workflows/` does not exist, so `CIAudit.findings = []`.
  A downstream consumer checks `if exit_code == 0 and len(findings) == 0` and marks the audit `PASS`!
- **Ambiguity / Loophole Exposed**:
  Empty finding lists (`findings == []`, `vulnerability_results == []`) are structurally indistinguishable from a clean scan unless paired with positive coverage/execution proof and empty `observability_gaps[]`.
- **Normative Closure (`PATCH-009` — Positive Observability Prerequisite for Clean Status)**:
  1. No component (`C-01`..`C-08`) may transition to a `VERIFIED` / `PASSED` / `CLEAN` state solely because `findings == []` or `exit_code == 0`.
  2. A clean verdict requires **both** `findings == []` **and** `observability_gaps == []` **and** positive execution observation (`VULNERABILITY_CHECKED`, `CI_EXECUTED`, `TEST_EXECUTED`).
  3. Any `SKIP` output from `run_dependency_audit.sh` or missing lockfile must populate `DependencyAudit.observability_gaps[]` and set `status = PARTIALLY_OBSERVABLE` / `UNKNOWN`.

---

### `AIF-010` — Audit does not authorize remediation

- **Target Contracts**: `C-02`..`C-07`, Existing Detectors (`secret-leak-scan`, `repo-onboarding-audit`)
- **Adversarial Case (`ADV-010` — Mutating Audit / Auto-Fix Flag Injection)**:
  While running `C-02` (`agent-change-scope-audit`) or `secret-leak-scan`, the audit discovers an unauthorized file `foo.bak` or a leaked token in `config.js`. Following `secret-leak-scan/SKILL.md` Step 2 (*"remove it from the working tree"*), the agent deletes `foo.bak` or edits `config.js` *during the audit*, then re-runs the detector and reports a clean audit (`P-002`)!
- **Ambiguity / Loophole Exposed**:
  `secret-leak-scan/SKILL.md` Step 2 mixes detection with remediation advice, and `C-02`..`C-05` did not mandate a pre-audit vs. post-audit snapshot check.
- **Normative Closure (`PATCH-010` — Audit Snapshot Invariance)**:
  1. Every audit/verifier execution (`C-02`, `C-03`, `C-04`, `C-05`, and all detector runs) must capture `S_audit_start` and `S_audit_end` composite digests and enforce:
     ```text
     S_audit_start == S_audit_end
     ```
  2. If `S_audit_start != S_audit_end`, the audit result is immediately invalidated with `AUDIT_MUTATION_VIOLATION` (`REJECTED`), and the mutation is recorded as an unauthorized action under `AIF-001` and `AIF-010`.

---

### `AIF-011` — Completion is conjunctive over mandatory criteria

- **Target Contracts**: `C-01` (`IntakeRequest`), `C-06` (`ArenaEvidenceReceipt`), `C-07` (`CompletionRequest`)
- **Adversarial Case (`ADV-011` — Criterion Dropping / Selective Criterion Forwarding)**:
  `C-01` records 4 mandatory acceptance criteria: `[C1: implementation, C2: unit tests, C3: secret scan, C4: CI workflow pass]`. When CI fails or is unconfigured, the agent constructs `CompletionRequest` (`C-07`) with `acceptance_criteria = [C1, C2, C3]` (dropping `C4`). Because `C1`, `C2`, and `C3` all have sufficient evidence, `∀ criterion ∈ CompletionRequest.acceptance_criteria` evaluates to `true` and returns `COMPLETABLE`!
- **Ambiguity / Loophole Exposed**:
  `C-07` evaluated its conjunction over `CompletionRequest.acceptance_criteria[]` without verifying that the array matched `C-01`'s `IntakeRequest.acceptance_criteria[]`.
- **Normative Closure (`PATCH-011` — Immutable Acceptance Criteria Binding Across `C-01 → C-06 → C-07`)**:
  1. `C-07` (`arena-completion-gate`) must verify:
     ```text
     CompletionRequest.acceptance_criteria == IntakeRequest.acceptance_criteria == ArenaEvidenceReceipt.request.acceptance_criteria
     ```
  2. Any missing, reworded, or downgraded mandatory criterion between `intake_result` and `CompletionRequest` triggers `CRITERION_TAMPERING` → `REJECTED`.

---

### `AIF-012` — Existing detectors produce evidence; they do not decide completion

- **Target Contracts**: `secret-leak-scan`, `dependency-vulnerability-audit`, `authorization-boundary-scan`, `docs-integrity-check`, `C-06`, `C-07`
- **Adversarial Case (`ADV-012` — Detector Exit-Code Short-Circuit to Completion)**:
  The agent runs `python3 .claude/skills/secret-leak-scan/scripts/scan_secrets.py .` (`exit 0`) and `python3 .claude/skills/authorization-boundary-scan/scripts/scan_authorization_boundary.py` (`exit 0`), and declares the repository `"Verified and Complete"` without running `C-06` or `C-07`.
- **Ambiguity / Loophole Exposed**:
  Existing detector scripts exit `0` when no hits are found, which is easily conflated with a terminal `PASS` decision.
- **Normative Closure (`PATCH-012` — Detector Output Wrapping via `EvidenceRef`)**:
  1. Raw detector exit codes (`0` or `1`) represent only `RESULT` (`0 pattern matches` vs `>=1 pattern matches`), never `EVIDENCE` or `DECISION`.
  2. No detector output can be consumed by `C-07` (`arena-completion-gate`) until normalized by `C-06` (`evidence-receipt-generator`) into an `EvidenceRef` with explicit `producer`, `producer_version`, `snapshot`, and bounded `claim_scope`.

---

### `AIF-013` — Completion gate consumes evidence; it does not manufacture evidence

- **Target Contracts**: `C-06` (`evidence-receipt-generator`), `C-07` (`arena-completion-gate`)
- **Adversarial Case (`ADV-013` — Fabricated Receipt / Unbacked `EvidenceRef` Injection)**:
  Instead of running tests, the agent writes a syntactically valid `ArenaEvidenceReceipt` JSON containing `"verified_claims": ["All tests pass"]` and `"evidence": { "commands": ["npm test"], "exit_codes": [0] }`, where the cited `EvidenceRef.source_locator` either does not exist or points to a hand-typed text file.
- **Ambiguity / Loophole Exposed**:
  JSON Schema validation (`bin/aif-verify`) verifies the structural shape of `ArenaEvidenceReceipt`, not whether the referenced execution records and artifact hashes correspond to real tool executions at `verification_snapshot`.
- **Normative Closure (`PATCH-013` — Evidence Provenance & Hash Verification)**:
  1. Every `EvidenceRef` in `ArenaEvidenceReceipt` and `CompletionRequest` must include a verifiable `source_locator` and `artifact_sha256` (or execution log digest) produced by a deterministic script or tool trace.
  2. `C-07` must verify that every `verified_claim` in `ArenaEvidenceReceipt` resolves through the unbroken 5-link chain:
     `CLAIM → REQUIRED EVIDENCE → ACTUAL EVIDENCE (resolvable EvidenceRef) → SNAPSHOT → PROVENANCE`.
     If any `EvidenceRef` is unresolvable or lacks provenance, `C-07` returns `UNVERIFIED` (`RECEIPT_INVALID`).

---

### `AIF-014` — A changed verification snapshot invalidates prior certification

- **Target Contracts**: `C-02`, `C-05`, `C-06`, `C-07`
- **Adversarial Case (`ADV-014` — The Post-Verification Edit & In-Repo Receipt Commit Paradox)**:
  - *Variant A (Post-test edit)*: Tests run and pass at `S2`. Before finishing, the agent makes a "minor" formatting or comment edit to `src/app.ts` or `README.md` (creating `S_final != S2`) and presents the receipt from `S2` as certifying `S_final` (`P-004`).
  - *Variant B (The In-Repo Receipt Paradox)*: Suppose `ArenaEvidenceReceipt` is written to a tracked file in the repository *after* tests run at `S2`. Writing or committing the receipt file itself changes the working tree / `HEAD` commit (`S_after_receipt != S2`), which would either self-invalidate `AIF-014` every time a receipt is saved, or tempt the implementation to weaken `AIF-014`!
- **Ambiguity / Loophole Exposed**:
  How does `AIF-014` remain a strict, zero-exception invariant (`verification_snapshot == current_subject_snapshot`) when the receipt artifact itself is generated after verification?
- **Normative Closure (`PATCH-014` — Subject-Tree Snapshot Canonicalization)**:
  1. The composite snapshot digest (`intake_snapshot`, `execution_snapshot`, `verification_snapshot`, `current_subject_snapshot`) is computed over the repository's **Subject Tree** (all repository paths excluding the designated ephemeral receipt output directory `.claude/assurance/receipts/` or external receipt store).
  2. Any modification to **any** subject path (code, config, tests, docs, `README.md`, comments, formatting) after `verification_snapshot` changes the Subject Tree digest (`current_subject_snapshot != verification_snapshot`), immediately invalidating prior certification (`VERIFICATION_STALE` / `EVIDENCE_MISMATCH`) and forcing `C-07` to return `INCOMPLETE` / `UNVERIFIED`.

---

## 3. Summary Table of the 14 Adversarial Cases & Normative Patches

| Invariant | Adversarial Attack ID & Name | Loophole Exposed in Draft | Normative Closure Patch |
|---|---|---|---|
| `AIF-001` | `ADV-001`: Retroactive Intake after mutation | `intake_snapshot` captured after first edit hides mutation from `DIFF(S0,S1)` | `PATCH-001`: Temporal ordering `intake_snapshot.captured_at <= min(execution.start_time)` |
| `AIF-002` | `ADV-002`: Symlink escape & mid-task branch switch | Lexical path strings ignore symlink targets and branch resets | `PATCH-002`: Canonical `realpath` + `(branch_or_ref, comparison_base)` lineage check |
| `AIF-003` | `ADV-003`: Piggybacking on pre-existing dirty file | Filename set difference misses agent edits to files already dirty at `S0` | `PATCH-003`: Per-file `(head_blob, index_blob, worktree_sha256, mode)` diffing |
| `AIF-004` | `ADV-004`: Dry-run / `--collect-only` masquerade | Flagged test commands exit `0` without running tests | `PATCH-004`: Reject dry-run/list flags; require `tests_executed > 0` for `TEST_EXECUTED` |
| `AIF-005` | `ADV-005`: Pipe exit-code masking (`\| tail`, `\|\| true`) | Outer shell pipeline returns `0` when test runner exited non-zero | `PATCH-005`: Require unmasked runner `exit_code == 0 ∧ tests_executed > 0 ∧ tests_failed == 0` |
| `AIF-006` | `ADV-006`: `.skip` injection & typecheck-as-test | Passing modified/skipped tests or typecheck claimed as behavioral verification | `PATCH-006`: Cross-check `C-02` test diff + `tests_skipped` delta + `claim ∩ coverage` |
| `AIF-007` | `ADV-007`: Uncommitted edit under same `HEAD` SHA | Bare commit SHA misses uncommitted working-tree or staged changes | `PATCH-007`: Composite digest `<head_sha>:<index_tree_sha>:<worktree_diff_sha256>` |
| `AIF-008` | `ADV-008`: Claim scope laundering in receipt | Narrow `EvidenceRef.claim_scope` cited by broad `verified_claims[]` string | `PATCH-008`: Enforce `scope(verified_claim) ⊆ ⋃ scope(EvidenceRef)` |
| `AIF-009` | `ADV-009`: Empty-array / `SKIP` collapse to `PASS` | `findings == []` when tool skipped/offline treated as clean scan | `PATCH-009`: Require `findings == [] ∧ observability_gaps == [] ∧ positive_execution` |
| `AIF-010` | `ADV-010`: Mutating audit / auto-fix during scan | Agent deletes/edits flagged file during audit step (`P-002`) | `PATCH-010`: Enforce `S_audit_start == S_audit_end` across every verifier/detector run |
| `AIF-011` | `ADV-011`: Mandatory criterion omission in `C-07` | Dropping a criterion from `CompletionRequest` makes `∀` vacuously true | `PATCH-011`: Enforce `CompletionRequest.acceptance_criteria == IntakeRequest.acceptance_criteria` |
| `AIF-012` | `ADV-012`: Detector exit-`0` short-circuit | Agent treats `scan_secrets.py` exit `0` as terminal completion decision | `PATCH-012`: Detectors emit `EvidenceRef` only; completion requires `C-06` + `C-07` |
| `AIF-013` | `ADV-013`: Hand-crafted synthetic receipt JSON | Schema-valid JSON with fake command strings accepted without artifact verification | `PATCH-013`: Verify `EvidenceRef.source_locator` & hash integrity across the 5-link chain |
| `AIF-014` | `ADV-014`: Post-verification edit & receipt commit paradox | Post-test doc/code tweak or receipt write shifts snapshot | `PATCH-014`: Subject-Tree composite digest (excluding `.claude/assurance/receipts/`) must match `S2` |

---

## 4. Expanded AIF v0.1 Invariant Set (`AIF-001` – `AIF-020` + Sub-Invariants `AIF-001A`..`AIF-014A`)

The adversarial review expands the freeze candidate from 14 to **20 primary invariants + 8 sub-invariants**, each bound directly to a canonical data model type in [`.claude/assurance/canonical-data-model.md`](canonical-data-model.md):

| Invariant ID | Normative Statement | Canonical Data Model Type Bound |
|---|---|---|
| `AIF-001` | Authority precedes mutation (`EXECUTED(action) ⇒ AUTHORIZED(action)`). | `AuthorityEvent`, `ExecutionRecord` |
| `AIF-001A` | Authority is time-bounded and action-scoped (`∃ E: action ∈ E.scope ∧ E.effective_from ≤ t < E.expires_at`). | `AuthorityEvent` |
| `AIF-002` | Scope is snapshot-relative across four snapshots (`S0 = intake`, `S1 = execution`, `S2 = verification`, `S3 = current/head`). | `SnapshotRef` |
| `AIF-002A` | Observations cannot silently transfer between snapshots without an explicit equivalence proof. | `SnapshotRef`, `EvidenceCoverage` |
| `AIF-003` | Agent changes require provenance (`DIFF(S0, S1)`). | `SnapshotRef`, `PathTransition` |
| `AIF-003A` | State transition ≠ actor causality (`STATE_CHANGE` vs `AGENT_ATTRIBUTED_CHANGE` vs `UNATTRIBUTED_CHANGE`). | `PathTransition`, `ExecutionRecord` |
| `AIF-004` | Declaration ≠ execution. | `ExecutionRecord` |
| `AIF-004A` | Execution identity includes command + working directory + environment digest + tool/version + subject snapshot, not command text alone. | `ExecutionRecord` |
| `AIF-005` | Execution ≠ success. | `ExecutionRecord` |
| `AIF-005A` | Process exit success (`exit_code == 0`) ≠ test success ≠ semantic criterion success (`PROCESS_RESULT` vs `TEST_RESULT` vs `SEMANTIC_RESULT`). | `ExecutionRecord` |
| `AIF-006` | Success ≠ verification. | `Claim`, `EvidenceCoverage` |
| `AIF-006A` | `VERIFIED` is always relative to an explicitly named claim (`VERIFY(claim, evidence, verification_method, snapshot)`). | `Claim` |
| `AIF-007` | Evidence has bounded claim scope (`EvidenceRef` must declare `subject`, `scope`, `method`, `snapshot`, `limitations`; `EvidenceCoverage(E, C) ∈ {SUFFICIENT, PARTIAL, IRRELEVANT, CONTRADICTORY, UNKNOWN}`). | `EvidenceRef`, `EvidenceCoverage` |
| `AIF-008` | Unknown remains unknown. | `Claim`, `Finding` |
| `AIF-008A` | `NOT_REQUESTED ≠ NOT_CHECKED ≠ NOT_OBSERVABLE ≠ UNKNOWN ≠ PARTIAL ≠ CONTRADICTED`. | `Claim`, `Finding` |
| `AIF-009` | Completion evaluates a structured `AcceptanceExpression` (`ALL`, `ANY`, `AT_LEAST_N`, `OPTIONAL`, `CONDITIONAL`). | `AcceptanceExpression` |
| `AIF-010` | Audit ≠ remediation (`AUDIT` must never implicitly transition into `REMEDIATION`; `Finding.remediation_authorized = false`). | `Finding`, `AuthorityEvent` |
| `AIF-011` | Completion requires criterion-appropriate evidence (`Criterion → EvidenceRequirement`). | `AcceptanceExpression` |
| `AIF-012` | Existing detectors produce evidence (`EvidenceRef`, `Finding`); they do not decide completion (`COMPLETABLE`). | `EvidenceRef`, `Finding` |
| `AIF-013` | Completion gate cannot manufacture evidence (`¬Evidence(C) ≠ Evidence(¬C)`). | `ArenaEvidenceReceipt` |
| `AIF-014` | Mutation invalidates intersecting snapshot-bound evidence. | `EvidenceCoverage`, `SnapshotRef` |
| `AIF-014A` | Evidence invalidation is claim-scope dependent (snapshot-independent evidence remains valid; intersecting subject mutations invalidate). | `EvidenceRef`, `EvidenceCoverage` |
| `AIF-015` | Evidence cannot satisfy a criterion across incompatible subjects, snapshots, scopes, or methods. | `EvidenceCoverage` |
| `AIF-016` | Evidence normalization may normalize representation, but may not broaden semantic `claim_scope`. | `EvidenceRef`, `Claim` |
| `AIF-017` | Contradictory evidence remains `CONTRADICTED` / `CONFLICT` (never silently picking the favorable result). | `Claim`, `EvidenceCoverage`, `Finding` |
| `AIF-018` | Skill assertions are not execution evidence (`DECLARATION_OF_RESULT ≠ EXECUTION_EVIDENCE`). | `EvidenceRef`, `ExecutionRecord` |
| `AIF-019` | Missing evidence is an explicit state (`NOT_CHECKED` / `UNVERIFIED`), not implicit success. | `Claim`, `AcceptanceExpression` |
| `AIF-020` | A completion decision must be deterministically reproducible from its receipt (`CompletionGate = Evaluate(AcceptanceExpression, ArenaEvidenceReceipt)`). | `AcceptanceExpression`, `ArenaEvidenceReceipt` |

---

## 5. Freeze Assessment

| Dimension | Current Status |
|---|---|
| **Original interface invariants** | `14 (AIF-001 .. AIF-014)` |
| **Adversarial invariant additions** | `+6 primary (AIF-015 .. AIF-020) & +8 sub-invariants (AIF-001A .. AIF-014A)` |
| **Canonical Data Model (9 types)** | `DEFINED IN .claude/assurance/canonical-data-model.md & schemas/aif-canonical-data-model.schema.json` |
| **Architecture** | `STRONG / PROVISIONAL` |
| **`SKILL.md` implementation** | `NOT YET (Blocked until Canonical Data Model & Interface Freeze sign-off)` |

