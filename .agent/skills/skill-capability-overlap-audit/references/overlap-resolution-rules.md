# Three Critical Overlap Resolution Rules & 4-Layer Skill Topology

## 1. Existing Detector Adapter Pattern

Instead of creating duplicate detector skills, map existing skills directly to AIF-0.1 Semantic Kernel objects:

```text
secret-leak-scan                  ──► Finding[] + EvidenceRef[]
dependency-vulnerability-audit    ──► Finding[] + EvidenceRef[]
authorization-boundary-scan       ──► Finding[] + EvidenceRef[]
repo-onboarding-audit             ──► Finding[] + EvidenceRef[]
docs-integrity-check              ──► Finding[] + EvidenceRef[]
doc-symbol-audit                  ──► Finding[] + EvidenceRef[]
session-git-sync-check            ──► SnapshotRef + Finding[] + EvidenceRef[]
contract-implementation-sync      ──► VerificationRecord + EvidenceRef[]
contract-freeze-gate              ──► Claim[] + VerificationRecord[]
```

## 2. Four-Layer Skill Architecture

1. **Layer 1 — Intake, Authority & Change Attribution**: `arena-intake-and-authority` (`C-01`), `agent-change-scope-audit` (`C-02`), `session-git-sync-check`.
2. **Layer 2 — Domain Detectors & Auditors**: `secret-leak-scan`, `dependency-vulnerability-audit`, `dependency-supply-chain-audit` (`C-03`), `authorization-boundary-scan`, `repo-onboarding-audit`, `docs-integrity-check`, `doc-symbol-audit`, `contract-implementation-sync`, `ci-workflow-audit` (`C-04`), `test-execution-and-evidence-audit` (`C-05`).
3. **Layer 3 — Normalization & Completion Gate**: `evidence-receipt-generator` (`C-06`), `arena-completion-gate` (`C-07`), `contract-freeze-gate`.
4. **Layer 4 — Meta-Assurance & Authoring**: `skill-evaluation-harness` (`C-08`), `skill-creator`.
