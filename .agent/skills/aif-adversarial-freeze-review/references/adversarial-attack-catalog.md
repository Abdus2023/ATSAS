# Adversarial Attack Catalog (`ADV-001`..`ADV-014`) & Forbidden Transitions (`FT-01`..`FT-10`)

## 1. Ten Forbidden State Transitions (`FT-01` – `FT-10`)

| ID | Forbidden Transition | Prevented By |
|---|---|---|
| `FT-01` | `CLAIMED -> VERIFIED` | `AIF-006`, `AIF-013`, `AIF-018` |
| `FT-02` | `DECLARED -> EXECUTED` | `AIF-004`, `AIF-004A` |
| `FT-03` | `EXECUTED -> PASSED` | `AIF-005`, `AIF-005A` |
| `FT-04` | `CI_CONFIGURED -> CI_PASSED` | `AIF-004`, `AIF-005` |
| `FT-05` | `SCANNER_CLEAN -> REPOSITORY_SAFE` | `AIF-007`, `AIF-016` |
| `FT-06` | `CODE_PRESENT -> IMPLEMENTED` | `AIF-006`, `AIF-007` |
| `FT-07` | `IMPLEMENTED -> VERIFIED` | `AIF-006`, `AIF-006A` |
| `FT-08` | `VERIFIED@snapshot_A -> VERIFIED@snapshot_B` | `AIF-002A`, `AIF-014`, `AIF-014A`, `AIF-015` |
| `FT-09` | `AUDIT_FINDING -> REMEDIATED` | `AIF-001`, `AIF-010` |
| `FT-10` | `UNKNOWN -> PASS` | `AIF-008`, `AIF-008A`, `AIF-013`, `AIF-019` |

## 2. Universal Execution Envelope

Every assurance skill must obey:
```text
SkillInput -> Observation/execution -> SkillResult -> EvidenceRef[] -> State classification
```
where `RESULT != EVIDENCE != DECISION`.
