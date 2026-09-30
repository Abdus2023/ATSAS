---
name: dependency-supply-chain-audit
description: Reconstructs and audits the 10-stage dependency supply-chain lifecycle (manifest, lockfile, resolution, source/registry, download, integrity, installation, build, artifact provenance, and vulnerability audit) under AIF-0.1.0 without mutating the repository (`NO_KNOWN_VULNERABILITIES != SUPPLY_CHAIN_ESTABLISHED`, `DECLARED != RESOLVED != INSTALLED != BUILT`). Enforces AIF-034..AIF-040 across DependencyManifestRecord, LockfileRecord, ResolutionRecord, SourceRecord, IntegrityRecord, InstallRecord, BuildRecord, ArtifactRecord, and DependencyEvidenceCoverage (SCOPE: ARENA_GENERIC).
---

# Dependency Supply-Chain Audit (`dependency-supply-chain-audit` — Component `C-03`)

```text
SCOPE: ARENA_GENERIC
AIF_VERSION: 0.1.0
COMPONENT_ID: C-03
MUTATES_REPOSITORY: false
```

- **Protocol Binding**: `AIF-0.1.0` ([`../_shared/aif/VERSION`](../_shared/aif/VERSION))
- **Contract ID**: `C-03` ([`../../assurance/component-contracts.md`](../../assurance/component-contracts.md))
- **Governing Invariants**: `AIF-007`, `AIF-008`, `AIF-008A`, `AIF-010`, `AIF-014`, `AIF-014A`, `AIF-026`, `AIF-027`, `AIF-028`, `AIF-034` (Declaration/Resolution Separation), `AIF-035` (Resolution/Installation Separation), `AIF-036` (Installation/Build Separation), `AIF-037` (Artifact Provenance), `AIF-038` (Vulnerability Scope), `AIF-039` (Supply-Chain Unknown Preservation), `AIF-040` (Resolution Snapshot Binding)

---

## 1. Boundary & Separation from `dependency-vulnerability-audit` (`8.1` & `8.12`)

`dependency-supply-chain-audit` does **not** duplicate [`dependency-vulnerability-audit`](../dependency-vulnerability-audit/SKILL.md):
- **`dependency-vulnerability-audit`**: *"Did the available vulnerability mechanism find known vulnerabilities?"* (`KNOWN VULNERABILITY STATUS`)
- **`dependency-supply-chain-audit`**: *"Can we establish what dependencies were selected, from where, with what integrity evidence, and what actually happened during installation/build?"* (`SUPPLY-CHAIN EVIDENCE`)

```text
NO_KNOWN_VULNERABILITIES ≠ SUPPLY_CHAIN_ESTABLISHED
LOCKFILE_MISSING         ≠ VULNERABLE
AUDIT_UNAVAILABLE        ≠ AUDIT_PASSED
```

### Read-Only Constraint (`8.3`)
This skill is strictly **read-only** by default (`MUTATES_REPOSITORY: false`). It must never run `npm install`, `npm update`, `npm audit fix` (`P-DEP-02`), or `npm dedupe`, nor generate a missing lockfile during an audit (`P-DEP-03`).

---

## 2. The 10-Stage Supply-Chain Lifecycle & 9 Evidence Records (`8.2` & `8.4`–`8.11`)

```text
MANIFEST → LOCKFILE → RESOLUTION → SOURCE/REG. → DOWNLOAD → INTEGRITY → INSTALL/BUILD → ARTIFACT → VULN AUDIT → AIF RECEIPT
```

**Fundamental Rule**: The chain is never assumed complete merely because later stages exist (`package.json + package-lock.json + npm audit clean` does not prove a historical installation produced `dist/app.js`).

1. **`DependencyManifestRecord`** (`8.4`): Declares requested ranges (`DECLARED`, not `RESOLVED`, `AIF-034`).
2. **`LockfileRecord`** (`8.4`): Records `status ∈ {PRESENT, MISSING, UNREADABLE, UNSUPPORTED, MULTIPLE, UNKNOWN}` (`status = MISSING`, never `lockfile = false`).
3. **`ResolutionRecord` & `ResolvedDependency`** (`8.5`): Distinguishes `DECLARED`, `RESOLVED`, `INSTALLED`, and `BUILT`; distinguishes compatible semver range resolution (`foo ^1.0` $\to$ `1.9.4` = `VALID_RESOLUTION`, `P-DEP-05`) from `MANIFEST_LOCK_DRIFT` (`DEP-SC-03`).
4. **`SourceRecord`** (`8.6`): `source_type ∈ {REGISTRY, GIT, GIT_COMMIT, LOCAL_PATH, TARBALL, WORKSPACE, UNKNOWN}`. `UNKNOWN` is never inferred as `REGISTRY` (`AIF-039`).
5. **`IntegrityRecord`** (`8.7`): `result ∈ {VERIFIED, MISMATCH, NOT_AVAILABLE, NOT_CHECKED, UNKNOWN}` (`NOT_CHECKED ≠ VERIFIED`, `NOT_AVAILABLE ≠ MISMATCH`).
6. **`InstallRecord`** (`8.8`): `result ∈ {SUCCESS, FAILURE, PARTIAL, INTERRUPTED, UNKNOWN, NOT_EXECUTED}` (`AIF-035`).
7. **`BuildRecord`** (`8.9`): Binds `input_snapshots[]`, `dependency_resolution_ref`, and `artifact_refs[]` (`AIF-036`, `AIF-040`).
8. **`ArtifactRecord`** (`8.10`): Traversable chain `Artifact → Build → Dependency Resolution → Lockfile → Manifest` (`AIF-037`). Without binding, `"dist/app.js exists"` is `ARTIFACT_OBSERVED` with `BUILD_PROVENANCE = UNKNOWN` (`DEP-SC-09`).
9. **`DependencyEvidenceCoverage`** (`8.11`): Summarizes stage coverage and `completeness ∈ {COMPLETE, PARTIAL, NOT_ESTABLISHED, UNKNOWN}`.

---

## 3. Deterministic Execution

```bash
# Run the 16-case Phase 8 supply-chain self-test suite (DEP-SC-01..10 + P-DEP-01..05 + StreamForge check)
python3 .claude/skills/dependency-supply-chain-audit/scripts/audit_supply_chain.py --self-test

# Audit a JSON supply-chain evidence payload
python3 .claude/skills/dependency-supply-chain-audit/scripts/audit_supply_chain.py path/to/supply-chain-input.json
```

See [`README.md`](README.md), [`references/evidence-model.md`](references/evidence-model.md), [`references/npm-profile.md`](references/npm-profile.md), and [`references/output-schema.md`](references/output-schema.md).
