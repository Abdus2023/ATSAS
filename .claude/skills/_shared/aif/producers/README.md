# AIF-0.1 Evidence Producer Registry (`producers/`)

- **Protocol Version**: `0.1.0` ([`../VERSION`](../VERSION))
- **Governing Spec**: [`../evidence.md`](../evidence.md) (Section 6)
- **Governing Invariants**: `AIF-007`, `AIF-008`, `AIF-010`, `AIF-012`, `AIF-016`, `AIF-026` (Evidence Monotonicity), `AIF-027` (Producer Independence)

---

## 1. Purpose

This directory is the machine-readable registry of existing skills adapted into **AIF Evidence Producers**. Each entry declares what the skill **can** and **cannot** prove, its three-level output mapping (`OBSERVED -> FINDING -> VERIFIED`), its mandatory `limitations[]`, and its explicit non-capabilities (`authority: false`, `admission: false`, `completion: false`, `mutation: false`).

---

## 2. Registered Evidence Producers

| Registry Entry | Skill | Domain | Supported Bounded Claim | Forbidden Claim Broadening (`AIF-026`) |
|---|---|---|---|---|
| [`secret-leak-scan.yaml`](./secret-leak-scan.yaml) | `secret-leak-scan` | Secret / Credential Scanning | `"No configured secret-pattern matches exist in the scanned paths."` | `"The repository contains no secrets."` |
| [`dependency-vulnerability-audit.yaml`](./dependency-vulnerability-audit.yaml) | `dependency-vulnerability-audit` | Dependency Advisory Audit | `"Configured ecosystem audit reported 0 high/critical advisories for lockfiles [L] at snapshot S."` | `"All dependencies are safe."` or `AUDIT_SKIPPED -> AUDIT_PASSED` |
| [`authorization-boundary-scan.yaml`](./authorization-boundary-scan.yaml) | `authorization-boundary-scan` | Content / Security Boundary | `"No obvious unauthorized-distribution/access-control-bypass mechanism was detected by this scan."` | `"Agent is authorized to modify repository X"` |
| [`docs-integrity-check.yaml`](./docs-integrity-check.yaml) | `docs-integrity-check` | Documentation Integrity | `"Required documentation references resolve for snapshot S."` | `"Documentation is complete and accurate."` |
| [`contract-implementation-sync.yaml`](./contract-implementation-sync.yaml) | `contract-implementation-sync` | Contract / Code Surface Sync | `"Exported symbols in implementation match declared contract surface at snapshot S."` | `"The implementation is correct."` |
| [`contract-freeze-gate.yaml`](./contract-freeze-gate.yaml) | `contract-freeze-gate` | Documentation Contract Freeze | `"The documentation contract satisfies the documentation freeze criteria."` | `"The implementation is correct."` |
| [`ci-workflow-audit.yaml`](./ci-workflow-audit.yaml) | `ci-workflow-audit` | CI Configuration, Execution & Artifact Binding | `"Workflow X / Required job J completed successfully for commit S."` | `"CI is green so newer commits or dirty working trees are verified"` (`AIF-028`) |
| [`test-execution-and-evidence-audit.yaml`](./test-execution-and-evidence-audit.yaml) | `test-execution-and-evidence-audit` | Test Discovery, Execution & Semantic Coverage | `"Executed test targets [T] passed non-vacuously with unmasked exit 0 at snapshot S."` | `"The implementation is bug-free and correct"` (`AIF-026`, `AIF-029`–`AIF-033`) |
| [`dependency-supply-chain-audit.yaml`](./dependency-supply-chain-audit.yaml) | `dependency-supply-chain-audit` | 10-Stage Dependency Supply Chain & Provenance | `"Manifest, lockfile, resolution, integrity, install, build, and artifact provenance observed at snapshot S."` | `"npm audit passed, therefore dependencies are safe / supply chain is established"` (`AIF-034`–`AIF-040`) |
| [`evidence-receipt-generator.yaml`](./evidence-receipt-generator.yaml) | `evidence-receipt-generator` | Immutable JCS Receipt Assembly, Normalization & Coverage | `"Receipt R records historical evidence, coverage, and verifications bound to snapshot S."` | `"Receipt is valid so claims are verified / task is complete"` (`AIF-041`–`AIF-048`) |




