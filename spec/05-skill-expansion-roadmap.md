# 05 — Arena Agent Mode Skill Expansion Architecture & Priority Roadmap

## 1. Core Finding: An Evidence-Oriented Repository Assurance System

Combining the fresh target-branch audit (`arena/01a0e9bd-streamforge-stremio`) with the external skill-library survey (`obra/superpowers`, `wshobson/agents`, `openai/skills`, `anthropics/skills`) establishes a clear architectural conclusion:

> **The missing layer is not “more skills” in general; it is an evidence-oriented repository assurance system.**

```text
StreamForge skills
       │
       │ strong
       ▼
Documentation / Contracts / Decisions
       │
       │
       ▼
Implementation parity
       │
       │
       X  (Gap boundary)
       │
       ▼
Repository Assurance
```

### 1.1 External Ecosystem Comparison & Why Arena Must Not Simply Copy Them

* **`obra/superpowers` (Verification & Process Discipline)**: Treats verification as a first-class skill (`verification-before-completion` requiring fresh command execution before completion claims), alongside systematic debugging (separating root-cause investigation, hypothesis, testing, implementation, and verification), TDD, worktrees, parallel-agent coordination, and **RED → GREEN → REFACTOR behavioral testing of skills themselves**.
* **`wshobson/agents` (Repository Assurance Breadth)**: Spans security scanning (SAST, STRIDE, attack trees, threat/mitigation mapping), CI/CD, infrastructure, operations, testing, deployment, and CI-integrated structural/drift/dead-link validation.

**Crucial Architectural Distinction**: External skill ecosystems mostly provide **developer workflow skills** (*"How does the agent perform a task?"*). **Arena Agent Mode (ATSAS + AIF)** requires a formal **authority → admission → execution → verification → evidence** stack:

```text
             ARENA AGENT
                  │
                  ▼
        ┌─────────────────────┐
        │ Authorization       │
        │ What may I do?      │
        └──────────┬──────────┘
                   ▼
        ┌─────────────────────┐
        │ Admission           │
        │ What is allowed now?│
        └──────────┬──────────┘
                   ▼
        ┌─────────────────────┐
        │ Execution           │
        │ What actually ran?  │
        └──────────┬──────────┘
                   ▼
        ┌─────────────────────┐
        │ Verification        │
        │ What did it prove?  │
        └──────────┬──────────┘
                   ▼
        ┌─────────────────────┐
        │ Evidence            │
        │ Can we reproduce it?│
        └─────────────────────┘
```

This preserves the foundational non-conflation chain:

```text
representation ≠ semantics ≠ evidence ≠ truth ≠ authority ≠ authorization ≠ admission ≠ execution ≠ success ≠ canonicality ≠ durability
```

---

## 2. Four-Layer Classification of Candidate Assurance Skills

All 19 candidate assurance skills operate on **repository primitives**:

```text
Git | filesystem | manifest | lockfile | CI configuration | tests | build system | artifacts | configuration | runtime metadata | execution output
```

rather than StreamForge domain concepts (`Stremio`, `SourceCandidate`, `provider adapter`, `media stream`). Consequently, their scope is overwhelmingly **`ARENA_GENERIC`**, while `.claude/skills/` serves as their governed distribution location (*"Location is not scope"*).

| Layer | Skill | Scope | Status |
| :--- | :--- | :--- | :--- |
| **A — Authority** | `01 arena-intake-and-authority` | `ARENA_GENERIC` | **Wave 1 (`P0`) — Interface Frozen (`W1`) + RED Matrix** |
| **A — Authority** | `02 agent-change-scope-audit` | `ARENA_GENERIC` | **Wave 1 (`P0`) — Interface Frozen (`W2`) + RED Matrix** |
| **A — Authority** | `parallel-agent-conflict-audit` | `ARENA_GENERIC` | Roadmap (`P4`) |
| **A — Authority** | `worktree-integrity-check` | `ARENA_GENERIC` | Roadmap (`P4`) |
| **B — Repository assurance** | `03 secret-and-credential-audit` | `ARENA_GENERIC` | **Wave 1 (`P1`) — Interface Frozen (`W3`) + RED Matrix** |
| **B — Repository assurance** | `04 dependency-supply-chain-audit` | `ARENA_GENERIC` | **Wave 1 (`P1`) — Interface Frozen (`W4`) + RED Matrix** |
| **B — Repository assurance** | `05 ci-workflow-audit` | `ARENA_GENERIC` | **Wave 1 (`P1`) — Interface Frozen (`W5`) + RED Matrix** |
| **B — Repository assurance** | `06 test-execution-and-evidence-audit` | `ARENA_GENERIC` | **Wave 1 (`P1`) — Interface Frozen (`W6`) + RED Matrix** |
| **B — Repository assurance** | `configuration-contract-audit` | `ARENA_GENERIC` | Roadmap (`P2`) |
| **B — Repository assurance** | `release-artifact-provenance` | `ARENA_GENERIC` | Roadmap (`P2`) |
| **B — Repository assurance** | `baseline-regression-audit` | `ARENA_GENERIC` | Roadmap (`P2`) |
| **C — Lifecycle assurance** | `api-compatibility-audit` | `ARENA_GENERIC` | Roadmap (`P3`) |
| **C — Lifecycle assurance** | `migration-safety-audit` | `ARENA_GENERIC` | Roadmap (`P3`) |
| **C — Lifecycle assurance** | `generated-artifact-sync` | `ARENA_GENERIC` | Roadmap (`P3`) |
| **C — Lifecycle assurance** | `runtime-deployment-audit` | `ARENA_GENERIC` | Roadmap (`P3`) |
| **C — Lifecycle assurance** | `operational-readiness-audit` | `ARENA_GENERIC` | Roadmap (`P3`) |
| **D — Evidence authority** | `07 evidence-receipt-generator` | `ARENA_GENERIC` | **Wave 1 (`P2`) — Interface Frozen (`W7`) + RED Matrix** |
| **D — Evidence authority** | `08 arena-completion-gate` | `ARENA_GENERIC` | **Wave 1 (`P0`) — Interface Frozen (`W8`) + RED Matrix** |
| **D — Meta** | `skill-evaluation-harness` | `ARENA_GENERIC` | **Wave 1.5 — Behavioral RED/GREEN/PRESSURE Harness** |

---

## 3. Focused Wave-1 Orchestration Topology (Avoiding a "Skill Zoo")

Rather than activating 19 uncoordinated skills at once, **Wave 1** focuses on an 8-skill spine that wraps **Repository Assurance** and **Contract Assurance** between **Intake/Change Scope** and **Completion Gate/Evidence Receipt**:

```text
                    Arena Agent
                        │
                        ▼
             ┌────────────────────┐
             │ 1. Intake/Authority│  (arena-intake-and-authority)
             └─────────┬──────────┘
                       │
                       ▼
             ┌────────────────────┐
             │ 2. Change Scope    │  (agent-change-scope-audit)
             └─────────┬──────────┘
                       │
                       ▼
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
 Repository Assurance          Contract Assurance
        │                             │
        ├─ secrets                    ├─ docs
        ├─ dependencies               ├─ symbols
        ├─ CI                         ├─ ADR
        ├─ tests                      ├─ freeze
        ├─ config                     └─ implementation sync
        └─ artifacts
        │                             │
        └──────────────┬──────────────┘
                       ▼
             ┌────────────────────┐
             │ 3. Completion Gate │  (arena-completion-gate)
             └─────────┬──────────┘
                       ▼
             ┌────────────────────┐
             │ Evidence Receipt   │  (evidence-receipt-generator)
             └────────────────────┘
```

### The Canonical Wave-1 Skill Pipeline (`01` – `08`)

1. `01 arena-intake-and-authority` (Layer A — Authority, `P0`)
2. `02 agent-change-scope-audit` (Layer A — Authority, `P0`)
3. `03 secret-and-credential-audit` (Layer B — Repository Assurance, `P1`)
4. `04 dependency-supply-chain-audit` (Layer B — Repository Assurance, `P1`)
5. `05 ci-workflow-audit` (Layer B — Repository Assurance, `P1`)
6. `06 test-execution-and-evidence-audit` (Layer B — Repository Assurance, `P1`)
7. `07 evidence-receipt-generator` (Layer C — Evidence Authority, `P2`)
8. `08 arena-completion-gate` (Layer C — Evidence Authority, `P0`)

**Current Gate Decision**: `PROVISIONALLY FROZEN — interface level` (see [`06-wave1-skill-interfaces.md`](./06-wave1-skill-interfaces.md) and [`07-wave1-red-pressure-matrix.md`](./07-wave1-red-pressure-matrix.md)). Wave-1 `SKILL.md` files are intentionally withheld until the RED/pressure-test matrix is reviewed and approved.

---

## 4. Dependency-Ranked Priority Order (`P0` → `P4`)

Implementation and interface freezing follow strict dependency order rather than subjective importance:

```text
P0 (Foundation: Authority, Scope Attribution & Completion Gate)
├── arena-intake-and-authority
├── agent-change-scope-audit
└── arena-completion-gate

P1 (Core Repository Assurance)
├── secret-and-credential-audit
├── dependency-supply-chain-audit
├── ci-workflow-audit
└── test-execution-and-evidence-audit

P2 (Receipts, Config, Regression & Provenance)
├── evidence-receipt-generator
├── configuration-contract-audit
├── baseline-regression-audit
└── release-artifact-provenance

P3 (Lifecycle, Compatibility & Runtime Assurance)
├── generated-artifact-sync
├── api-compatibility-audit
├── migration-safety-audit
├── runtime-deployment-audit
└── operational-readiness-audit

P4 (Multi-Agent & Behavioral Meta-Verification)
├── parallel-agent-conflict-audit
├── worktree-integrity-check
└── skill-evaluation-harness  (Note: candidate to promote toward P1 as new skills are authored)
```

---

## 5. Structural vs. Behavioral Skill Validation (`skill-evaluation-harness`)

`skill-creator/scripts/validate_skill.py` validates **syntax and structure** (`SKILL.md` exists, frontmatter valid, `name`/`description`/`SCOPE` valid, referenced files exist). However, **structural validity is not behavioral validity**:

```text
skill validation
       │
       ├── syntax/structure   (validate_skill.py)
       │
       └── behavior           (skill-evaluation-harness)
```

`skill-evaluation-harness` answers: *"Did the skill actually change agent behavior under realistic and adversarial pressure?"* using the **RED → GREEN → REFACTOR** evidence loop:

```text
BASELINE (Without skill)
   ↓
Agent violates expected rule
   ↓
SKILL ADDED
   ↓
Same scenario
   ↓
Agent complies
   ↓
PRESSURE VARIANTS (Scope pressure / Evidence pressure / Ambiguity)
   ↓
No rationalization loophole
```
