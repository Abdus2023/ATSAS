# ATSAS — Arena Tools, Skills, Agentic System

> **ATSAS** defines and organizes what an Arena agent can use and how its agentic system operates.  
> **AIF (Agent Assurance Interface)** defines what can legitimately be claimed about the resulting work.

## Foundational Axioms

- **A skill is not evidence.**
- **A tool result is not automatically verification.**
- **Execution is not completion.**
- **Completion is an evidence-backed claim (`NO EVIDENCE -> NO VERIFIED CLAIM`).**

## Epistemic States

| State | Meaning | May Support `COMPLETE`? |
| :--- | :--- | :---: |
| `VERIFIED` | Sufficient, fresh, scope-bounded, snapshot-bound evidence satisfies the claim. | Yes |
| `UNKNOWN` | Claim has not yet been evaluated or observation is indeterminate. | No |
| `NOT_OBSERVABLE` | The execution environment or tool surface cannot observe the target property. | No |
| `PARTIAL` | Evidence covers only a subset of the declared scope or acceptance criteria. | No |
| `STALE` | Evidence is bound to an older repository snapshot that was subsequently modified. | No |
| `MISMATCH` | Observed snapshot, scope, or output diverges from the claimed target or value. | No |
| `CONTRADICTED` | Direct counter-evidence refutes the claim or violates an acceptance criterion. | No |
