# ATSAS — Arena Tools, Skills, Agentic System

> **ATSAS** defines and organizes what an Arena agent can use and how its agentic system operates.  
> **AIF (Agent Assurance Interface)** defines what can legitimately be claimed about the resulting work.

---

## Overview

**ATSAS (Arena Tools, Skills, Agentic System)** is a repository-governed architecture for extending and assuring agent-driven software work in Arena. It organizes **tools, skills, agent behavior, repository constraints, execution protocols, and assurance mechanisms** into explicit, composable interfaces.

```text
                 ATSAS
                   │
       ┌───────────┼───────────┐
       ↓           ↓           ↓
     TOOLS       SKILLS      AGENTIC
       │           │         SYSTEM
       │           │           │
       └───────────┼───────────┘
                   ↓
             REPOSITORY
             GOVERNANCE
                   │
                   ↓
                  AIF
                   │
                   ↓
              ASSURANCE
```

---

## Relationship to AIF

**ATSAS** and **AIF** are distinct, complementary layers — **not** synonyms:

```text
ATSAS
└── Agentic System
    ├── Tools
    ├── Skills
    ├── Protocols
    ├── Repository interaction
    └── Agent behavior
             │
             ↓
            AIF
    Agent Assurance Interface
             │
    ├── Authority
    ├── Admission
    ├── Execution
    ├── Observation
    ├── Verification
    ├── Evidence
    ├── Acceptance
    └── Completion
```

### Architectural Boundary

* **ATSAS** = **capability + behavior architecture** (what an Arena agent can use and how its agentic system operates)
* **AIF** = **assurance + claim architecture** (what can legitimately be claimed about the resulting work)

### Foundational Axioms

> **A skill is not evidence.**  
> **A tool result is not automatically verification.**  
> **Execution is not completion.**  
> **Completion is an evidence-backed claim.**

---

## AIF — Agent Assurance Interface

> **AIF — Evidence-bound assurance for agent-driven software work.**

### Description

**AIF (Agent Assurance Interface)** is a repository-governed assurance protocol for agent-driven software work. It defines a common semantic interface for **authority, admission, execution, change attribution, observation, verification, evidence, acceptance, and completion**.

AIF prevents unsupported completion claims by binding every verified claim to its **scope, repository snapshot, execution context, evidence, provenance, and acceptance criteria**. It preserves uncertainty and partial observability through explicit states such as `UNKNOWN`, `NOT_OBSERVABLE`, `PARTIAL`, `STALE`, `MISMATCH`, and `CONTRADICTED`, rather than collapsing them into a binary pass/fail result.

AIF is **not** an agent framework, task executor, security scanner, CI system, or remediation engine. It is an **assurance layer** that composes those capabilities while establishing the semantic contract by which their outputs can be observed, verified, evidenced, accepted, and used to support completion claims.

```text
AUTHORITY
    ↓
ADMISSION
    ↓
EXECUTION
    ↓
OBSERVATION
    ↓
VERIFICATION
    ↓
EVIDENCE
    ↓
ACCEPTANCE
    ↓
COMPLETION
```

### Core Principle

> **No claim is verified without sufficient, scope-bounded, snapshot-bound evidence. No task is complete without evidence satisfying every mandatory acceptance criterion.**

### Architectural Distinction: Execution vs. Assurance

```text
AIF does not make the work happen.
AIF determines what may be claimed about what happened.
```

| Concern | Authority / Semantic Layer |
| :--- | :--- |
| May this operation occur? | **Authority / Admission** |
| Did an operation actually execute? | **Execution evidence** |
| What changed? | **Change attribution** |
| What was observable? | **Observation** |
| Does observation satisfy the claim? | **Verification** |
| What proves the verification? | **Evidence** |
| Does evidence satisfy the contract? | **Acceptance** |
| May the task be declared complete? | **Completion** |

This separation enforces the **“NO EVIDENCE → NO VERIFIED CLAIM”** invariant without turning AIF itself into CI, an executor, or a policy engine.

---

## Epistemic & Assurance States

Rather than collapsing verification into a lossy boolean (`pass` / `fail`), AIF preserves explicit epistemic states across observations, claims, and acceptance criteria:

| State | Meaning | May Support `COMPLETE`? |
| :--- | :--- | :---: |
| `VERIFIED` | Sufficient, fresh, scope-bounded, snapshot-bound evidence satisfies the claim. | Yes |
| `UNKNOWN` | Claim has not yet been evaluated or observation is indeterminate. | No |
| `NOT_OBSERVABLE` | The execution environment or tool surface cannot observe the target property. | No |
| `PARTIAL` | Evidence covers only a subset of the declared scope or acceptance criteria. | No |
| `STALE` | Evidence is bound to an older repository snapshot that was subsequently modified. | No |
| `MISMATCH` | Observed snapshot, scope, or output diverges from the claimed target or value. | No |
| `CONTRADICTED` | Direct counter-evidence refutes the claim or violates an acceptance criterion. | No |

---

## Repository Structure

```text
ATSAS/
├── README.md                                  # Canonical overview of ATSAS and AIF
├── ARENA_REPOSITORY_ASSURANCE_MATRIX.md       # 18-domain Repository Assurance & Regression Matrix
├── ARENA_ASSURANCE_TEST_MATRIX.md             # 42-case (AAI-001..034, P-001..008) Assurance Test Matrix v0.1
├── ARENA_CAPABILITY_OVERLAP_MATRIX.md         # 14-skill × 42-case Capability Overlap & Adapter Audit
├── ARENA_AIF_V01_FREEZE_REVIEW.md             # Adversarial Freeze Review of AIF-001..020 (+A) & C-01..C-08
├── ARENA_CANONICAL_DATA_MODEL.md              # Canonical Data Model v0.1 (14-Type Semantic Kernel)
├── ARENA_SEMANTIC_KERNEL_LAYOUT_REVIEW.md     # Semantic Kernel Layout, Ownership & Versioning Freeze Review
├── ARENA_PHASE12_INTERFACE_FREEZE_AND_BRANCH_AUDIT.md # Phase 12 Ownership Freeze & Phase 13/14 Consistency Audit
├── .agent/                                    # Phase 0/1 Engineering Process Archive & CLI Wrappers
│   ├── README.md                              # End-to-end process pipeline & quickstart for .agent/
│   ├── tools/                                 # Zero-dependency CLI wrappers (aif-red-suite delegates to tests/aif-v01-red-suite.py)
│   └── skills/                                # 9 meta-engineering process skills + _shared/aif/ (VERSION = 0.1.0)
├── .claude/
│   ├── assurance/                             # Canonical executable assurance design & audit artifacts
│   │   ├── invariants.md                      # 11 Arena Assurance Invariants (AAI-001..AAI-011)
│   │   ├── test-matrix.md                     # Historical Phase 0/1 Test Matrix (expanded to 49 cases in _shared/aif/tests/cases.yaml)
│   │   ├── state-model.md                     # 6-stage pipeline, state machine & orthogonal dimensions
│   │   ├── evidence-schema.md                 # 5-snapshot ArenaEvidenceReceipt & SkillEvalReceipt
│   │   ├── capability-map.md                  # Capability-by-capability audit of .claude/skills/
│   │   ├── component-contracts.md             # v0.1 Normative Interface Contracts (C-01..C-08)
│   │   ├── aif-v01-freeze-review.md           # Adversarial Freeze Review of C-01..C-08
│   │   ├── canonical-data-model.md            # Canonical Data Model v0.1 (14 Core Types across 13 Modular Schemas)
│   │   ├── semantic-kernel-layout-review.md   # Semantic Kernel Layout, Ownership & Versioning Freeze Review
│   │   ├── phase12-interface-freeze-audit.md  # Phase 12 Cross-Skill Ownership & Interface Freeze Boundary
│   │   └── phase13-consistency-normalization-audit.md # Phase 13 & 14 Consistency, Normalization & Execution Verification Report
│   └── skills/                                # Canonical ATSAS Agent Skills library (22 skills + _shared/aif/ kernel)
│       ├── README.md                          # Skills index (14 imported + 8 Wave-1 AIF skills), provenance & quickstart
│       ├── _shared/aif/                       # Non-skill AIF-0.1.0 Semantic Kernel (55 invariants AIF-001..055 + 8 *A, 13 schemas, 10 producers, 49 cases)
│       ├── arena-intake-and-authority/        # Wave-1 (C-01): Authority & admission owner
│       ├── agent-change-scope-audit/          # Wave-1 (C-02): Change attribution & scope producer
│       ├── dependency-supply-chain-audit/     # Wave-1 (C-03): Dependency supply-chain provenance producer
│       ├── ci-workflow-audit/                 # Wave-1 (C-04): CI configuration & execution evidence producer
│       ├── test-execution-and-evidence-audit/ # Wave-1 (C-05): Test execution & coverage evidence producer
│       ├── evidence-receipt-generator/        # Wave-1 (C-06): RFC 8785 JCS SHA-256 ArenaEvidenceReceipt assembler
│       ├── arena-completion-gate/             # Wave-1 (C-07): Pure completion gate evaluator (completion owner)
│       ├── skill-evaluation-harness/          # Wave-1 (C-08): 4-level Oracle & 79-case behavioral evaluation harness
│       ├── adr-writer/                        # Architecture Decision Record & ledger authoring
│       ├── authorization-boundary-scan/       # Compliance & content authorization boundary scanner
│       ├── contract-freeze-gate/              # Documentation audit & freeze-gate evaluator
│       ├── contract-implementation-sync/      # Contract-to-code field-for-field parity checker
│       ├── contract-normalization-pass/       # End-to-end contract normalization orchestrator
│       ├── dependency-vulnerability-audit/    # Lockfile dependency vulnerability auditor
│       ├── doc-symbol-audit/                  # Cross-doc symbol declaration & diff extractor
│       ├── docs-integrity-check/              # Markdown fence balance & internal link checker
│       ├── docs-monolith-partition/           # Monolith-to-partitioned-docs migration workflow
│       ├── docs-normalization-commit-plan/    # Ordered commit planning for normalization passes
│       ├── repo-onboarding-audit/             # AGENTS.md / CLAUDE.md onboarding auditor
│       ├── secret-leak-scan/                  # Zero-dependency hardcoded credential scanner
│       ├── session-git-sync-check/            # Sandbox git checkout vs. remote branch verifier
│       └── skill-creator/                     # Agent Skills generator & structural spec validator
├── spec/                                      # Formal specifications
│   ├── 00-overview.md                         # Architectural overview & boundary axioms
│   ├── 01-atsas-architecture.md               # ATSAS: Tools, Skills, Agentic System & Governance
│   ├── 02-aif-protocol.md                     # AIF: 9-concern protocol & Completion State Machine
│   ├── 03-epistemic-states.md                 # Non-binary epistemic state model & lattice
│   ├── 04-invariants-and-axioms.md            # Normative invariants (AIF-INV-001 .. AIF-INV-008)
│   ├── 05-skill-expansion-roadmap.md          # 4-Layer & P0..P4 Arena Skill Expansion Roadmap
│   ├── 06-wave1-skill-interfaces.md           # Provisionally Frozen Wave-1 Skill Interfaces (W1..W8)
│   └── 07-wave1-red-pressure-matrix.md        # Wave-1 RED & Pressure-Test Behavioral Matrix
├── schemas/                                   # Language-agnostic JSON Schemas (Draft 2020-12)
│   ├── atsas-tool.schema.json                 # Tool capability & observation contract
│   ├── atsas-skill.schema.json                # Skill definition & verification boundary
│   ├── atsas-governance.schema.json           # Repository governance & authority policy
│   ├── aif-snapshot.schema.json               # Repository snapshot & change attribution
│   ├── aif-execution.schema.json              # Admitted execution & raw observation record
│   ├── aif-evidence.schema.json               # Scope-bounded, snapshot-bound evidence artifact
│   ├── aif-claim.schema.json                  # Epistemic claim & verification record
│   ├── aif-canonical-data-model.schema.json   # Canonical Data Model v0.1 (9 Core Shared Types)
│   ├── aif-evidence-ref.schema.json           # Shared EvidenceRef v0.1 contract
│   ├── aif-evidence-receipt.schema.json       # ArenaEvidenceReceipt (W7) contract
│   ├── aif-skill-eval-receipt.schema.json     # SkillEvalReceipt (PHASE 2) behavioral eval contract
│   └── aif-completion-manifest.schema.json    # End-to-end AIF assurance & completion manifest
├── examples/                                  # Canonical valid & invalid assurance manifests
│   ├── governance-policy.json                 # Example repository governance contract
│   ├── tool-bash.json                         # Example ATSAS Tool capability contract
│   ├── skill-tdd.json                         # Example ATSAS Skill procedural contract
│   ├── valid-canonical-data-model.json        # Valid 9-Type Canonical Data Model v0.1 bundle
│   ├── valid-evidence-ref.json                # Valid shared EvidenceRef v0.1 instance
│   ├── valid-evidence-receipt.json            # Valid ArenaEvidenceReceipt (W7) instance
│   ├── valid-skill-eval-receipt.json          # Valid SkillEvalReceipt (PHASE 2) instance
│   ├── valid-completion-manifest.json         # Valid end-to-end VERIFIED completion manifest
│   ├── invalid-stale-evidence.json            # Rejected: post-evidence edit renders claim STALE
│   ├── invalid-partial-observability.json     # Rejected: PARTIAL / NOT_OBSERVABLE criteria
│   └── invalid-skill-as-evidence.json         # Rejected: skill invocation claimed without evidence
├── bin/
│   └── aif-verify                             # Reference invariant (AIF-001..055) & schema validator CLI
└── tests/
    ├── aif-v01-red-suite.py                   # Canonical AIF-0.1.0 kernel, 63-invariant & 49-case behavioral suite
    └── run-tests.sh                           # Single canonical repository test entrypoint
```

---

## Bundled ATSAS Skills Library (`.claude/skills/`)

`.claude/skills/` contains **22 validated Agent Skills** (`14` skills imported from `Abdus2023/streamforge-stremio` + `8` Wave-1 AIF-0.1.0 components `C-01`..`C-08`) plus the non-skill shared semantic kernel [`.claude/skills/_shared/aif/`](./.claude/skills/_shared/aif/) (`VERSION = 0.1.0`, `55` primary invariants `AIF-001`..`AIF-055` + `8` sub-invariants = `63` rules, `13` modular JSON Schemas encoding the `14` core Semantic Kernel types, `10` producer adapter contracts, and the `49`-case `cases.yaml` behavioral specification).

| Skill | Scope / Adaptation | Role / Layer | Bundled Scripts / Assets |
| :--- | :--- | :--- | :--- |
| [`arena-intake-and-authority`](./.claude/skills/arena-intake-and-authority/) | `ARENA_GENERIC` | `C-01` Authority & Admission Owner | `scripts/evaluate_intake.py` (`14/14` tests) |
| [`agent-change-scope-audit`](./.claude/skills/agent-change-scope-audit/) | `ARENA_GENERIC` | `C-02` Change Attribution & Scope Producer | `scripts/audit_change_scope.py` (`9/9` tests) |
| [`dependency-supply-chain-audit`](./.claude/skills/dependency-supply-chain-audit/) | `ARENA_GENERIC` | `C-03` Dependency Provenance Producer | `scripts/audit_supply_chain.py` (`16/16` tests) |
| [`ci-workflow-audit`](./.claude/skills/ci-workflow-audit/) | `ARENA_GENERIC` | `C-04` CI Configuration & Run Evidence Producer | `scripts/audit_ci_workflow.py` (`21/21` tests) |
| [`test-execution-and-evidence-audit`](./.claude/skills/test-execution-and-evidence-audit/) | `ARENA_GENERIC` | `C-05` Test Execution & Coverage Evidence Producer | `scripts/audit_test_execution.py` (`27/27` tests) |
| [`evidence-receipt-generator`](./.claude/skills/evidence-receipt-generator/) | `ARENA_GENERIC` | `C-06` RFC 8785 JCS SHA-256 Receipt Assembler | `scripts/generate_receipt.py`, `validate_receipt.py`, `canonicalize_receipt.py` (`19/19` tests) |
| [`arena-completion-gate`](./.claude/skills/arena-completion-gate/) | `ARENA_GENERIC` | `C-07` Pure Completion Gate Evaluator (Completion Owner) | `scripts/evaluate_completion.py`, `validate_completion_result.py` (`22/22` tests) |
| [`skill-evaluation-harness`](./.claude/skills/skill-evaluation-harness/) | `ARENA_GENERIC` | `C-08` 4-Level Oracle & Skill Behavior Evaluator | `scripts/discover_cases.py`, `run_case.py`, `run_suite.py`, `compare_result.py`, `generate_report.py` (`13/13` tests, `79` corpus cases) |
| [`session-git-sync-check`](./.claude/skills/session-git-sync-check/) | `ARENA_GENERIC` | Repository Hygiene | `scripts/git_sync_check.sh` |
| [`repo-onboarding-audit`](./.claude/skills/repo-onboarding-audit/) | `ARENA_GENERIC` | Repository Hygiene | `scripts/audit_agents_md.py` |
| [`dependency-vulnerability-audit`](./.claude/skills/dependency-vulnerability-audit/) | `ARENA_GENERIC` | Security & Hygiene | `scripts/run_dependency_audit.sh`, `scripts/_summarize_npm_audit.py` |
| [`secret-leak-scan`](./.claude/skills/secret-leak-scan/) | `ARENA_GENERIC` | Security & Hygiene | `scripts/scan_secrets.py` |
| [`authorization-boundary-scan`](./.claude/skills/authorization-boundary-scan/) | `ARENA_GENERIC` (`STREAMFORGE`) | Content Compliance Boundary | `scripts/scan_authorization_boundary.py` |
| [`docs-monolith-partition`](./.claude/skills/docs-monolith-partition/) | `ARENA_GENERIC` | Contract & Docs Architecture | `assets/migration-matrix-template.md`, `references/maintenance-rules.md` |
| [`docs-integrity-check`](./.claude/skills/docs-integrity-check/) | `ARENA_GENERIC` | Contract & Docs Verification | `scripts/check_fences.sh`, `scripts/check_links.py` |
| [`doc-symbol-audit`](./.claude/skills/doc-symbol-audit/) | `ARENA_GENERIC` | Contract & Docs Verification | `scripts/list_declared_symbols.py`, `scripts/extract_symbol_occurrences.py` |
| [`adr-writer`](./.claude/skills/adr-writer/) | `ARENA_GENERIC` | Decision Governance | `assets/adr-template.md`, `assets/ledger-entry-template.md`, `references/status-discipline.md` |
| [`contract-freeze-gate`](./.claude/skills/contract-freeze-gate/) | `ARENA_GENERIC` (`STREAMFORGE`) | Documentation Freeze Gate | `assets/documentation-audit-template.md`, `references/freeze-gate-checklist.md` |
| [`contract-implementation-sync`](./.claude/skills/contract-implementation-sync/) | `ARENA_GENERIC` (`STREAMFORGE`) | Contract-to-Code Parity | `scripts/check_contract_parity.py` |
| [`docs-normalization-commit-plan`](./.claude/skills/docs-normalization-commit-plan/) | `ARENA_GENERIC` | Change Attribution & Git | `references/commit-ordering-checklist.md` |
| [`contract-normalization-pass`](./.claude/skills/contract-normalization-pass/) | `ARENA_GENERIC` (`STREAMFORGE`) | Normalization Orchestration | `assets/final-report-long-template.md`, `assets/final-report-short-template.md`, `references/operating-principles.md` |
| [`skill-creator`](./.claude/skills/skill-creator/) | `ARENA_GENERIC` | Skill Authoring & Structural Validator | `scripts/validate_skill.py`, `references/writing-patterns.md`, `references/lessons-learned.md` |

---

## Quickstart: Canonical Verification Entrypoint

`./tests/run-tests.sh` is the **single canonical test entrypoint** for the repository. It validates all JSON Schemas, compliant/rejected manifests, all 22 skills in `.claude/skills/`, the `AIF-0.1.0` kernel & 49-case RED/Pressure suite (`tests/aif-v01-red-suite.py`), all `C-01`..`C-08` component self-tests, and Phase 12/13 consistency invariants.

### Validate a compliant completion manifest

```bash
./bin/aif-verify examples/valid-completion-manifest.json
```

### Inspect invariant violations on invalid manifests

```bash
# Fails AIF-INV-003 (Snapshot freshness / STALE evidence)
./bin/aif-verify examples/invalid-stale-evidence.json

# Fails AIF-INV-005 & AIF-INV-007 (PARTIAL / NOT_OBSERVABLE states)
./bin/aif-verify examples/invalid-partial-observability.json

# Fails AIF-INV-001 & AIF-INV-002 (Skill / execution claimed as evidence)
./bin/aif-verify examples/invalid-skill-as-evidence.json
```

### Run the full test suite

```bash
./tests/run-tests.sh
```
