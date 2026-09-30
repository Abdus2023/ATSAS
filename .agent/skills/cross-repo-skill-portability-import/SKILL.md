---
name: cross-repo-skill-portability-import
description: Imports, normalizes, and audits Agent Skills across repositories while enforcing the "Location is not scope" governance rule (`SCOPE: ARENA_GENERIC` vs `SCOPE: STREAMFORGE_REPO` and `ADAPTATION:` tags). Use whenever importing skills from another repository or branch (such as streamforge-stremio), checking whether skills in `.claude/skills/` or `.agent/skills/` contain unflagged domain-specific coupling, or running portability + structural + fence + link + secret hygiene checks on a skill library.
---

# Cross-Repository Skill Portability Import & Audit

```text
SCOPE: ARENA_GENERIC
```

```yaml
aif:
  version: "0.1"
  consumes:
    - SnapshotRef
  produces:
    - EvidenceRef
    - Finding
  mutates_repository: false
```

Imports and audits Agent Skills across repositories while preventing silent domain coupling through the **"Location is not scope"** governance rule.

## Workflow

### Step 1 — Classify Portability Scope ("Location is not scope")

Read `references/location-is-not-scope.md` before copying or modifying any skill directory. Just because a skill lives inside a domain repository (e.g., `streamforge-stremio/.claude/skills/`) does not make it domain-specific, and just because a skill is imported into a generic repository (`ATSAS`) does not mean its domain assumptions have been documented.

Every skill must explicitly declare in its `SKILL.md` body:
- `SCOPE: ARENA_GENERIC` (reusable across Arena repositories) or `SCOPE: STREAMFORGE_REPO` (domain-specific)
- `ADAPTATION: <REPO_NAME>` when a generic skill bundles default rules or examples tailored to a specific repository.

### Step 2 — Run the Portability & Structural Audit Script

Execute `scripts/audit_skill_portability.py` against the target skills directory (e.g., `.claude/skills` or `.agent/skills`):

```bash
python3 .agent/skills/cross-repo-skill-portability-import/scripts/audit_skill_portability.py .claude/skills
```

This script deterministically verifies:
1. Every non-`_`-prefixed skill directory passes Agent Skills structural rules (`SKILL.md`, frontmatter `name` & `description`, resource existence).
2. Every skill declares `SCOPE:` (`ARENA_GENERIC` or `STREAMFORGE_REPO`).
3. Any skill referencing domain-specific terms (e.g., `StreamForge`, `Stremio`, `addon`) without an explicit `ADAPTATION:` or `SCOPE:` annotation is flagged.

### Step 3 — Verify Markdown Fences, Links, and Secret Hygiene

After running `scripts/audit_skill_portability.py`, run the companion repository hygiene checks:
- Code fence balance (`check_fences.sh`)
- Relative link resolution (`check_links.py`)
- Secret leak scan (`scan_secrets.py`)
