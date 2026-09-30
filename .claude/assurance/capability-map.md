# Arena Assurance Capability Map & Four-Layer Architecture (v0.1)

> **Status**: `VERIFIED` (Overlap Audit Complete — Normative Input to v0.1 Component Contracts)
> **Scope**: `ARENA_GENERIC`

---

## 1. Current Capability Map (`.claude/skills/` vs. Assurance Requirements)

| Assurance capability | Existing skill | Coverage | Gap |
|---|---|---|---|
| Git snapshot freshness | `session-git-sync-check` | `HIGH` | none obvious (not a change-provenance `DIFF(S0, S1)` system) |
| Repository onboarding | `repo-onboarding-audit` | `HIGH` | authority still absent |
| Content/access authorization boundary | `authorization-boundary-scan` | `HIGH` | agent authority is different |
| Secret scanning | `secret-leak-scan` | `HIGH` | history/evidence model is weak (`detector`, not receipt/authority) |
| Dependency vulnerabilities | `dependency-vulnerability-audit` | `HIGH` | broader supply-chain evidence absent |
| Documentation integrity | `docs-integrity-check` | `HIGH` | criterion-specific |
| Contract consistency | `contract-implementation-sync` | `HIGH` | not general execution verification |
| Contract freeze | `contract-freeze-gate` | `HIGH` | not general completion gate |
| Multi-stage contract workflow | `contract-normalization-pass` | `HIGH` | documentation-specific |
| Agent action authority | — | `NONE` | **new primitive (`01 arena-intake-and-authority`)** |
| Agent change-scope attribution (`DIFF(S0, S1)`) | — | `NONE` | **new primitive (`02 agent-change-scope-audit`)** |
| Supply-chain resolution/integrity/provenance | `dependency-vulnerability-audit` | `LOW` | **broader skill needed (`03 dependency-supply-chain-audit`)** |
| CI configuration/execution distinction | — | `NONE` | **new primitive (`04 ci-workflow-audit`)** |
| Test execution evidence | — | `NONE` | **new primitive (`05 test-execution-and-evidence-audit`)** |
| Evidence receipt/provenance | — | `NONE` | **new primitive (`06 evidence-receipt-generator`)** |
| General completion gate | — | `NONE` | **new primitive (`07 arena-completion-gate`)** |
| Behavioral skill evaluation | `skill-creator` | `LOW` | **major gap (`08 skill-evaluation-harness`)** |

---

## 2. Three Structural Corrections from the Overlap Audit

### 2.1 Two Kinds of Authorization (Never Merge)

```text
                       AUTHORIZATION
                             │
              ┌──────────────┴──────────────┐
              │                             │
       DOMAIN AUTHORITY              AGENT AUTHORITY
              │                             │
     "Is this content/use            "May this agent
      permitted?"                     modify this?"
              │                             │
     authorization-                 arena-intake-
     boundary-scan                  and-authority
```

- `authorization-boundary-scan` asks: *"Does this implementation appear to violate the project's content/authorization boundary?"*
- `arena-intake-and-authority` asks: *"Was THIS AGENT authorized to perform THIS ACTION on THIS RESOURCE under THIS REQUEST?"*

### 2.2 Secret Scanning: Don't Create Another Skill (`Secret skill needed = NO`)

`secret-leak-scan` already distinguishes `HIGH`, `LOW`, `placeholder`, and `clean`, and explicitly warns that *a clean scan is not proof of safety*. The missing capability is **evidence integration**, not another regex scanner:

```text
secret-leak-scan             = detector (0 HIGH, 0 LOW, scanner=specific heuristic, coverage=current tree only)
      ↓
evidence-receipt-generator   = evidence adapter (binds result + coverage metadata + snapshot S2 into SCANNER_NO_MATCH)
      ↓
arena-completion-gate        = decision authority (evaluates whether that scoped claim satisfies the acceptance criterion)
```

### 2.3 Dependency Vulnerability Audit: Compose as Detector (`New vulnerability scanner needed = NO`)

`dependency-vulnerability-audit` remains intact as the advisory detector and is consumed by `dependency-supply-chain-audit`:

```text
dependency-vulnerability-audit
          │
          │ detector
          ▼
dependency-supply-chain-audit
          │
          ├── manifest
          ├── lockfile
          ├── resolution
          ├── registry
          ├── integrity
          ├── lifecycle
          ├── provenance
          └── vulnerability result
```

---

## 3. Revised Eight-Component Set (`01` – `08`)

| ID | Component Name | Layer | Functional Role | Relationship to Existing `.claude/skills/` |
|---|---|---|---|---|
| `01` | `arena-intake-and-authority` | `AUTHORITY` | Authority / Decision | New primitive; composes `session-git-sync-check` (`S0`) & `repo-onboarding-audit` (context); orthogonal to `authorization-boundary-scan` |
| `02` | `agent-change-scope-audit` | `VERIFICATION / AUDIT` | Verifier (Change Provenance) | New primitive; computes `AGENT_CHANGE = DIFF(S0, S1)` separating `PREEXISTING` (`DIFF(comparison_base, S0)`) & `GENERATED` |
| `03` | `dependency-supply-chain-audit` | `VERIFICATION / AUDIT` | Verifier (Orchestrator) | Orchestrates `dependency-vulnerability-audit` detector + manifest, lockfile, resolution, registry, integrity, lifecycle, provenance |
| `04` | `ci-workflow-audit` | `VERIFICATION / AUDIT` | Verifier | New primitive; separates `CI_CONFIGURATION` (`WHAT CI IS CONFIGURED TO DO`) from `CI_EXECUTION` (`WHAT CI ACTUALLY EXECUTED`) |
| `05` | `test-execution-and-evidence-audit` | `VERIFICATION / AUDIT` | Verifier | New primitive; enforces `TEST_AVAILABLE → TEST_STARTED → TEST_EXECUTED → TEST_PASSED → TEST_EVIDENCED` |
| `06` | `evidence-receipt-generator` | `DECISION / ASSURANCE` | Evidence Infrastructure | New primitive; adapts detector outputs (`secret-leak-scan`, `docs-integrity-check`, etc.) & verifier outputs into `ArenaEvidenceReceipt` |
| `07` | `arena-completion-gate` | `DECISION / ASSURANCE` | Authority / Decision | New terminal gate; evaluates mandatory acceptance criteria over `ArenaEvidenceReceipt`; composes `contract-freeze-gate` when applicable |
| `08` | `skill-evaluation-harness` | `META / DEVELOPMENT` | Meta-Assurance | New behavioral evaluator (`RED → GREEN → Pressure → Regression`) paired with `skill-creator` emitting `SkillEvalReceipt` |

---

## 4. Four-Layer `.claude/skills/` Architecture & Five Component Roles

```text
┌─────────────────────────────────────────────────────────┐
│                 DECISION / ASSURANCE                    │
│                                                         │
│  arena-completion-gate              [07 new authority]  │
│  evidence-receipt-generator         [06 new evidence]   │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                 VERIFICATION / AUDIT                    │
│                                                         │
│  agent-change-scope-audit           [02 new verifier]   │
│  ci-workflow-audit                  [04 new verifier]   │
│  test-execution-and-evidence-audit  [05 new verifier]   │
│  dependency-supply-chain-audit      [03 new verifier]   │
│                                                         │
│  secret-leak-scan                   [existing detector] │
│  dependency-vulnerability-audit     [existing detector] │
│  authorization-boundary-scan        [existing detector] │
│  docs-integrity-check               [existing detector] │
│  contract-implementation-sync       [existing verifier] │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                    AUTHORITY                             │
│                                                         │
│  arena-intake-and-authority         [01 new authority]  │
│  repo-onboarding-audit              [existing context]  │
│  session-git-sync-check             [existing]          │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                    META / DEVELOPMENT                    │
│                                                         │
│  skill-creator                      [existing]          │
│  skill-evaluation-harness           [08 new meta]       │
└─────────────────────────────────────────────────────────┘
```

### Separation of Detectors vs. Verifiers vs. Authorities

| Role | Responsibility | Components |
|---|---|---|
| **Detectors** | Discover raw repository facts; never declare task completion. | `secret-leak-scan`, `dependency-vulnerability-audit`, `authorization-boundary-scan`, `docs-integrity-check`, `doc-symbol-audit` |
| **Verifiers** | Establish narrower, snapshot-bound verification claims. | `contract-implementation-sync`, `test-execution-and-evidence-audit`, `ci-workflow-audit`, `agent-change-scope-audit`, `dependency-supply-chain-audit` |
| **Authority / Decision** | Determine whether the next state transition (`ADMITTED`, `COMPLETABLE`) is permitted. | `arena-intake-and-authority`, `arena-completion-gate`, `contract-freeze-gate` (for doc freeze) |
| **Evidence Infrastructure** | Bind claims, detector outputs, and 3-snapshot provenance into `ArenaEvidenceReceipt` without manufacturing missing evidence. | `evidence-receipt-generator` |
| **Meta-Assurance** | Author, structurally validate, and behaviorally evaluate skills under `RED → GREEN → Pressure`. | `skill-creator`, `skill-evaluation-harness` |

---

## 5. Capability Matrix Against the 42 Behavioral Cases

Legend: `✓` = substantially covered (`COVERED` / strong existing detector), `~` = partial coverage (`PARTIALLY_COVERED` / `CONFLICTING` edge needing adapter), `—` = genuine gap (`UNCOVERED`). Note: documentation-specific skills (`docs-monolith-partition`, `doc-symbol-audit`, `adr-writer`, `docs-normalization-commit-plan`, `contract-normalization-pass`) are retained as `ORPHANED` relative to the 42 runtime cases, and `DUPLICATE` creation of secret/vulnerability scanners is prevented by reusing `secret-leak-scan` and `dependency-vulnerability-audit`.

| Case ID | Scenario | Existing Coverage | Target Component / Layer | Classification Detail |
|---|---|---|---|---|
| `AAI-001` | Vague `"fix everything"` scope | `—` | `01 arena-intake-and-authority` | `UNCOVERED` |
| `AAI-002` | `"Investigate CI"` (`INSPECT_ONLY`) | `—` | `01 arena-intake-and-authority` | `UNCOVERED` |
| `AAI-003` | One explicit file authorized | `—` | `01 arena-intake-and-authority` | `UNCOVERED` |
| `AAI-004` | Repo policy approval conflict | `—` | `01 arena-intake-and-authority` | `UNCOVERED` |
| `AAI-005` | Unauthorized `README.md` diff | `—` | `02 agent-change-scope-audit` | `UNCOVERED` |
| `AAI-006` | Generated `dist/` artifact | `—` | `02 agent-change-scope-audit` | `UNCOVERED` |
| `AAI-007` | Pre-existing dirty tree (`DIFF(S0, S1)`) | `—` | `02 agent-change-scope-audit` | `PARTIALLY_COVERED` (`session-git-sync-check` checks sync, not `DIFF(S0,S1)`) |
| `AAI-008` | Unrelated file deletion | `—` | `02 agent-change-scope-audit` | `UNCOVERED` |
| `AAI-009` | `.env.example` placeholder | `✓` | `secret-leak-scan` + `06 evidence-receipt-generator` | `COVERED` by detector (`PLACEHOLDER_RE`); adapted into receipt by `06` |
| `AAI-010` | High-entropy / suspicious fixture | `✓` | `secret-leak-scan` + `06 evidence-receipt-generator` | `PARTIALLY_COVERED` (`LOW` regex in `secret-leak-scan`; adapted as `SUSPECTED`) |
| `AAI-011` | Historical Git secret exposure | `~` | `secret-leak-scan` + `06 evidence-receipt-generator` | `PARTIALLY_COVERED` (`secret-leak-scan` flags working-tree scope limit) |
| `AAI-012` | Single scanner coverage scope | `~` | `06 evidence-receipt-generator` | `PARTIALLY_COVERED` (`SCANNER_NO_MATCH` / `PARTIAL_COVERAGE` receipt binding) |
| `AAI-013` | Manifest without lockfile | `~` | `03 dependency-supply-chain-audit` | `CONFLICTING` (`run_dependency_audit.sh` exits `0`; `03` classifies `PARTIALLY_OBSERVABLE`) |
| `AAI-014` | Manifest / lockfile drift | `—` | `03 dependency-supply-chain-audit` | `UNCOVERED` |
| `AAI-015` | Transitive vulnerability | `✓` | `dependency-vulnerability-audit` (consumed by `03`) | `COVERED` by existing detector (`DUPLICATE` scanner avoided) |
| `AAI-016` | `postinstall` lifecycle script | `—` | `03 dependency-supply-chain-audit` | `UNCOVERED` |
| `AAI-017` | Alternate registry configured | `—` | `03 dependency-supply-chain-audit` | `UNCOVERED` |
| `AAI-018` | `package.json` `"test"` script exists | `✓` | `repo-onboarding-audit` (consumed by `05`) | `COVERED` by `detect_manifests()` (`TEST_DECLARED` / `TEST_AVAILABLE`) |
| `AAI-019` | Workflow exists, no run | `—` | `04 ci-workflow-audit` | `UNCOVERED` |
| `AAI-020` | Stale CI run at old commit | `—` | `04 ci-workflow-audit` | `UNCOVERED` |
| `AAI-021` | Broad workflow permissions | `—` | `04 ci-workflow-audit` | `UNCOVERED` |
| `AAI-022` | Unsupported `"tests pass"` claim | `—` | `05 test-execution-and-evidence-audit` | `UNCOVERED` |
| `AAI-023` | Stale test output (`S2 != S1`) | `—` | `05 test-execution-and-evidence-audit` | `UNCOVERED` |
| `AAI-024` | Partial test suite execution | `—` | `05 test-execution-and-evidence-audit` | `UNCOVERED` |
| `AAI-025` | Missing process exit code | `—` | `05 test-execution-and-evidence-audit` | `UNCOVERED` |
| `AAI-026` | Modified tests in implementation diff | `—` | `05 test-execution-and-evidence-audit` | `UNCOVERED` |
| `AAI-027` | Unsupported receipt CI claim | `—` | `06 evidence-receipt-generator` | `UNCOVERED` |
| `AAI-028` | Snapshot mismatch (`S2 != head_commit`) | `—` | `06 evidence-receipt-generator` | `PARTIALLY_COVERED` (`bin/aif-verify` enforces `AAI-011`) |
| `AAI-029` | Narrow typecheck claim | `—` | `06 evidence-receipt-generator` | `UNCOVERED` |
| `AAI-030` | Narrow scanner scope claim | `—` | `06 evidence-receipt-generator` | `UNCOVERED` |
| `AAI-031` | Untested implementation code | `—` | `07 arena-completion-gate` | `UNCOVERED` |
| `AAI-032` | Passing tests with scope violation | `—` | `07 arena-completion-gate` | `UNCOVERED` |
| `AAI-033` | Split evidence across snapshots | `—` | `07 arena-completion-gate` | `UNCOVERED` |
| `AAI-034` | Missing mandatory criterion evidence | `—` | `07 arena-completion-gate` | `PARTIALLY_COVERED` (`contract-freeze-gate` covers doc freeze only) |
| `P-001` | `"Done, everything implemented and tested"` | `—` | `05` + `06` + `07` (`08` pressure harness) | `UNCOVERED` |
| `P-002` | Audit edits unauthorized file to pass | `—` | `02` + `07` (`08` pressure harness) | `CONFLICTING` (enforces `AAI-010` `AUDIT ≠ REMEDIATION`) |
| `P-003` | Test runner unavailable | `—` | `05` + `06` + `07` (`08` pressure harness) | `UNCOVERED` (`NOT_OBSERVABLE`, never `PASSED`) |
| `P-004` | Verify `HEAD` A, then `HEAD` changes to B | `~` | `06` + `07` (`08` pressure harness) | `PARTIALLY_COVERED` (`AAI-011` `S2 != head_commit`) |
| `P-005` | User asks to `"just mark it complete"` | `—` | `01` + `07` (`08` pressure harness) | `UNCOVERED` |
| `P-006` | Scanner unavailable | `~` | `03` + `06` (`08` pressure harness) | `CONFLICTING` (`run_dependency_audit.sh` `SKIP` exit code; `06` records `PARTIAL_COVERAGE`) |
| `P-007` | CI unavailable, local tests pass | `—` | `04` + `05` + `07` (`08` pressure harness) | `UNCOVERED` |
| `P-008` | Authorized scope expands mid-task | `—` | `01` + `02` + `07` (`08` pressure harness) | `UNCOVERED` |

---

## 6. Post-Audit Architecture Status

| Requirement / Layer | Status |
|---|---|
| **Existing detector coverage** | `VERIFIED` (`secret-leak-scan`, `dependency-vulnerability-audit`, `authorization-boundary-scan`, `docs-integrity-check`, `repo-onboarding-audit`, `session-git-sync-check`, `contract-implementation-sync`, `contract-freeze-gate`, `contract-normalization-pass`, `doc-symbol-audit`, `adr-writer`, `docs-monolith-partition`, `docs-normalization-commit-plan`, `skill-creator`) |
| **Major duplication identified** | `VERIFIED` |
| **Separate secret skill needed** | `NO` (`secret-leak-scan` = detector; `evidence-receipt-generator` = adapter; `arena-completion-gate` = authority) |
| **New vulnerability scanner needed** | `NO` (`dependency-vulnerability-audit` retained as detector) |
| **Broader supply-chain layer (`03 dependency-supply-chain-audit`)** | `REQUIRED` |
| **Agent authority layer (`01 arena-intake-and-authority`)** | `REQUIRED` |
| **Change provenance layer (`02 agent-change-scope-audit`, `DIFF(S0, S1)`)** | `REQUIRED` |
| **CI evidence layer (`04 ci-workflow-audit`)** | `REQUIRED` |
| **Test evidence layer (`05 test-execution-and-evidence-audit`)** | `REQUIRED` |
| **Receipt layer (`06 evidence-receipt-generator`)** | `REQUIRED` |
| **Completion authority (`07 arena-completion-gate`)** | `REQUIRED` |
| **Skill behavioral evaluation (`08 skill-evaluation-harness`)** | `REQUIRED` |
