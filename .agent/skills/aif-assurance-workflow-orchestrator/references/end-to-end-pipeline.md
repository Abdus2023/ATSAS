# End-to-End ATSAS & AIF Assurance Engineering Pipeline Reference

## 1. Stage-to-Skill & Tool Mapping

| Stage | Skill in `.agent/skills/` | Verification Script / CLI Tool |
|---|---|---|
| **Stage 1** | `atsas-aif-architecture-bootstrap` | `scripts/verify_architecture_layout.py` |
| **Stage 2** | `cross-repo-skill-portability-import` | `scripts/audit_skill_portability.py` |
| **Stage 3** | `assurance-test-matrix-designer` | `scripts/validate_test_matrix.py` |
| **Stage 4** | `skill-capability-overlap-audit` | `scripts/check_capability_overlap.py` |
| **Stage 5** | `aif-component-contract-designer` | `scripts/validate_component_contracts.py` |
| **Stage 6** | `aif-adversarial-freeze-review` | `scripts/run_freeze_audit.py` |
| **Stage 7** | `aif-semantic-kernel-engineer` | `scripts/verify_semantic_kernel.py` + `.agent/tools/aif-red-suite` |
| **Meta** | `skill-creator` | `scripts/validate_skill.py --all .agent/skills` |

## 2. Non-Bypassable Gate Rule

No stage may be marked `VERIFIED` if an upstream stage reports `UNKNOWN`, `MISMATCH`, `STALE`, or `CONTRADICTED`.
