#!/usr/bin/env python3
"""
verify_architecture_layout.py — Verify ATSAS & AIF foundational architecture artifacts,
epistemic state definitions, and strict 'ATSAS' casing.
"""

from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_SPEC_FILES = (
    "README.md",
    "spec/00-overview.md",
    "spec/01-atsas-architecture.md",
    "spec/02-aif-protocol.md",
    "spec/03-epistemic-states.md",
    "spec/04-invariants-and-axioms.md",
)

REQUIRED_STATES = (
    "VERIFIED",
    "UNKNOWN",
    "NOT_OBSERVABLE",
    "PARTIAL",
    "STALE",
    "MISMATCH",
    "CONTRADICTED",
)


def main() -> int:
    repo_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []

    for rel in REQUIRED_SPEC_FILES:
        p = repo_root / rel
        if not p.is_file():
            errors.append(f"Missing required specification artifact: {rel}")
            continue
        text = p.read_text(encoding="utf-8")
        if "ATSAs" in text:
            errors.append(f"Forbidden acronym casing 'ATSAs' found in {rel} (must be 'ATSAS')")

    readme_path = repo_root / "README.md"
    if readme_path.is_file():
        readme_text = readme_path.read_text(encoding="utf-8")
        for st in REQUIRED_STATES:
            if st not in readme_text:
                errors.append(f"README.md missing epistemic state '{st}'")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(
        f"OK: ATSAS/AIF architecture verified across {len(REQUIRED_SPEC_FILES)} core files and {len(REQUIRED_STATES)} epistemic states."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
