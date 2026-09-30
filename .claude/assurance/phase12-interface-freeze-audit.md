# Phase 12 — Cross-Skill Consolidation, Responsibility Freeze & Branch Audit

- **Protocol Version**: `AIF-0.1.0` ([`../skills/_shared/aif/VERSION`](../skills/_shared/aif/VERSION))
- **Evaluated Branch**: `arena/01a0ecca-atsas` (`S0 = 15f7fa0` initial commit $\to$ `S1 = ea23125` implementation commit $\to$ `S2 = b9a9ce5` $\to$ Phase 13/14 normalized state)
- **Evaluated Corpus**: `cases.yaml` (`41 RED + 8 PRESSURE = 49` core cases) & `aif-eval-corpus-0.2` (`79` harness cases)

---

## 1. Three Structural Categories & Dependency Direction (`12.1`–`12.3`)

Rather than treating every component as an undifferentiated natural-language skill, the architecture freezes around three distinct structural categories:

```text
AIF KERNEL
    semantic model (.claude/skills/_shared/aif/ — NOT a skill)

AIF EVIDENCE PRODUCERS
    repository observation procedures (bounded producer skills + existing scanners via adapters)

AIF EVALUATORS
    pure acceptance evaluation (arena-completion-gate) & skill behavior evaluation (skill-evaluation-harness)
```

### Mandatory Dependency Direction (`12.3`)

```text
                  AIF KERNEL
                   /   |   \
                  /    |    \
                 ▼     ▼     ▼
            producers receipt gate
                 │       │      │
                 └───────┴──────┘
                         │
                         ▼
                 evaluation harness
```

- `_shared/aif/` never depends on any skill.
- `arena-completion-gate` never invokes `arena-intake-and-authority`, `evidence-receipt-generator`, or any scanner/test skill (preserving pure evaluation `CompletionResult = Evaluate(AcceptanceExpression, ArenaEvidenceReceipt, EvaluatorVersion)`).

---

## 2. Normative Responsibility Matrix (`12.4`)

| Component | May Observe | May Execute | May Mutate | Produces Evidence | Establishes Authority | Decides Completion |
|---|---|---|---|---|---|---|
| **AIF Kernel (`_shared/aif/`)** | `no` | `no` | `no` | model only | `no` | `no` |
| **Intake/Authority (`arena-intake-and-authority`)** | `yes` | `no` | `no` | authority/admission | **`yes` (ONLY)** | `no` |
| **Scope Audit (`agent-change-scope-audit`)** | `yes` | limited/read-only | `no` | change evidence | `no` | `no` |
| **CI Audit (`ci-workflow-audit`)** | `yes` | inspect CI records | `no` | CI evidence | `no` | `no` |
| **Test Audit (`test-execution-and-evidence-audit`)** | `yes` | tests if authorized | `no` | test evidence | `no` | `no` |
| **Supply Chain (`dependency-supply-chain-audit`)** | `yes` | audit commands if authorized | `no` | dependency evidence | `no` | `no` |
| **Existing Scanners (14 imported skills)** | `yes` | scanner-specific | normally `no` | domain evidence | `no` | `no` |
| **Receipt Generator (`evidence-receipt-generator`)** | `yes` | `no` | `no` | normalized receipt | `no` | `no` |
| **Completion Gate (`arena-completion-gate`)** | **receipt only** | `no` | `no` | completion result | `no` | **`yes` (ONLY)** |
| **Evaluation Harness (`skill-evaluation-harness`)** | controlled test subject | `yes` | **sandbox only** | evaluation evidence | `no` | **skill-eval only** |

```text
ONLY arena-intake-and-authority may establish authority.
ONLY arena-completion-gate may evaluate repository task completion.
NO OTHER SKILL may silently perform either role.
```

---

## 3. Disambiguated Terminology & Adapter Contract (`12.5`–`12.10`, `12.18`)

- **Two Meanings of Authorization (`12.6`)**:
  - `arena-intake-and-authority` = **Agent Authority** (*"Is this agent/request authorized to perform this action on this repository/path/state?"*).
  - `authorization-boundary-scan` = **Content Authority** (*"Does repository code violate StreamForge's declared authorized/licensed/public-domain/user-owned content boundary?"*).
- **Three Meanings of Audit (`12.7`)**:
  - **Repository audit** (`agent-change-scope-audit`, `repo-onboarding-audit`), **Security/Domain audit** (`secret-leak-scan`, `dependency-vulnerability-audit`, `dependency-supply-chain-audit`), and **Completion evaluation** (`arena-completion-gate`) remain strictly separate.
- **`skill-creator` vs `skill-evaluation-harness` (`12.18`)**:
  - `skill-creator` = how to author and structurally validate a skill (`validate_skill.py`).
  - `skill-evaluation-harness` = how to empirically challenge and verify skill behavior under `RED`, `GREEN`, `PRESSURE`, and `REGRESSION` cases.
- **Universal Producer Contract (`12.8`)**:
  - `SkillExecutionContext { request_id, execution_id, actor, repository, subject_snapshot, tool, tool_version, started_at, ended_at }`
  - `EvidenceProducerOutput { producer, producer_version, aif_version, execution_context, evidence[], findings[], verifications[], limitations[], coverage }` with explicit `does_not_produce: [authority, admission, completion]`.
- **Action Granularity & Explicit Non-Mutation Contract (`12.9`–`12.10`)**:
  - `Action { operation, paths, commands, external_effects }` (e.g., `execute "npm test"` allowed while `execute "npm install"` and `modify package.json` are forbidden).
  - Audit skills explicitly declare `mutation: allowed: false` (`MUTATES_REPOSITORY: false`); if `DECLARED: mutation = false` and `OBSERVED: mutation = true`, the harness classifies `SKILL_CONTRACT_VIOLATION`.

---

## 4. Frozen Orthogonal State Dimensions, 5-Snapshot Model & Attribution (`12.11`–`12.15`, `12.19`)

- **Orthogonal Dimensions (`12.12`)**:
  - `Authority`: `AUTHORIZED | NOT_AUTHORIZED | UNKNOWN | EXPIRED | CONFLICTING`
  - `Admission`: `ADMITTED | INSPECT_ONLY | BLOCKED | REJECTED`
  - `Execution`: `NOT_STARTED | RUNNING | COMPLETED | INTERRUPTED | UNKNOWN`
  - `Process outcome`: `SUCCESS | FAILURE | MIXED | SKIPPED | UNKNOWN`
  - `Evidence`: `OBSERVED | PARTIAL | MISSING | CONTRADICTORY | STALE | MISMATCH | NOT_OBSERVABLE`
  - `Verification`: `VERIFIED | PARTIAL | UNVERIFIED | CONTRADICTED | STALE | MISMATCH | NOT_OBSERVABLE`
  - `Completion`: `COMPLETABLE | INCOMPLETE | BLOCKED | CONTRADICTED | INVALID`
- **Five-Snapshot Provenance Model (`12.13`–`12.14`)**:
  - `comparison_base`, `intake_snapshot`, `execution_snapshot`, `verification_snapshot`, `current_snapshot`, with explicit `working_tree_state` and `index_state` (`CLEAN | DIRTY | PARTIAL | UNKNOWN`).
- **Attribution Freeze (`12.15`)**:
  - `PREEXISTING | AGENT_ATTRIBUTED | EXTERNAL_ATTRIBUTED | GENERATED | UNATTRIBUTED | UNKNOWN` (`git diff ≠ agent attribution`).
- **Frozen `AIF-CORE 0.1` Invariants (`12.19`)**:
  - Controlled set: `AIF-001 .. AIF-055` (plus 8 sub-invariants `AIF-001A .. AIF-014A` = `63` normative rules in [`../skills/_shared/aif/invariants.md`](../skills/_shared/aif/invariants.md)). Any future invariant beyond `AIF-055` must enter as `PROPOSED` until a new AIF version is cut.

---

## 5. Ground-Truth Branch & CI Observability Audit (`arena/01a0ecca-atsas`)

| Dimension | Observed State | Evidence |
|---|---|---|
| **Branch** | `arena/01a0ecca-atsas` (tracking `origin/arena/01a0ecca-atsas`) | `git status -sb` |
| **Commit Progression** | `S0 = 15f7fa0` (`Initial commit`) $\to$ `S1 = ea23125` (AIF-0.1.0 kernel, 22 skills `C-01..C-08`, evaluation harness) $\to$ `S2 = b9a9ce5` $\to$ Phase 13/14 normalized commit | `git log --oneline` |
| **`.claude/skills/_shared/aif/` Kernel** | `PRESENT` & `VERIFIED` (`VERSION = 0.1.0`, 7 docs, 13 modular JSON schemas encoding the 14 core types, 3 test files with 49 behavioral cases in `cases.yaml`, 10 producer contracts, 0 runtime code files) | `python3 tests/aif-v01-red-suite.py` (`145/145 PASS`) |
| **`.claude/skills/` Inventory** | `22` validated skills (`14` imported StreamForge skills + `8` Wave-1 AIF skills `C-01`..`C-08`) | `validate_skill.py --all .claude/skills` (`22/22 PASS`) |
| **GitHub Actions / CI Observability** | `.github/workflows/` is `NOT PRESENT` on this branch (`CI_CONFIGURED = NOT_OBSERVED`, `CI_EXECUTED = NOT_OBSERVED`, `CI_PASSED = NOT_OBSERVED`). Per `AIF-004`, `AIF-008`, and `AIF-028`, this records absence of remote GitHub Actions execution evidence, **not** local test failure. | `ci-workflow-audit` (`NOT_FOUND` observation) |
| **Canonical Local Test Entrypoint** | `./tests/run-tests.sh` | All `117/117` repository checks passing |
