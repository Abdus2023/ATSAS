---
name: aif-adversarial-freeze-review
description: Conducts an adversarial freeze review of component contracts (`C-01`..`C-08`), state transitions (`FT-01`..`FT-10`), and interface invariants (`AIF-001`..`AIF-020` + sub-invariants `AIF-001A`..`AIF-014A`) BEFORE freezing interfaces or authoring `SKILL.md` files. Use whenever reviewing assurance contracts for loopholes (vacuous 0-test passes, shell pipeline exit-code masking, split-snapshot evidence, optimistic ANY over CONTRADICTED claims, semantic claim broadening, or self-attesting SKILL_OUTPUT) or verifying freeze readiness.
---

# AIF Adversarial Freeze Review (`ADV-001`..`ADV-014` & `AIF-001`..`AIF-020`)

```text
SCOPE: ARENA_GENERIC
```

```yaml
aif:
  version: "0.1"
  consumes:
    - Request
    - Claim
    - AcceptanceExpression
  produces:
    - Finding
    - VerificationRecord
  mutates_repository: false
```

Subjects candidate skill contracts (`C-01`..`C-08`) and assurance invariants to adversarial red-team stress testing before allowing interface freeze or `SKILL.md` implementation.

## Workflow

### Step 1 — Test Contracts Against the 14 Adversarial Loophole Classes (`ADV-001` – `ADV-014`)

Read `references/adversarial-attack-catalog.md` and attempt to break every proposed contract using concrete exploit scenarios:

- **Retroactive authority laundering** (`ADV-001` -> `AIF-001`, `AIF-001A`)
- **Dirty working-tree vs. clean HEAD conflation** (`ADV-002` -> `AIF-002`, `AIF-002A`)
- **Inferring agent causality from `DIFF(S0,S1)` alone** (`ADV-003` -> `AIF-003`, `AIF-003A`)
- **Shell pipeline exit-code masking (`pytest | tee`)** (`ADV-004` -> `AIF-004`, `AIF-004A`)
- **Vacuous test pass (`0 tests discovered`, `exit_code == 0`)** (`ADV-005` -> `AIF-005`, `AIF-005A`)
- **Wrong-command verification (`lint` used to verify `unit tests`)** (`ADV-006` -> `AIF-006`, `AIF-006A`)
- **Cross-snapshot / split-snapshot evidence assembly** (`ADV-007`, `ADV-014` -> `AIF-007`, `AIF-014`, `AIF-014A`, `AIF-015`)
- **Semantic claim broadening during receipt normalization (`Normalize(E) = ExpandClaim(E)`)** (`ADV-008` -> `AIF-016`)
- **Collapsing `NOT_OBSERVABLE` / `UNKNOWN` into `PASS`** (`ADV-009` -> `AIF-008`, `AIF-008A`, `AIF-019`)
- **Autonomous audit-to-remediation loop** (`ADV-010` -> `AIF-010`)
- **Optimistic `ANY` erasing `CONTRADICTED` evidence** (`ADV-011` -> `AIF-009`, `AIF-011`, `AIF-017`)
- **Self-attesting `SKILL_OUTPUT` (`verified: true`)** (`ADV-012`, `ADV-013` -> `AIF-012`, `AIF-013`, `AIF-018`, `AIF-020`)

### Step 2 — Record Patches & Expanded Sub-Invariants

Use `assets/freeze-review-template.md` to document each adversarial attack (`ADV-XXX`), its required contract patch (`PATCH-XXX`), and the resulting invariant (`AIF-001`..`AIF-020` + `AIF-001A`..`AIF-014A`).

### Step 3 — Run the Deterministic Freeze Audit Script

Execute `scripts/run_freeze_audit.py` to verify that all 8 contracts (`C-01`..`C-08`), 10 forbidden transitions (`FT-01`..`FT-10`), 14 adversarial cases (`ADV-001`..`ADV-014`), 14 patches (`PATCH-001`..`PATCH-014`), and 28 invariants (`AIF-001`..`AIF-020` + `AIF-001A`..`AIF-014A`) are present and synchronized:

```bash
python3 .agent/skills/aif-adversarial-freeze-review/scripts/run_freeze_audit.py
```
