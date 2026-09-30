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
├── .agent/                                    # Reusable ATSAS Tools, AIF-0.1 Protocol Kernel & Process Skills
│   ├── README.md                              # End-to-end process pipeline & quickstart for .agent/
│   ├── tools/                                 # Zero-dependency CLI tools + ATSAS Tool contracts
│   └── skills/                                # 7 process skills + _shared/aif/ protocol kernel
├── .claude/
│   ├── assurance/                             # Canonical executable assurance design artifacts
│   │   ├── invariants.md                      # 11 Arena Assurance Invariants (AAI-001..AAI-011)
│   │   ├── test-matrix.md                     # 42-case Behavioral & Pressure Test Matrix v0.1
│   │   ├── state-model.md                     # 6-stage pipeline, state machine & 4-axis vocabulary
│   │   ├── evidence-schema.md                 # 3-snapshot ArenaEvidenceReceipt & SkillEvalReceipt
│   │   ├── capability-map.md                  # Capability-by-capability audit of .claude/skills/
│   │   ├── component-contracts.md             # v0.1 Normative Interface Contracts (C-01..C-08)
│   │   ├── aif-v01-freeze-review.md           # 20-Invariant (+8 Sub-Invariant) Adversarial Freeze Review
│   │   ├── canonical-data-model.md            # Canonical Data Model v0.1 (14-Type Semantic Kernel)
│   │   └── semantic-kernel-layout-review.md   # Semantic Kernel Layout, Ownership & Versioning Freeze Review
│   └── skills/                                # Bundled ATSAS Agent Skills library (14 imported skills)
│       ├── README.md                          # Skills index, provenance, and quickstart
│       ├── adr-writer/                        # Architecture Decision Record & ledger authoring
│       ├── authorization-boundary-scan/       # Compliance & authorization boundary scanner
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
│       └── skill-creator/                     # Agent Skills generator & spec validator
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
│   └── aif-verify                             # Reference invariant & schema validator CLI
└── tests/
    └── run-tests.sh                           # Automated test suite for schemas, skills & invariants
```

---

## Bundled ATSAS Skills Library (`.claude/skills/`)

`.claude/skills/` currently contains the 14 [Agent Skills](https://agentskills.io/specification) imported from `Abdus2023/streamforge-stremio` (`arena/01a0e9bd-streamforge-stremio`), each annotated with its explicit portability scope (`SCOPE: ARENA_GENERIC`, plus `ADAPTATION: STREAMFORGE` where applicable) under the **"Location is not scope"** governance rule.

The 8 **Wave-1 Repository Assurance Skills** (`01 arena-intake-and-authority`, `02 agent-change-scope-audit`, `03 secret-and-credential-audit`, `04 dependency-supply-chain-audit`, `05 ci-workflow-audit`, `06 test-execution-and-evidence-audit`, `07 evidence-receipt-generator`, `08 arena-completion-gate`) are **`PROVISIONALLY FROZEN — interface level`** in [`spec/06-wave1-skill-interfaces.md`](./spec/06-wave1-skill-interfaces.md) with their pre-`SKILL.md` behavioral test cases in [`spec/07-wave1-red-pressure-matrix.md`](./spec/07-wave1-red-pressure-matrix.md):

| Skill | Scope / Adaptation | Category | Bundled Scripts / Assets |
| :--- | :--- | :--- | :--- |
| [`session-git-sync-check`](./.claude/skills/session-git-sync-check/) | `ARENA_GENERIC` | Repository Hygiene | `scripts/git_sync_check.sh` |
| [`repo-onboarding-audit`](./.claude/skills/repo-onboarding-audit/) | `ARENA_GENERIC` | Repository Hygiene | `scripts/audit_agents_md.py` |
| [`dependency-vulnerability-audit`](./.claude/skills/dependency-vulnerability-audit/) | `ARENA_GENERIC` | Security & Hygiene | `scripts/run_dependency_audit.sh`, `scripts/_summarize_npm_audit.py` |
| [`secret-leak-scan`](./.claude/skills/secret-leak-scan/) | `ARENA_GENERIC` | Security & Hygiene | `scripts/scan_secrets.py` |
| [`authorization-boundary-scan`](./.claude/skills/authorization-boundary-scan/) | `ARENA_GENERIC` (`STREAMFORGE`) | Governance & Compliance | `scripts/scan_authorization_boundary.py` |
| [`docs-monolith-partition`](./.claude/skills/docs-monolith-partition/) | `ARENA_GENERIC` | Contract & Docs Architecture | `assets/migration-matrix-template.md`, `references/maintenance-rules.md` |
| [`docs-integrity-check`](./.claude/skills/docs-integrity-check/) | `ARENA_GENERIC` | Contract & Docs Verification | `scripts/check_fences.sh`, `scripts/check_links.py` |
| [`doc-symbol-audit`](./.claude/skills/doc-symbol-audit/) | `ARENA_GENERIC` | Contract & Docs Verification | `scripts/list_declared_symbols.py`, `scripts/extract_symbol_occurrences.py` |
| [`adr-writer`](./.claude/skills/adr-writer/) | `ARENA_GENERIC` | Decision Governance | `assets/adr-template.md`, `assets/ledger-entry-template.md`, `references/status-discipline.md` |
| [`contract-freeze-gate`](./.claude/skills/contract-freeze-gate/) | `ARENA_GENERIC` (`STREAMFORGE`) | Assurance Gate | `assets/documentation-audit-template.md`, `references/freeze-gate-checklist.md` |
| [`contract-implementation-sync`](./.claude/skills/contract-implementation-sync/) | `ARENA_GENERIC` (`STREAMFORGE`) | Contract-to-Code Assurance | `scripts/check_contract_parity.py` |
| [`docs-normalization-commit-plan`](./.claude/skills/docs-normalization-commit-plan/) | `ARENA_GENERIC` | Change Attribution & Git | `references/commit-ordering-checklist.md` |
| [`contract-normalization-pass`](./.claude/skills/contract-normalization-pass/) | `ARENA_GENERIC` (`STREAMFORGE`) | Orchestration | `assets/final-report-long-template.md`, `assets/final-report-short-template.md`, `references/operating-principles.md` |
| [`skill-creator`](./.claude/skills/skill-creator/) | `ARENA_GENERIC` | Meta-Skill & Validator | `scripts/validate_skill.py`, `references/writing-patterns.md`, `references/lessons-learned.md` |

---

## Quickstart: Validating Assurance Manifests

The repository includes `bin/aif-verify`, a zero-dependency reference validator that checks AIF Completion Manifests against both the structural contracts (`schemas/`) and the normative AIF assurance invariants (`spec/04-invariants-and-axioms.md`).

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
