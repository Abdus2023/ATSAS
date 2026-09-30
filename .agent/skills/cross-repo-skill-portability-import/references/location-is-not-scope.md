# "Location Is Not Scope" — Skill Portability Governance Rule

## 1. Core Principle

A skill's file-system location (`streamforge-stremio/.claude/skills/` vs. `ATSAS/.claude/skills/` vs. `ATSAS/.agent/skills/`) does **not** determine its semantic portability scope.

## 2. Required Scope & Adaptation Annotations

Every `SKILL.md` must include a scope block near the top of its Markdown body:

### Purely Generic Skill
```text
SCOPE: ARENA_GENERIC
```

### Generic Skill with Repository-Specific Default Rules or Examples
```text
SCOPE: ARENA_GENERIC
ADAPTATION: STREAMFORGE
```

### Repository-Specific Skill
```text
SCOPE: STREAMFORGE_REPO
```

## 3. Shared Protocol Directory Convention (`_shared/`)

Any directory under a skills root whose name begins with an underscore (such as `_shared/aif/`) is a **versioned protocol dependency**, not an executable skill. Portability and skill validators must skip `_`-prefixed directories during skill enumeration and validate them via the semantic kernel validator (`aif-red-suite` / `aif-verify`).
