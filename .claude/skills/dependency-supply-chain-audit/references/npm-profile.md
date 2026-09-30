# npm / Node.js Supply-Chain Profile (`npm-profile.md`)

- **Component**: `C-03` (`dependency-supply-chain-audit`)
- **Target Ecosystem**: Node.js / `npm` (`package.json`, `package-lock.json`, `.npmrc`)

---

## 1. Read-Only Inspection Rules (`8.3` & `8.16`)

1. **Forbidden Mutating Commands During Audit**:
   - `npm install`, `npm ci`, `npm update`, `npm audit fix`, `npm dedupe`, `npm pkg set`
   - Running any of these without explicit `MODIFY`/`EXECUTE` authority in `AdmissionRecord` triggers `UNAUTHORIZED_MUTATION` (`P-DEP-02`) or `SCOPE_VIOLATION` (`P-DEP-03`).
2. **Range vs Concrete Lock Resolution (`P-DEP-05` vs `DEP-SC-03`)**:
   - A caret/tilde range in `package.json` (`"foo": "^1.0.0"`) matched to `"version": "1.9.4"` in `package-lock.json` is classified as `VALID_RESOLUTION`.
   - A major-version or pinned-version mismatch (`"foo": "^2.0.0"` in `package.json` vs `"version": "1.9.4"` in `package-lock.json`) is classified as `MANIFEST_LOCK_DRIFT`.
3. **Source & Registry Provenance (`DEP-SC-06` & `AIF-039`)**:
   - Inspects `resolved` URLs (`https://registry.npmjs.org/...`, `git+ssh://...`, `file:...`) and `.npmrc` registry settings.
   - If `resolved` is absent, `source_type` is recorded as `UNKNOWN` (never inferred as `REGISTRY`).
4. **Current StreamForge Branch Implication (`8.16`)**:
   - Presence of `package.json` establishes `MANIFEST = PRESENT` (`DECLARED` dependencies only) and never implies lockfile resolution, installation, build, or vulnerability status without inspecting each corresponding stage explicitly.
