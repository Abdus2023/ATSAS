# `dependency-supply-chain-audit` (`C-03`)

Read-only `AIF-0.1.0` evidence producer that reconstructs and audits the 10-stage dependency supply-chain chain (`MANIFEST → LOCKFILE → RESOLUTION → SOURCE/REGISTRY → DOWNLOAD → INTEGRITY → INSTALL/BUILD → ARTIFACT → VULN AUDIT → AIF RECEIPT`).

## Directory Structure

```text
.claude/skills/dependency-supply-chain-audit/
├── SKILL.md
├── README.md
├── scripts/
│   └── audit_supply_chain.py
└── references/
    ├── evidence-model.md
    ├── npm-profile.md
    └── output-schema.md
```

## Governing Invariants (`AIF-034` – `AIF-040`)

- **`AIF-034` — Declaration/Resolution Separation**: `DECLARED(dependency) ≠ RESOLVED(dependency)`
- **`AIF-035` — Resolution/Installation Separation**: `RESOLVED(dependency) ≠ INSTALLED(dependency)`
- **`AIF-036` — Installation/Build Separation**: `INSTALLED(dependency) ≠ USED_IN_BUILD(dependency)`
- **`AIF-037` — Artifact Provenance**: `ARTIFACT_CLAIM requires PROVEN_BUILD_ORIGIN`
- **`AIF-038` — Vulnerability Scope**: `VULNERABILITY_AUDIT_RESULT` satisfies only vulnerability-audit claims, never general supply-chain trust (`NO_KNOWN_VULNERABILITIES ≠ SUPPLY_CHAIN_ESTABLISHED`)
- **`AIF-039` — Supply-Chain Unknown Preservation**: `UNOBSERVABLE(stage) ⇒ UNKNOWN(stage)`
- **`AIF-040` — Resolution Snapshot Binding**: Resolution evidence is valid only when its manifest/lockfile subject matches the required snapshot
