# ATSAS vs. AIF Boundary Axioms & 9-Concern Protocol Reference

## 1. Architectural Separation

```text
ATSAS (Capability & Behavior Layer)
└── Agentic System
    ├── Tools (declarative capability + raw observation contracts)
    ├── Skills (procedural workflows + progressive disclosure)
    ├── Protocols
    ├── Repository interaction
    └── Agent behavior
             │
             ↓
AIF (Agent Assurance Interface — Claim & Evidence Layer)
    ├── Authority
    ├── Admission
    ├── Execution
    ├── Change Attribution
    ├── Observation
    ├── Verification
    ├── Evidence
    ├── Acceptance
    └── Completion
```

## 2. Concern-to-Question Mapping

| Concern | Question Answered |
|---|---|
| **Authority / Admission** | May this operation occur, and within what action/path/time scope? |
| **Execution** | Did an operation actually execute (`command + context + time + snapshot + exit_code`)? |
| **Change Attribution** | What changed between snapshots, and what is the provenance basis for actor causality? |
| **Observation** | What was directly observable vs. `NOT_OBSERVABLE`? |
| **Verification** | Does the observation satisfy a specific, bounded `Claim`? |
| **Evidence** | What content-addressed artifact (`EvidenceRef`) proves the verification at that snapshot? |
| **Acceptance** | Does `EvidenceCoverage(E, C)` satisfy the task's `AcceptanceExpression`? |
| **Completion** | May the task be declared `COMPLETABLE` by `arena-completion-gate`? |
