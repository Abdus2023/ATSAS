#!/usr/bin/env python3
"""
run_assurance_pipeline.py — Execute all 7 stage verification scripts in .agent/skills/
plus .agent/tools/ contract and RED suite checks in causal order.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    agent_dir = repo_root / ".agent"

    steps = [
        (
            "Stage 1: Architecture Bootstrap",
            [
                sys.executable,
                str(agent_dir / "skills" / "atsas-aif-architecture-bootstrap" / "scripts" / "verify_architecture_layout.py"),
                str(repo_root),
            ],
        ),
        (
            "Stage 2: Cross-Repo Skill Portability Audit",
            [
                sys.executable,
                str(agent_dir / "skills" / "cross-repo-skill-portability-import" / "scripts" / "audit_skill_portability.py"),
                str(repo_root / ".claude" / "skills"),
                str(agent_dir / "skills"),
            ],
        ),
        (
            "Stage 3: 42-Case Assurance Test Matrix Validation",
            [
                sys.executable,
                str(agent_dir / "skills" / "assurance-test-matrix-designer" / "scripts" / "validate_test_matrix.py"),
            ],
        ),
        (
            "Stage 4: Capability Overlap & Adapter Boundary Audit",
            [
                sys.executable,
                str(agent_dir / "skills" / "skill-capability-overlap-audit" / "scripts" / "check_capability_overlap.py"),
                str(repo_root),
            ],
        ),
        (
            "Stage 5: Component Contracts (C-01..C-08) Validation",
            [
                sys.executable,
                str(agent_dir / "skills" / "aif-component-contract-designer" / "scripts" / "validate_component_contracts.py"),
                str(repo_root),
            ],
        ),
        (
            "Stage 6: Adversarial Freeze Review (ADV-001..014 & AIF-001..020)",
            [
                sys.executable,
                str(agent_dir / "skills" / "aif-adversarial-freeze-review" / "scripts" / "run_freeze_audit.py"),
                str(repo_root),
            ],
        ),
        (
            "Stage 7: AIF-0.1 Semantic Kernel & 28-Case RED Suite",
            [
                sys.executable,
                str(agent_dir / "skills" / "aif-semantic-kernel-engineer" / "scripts" / "verify_semantic_kernel.py"),
                str(repo_root),
            ],
        ),
        (
            "Meta-Stage: Validate All Skills in .agent/skills/",
            [
                sys.executable,
                str(agent_dir / "skills" / "skill-creator" / "scripts" / "validate_skill.py"),
                "--all",
                str(agent_dir / "skills"),
            ],
        ),
    ]

    for label, cmd in steps:
        proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            print(f"[FAIL] {label}\n{proc.stdout}\n{proc.stderr}", file=sys.stderr)
            return 1
        print(f"[PASS] {label}")

    print("\nOK: Full 8-stage ATSAS & AIF assurance engineering pipeline verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
