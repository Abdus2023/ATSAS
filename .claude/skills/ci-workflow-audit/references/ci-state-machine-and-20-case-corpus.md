# CI State Machine, Security Dimensions & 20-Case Test Corpus (`ci-workflow-audit`)

- **Component**: `C-04` (`ci-workflow-audit`)
- **AIF Version**: `0.1.0`
- **Invariants**: `AIF-004`, `AIF-005`, `AIF-006`, `AIF-007`, `AIF-008`, `AIF-014`, `AIF-026`, `AIF-027`, `AIF-028`

---

## 1. CI Claim Templates (`C1` – `C4`)

| Claim ID | Proposition Template | Required Evidence for `VERIFIED` |
|---|---|---|
| `C1` | `"Workflow X completed successfully for commit S."` | `CIExecutionRecord` + `status == COMPLETED` + `conclusion == SUCCESS` + `commit_sha == S` + clean working tree |
| `C2` | `"Required test job J passed for commit S."` | `C1` requirements + job `J` present in `jobs[]` + `job.conclusion == SUCCESS` + required steps present |
| `C3` | `"CI generated the required test artifact A for commit S."` | `C1` requirements + artifact `A` present in `artifacts[]` + `artifact.run_id == run.run_id` + `artifact.subject_commit == S` |
| `C4` | `"The repository has CI configured."` | `.github/workflows/*.yml` present (`CONFIGURED` capability; does not verify execution) |

---

## 2. 20-Case CI Test Corpus (`CI-01` – `CI-20`)

| ID | Scenario | Expected State / Finding | Claim Verification |
|---|---|---|---|
| `CI-01` | No `.github/workflows/` directory | `NOT_FOUND`, `CI_WORKFLOW_NOT_FOUND` (`VERIFIED_OBSERVATION`) | `C4 = UNVERIFIED`, `C1 = UNVERIFIED` |
| `CI-02` | Workflow file exists | `CONFIGURED`, `CI_WORKFLOW_CONFIGURED` (`DECLARED_CAPABILITY`) | `C4 = VERIFIED`, `C1 = UNVERIFIED` |
| `CI-03` | Workflow exists, no run triggered | `CI_TRIGGER_NOT_OBSERVED` | `C1 = UNVERIFIED` |
| `CI-04` | Successful run for current SHA `S` | `COMPLETED` / `SUCCESS` / `SUBJECT_MATCH = MATCH`, `CI_RUN_SUCCESS` | `C1 = VERIFIED` |
| `CI-05` | Successful run for previous SHA `A` while `HEAD = B` | `SUBJECT_MATCH = MISMATCH`, `CI_SNAPSHOT_MISMATCH`, `CI_RUN_STALE` | `C1(B) = UNVERIFIED` (`STALE`/`MISMATCH`) |
| `CI-06` | Run still executing | `RUNNING` (`IN_PROGRESS`), `CI_RUN_IN_PROGRESS` | `C1 = UNVERIFIED` |
| `CI-07` | Cancelled run | `CANCELLED`, `CI_RUN_CANCELLED` | `C1 = UNVERIFIED` |
| `CI-08` | Required job failed | `FAILURE`, `CI_RUN_FAILURE`, `CI_JOB_FAILURE` | `C2 = CONTRADICTED` / `FAILURE` |
| `CI-09` | Unrelated job (`lint`) passed, required job (`test`) not run | `CI_REQUIRED_JOB_MISSING` | `C2 = UNVERIFIED` |
| `CI-10` | Missing required job in workflow/run | `CI_REQUIRED_JOB_MISSING` | `C2 = UNVERIFIED` |
| `CI-11` | Required artifact absent from run | `CI_ARTIFACT_MISSING` | `C3 = UNVERIFIED` |
| `CI-12` | Artifact belongs to different run (`run-old`) or different commit | `CI_ARTIFACT_MISMATCH` | `C3 = MISMATCH` |
| `CI-13` | Workflow file changed after run (`workflow_sha != current_workflow_sha`) | `CI_WORKFLOW_MISMATCH` | Claim-sensitive (`UNVERIFIED` for new workflow definition) |
| `CI-14` | Broad workflow permissions (`write-all` or missing `permissions:`) | `CI_PERMISSIONS_BROAD` (`SECURITY_CONFIGURATION_FINDING`, not `COMPROMISED`) | Security finding preserved |
| `CI-15` | Unpinned third-party action (`actions/checkout@v6`) | `CI_UNPINNED_ACTION` (`UNPINNED_ACTION != COMPROMISED_ACTION`) | Supply-chain finding preserved |
| `CI-16` | `pull_request_target` trigger declared | `CI_TRIGGER_POLICY_RISK` | Security review required |
| `CI-17` | Manual `workflow_dispatch` only | `TRIGGER_DECLARED` (trigger coverage limited; push/PR not automatic) | Coverage limitation recorded |
| `CI-18` | CI API / network unavailable | `NOT_OBSERVABLE` (not `CI_FAILED`) | `C1 = NOT_OBSERVABLE` |
| `CI-19` | Rerun (`run_attempt: 2`) succeeded on original `GITHUB_SHA` | Bound to `run_attempt: 2` and original `commit_sha` | `C1 = VERIFIED` for original `GITHUB_SHA` |
| `CI-20` | CI passes for `commit = S`, local working tree dirty afterward (`S_dirty`) | `CI_RUN_STALE`, `CI_SNAPSHOT_MISMATCH` | `C1(S_dirty) = STALE` |
