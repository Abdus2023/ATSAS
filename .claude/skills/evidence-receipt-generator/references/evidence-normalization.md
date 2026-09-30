# Evidence Normalization & Source Locators (`evidence-normalization.md`)

- **Component**: `C-06` (`evidence-receipt-generator`)
- **Governing Invariants**: `AIF-008`, `AIF-016`, `AIF-026`, `AIF-045`, `AIF-047`

---

## 1. Normalization Non-Expansion (`9.7` & `AIF-045`)

```text
SOURCE CLAIM → NORMALIZED CLAIM (same or narrower semantic scope)
```

| Producer | Source Observation | Allowed Normalized Proposition | Forbidden Expansion |
|---|---|---|---|
| `secret-leak-scan` | `"No matches in scanned paths."` | `"No matching patterns were observed in the scanned paths."` | `"No secrets exist in the repository."` |
| `ci-workflow-audit` | `.github/workflows/ci.yml` present | `"CI workflow is CONFIGURED."` | `"CI passed."` (`P-REC-02`) |
| `test-execution-and-evidence-audit` | `tsc --noEmit` exited `0` | `"TypeScript typecheck passed at snapshot S."` | `"Full tests passed."` |
| Any producer | `status = UNKNOWN` | `status = UNKNOWN` | `status = false` / `PASS` (`P-REC-06`) |

---

## 2. Standardized `source_locator` URI Schemes (`9.9`)

| `source_type` | Canonical `source_locator` Format |
|---|---|
| `COMMAND_OUTPUT` | `execution://exec-123/stdout` |
| `FILE_CONTENT` | `git://blob/abc123/path/to/file` |
| `CI_RUN` | `ci://run/456` |
| `CI_ARTIFACT` | `ci://run/456/artifact/report.json` |
| `TEST_REPORT` | `test://execution/789/report` |
| `SCANNER_RESULT` | `scanner://secret-leak-scan/123` |
| `HUMAN_AUTHORIZATION` | `authority://event/42` |
