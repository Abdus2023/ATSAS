#!/usr/bin/env python3
"""
audit_skill_portability.py — Deterministically audit a skills directory for
Agent Skills spec conformance and the 'Location is not scope' portability rule.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


SCOPE_RE = re.compile(r"^SCOPE:\s*(ARENA_GENERIC|STREAMFORGE_REPO)\s*$", re.MULTILINE)
ADAPTATION_RE = re.compile(r"^ADAPTATION:\s*([A-Z0-9_-]+)\s*$", re.MULTILINE)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: audit_skill_portability.py <skills-dir> [<skills-dir> ...]", file=sys.stderr)
        return 2

    errors: list[str] = []
    checked = 0

    for arg in sys.argv[1:]:
        root = Path(arg).resolve()
        if not root.is_dir():
            errors.append(f"Skills directory not found: {arg}")
            continue

        for skill_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            if skill_dir.name.startswith("_"):
                continue
            checked += 1
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                errors.append(f"{skill_dir.name}: missing SKILL.md")
                continue
            text = skill_md.read_text(encoding="utf-8")
            m_scope = SCOPE_RE.search(text)
            if not m_scope:
                errors.append(
                    f"{skill_dir.name}: missing 'SCOPE: ARENA_GENERIC' or 'SCOPE: STREAMFORGE_REPO'"
                )
            else:
                scope_val = m_scope.group(1)
                m_adapt = ADAPTATION_RE.search(text)
                adapt_val = m_adapt.group(1) if m_adapt else "NONE"
                print(f"OK    {skill_dir.name:38s} SCOPE={scope_val} ADAPTATION={adapt_val}")

    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        return 1

    print(f"\nPortability audit passed: {checked} skill(s) verified, 0 errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
