#!/usr/bin/env python3
"""
run_freeze_audit.py — Verify that .claude/assurance/component-contracts.md and
.claude/assurance/aif-v01-freeze-review.md contain all C-01..C-08, FT-01..FT-10,
ADV-001..ADV-014, PATCH-001..PATCH-014, and AIF-001..AIF-020 (+A).
"""

from __future__ import annotations

import sys
from pathlib import Path


SUB_INVARIANTS = (
    "AIF-001A",
    "AIF-002A",
    "AIF-003A",
    "AIF-004A",
    "AIF-005A",
    "AIF-006A",
    "AIF-008A",
    "AIF-014A",
)


def main() -> int:
    repo_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    contracts_path = repo_root / ".claude" / "assurance" / "component-contracts.md"
    review_path = repo_root / ".claude" / "assurance" / "aif-v01-freeze-review.md"

    errors: list[str] = []
    if not contracts_path.is_file():
        errors.append("Missing .claude/assurance/component-contracts.md")
    if not review_path.is_file():
        errors.append("Missing .claude/assurance/aif-v01-freeze-review.md")
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    contracts_text = contracts_path.read_text(encoding="utf-8")
    review_text = review_path.read_text(encoding="utf-8")

    for i in range(1, 9):
        cid = f"C-{i:02d}"
        if f"`{cid}`" not in contracts_text:
            errors.append(f"component-contracts.md missing `{cid}`")
        if f"`{cid}`" not in review_text:
            errors.append(f"aif-v01-freeze-review.md missing `{cid}`")

    for i in range(1, 11):
        ft_id = f"FT-{i:02d}"
        if f"`{ft_id}`" not in contracts_text:
            errors.append(f"component-contracts.md missing `{ft_id}`")

    for i in range(1, 15):
        adv_id = f"ADV-{i:03d}"
        patch_id = f"PATCH-{i:03d}"
        if f"`{adv_id}`" not in review_text:
            errors.append(f"aif-v01-freeze-review.md missing `{adv_id}`")
        if f"`{patch_id}`" not in review_text:
            errors.append(f"aif-v01-freeze-review.md missing `{patch_id}`")

    for i in range(1, 21):
        aif_id = f"AIF-{i:03d}"
        if f"`{aif_id}`" not in contracts_text:
            errors.append(f"component-contracts.md missing `{aif_id}`")
        if f"`{aif_id}`" not in review_text:
            errors.append(f"aif-v01-freeze-review.md missing `{aif_id}`")

    for sub_id in SUB_INVARIANTS:
        if f"`{sub_id}`" not in contracts_text:
            errors.append(f"component-contracts.md missing `{sub_id}`")
        if f"`{sub_id}`" not in review_text:
            errors.append(f"aif-v01-freeze-review.md missing `{sub_id}`")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(
        "OK: Freeze review verified (8 contracts, 10 forbidden transitions, 14 adversarial cases, 14 patches, 28 invariants)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
