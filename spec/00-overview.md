# 00 — Architectural Overview: ATSAS & AIF

## 1. Purpose

Agent-driven software engineering requires two distinct architectural capabilities that are frequently conflated:

1. **Capability and Behavior Architecture (ATSAS):** Organizing what an agent can invoke (tools), what procedural patterns it follows (skills), how its agentic loop interacts with the repository, and what repository governance rules apply.
2. **Assurance and Claim Architecture (AIF):** Defining the semantic contract that governs what may legitimately be claimed about the work performed, what evidence is required to verify a claim, and when a task may be declared complete.

When these two layers are conflated, agents routinely mistake **activity for assurance**—treating the invocation of a skill, the execution of a tool, or the absence of an immediate error as proof that a task is complete.

**ATSAS (Arena Tools, Skills, Agentic System)** and **AIF (Agent Assurance Interface)** resolve this by establishing an explicit, repository-governed architectural boundary between **doing the work** and **proving what can be claimed about the work**.

---

## 2. System Topology

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

### 2.1 Layer Decomposition

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

---

## 3. Architectural Boundary

| Dimension | ATSAS (Arena Tools, Skills, Agentic System) | AIF (Agent Assurance Interface) |
| :--- | :--- | :--- |
| **Primary Role** | Capability + behavior architecture | Assurance + claim architecture |
| **Core Question** | *What can the agent use and how does it operate?* | *What may legitimately be claimed about the resulting work?* |
| **Primitives** | Tools, Skills, Agentic Protocols, Repository Governance | Authority, Admission, Execution, Change Attribution, Observation, Verification, Evidence, Acceptance, Completion |
| **Output** | Repository mutations, command executions, raw observations | Epistemic claims, bound evidence bundles, completion verdicts |

### 3.1 Boundary Axioms

1. **A skill is not evidence.** Following a prescribed procedural workflow does not prove that the target outcome was achieved or that repository invariants hold.
2. **A tool result is not automatically verification.** A tool invocation produces a raw observation (e.g., stdout, exit code, file diff); whether that observation satisfies a specific claim requires explicit verification bound to scope and snapshot.
3. **Execution is not completion.** Running a build, linter, or test command is an execution event, not an unqualified completion state.
4. **Completion is an evidence-backed claim.** A task may only transition to `COMPLETE` when every mandatory acceptance criterion is satisfied by sufficient, scope-bounded, snapshot-bound evidence.

---

## 4. What AIF Is — and What It Is Not

**AIF (Agent Assurance Interface)** is a repository-governed assurance protocol for agent-driven software work.

```text
AIF does not make the work happen.
AIF determines what may be claimed about what happened.
```

* **AIF is NOT an agent framework or planner:** It does not decide which skill or tool the agent should invoke next; ATSAS governs agentic behavior and tool/skill composition.
* **AIF is NOT a task executor or runtime sandbox:** It does not execute shell commands or mutate files; it records admission, execution provenance, change attribution, and observations from executors.
* **AIF is NOT a security scanner, test runner, or CI system:** It consumes observations produced by test runners, compilers, linters, and scanners, and subjects their outputs to scope-bounded, snapshot-bound verification and evidence rules.
* **AIF is NOT a remediation engine:** When verification fails (`CONTRADICTED`, `STALE`, `PARTIAL`, `MISMATCH`), AIF surfaces the exact epistemic state and violated criterion back to the ATSAS agentic system rather than silently masking or auto-remediating the failure.
