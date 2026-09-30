---
name: skill-capability-overlap-audit
description: Audits an existing skill library against the 42-case Arena Assurance Test Matrix (`AAI-001`..`AAI-034`, `P-001`..`P-008`) to classify coverage (`COVERED`, `PARTIALLY_COVERED`, `UNCOVERED`, `DUPLICATE`, `CONFLICTING`, `ORPHANED`) and prevent duplicate or conflicting skills before authoring new `SKILL.md` files. Use whenever planning new assurance skills, deciding whether to wrap an existing detector with an `EvidenceRef` adapter versus creating a new skill, or verifying the separation between application security (`authorization-boundary-scan`) and agent task authority (`arena-intake-and-authority`).
---

# Skill Capability Overlap & Adapter Boundary Audit

```text
SCOPE: ARENA_GENERIC
```

```yaml
aif:
  version: "0.1"
  consumes:
    - SnapshotRef
  produces:
    - Finding
    - EvidenceRef
  mutates_repository: false
```

Prevents skill duplication, responsibility collisions, and "god skill" sprawl by auditing existing skills against the 42-case behavioral and pressure test matrix before any new `SKILL.md` is created.

## Workflow

### Step 1 — Apply the Three Overlap Resolution Rules

Read `references/overlap-resolution-rules.md` before proposing any new skill directory:

1. **Adapter Over Duplication (`secret-leak-scan` vs. `secret-and-credential-audit`)**:
   - When an existing detector skill already performs the core scan (e.g., `secret-leak-scan`), do **not** create a duplicate skill. Wrap its output in a canonical `EvidenceRef` + `Finding` adapter.
2. **Two Kinds of Authorization (`authorization-boundary-scan` != `arena-intake-and-authority`)**:
   - `authorization-boundary-scan` is an **application/compliance security detector** scanning repository source code and docs.
   - `arena-intake-and-authority` (`C-01`) is **agent task/governance authority** producing `Request`, `AuthorityEvent[]`, and `AdmissionRecord`. Never merge them.
3. **Detectors Never Decide Completion (`AIF-010`, `AIF-012`)**:
   - Existing detectors emit `Finding[]` + `EvidenceRef[]` only (with `remediation_authorized: false`) and never emit `CompletionResult`.

### Step 2 — Classify All 42 Test Cases & All Existing Skills

Ensure `.claude/assurance/capability-map.md` and `ARENA_CAPABILITY_OVERLAP_MATRIX.md` classify every existing skill and every test case (`AAI-001`..`AAI-034`, `P-001`..`P-008`) using the six canonical labels:
- `COVERED`
- `PARTIALLY_COVERED`
- `UNCOVERED`
- `DUPLICATE`
- `CONFLICTING`
- `ORPHANED`

### Step 3 — Run Deterministic Capability Overlap Verification

Execute `scripts/check_capability_overlap.py` to verify that every skill in `.claude/skills/` is accounted for in the capability map and that all 42 test cases and 6 classification labels are present:

```bash
python3 .agent/skills/skill-capability-overlap-audit/scripts/check_capability_overlap.py
```
