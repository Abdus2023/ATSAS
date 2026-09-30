# `.agent/` — Reusable ATSAS Tools, AIF-0.1 Protocol Kernel & Engineering Skills

> Packaged and validated using `skill-creator` (`python3 .agent/skills/skill-creator/scripts/validate_skill.py --all .agent/skills`).

This directory packages **every end-to-end engineering process used from the first message of the ATSAS & AIF session** into reusable, zero-dependency **CLI tools** (`.agent/tools/`), **ATSAS Tool Capability Contracts** (`.agent/tools/contracts/`), the **shared `AIF-0.1` Semantic Kernel** (`.agent/skills/_shared/aif/`), and **9 Agent Skills** (`.agent/skills/`).

---

## 1. End-to-End Process Pipeline Captured in `.agent/`

```text
[Process 1] atsas-aif-architecture-bootstrap
    │       Separates ATSAS (capability/behavior) from AIF (claim/assurance),
    │       defines the 9-concern pipeline & non-binary epistemic states.
    ▼
[Process 2] cross-repo-skill-portability-import
    │       Imports & audits skills across repos enforcing "Location is not scope"
    │       (SCOPE: ARENA_GENERIC / STREAMFORGE_REPO + ADAPTATION tags).
    ▼
[Process 3] assurance-test-matrix-designer
    │       Applies RED/Pressure TDD to skills BEFORE writing SKILL.md:
    │       18 domains, 11 AAI invariants, 42-case matrix (AAI-001..034, P-001..008).
    ▼
[Process 4] skill-capability-overlap-audit
    │       Audits existing skills vs. the 42-case matrix, prevents duplicate skills
    │       via EvidenceRef adapters, separates app-security authz from task authority.
    ▼
[Process 5] aif-component-contract-designer
    │       Defines the 8 normative component contracts (C-01..C-08), universal
    │       envelope (RESULT != EVIDENCE != DECISION), and PHASE 0..12 order.
    ▼
[Process 6] aif-adversarial-freeze-review
    │       Red-teams contracts C-01..C-08 against 14 adversarial attacks (ADV-001..014),
    │       enforces FT-01..FT-10, and expands invariants to AIF-001..AIF-020 (+A).
    ▼
[Process 7] aif-semantic-kernel-engineer
    │       Packages the 14-type AIF-0.1 Semantic Kernel under _shared/aif/
    │       (not as a "god skill") and runs the 28-case Phase 0/1 RED test suite.
    ▼
[Process 8] aif-assurance-workflow-orchestrator
    │       Orchestrates all stages in causal order and evaluates receipts & completion.
    ▼
[Process 9] skill-creator
            Packages, refactors, smoke-tests, and structurally validates Agent Skills.
```

---

## 2. Directory Layout

```text
.agent/
├── README.md                                          # This index & workflow guide
├── tools/                                             # 7 Standalone zero-dependency CLI tools
│   ├── aif-verify                                     # Schema & AIF-001..020 (+A) validator CLI
│   ├── aif-snapshot-capture                           # 5-role SnapshotRef capture CLI (CLEAN vs DIRTY)
│   ├── aif-change-audit                               # ChangeRecord & path-scope auditor CLI
│   ├── aif-exec-record                                # ExecutionRecord wrapper (PROCESS/TEST/SEMANTIC)
│   ├── aif-coverage-eval                              # EvidenceCoverage(E,C) & Intersects(Change,Claim) CLI
│   ├── aif-completion-eval                            # Pure-function CompletionResult gate evaluator CLI
│   ├── aif-red-suite                                  # Phase 0/1 28-case RED invariant suite runner
│   └── contracts/                                     # 7 ATSAS Tool Capability Contracts (Draft 2020-12)
│       ├── aif-verify.tool.json
│       ├── aif-snapshot-capture.tool.json
│       ├── aif-change-audit.tool.json
│       ├── aif-exec-record.tool.json
│       ├── aif-coverage-eval.tool.json
│       ├── aif-completion-eval.tool.json
│       └── aif-red-suite.tool.json
└── skills/                                            # 9 Reusable Agent Skills + Shared AIF Kernel
    ├── _shared/
    │   └── aif/                                       # Versioned AIF-0.1 Semantic Kernel (non-skill)
    │       ├── VERSION                                # 0.1
    │       ├── README.md
    │       ├── invariants.md
    │       ├── states.md
    │       ├── evidence-rules.md
    │       ├── compatibility.md
    │       └── schema/                                # 13 modular Draft 2020-12 JSON Schemas
    ├── atsas-aif-architecture-bootstrap/              # Process 1 Skill
    ├── cross-repo-skill-portability-import/           # Process 2 Skill
    ├── assurance-test-matrix-designer/                # Process 3 Skill
    ├── skill-capability-overlap-audit/                # Process 4 Skill
    ├── aif-component-contract-designer/               # Process 5 Skill
    ├── aif-adversarial-freeze-review/                 # Process 6 Skill
    ├── aif-semantic-kernel-engineer/                  # Process 7 Skill
    ├── aif-assurance-workflow-orchestrator/           # Process 8 Skill
    └── skill-creator/                                 # Process 9 Meta-Skill & Validator
```

---

## 3. Quickstart Commands

### Validate all 9 skills in `.agent/skills/` with `skill-creator`
```bash
python3 .agent/skills/skill-creator/scripts/validate_skill.py --all .agent/skills
```

### Run the end-to-end pipeline orchestrator
```bash
python3 .agent/skills/aif-assurance-workflow-orchestrator/scripts/run_assurance_pipeline.py
```

### Run the 7 standalone `.agent/tools/` CLIs
```bash
./.agent/tools/aif-snapshot-capture --role current_snapshot
./.agent/tools/aif-change-audit --admitted-path ".agent/**" --admitted-path ".claude/**" --admitted-path "schemas/**" --admitted-path "examples/**" --admitted-path "bin/**" --admitted-path "tests/**" --admitted-path "README.md" --admitted-path "ARENA_*.md"
./.agent/tools/aif-exec-record --command "echo ok"
./.agent/tools/aif-coverage-eval --bundle examples/valid-canonical-data-model.json --evidence-id ev-test-stdout-001 --claim-id claim-test-suite-verified
./.agent/tools/aif-completion-eval examples/valid-canonical-data-model.json
./.agent/tools/aif-verify examples/valid-canonical-data-model.json
./.agent/tools/aif-red-suite
```
