# The Eight AIF Component Contracts (`C-01`..`C-08`) & Responsibility Matrix

| Contract | Component Name | Produces (Kernel Objects) | Does Not Decide |
|---|---|---|---|
| `C-01` | `arena-intake-and-authority` | `Request`, `AuthorityEvent[]`, `AdmissionRecord`, `AcceptanceExpression` | Task completion |
| `C-02` | `agent-change-scope-audit` | `SnapshotRef`, `ChangeRecord[]`, `Finding[]`, `EvidenceRef[]` | Task authorization |
| `C-03` | `dependency-supply-chain-audit` | `Finding[]`, `EvidenceRef[]` | Task completion |
| `C-04` | `ci-workflow-audit` | `ExecutionRecord[]`, `Finding[]`, `EvidenceRef[]`, `VerificationRecord[]` | Overall repository success |
| `C-05` | `test-execution-and-evidence-audit` | `ExecutionRecord[]`, `EvidenceRef[]`, `VerificationRecord[]` | Overall task completion |
| `C-06` | `evidence-receipt-generator` | `EvidenceCoverage[]`, `ArenaEvidenceReceipt` | Missing evidence (never fabricates) |
| `C-07` | `arena-completion-gate` | `CompletionResult` | New evidence or autonomous remediation |
| `C-08` | `skill-evaluation-harness` | `SkillEvalReceipt` | Repository task completion |
