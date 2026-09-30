# ARENA_REPOSITORY_ASSURANCE_MATRIX

> **Canonical Repository Assurance Matrix for Arena Agent Mode (ATSAS + AIF)**  
> Unifying **Contract Assurance** and **Repository Assurance** under evidence-bound completion gates.

---

## 1. Architectural Convergence

A complete **Arena Agent Mode** requires two complementary assurance halves that converge at the **AIF Completion Gate**:

1. **Contract Assurance** (established by the documentation-as-contract workflow):
   ```text
   DOCUMENTATION → CONTRACT → DECISION → IMPLEMENTATION PARITY
   ```
2. **Repository Assurance** (established by the repository/operational correctness layer):
   ```text
   REPOSITORY → SECURITY → DEPENDENCIES → TESTS → CI → RUNTIME → ARTIFACT → RELEASE → EVIDENCE
   ```

```text
                       ARENA AGENT MODE (ATSAS + AIF)
                                     │
                      ┌──────────────┴──────────────┐
                      │                             │
                GOVERNANCE                     ASSURANCE
                      │                             │
              ┌───────┼────────┐         ┌──────────┼───────────┐
              │       │        │         │          │           │
            intake  scope  authority  security   supply      release
                                                  chain     provenance
              │       │        │         │          │           │
              └───────┴────────┘         └──────────┼───────────┘
                      │                             │
                      └──────────────┬──────────────┘
                                     │
                          repository correctness
                                     │
                ┌────────────────────┼───────────────────┐
                │                    │                   │
              docs                 code                runtime
                │                    │                   │
          contract sync          tests/CI          deployment
                │                    │                   │
                └────────────────────┼───────────────────┘
                                     │
                              COMPLETION GATE
                                     │
                              EVIDENCE RECEIPT
                                     │
                               CLAIM STATUS
```

---

## 2. Canonical Repository Assurance Matrix

Every task or audit executed in **Arena Agent Mode** evaluates the applicable rows of this matrix. No row may be marked `VERIFIED` without its corresponding empirical evidence bound to the current repository snapshot.

| # | Domain | Normative Question | Primary Skill / Gate | Required Evidence Artifact | Allowed Statuses |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Git** | Is `HEAD` the intended remote tip and is the working tree state known? | `session-git-sync-check` | `git rev-parse HEAD`, remote ref comparison, `git status --porcelain` | `VERIFIED`, `STALE`, `MISMATCH`, `BLOCKED` |
| 2 | **Scope** | Is this operation and file set explicitly authorized by the task intake? | `arena-intake-and-authority` | Signed/validated intake contract (`intake-contract.json`) vs. actual diff paths | `ADMITTED`, `REJECTED`, `ESCALATED` |
| 3 | **Docs** | Are authoritative contracts unique, fence-balanced, and link-valid? | `docs-integrity-check`, `doc-symbol-audit` | Fence/link check output + symbol occurrence diff across docs tree | `VERIFIED`, `CONTRADICTED`, `PARTIAL` |
| 4 | **Code** | Does the implementation match the frozen contract field-for-field? | `contract-implementation-sync` | `check_contract_parity.py` execution output at current snapshot | `VERIFIED`, `MISMATCH`, `PARTIAL`, `NOT_OBSERVABLE` |
| 5 | **Tests** | Are contract invariants and failure modes exercised by real tests? | `test-coverage-contract-audit` | Invariant-to-test mapping + test runner execution log & exit code | `VERIFIED`, `PARTIAL`, `CONTRADICTED`, `NOT_OBSERVABLE` |
| 6 | **CI** | Does CI actually execute and enforce required verification gates? | `ci-workflow-audit` | Workflow trigger/filter/command audit + CI execution run log | `VERIFIED`, `PARTIAL`, `MISMATCH`, `NOT_OBSERVABLE` |
| 7 | **Secrets** | Are working tree and Git commit history free of leaked credentials? | `secret-leak-scan`, `secret-and-credential-audit` | Scanner execution report across working tree and commit range | `VERIFIED`, `CONTRADICTED`, `PARTIAL` |
| 8 | **Dependencies** | Are vulnerable, deprecated, or lockfile-drifted dependencies accounted for? | `dependency-vulnerability-audit`, `dependency-supply-chain-audit` | Manifest ↔ lockfile parity check + native advisory scan summary | `VERIFIED`, `CONTRADICTED`, `PARTIAL`, `NOT_OBSERVABLE` |
| 9 | **Config** | Do source, `.env.example`, `README`, CI, and container configs agree? | `configuration-contract-audit` | Cross-boundary configuration matrix (`MISSING`, `CONFLICTING`, `UNDOCUMENTED`) | `VERIFIED`, `MISMATCH`, `PARTIAL` |
| 10 | **License** | Are repository, manifest, and dependency licensing obligations consistent? | `license-compliance-audit` | Repository `LICENSE` ↔ manifest SPDX ↔ dependency license table | `VERIFIED`, `MISMATCH`, `UNKNOWN` |
| 11 | **Generated** | Are generated code/types/schemas synchronized with their source-of-truth? | `generated-artifact-sync` | Regeneration dry-run + `git diff --exit-code` cleanliness proof | `VERIFIED`, `STALE`, `MISMATCH` |
| 12 | **Build** | Is the build artifact reproducible and traceable to the current snapshot? | `release-artifact-provenance` | Build command execution log + output artifact SHA-256 digest | `VERIFIED`, `CONTRADICTED`, `NOT_OBSERVABLE` |
| 13 | **Release** | Does the release artifact correspond to the reviewed commit and tag? | `release-artifact-provenance` | Tag → Commit SHA → Build → Artifact Digest → Provenance Manifest chain | `VERIFIED`, `MISMATCH`, `PARTIAL`, `NOT_OBSERVABLE` |
| 14 | **Runtime** | Does the container or service build, start, and pass readiness checks? | `runtime-deployment-audit` | Container/process startup log + health/readiness endpoint probe | `VERIFIED`, `PARTIAL`, `CONTRADICTED`, `NOT_OBSERVABLE` |
| 15 | **Migration** | Are schema/state/config migrations forward-safe, idempotent, and reversible? | `migration-safety-audit` | Forward apply + rollback/downgrade + idempotence execution evidence | `VERIFIED`, `PARTIAL`, `CONTRADICTED`, `NOT_OBSERVABLE` |
| 16 | **API** | Is public API / wire / CLI compatibility preserved or explicitly versioned? | `api-compatibility-audit` | Baseline vs. target API surface diff (`ADDED`, `REMOVED`, `BREAKING`) | `VERIFIED`, `CONTRADICTED`, `UNKNOWN` |
| 17 | **Observability** | Can liveness, readiness, timeouts, and degraded modes be observed? | `operational-readiness-audit` | `/health/live` vs. `/health/ready` verification + timeout/shutdown trace | `VERIFIED`, `PARTIAL`, `NOT_OBSERVABLE` |
| 18 | **Completion** | Is every mandatory claim backed by fresh, snapshot-bound evidence? | `arena-completion-gate`, `bin/aif-verify` | Validated AIF Completion Manifest & Completion Evidence Receipt | `PROVED`, `VERIFIED`, `PARTIALLY_VERIFIED`, `PROVISIONAL`, `BLOCKED` |

---

## 3. Domain Non-Conflation Rules

AIF and the Repository Assurance Matrix forbid collapsing distinct operational states into a single boolean check:

### 3.1 Task Authority (`arena-intake-and-authority`)
```text
user asked "inspect"   ≠   agent authorized to edit
user asked "analyze"   ≠   agent authorized to implement
issue exists in repo   ≠   agent authorized to fix out-of-scope files
```

### 3.2 Dependency & Supply Chain (`dependency-supply-chain-audit`)
```text
dependency exists
        ≠
dependency is supported
        ≠
dependency is current
        ≠
dependency has no known vulnerability
        ≠
dependency license is compatible
        ≠
lockfile resolves what CI expects
```

### 3.3 Continuous Integration (`ci-workflow-audit`)
```text
workflow file contains command
        ≠
workflow trigger/path filter matches branch
        ≠
workflow actually executed command
        ≠
command succeeded without ignore-error suppression
        ≠
required gate passed
```

### 3.4 Release & Artifact Provenance (`release-artifact-provenance`)
```text
build succeeded
        ≠
artifact exists
        ≠
artifact corresponds to reviewed source commit
        ≠
artifact is the artifact being deployed
        ≠
artifact digest can be independently verified
```

### 3.5 Migration Safety (`migration-safety-audit`)
```text
migration syntax is valid
        ≠
migration runs on empty state
        ≠
migration preserves existing data
        ≠
migration is idempotent on restart
        ≠
migration is safely reversible (rollback/downgrade)
```

### 3.6 Runtime & Container Readiness (`runtime-deployment-audit` & `operational-readiness-audit`)
```text
container image builds
        ≠
container process starts
        ≠
liveness endpoint (/health/live) responds
        ≠
application dependencies and readiness (/health/ready) are actually ready
```

---

## 4. Baseline Regression Matrix (`baseline-regression-audit`)

Whereas `contract-implementation-sync` verifies whether the implementation matches the **contract**, the **Baseline Regression Matrix** verifies whether a change introduced a regression relative to the **accepted repository baseline**:

```text
BASELINE (Snapshot S_0)
   ├── tests
   ├── behavior
   ├── artifacts
   ├── API surface
   └── resource/performance profile
          │
          ▼
       CHANGE (Snapshot S_final)
          │
          ▼
     RE-EXECUTE & COMPARE
          │
          ▼
   REGRESSION MATRIX
```

Every compared check or invariant is classified into one of six explicit states rather than a summary "tests passed":

| Regression State | Baseline ($S_0$) | Target ($S_{\text{final}}$) | Assurance Interpretation |
| :--- | :---: | :---: | :--- |
| `KNOWN_PASS` / `UNCHANGED` | Pass | Pass | Baseline behavior preserved (`VERIFIED`). |
| `KNOWN_FAIL` | Fail | Fail | Pre-existing failure; must be disclosed in `REMAINING_FAILURES`, never masked as pass. |
| `NEW_PASS` | Fail / Absent | Pass | Defect resolved or new invariant test added and verified (`VERIFIED`). |
| `NEW_FAIL` | Pass | Fail | **Regression introduced** (`CONTRADICTED` — blocks `COMPLETE`). |
| `UNCHANGED` | N/A (Metric) | Within bound | Non-boolean metric or artifact within accepted tolerance. |
| `UNKNOWN` | Unobserved | Unobserved | Not executed in one or both snapshots (`NOT_OBSERVABLE` / `UNKNOWN`). |
