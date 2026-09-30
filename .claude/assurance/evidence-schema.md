# Arena Assurance Evidence & Skill Evaluation Schemas (v0.1)

```text
Document Class: HISTORICAL
Protocol: AIF-0.1.0
Evaluated Snapshot: 15f7fa01778f06821d1c5c9c285bb0d666e04f8b
Currentness: HISTORICAL — NOT CURRENT BRANCH EVIDENCE (Normative authority is .claude/skills/_shared/aif/schema/)
```

> **Status**: `PROVISIONAL` (PHASE 2 & PHASE 3 Design Artifact)
> **Scope**: `ARENA_GENERIC`
> **Machine Schemas**: `schemas/aif-evidence-receipt.schema.json`, `schemas/aif-skill-eval-receipt.schema.json`

---

## 1. Three-Snapshot Change-Provenance Model (`S0`, `S1`, `S2`)

A single overloaded `base` or `snapshot` field is insufficient to separate pre-existing dirty working-tree changes (`AAI-007`) from agent mutations (`AAI-005`..`008`) and post-execution verification drift (`AAI-023`, `AAI-028`, `P-004`).

```text
BASELINE
   │
   │ repository state before task
   ▼
S0 / INTAKE SNAPSHOT (subject.intake_snapshot)
   │
   │ agent execution: AGENT_CHANGE = DIFF(S0, S1)
   ▼
S1 / POST-EXECUTION SNAPSHOT (subject.execution_snapshot)
   │
   │ verification commands executed
   ▼
S2 / VERIFICATION SNAPSHOT (subject.verification_snapshot)
```

### 1.1 Five Distinct Repository References

| Field in `subject` | Meaning | Why It Cannot Be Overloaded |
|---|---|---|
| `comparison_base` | Merge-base / branch ancestor commit | Measures branch history relative to `main`, which includes prior commits and pre-existing state. |
| `intake_snapshot` (`S0`) | Observed repository state (`commit_sha` + working-tree digest) when the task began | Separates pre-existing dirty files (`DIFF(comparison_base, S0)`) from agent changes (`DIFF(S0, S1)`). |
| `execution_snapshot` (`S1`) | Repository state immediately after agent execution | Captures the exact subject produced by the agent (`AGENT_CHANGE = DIFF(S0, S1)`). |
| `verification_snapshot` (`S2`) | Repository state when verification checks ran | Proves whether verification ran against `S1` (`S1 == S2`) or against a stale/mutated state (`S1 != S2`). |
| `head_commit` (`HEAD`) | Current commit ref when the receipt/gate is evaluated | Detects if a new commit or reset occurred after `S2` (`AAI-011`). |

- **Stability condition**:
  - For a read-only audit/inspection task: `S0 == S1 == S2 == head_commit` (enforces `AAI-010` `AUDIT ≠ REMEDIATION`).
  - For a mutation task: `AGENT_CHANGE = DIFF(S0, S1)` and `S1 == S2 == head_commit` (enforces `AAI-003` and `AAI-011`).
  - If `S1 != S2` or `S2 != head_commit`, `verification.snapshot_binding` must be set to `VERIFICATION_STALE` or `EVIDENCE_MISMATCH`.

---

## 2. Revised `ArenaEvidenceReceipt` Schema (v0.1)

Notice that `conclusion` is strictly **downstream** from `evidence` and `findings`—it can never invent `verified_claims` not backed by `evidence`.

```text
ArenaEvidenceReceipt {
  receipt_id
  schema_version

  subject {
    repository
    branch
    comparison_base
    intake_snapshot
    execution_snapshot
    verification_snapshot
    head_commit
  }

  request {
    request_id
    requested_actions[]
    acceptance_criteria[]
  }

  authority {
    actor
    authority_basis
    authority_status
    scope[]
  }

  execution {
    status
    actions[]
    commands[]
    changed_paths[]
  }

  verification {
    checks[]
    snapshot_binding
    result
  }

  evidence {
    artifacts[]
    commands[]
    outputs[]
    exit_codes[]
    timestamps[]
    provenance[]
  }

  findings {
    facts[]
    blockers[]
    unknowns[]
    stale_evidence[]
    mismatches[]
  }

  conclusion {
    status
    verified_claims[]
    unverified_claims[]
    unmet_criteria[]
  }
}
```

### 2.1 Detector-to-Receipt Adaptation Pattern (Example: `secret-leak-scan`)

`secret-leak-scan` is an existing **detector** (`0 HIGH, 0 LOW, scanner=specific heuristic, coverage=current tree only`). `evidence-receipt-generator` adapts its output into `ArenaEvidenceReceipt` without inflating it into `"SECURITY PASS"`:

- `evidence.commands`: `["python3 .claude/skills/secret-leak-scan/scripts/scan_secrets.py ."]`
- `evidence.exit_codes`: `[0]`
- `evidence.provenance`: `["detector:secret-leak-scan@0.1.0(scope=working_tree_only)"]`
- `findings.facts`: `["SCANNER_NO_MATCH: no matching credentials detected by secret-leak-scan in the inspected current-tree scope"]`
- `findings.unknowns`: `["GIT_HISTORY_SECRET_SCAN: NOT_EXECUTED (working-tree scanner only)"]`
- `conclusion`: Evaluated downstream by `arena-completion-gate` against `request.acceptance_criteria[]`.

---

## 3. Skill Evaluation Harness Contract (`SkillEvalReceipt`)

Moving `skill-evaluation-harness` (`08`) to **PHASE 2** ensures every skill and adapter is behaviorally tested across four dimensions (`Trigger precision`, `Behavioral correctness`, `Safety / boundary adherence`, `Regression stability`) before freezing.

```text
SkillEvalReceipt {
    kind: "SkillEvalReceipt"
    schema_version
    skill_id
    skill_revision
    test_id

    input {
        prompt
        repository_snapshot
        authority_context
    }

    baseline {
        skill_enabled: false
        behavior
        observed_output
    }

    treatment {
        skill_enabled: true
        behavior
        observed_output
    }

    pressure {
        mutation_attempt
        observed_response
    }

    assertions {
        expected[]
        observed[]
        passed[]
        failed[]
        unknown[]
    }

    evidence {
        commands[]
        artifacts[]
        snapshot
        timestamps[]
    }

    conclusion {
        status
        dimensions {
            trigger_precision
            behavioral_correctness
            safety_boundary_adherence
            regression_stability
        }
    }
}
```
