---
name: ci-workflow-audit
description: Audits CI workflow configuration (.github/workflows/), trigger policies, action pinning, permissions, CIExecutionRecord runs, artifacts, and commit/snapshot binding under AIF-0.1.0 without collapsing CI into a single boolean (`CI workflow exists != triggered != ran != tested this commit`). Use whenever checking whether CI is configured, whether a CI run or artifact verifies the current HEAD/snapshot (AIF-028), or when auditing workflow security and trigger policies (SCOPE: ARENA_GENERIC).
---

# CI Workflow Audit (`ci-workflow-audit` — Component `C-04`)

```text
SCOPE: ARENA_GENERIC
AIF_VERSION: 0.1.0
COMPONENT_ID: C-04
MUTATES_REPOSITORY: false
```

- **Protocol Binding**: `AIF-0.1.0` ([`../_shared/aif/VERSION`](../_shared/aif/VERSION))
- **Contract ID**: `C-04` ([`../../assurance/component-contracts.md`](../../assurance/component-contracts.md))
- **Governing Invariants**: `AIF-004`, `AIF-005`, `AIF-006`, `AIF-007`, `AIF-008`, `AIF-014`, `AIF-026`, `AIF-027`, `AIF-028` (CI Subject Binding)

---

## 1. Purpose & The Six CI Questions (`Q1` – `Q6`)

`ci-workflow-audit` answers six distinct questions that must **never** collapse into a single `CI_PASS` boolean:

```text
CI workflow exists
  ≠ CI was triggered
  ≠ CI ran successfully
  ≠ CI tested this commit
  ≠ CI artifact corresponds to this commit
  ≠ release is verified
```

| Question | Dimension | Possible Values |
|---|---|---|
| **Q1**: Is CI configured? | `configuration_state` | `NOT_FOUND`, `CONFIGURED` |
| **Q2**: What can the configured workflow execute? | `declared_capability` | Declared `triggers`, `jobs`, `steps`, `permissions`, `actions` (capability $\neq$ execution) |
| **Q3**: Was a workflow run actually triggered? | `trigger_state` | `TRIGGERED`, `TRIGGER_NOT_OBSERVED`, `NOT_OBSERVABLE` |
| **Q4**: Did it execute against the required snapshot? | `subject_match` (`AIF-028`) | `MATCH`, `MISMATCH`, `UNKNOWN` (`commit_sha` / `GITHUB_SHA` vs `workflow_sha` / `GITHUB_WORKFLOW_SHA` vs local working-tree state) |
| **Q5**: What was the actual result? | `run_state` / `conclusion` | `RUNNING` (`IN_PROGRESS`), `CANCELLED`, `COMPLETED` (`SUCCESS`, `FAILURE`, `NEUTRAL`, `UNKNOWN`) |
| **Q6**: Does the resulting evidence satisfy the claim? | `claim_verification` | `VERIFIED`, `UNVERIFIED`, `STALE`, `MISMATCH`, `PARTIAL`, `NOT_OBSERVABLE` |

---

## 2. CI Execution, Evidence & Artifact Binding

1. **`CIExecutionRecord`** ([`../_shared/aif/schema/execution-record.schema.json`](../_shared/aif/schema/execution-record.schema.json)):
   Records `run_id`, `workflow_id`, `workflow_name`, `workflow_file`, `event`, `actor`, `repository`, `ref`, `commit_sha` (`GITHUB_SHA`), `workflow_sha` (`GITHUB_WORKFLOW_SHA`), `run_attempt`, `status`, `conclusion`, `started_at`, `completed_at`, `jobs[]`, `artifacts[]`, and `environment_digest`.
2. **`EvidenceRef`** (`source_type: "CI_RUN"`):
   Scope binds `repository`, `workflow`, `workflow_file`, `event`, `ref`, `commit_sha`, `run_id`, `run_attempt`, `jobs`, `steps`, and `conclusion`.
3. **Artifact Provenance**:
   Every CI artifact carries `artifact_id`, `name`, `digest` (`sha256:...`), `run_id`, `subject_commit`, and `created_at`. An artifact from run `A` never certifies run `B` or snapshot `S2`.
4. **Invariant `AIF-028` — CI Subject Binding**:
   $$\text{VERIFY}(C, \text{CI\_E}) \implies \text{Subject}(C) \equiv \text{Subject}(\text{CI\_E})$$
   If `HEAD = B` and a CI run succeeded on `commit = A`, the result is `CI_RUN = SUCCESS`, `CI_SUBJECT = A`, `CURRENT_SNAPSHOT = B`, `CLAIM(B) = UNVERIFIED` (`CI_SNAPSHOT_MISMATCH` / `CI_RUN_STALE`).

---

## 3. Standardized CI Findings (20 Codes)

```text
CI_WORKFLOW_NOT_FOUND        CI_WORKFLOW_CONFIGURED       CI_TRIGGER_NOT_OBSERVED
CI_RUN_FOUND                 CI_RUN_IN_PROGRESS           CI_RUN_SUCCESS
CI_RUN_FAILURE               CI_RUN_CANCELLED             CI_RUN_STALE
CI_SNAPSHOT_MISMATCH         CI_WORKFLOW_MISMATCH         CI_JOB_FAILURE
CI_REQUIRED_JOB_MISSING      CI_REQUIRED_STEP_MISSING     CI_ARTIFACT_MISSING
CI_ARTIFACT_MISMATCH         CI_EVIDENCE_INCOMPLETE       CI_PERMISSIONS_BROAD
CI_UNPINNED_ACTION           CI_TRIGGER_POLICY_RISK
```

### Workflow Security & Trigger Policy Separation
- **Permissions**: Missing or write-all `permissions:` emits `CI_PERMISSIONS_BROAD` (`SECURITY_CONFIGURATION_FINDING`, not `COMPROMISED`).
- **Action Pinning**: Tag/branch refs (`uses: actions/checkout@v6`) emit `CI_UNPINNED_ACTION`, distinguished from immutable 40-hex commit SHAs (`UNPINNED_ACTION ≠ COMPROMISED_ACTION`).
- **Trigger Policy**: Distinguishes `push`, `pull_request`, `pull_request_target` (`CI_TRIGGER_POLICY_RISK`), `workflow_dispatch`, `workflow_run`, `schedule`, and `repository_dispatch`, reporting `TRIGGER_DECLARED`, `TRIGGER_POLICY_OBSERVED`, or `TRIGGER_POLICY_UNKNOWN`.

---

## 4. StreamForge Branch Representation (`NOT_FOUND` $\neq$ `CI_FAILED`)

When `.github/workflows/` is absent (as in `arena/01a0e9bd-streamforge-stremio` where `package.json` and `package-lock.json` define local scripts only):
- Emits `Finding(category="CI_CONFIGURATION", code="CI_WORKFLOW_NOT_FOUND", status="VERIFIED_OBSERVATION", proposition="No GitHub Actions workflow files were observed in the inspected branch.")`.
- Explicitly preserves `not_implied: ["CI_FAILED", "TESTS_FAILED", "REPOSITORY_UNTESTED", "RELEASE_BLOCKED"]`.

---

## 5. Deterministic Execution

```bash
# Run the 21-case adversarial CI self-test suite (CI-01..CI-20 + StreamForge NOT_FOUND check)
python3 .claude/skills/ci-workflow-audit/scripts/audit_ci_workflow.py --self-test

# Evaluate a JSON CI audit input
python3 .claude/skills/ci-workflow-audit/scripts/audit_ci_workflow.py path/to/ci-audit-input.json
```

See [`references/ci-state-machine-and-20-case-corpus.md`](references/ci-state-machine-and-20-case-corpus.md) for the full 20-case CI test matrix (`CI-01`..`CI-20`) and claim rules (`C1`..`C4`).
