# 03 — Epistemic & Assurance State Model

## 1. Motivation: Rejecting Binary Collapse

Traditional automation pipelines collapse verification outcomes into a binary `PASS` / `FAIL` boolean. In agent-driven software engineering, binary collapse is dangerous because it obscures the difference between:

* A test suite that passed (`VERIFIED`),
* A test suite that passed **before** the agent made a "minor cleanup edit" (`STALE`),
* A unit test that passed while integration tests could not run due to missing credentials (`PARTIAL` / `NOT_OBSERVABLE`),
* A verification step that checked the wrong file or branch (`MISMATCH`), and
* A claim that was never checked at all (`UNKNOWN`).

**AIF preserves uncertainty and partial observability through explicit epistemic states.**

---

## 2. Canonical Epistemic States

| State | Code | Definition |
| :--- | :--- | :--- |
| **Verified** | `VERIFIED` | Sufficient, fresh, scope-bounded, snapshot-bound, non-contradicted evidence satisfies the claim predicate across its entire declared scope. |
| **Unknown** | `UNKNOWN` | Initial or unevaluated state; no verification observation has been bound to the claim, or the observation is inconclusive. |
| **Not Observable** | `NOT_OBSERVABLE` | The target property cannot be observed from the current execution environment, tool surface, or permissions (e.g., external service unavailable, hardware dependency absent). |
| **Partial** | `PARTIAL` | Valid evidence exists for a strict subset of the claim's declared scope or conditions, leaving the remainder unverified or unobserved. |
| **Stale** | `STALE` | Evidence was previously `VERIFIED` against snapshot $S_i$, but the workspace has since transitioned to snapshot $S_j$ ($j > i$) with modifications intersecting the claim's scope. |
| **Mismatch** | `MISMATCH` | The bound observation or evidence refers to a different scope, snapshot, target artifact, or configuration than the claim asserts. |
| **Contradicted** | `CONTRADICTED` | Empirical observation directly refutes the claim predicate (e.g., failing test assertion, compiler error, schema validation failure, violated invariant). |

---

## 3. State Transition Rules

```text
                    ┌──────────────────┐
                    │     UNKNOWN      │
                    └────────┬─────────┘
                             │
         ┌───────────┬───────┼───────┬───────────┬────────────┐
         ↓           ↓       ↓       ↓           ↓            ↓
  NOT_OBSERVABLE  MISMATCH PARTIAL VERIFIED CONTRADICTED      │
                             │       │                        │
                             │       │ (Workspace mutated     │
                             │       │  in covered scope)     │
                             │       ↓                        │
                             └───→ STALE ←────────────────────┘
```

1. **Initialization**: Every claim starts in `UNKNOWN`.
2. **Promotion to `VERIFIED`**: A claim transitions to `VERIFIED` **only** when:
   * At least one valid Evidence artifact is bound to the claim,
   * The Evidence `snapshot_id` matches the target repository snapshot,
   * The Evidence `scope` covers 100% of the claim's declared `scope`,
   * The underlying Observation has `observability_status: "FULL"`, and
   * No bound Observation or Evidence contradicts the claim.
3. **Invalidation to `STALE`**: Whenever a mutating tool execution creates a new snapshot $S_{\text{new}}$ whose modified paths intersect a `VERIFIED` claim's scope (or when full-tree freshness is required), the claim transitions immediately from `VERIFIED` to `STALE`.
4. **Subset Coverage to `PARTIAL`**: If Evidence is fresh and non-contradicted, but either `observability_status == "PARTIAL"` or the Evidence `scope` covers only a proper subset of the claim's `scope`, the state **must** be at most `PARTIAL`.
5. **Refutation to `CONTRADICTED`**: Any fresh observation demonstrating predicate failure transitions the claim to `CONTRADICTED`, overriding prior `VERIFIED` or `PARTIAL` states.

---

## 4. Aggregation Lattice (Multi-Claim & Acceptance Composition)

When an **Acceptance Criterion** or **Task Completion Verdict** aggregates multiple mandatory claims $C_1, C_2, \dots, C_n$, the composite epistemic state is governed by a dominance order (from most severe blocker to fully verified):

$$\text{CONTRADICTED} \succ \text{MISMATCH} \succ \text{STALE} \succ \text{NOT\_OBSERVABLE} \succ \text{UNKNOWN} \succ \text{PARTIAL} \succ \text{VERIFIED}$$

### Composition Rules

* **Universal Verification for Acceptance**: A composite acceptance criterion achieves `VERIFIED` (and thus `ACCEPTED`) **if and only if** $\forall i \in \{1..n\}, \text{state}(C_i) = \text{VERIFIED}$.
* **No Silent Promotion**: A `PARTIAL`, `NOT_OBSERVABLE`, `STALE`, `MISMATCH`, or `UNKNOWN` claim **must never** be rounded up to `VERIFIED` during aggregation.
* **Explicit Blocker Reporting**: When a task cannot be declared `COMPLETE`, the AIF Completion Manifest must preserve the exact set of non-`VERIFIED` states and the criterion IDs they block.
