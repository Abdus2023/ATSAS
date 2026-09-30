# 01 — ATSAS Architecture Specification

## 1. Definition

**ATSAS (Arena Tools, Skills, Agentic System)** is a repository-governed architecture for extending and assuring agent-driven software work in Arena. It organizes **tools, skills, agent behavior, repository constraints, execution protocols, and assurance mechanisms** into explicit, composable interfaces.

ATSAS consists of four primary architectural tiers that feed into the **Agent Assurance Interface (AIF)**:

1. **Tools** — Bounded operational primitives that inspect, mutate, or execute within the workspace or external environment.
2. **Skills** — Reusable procedural workflows, domain patterns, and composition playbooks that guide how the agent applies tools.
3. **Agentic System** — The behavioral engine governing planning, state management, repository interaction protocols, and assurance handoff.
4. **Repository Governance** — Declarative repository-scoped policies that constrain authority, scope, protected paths, and mandatory acceptance gates.

---

## 2. Tools

In ATSAS, a **Tool** is an atomic, schema-defined capability exposed to the agent (e.g., `read_file`, `edit_file`, `bash`, `start_process`, `web_search`).

### 2.1 Tool Contract Requirements

Every tool registered in an ATSAS environment is characterized by:

* **Identifier & Version (`tool_id`, `version`)**: Canonical identity of the tool interface.
* **Capability Class (`capability_class`)**:
  * `READ_ONLY` — Inspects repository or environment state without mutation.
  * `WORKSPACE_MUTATION` — Creates, modifies, or deletes files in the repository workspace.
  * `PROCESS_EXECUTION` — Executes arbitrary or parameterized commands/processes.
  * `EXTERNAL_IO` — Interacts with external network resources or APIs.
* **Side-Effect Profile (`mutates_repository`, `network_access`, `persistent_process`)**: Declares how the tool can alter the repository snapshot or runtime environment.
* **Authority Requirement (`required_authority`)**: Minimum authority level or admission rule required before invocation.
* **Observation Profile (`observability`)**: Defines what raw outputs the tool emits (e.g., `exit_code`, `stdout`, `stderr`, `file_diff`, `port_bindings`) and what blind spots may exist (`PARTIAL` or `NOT_OBSERVABLE` dimensions).

### 2.2 Tool Output vs. Verification

> **Axiom:** *A tool result is not automatically verification.*

When a tool completes, its output enters AIF at the **Execution** and **Observation** stages—never directly at the **Verification** or **Completion** stage. For example:
* `edit_file` returning `"status": "success"` proves that an edit operation executed and mutated the file; it does **not** verify that the code compiles or satisfies the user's requirement.
* `bash` returning `exit_code: 0` for `pytest tests/unit/test_parser.py` is an observation scoped only to `tests/unit/test_parser.py` at a specific repository snapshot; it does **not** verify integration tests or survive a subsequent file edit (`STALE`).

---

## 3. Skills

In ATSAS, a **Skill** is a structured, reusable unit of procedural guidance that orchestrates tools and reasoning steps to perform a class of software engineering tasks (e.g., *debugging a failing build*, *migrating a database schema*, *performing a security review*).

### 3.1 Skill Contract Requirements

Every ATSAS skill declaration (`schemas/atsas-skill.schema.json`) defines:

* **Identifier & Domain (`skill_id`, `version`, `domain`)**: Unique name and engineering domain.
* **Preconditions (`preconditions`)**: Repository state or context required before invoking the skill.
* **Allowed Tools (`allowed_tools`)**: The subset of ATSAS tools the skill is permitted to orchestrate.
* **Procedural Workflow (`steps`)**: Ordered or conditional behavioral steps.
* **Expected Verification Criteria (`verification_requirements`)**: The acceptance criteria that **must** be independently verified through AIF after the skill finishes executing.

### 3.2 Skill Execution vs. Evidence

> **Axiom:** *A skill is not evidence.*

Invoking a skill—or completing every step in a skill's checklist—confers **zero** epistemic status in AIF. A skill shapes **agent behavior**; only concrete observations produced during execution, bound to the resulting repository snapshot and evaluated against verification predicates, constitute **evidence**.

### 3.3 Location Is Not Scope (Skill Portability & Extraction Lifecycle)

All skills governed, versioned, tested, and released by this repository reside in `.claude/skills/` to preserve repo-local discoverability and avoid premature multi-repository packaging decisions.

> **Rule:** *Location is not scope.*  
> `.claude/skills/` means *"Skills currently governed, versioned, tested, and released by this Arena repository."* It does **not** mean *"Skills are permanently specific to StreamForge or a single project."*

Instead, every skill explicitly declares its portability inside `SKILL.md` (enforced by `validate_skill.py` and `schemas/atsas-skill.schema.json`):

```text
SCOPE: ARENA_GENERIC
```
or
```text
SCOPE: STREAMFORGE_REPO
```
or, where a generic workflow includes repository-specific templates or compliance patterns:
```text
SCOPE: ARENA_GENERIC
ADAPTATION: STREAMFORGE
```

A skill is extracted into a standalone external skill library only after completing the full maturation lifecycle:

```text
prototype
  ↓
use on real repos
  ↓
failure cases
  ↓
skill tests
  ↓
interface freeze
  ↓
reuse evidence
  ↓
extraction
```

This aligns skill governance with the repository's **freeze → formalize → implement → test → release gate → tag** discipline.

---

## 4. Agentic System

The **Agentic System** is the runtime coordinator within ATSAS that binds Tools and Skills to Repository Governance and AIF.

### 4.1 Responsibilities

1. **Task Decomposition & Scope Binding**: Translating a user request and repository governance rules into explicit claims and mandatory acceptance criteria before declaring completion.
2. **Protocol Enforcement**: Ensuring every mutating or side-effecting tool invocation passes through **Authority** and **Admission** checks.
3. **Snapshot Tracking & Change Attribution**: Capturing repository snapshots (commit SHA, working tree hash, diff attribution) before and after workspace mutations so that any subsequent observation is strictly snapshot-bound.
4. **Honest Epistemic Reporting**: Preserving AIF's non-binary epistemic states (`UNKNOWN`, `NOT_OBSERVABLE`, `PARTIAL`, `STALE`, `MISMATCH`, `CONTRADICTED`) when communicating status to the user or downstream systems.

---

## 5. Repository Governance

**Repository Governance** is the bridge between ATSAS (capabilities/behavior) and AIF (assurance/claims). Governance policies live inside the repository (e.g., `.atsas/governance.json` or `governance-policy.json`, validated by `schemas/atsas-governance.schema.json`) and define:

* **Authority Boundaries**: Which operations are permitted, restricted, or require explicit human confirmation (e.g., branch constraints, forbidden destructive git operations, network egress rules).
* **Protected Paths**: Files or directories that cannot be modified without elevated admission (e.g., `.git/`, security policies, lockfiles).
* **Snapshot Hygiene**: Rules governing untracked artifacts, build outputs, and diff size thresholds.
* **Mandatory Acceptance Gates**: Baseline verification criteria required for any task affecting specific repository scopes (e.g., schema validation, unit tests, lint checks, type checks).
