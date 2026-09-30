# AIF-0.1.0 Behavioral Test Corpus (`tests/README.md`)

- **Document Class**: `EXECUTABLE-CONFORMANCE`
- **Protocol Family / Concrete Version**: `AIF-0.1` / `0.1.0` ([`../VERSION`](../VERSION))
- **Corpus File**: [`cases.yaml`](./cases.yaml) (`corpus_id: aif-behavioral-v1`, `41 RED + 8 PRESSURE = 49 cases`, plus `first_red_gate`)
- **Oracle Specification**: [`oracle.md`](./oracle.md)

---

## 1. Three Levels of Testing

The 49 behavioral cases in [`cases.yaml`](./cases.yaml) are evaluated across three distinct test classes so that an integration failure is never misdiagnosed as a semantic kernel failure:

```text
             AIF-0.1
                │
        ┌───────┴────────┐
        ▼                ▼
 semantic tests      skill tests
        │                │
        └───────┬────────┘
                ▼
          integration
             tests
                │
                ▼
          regression set
```

1. **A. Semantic Tests (`semantic`)**: Test the `AIF-0.1` kernel directly (`EXECUTED + NOT_AUTHORIZED -> AUTHORITY_VIOLATION`) without requiring a live repository.
2. **B. Skill Behavioral Tests (`skill_behavioral`)**: Test whether an individual skill correctly applies `AIF-0.1` (`ci-workflow-audit` + workflow exists + no CI execution -> `configured / execution unknown`).
3. **C. Integration Tests (`integration`)**: Test whether multiple skills preserve semantics across handoffs (`secret-leak-scan -> Finding + EvidenceRef -> evidence-receipt-generator -> ArenaEvidenceReceipt -> arena-completion-gate`).

---

## 2. 55-Invariant Coverage Matrix (`AIF-001` .. `AIF-055`, `41 RED + 8 PRESSURE = 49 Cases`)

| Invariant | Rule Summary | RED Case(s) | Pressure Case(s) | Integration |
|---|---|---|---|---|
| `AIF-001` | Authority precedes mutation (`EXECUTED ^ NOT_AUTHORIZED => AUTHORITY_VIOLATION`) | `RED-001`, `RED-002`, `RED-004` | `P-08` | yes |
| `AIF-002` | Snapshot identity & scope (`commit` != working state) | `RED-003`, `RED-005`, `RED-006`, `RED-008`, `RED-032` | `P-02`, `P-04` | yes |
| `AIF-003` | Provenance & attribution (`DIFF(S0,S1)` != actor attribution) | `RED-003`, `RED-005`..`RED-008`, `RED-032` | `P-04`, `P-08` | yes |
| `AIF-004` | Declaration != execution | `RED-002`, `RED-018`, `RED-019` | `P-03` | yes |
| `AIF-005` | Execution != success | `RED-024`, `RED-025` | `P-03` | yes |
| `AIF-006` | Success != verification | `RED-022`, `RED-026`, `RED-029` | `P-01` | yes |
| `AIF-007` | Evidence bounded by subject, scope, snapshot, method | `RED-009`, `RED-010`, `RED-016`, `RED-017`, `RED-021`, `RED-027`, `RED-030` | `P-06` | yes |
| `AIF-008` | Unknown preservation (`NOT_CHECKED != NOT_OBSERVABLE != PASS`) | `RED-013`, `RED-019` | `P-03`, `P-06` | yes |
| `AIF-009` | Declarative `AcceptanceExpression` evaluation | `RED-031`, `RED-034` | `P-05` | yes |
| `AIF-010` | Audit != remediation (`AUDIT FINDING -> REPORT -> STOP`) | `RED-005` | `P-02` | yes |
| `AIF-011` | Independent criterion evidence | `RED-034` | `P-07` | yes |
| `AIF-012` | Detector finding != completion judgment | `RED-030` | `P-06` | yes |
| `AIF-013` | Completion cannot manufacture evidence | `RED-022`, `RED-027` | `P-01` | yes |
| `AIF-014` | Mutation invalidates intersecting evidence | `RED-020`, `RED-023`, `RED-028`, `RED-033` | `P-04` | yes |
| `AIF-015` | Subject & snapshot compatibility | `RED-011`, `RED-028` | `P-04` | yes |
| `AIF-016` | Normalization cannot broaden claims | `RED-012`, `RED-030` | `P-06` | yes |
| `AIF-017` | Contradiction preservation (`E1 CLEAN` vs `E2 FINDING`) | `RED-014`, `RED-015`, **`RED-035`** | `P-04` | yes |
| `AIF-018` | Skill assertions != evidence | `RED-022` | `P-01` | yes |
| `AIF-019` | Missing evidence remains explicit | `RED-034` | `P-03`, `P-05` | yes |
| `AIF-020` | Receipt reproducibility (`Evaluate(R) == Evaluate(R)`) | **`RED-036`** | `P-04`, `P-05`, `P-07` | yes |
| `AIF-021` | No retroactive authorization (`T2 > T1` cannot authorize execution at `T1`) | `RED-001`, `RED-004` (`evaluate_intake.py --case AIF-021`) | `P-08` | yes |
| `AIF-022` | Authority is non-transitive by default (across actors and actions) | `RED-002`, `RED-003` (`evaluate_intake.py --case AIF-022`) | `P-08` | yes |
| `AIF-023` | Attribution is evidence-dependent (`DIFF(S0,S1)` != `AGENT_ATTRIBUTED`) | `RED-006`, `RED-007`, **`RED-037`**, **`RED-039`**, **`RED-040`** | `P-04`, `P-08` | yes |
| `AIF-024` | Pre-existing state is not agent responsibility (`DIRTY@S0` -> `PREEXISTING`) | `RED-006`, **`RED-038`** | `P-04` | yes |
| `AIF-025` | Scope audit is snapshot-relative (`S0 -> S1` audit is `STALE` at `S2`) | `RED-020`, `RED-028`, **`RED-041`** | `P-04` | yes |
| `AIF-026` | Evidence Monotonicity (`Strength(Adapter(E)) <= Strength(E)`) | `RED-012`, `RED-030` (`ADP-01`, `ADP-10`, `ADP-11`, `ADP-14`) | `P-06` | yes |
| `AIF-027` | Producer Independence (producers never emit completion verdicts) | `RED-022`, `RED-030` (`ADP-12`) | `P-01`, `P-06` | yes |
| `AIF-028` | CI Subject Binding (`VERIFY(C, CI_E) => Subject(C) == Subject(CI_E)`) | `RED-020` (`CI-04`, `CI-05`, `CI-12`, `CI-13`, `CI-19`, `CI-20`) | `P-03`, `P-07` | yes |
| `AIF-029` | Execution Evidence (`PASS_CLAIM => EXECUTION_OBSERVED`) | `RED-022`, `RED-024`, `RED-025` (`TEST-01`, `TEST-05`) | `P-TEST-01`, `P-TEST-03` | yes |
| `AIF-030` | Discovery Completeness (`ALL_REQUIRED_TESTS => DISCOVERY_COVERAGE_SUFFICIENT`) | `RED-026` (`TEST-02`, `TEST-03`, `TEST-08`, `TEST-19`) | `P-03`, `P-07` | yes |
| `AIF-031` | Test Snapshot Binding (`TEST(S0)=PASS + SOURCE(S0->S1) changed => STALE/UNVERIFIED`) | `RED-027` (`TEST-06`, `TEST-07`) | `P-TEST-04` | yes |
| `AIF-032` | Test Scope Preservation (`selected < required` is `PARTIAL`) | `RED-026` (`TEST-02`, `TEST-08`, `TEST-09`, `TEST-10`) | `P-01`, `P-07` | yes |
| `AIF-033` | Test Result Non-Transitivity (`TYPECHECK_PASS != UNIT_TEST_PASS != IMPLEMENTATION_CORRECT`) | `RED-030` (`TEST-18`, `TEST-19`) | `P-06`, `P-07` | yes |
| `AIF-034` | Declaration/Resolution Separation (`DECLARED != RESOLVED`) | `DEP-SC-01`, `DEP-SC-03` | `P-DEP-05` | yes |
| `AIF-035` | Resolution/Installation Separation (`RESOLVED != INSTALLED`) | `DEP-SC-02` | `P-03` | yes |
| `AIF-036` | Installation/Build Separation (`INSTALLED != USED_IN_BUILD`) | `DEP-SC-02`, `DEP-SC-10` | `P-04` | yes |
| `AIF-037` | Artifact Provenance (`ARTIFACT_CLAIM requires PROVEN_BUILD_ORIGIN`) | `DEP-SC-09`, `DEP-SC-10` | `P-04` | yes |
| `AIF-038` | Vulnerability Scope (`NO_KNOWN_VULNERABILITIES != SUPPLY_CHAIN_ESTABLISHED`) | `DEP-SC-01`, `DEP-SC-04`, `DEP-SC-05` | `P-DEP-01` | yes |
| `AIF-039` | Supply-Chain Unknown Preservation (`UNOBSERVABLE(stage) => UNKNOWN(stage)`) | `DEP-SC-05`, `DEP-SC-06`, `DEP-SC-09` | `P-03`, `P-06` | yes |
| `AIF-040` | Resolution Snapshot Binding (`manifest/lockfile subject == required snapshot`) | `DEP-SC-10` | `P-DEP-04` | yes |
| `AIF-041` | Receipt Immutability (`R1` immutable; mutation requires `R2` with `previous_receipt_id`) | `RECEIPT-10` | `P-REC-07` | yes |
| `AIF-042` | Receipt Determinism (RFC 8785 JCS + SHA-256 `receipt_id`) | `RED-036`, `RECEIPT-05` | `P-REC-07` | yes |
| `AIF-043` | Evidence Referential Integrity (`evidence_id`, `source_locator`, `content_digest`) | `RECEIPT-01`, `RECEIPT-07`, `RECEIPT-08` | `P-01` | yes |
| `AIF-044` | Receipt Validation Non-Transitivity (`VALID_RECEIPT != VERIFIED_CLAIMS`) | `RECEIPT-09`, `RECEIPT-12` | `P-REC-01` | yes |
| `AIF-045` | Normalization Non-Expansion (normalized scope $\le$ source scope) | `RED-012`, `RECEIPT-03`, `RECEIPT-11` | `P-REC-02`, `P-REC-06` | yes |
| `AIF-046` | Contradiction Preservation (`E1..E3` retained with `CONTRADICTED`) | `RED-014`, `RED-035`, `RECEIPT-04` | `P-REC-05` | yes |
| `AIF-047` | Historical Snapshot Preservation (evidence retains capture snapshot) | `RECEIPT-02`, `RECEIPT-10` | `P-REC-04` | yes |
| `AIF-048` | Completion Separation (receipt generator cannot authorize, admit, or complete) | `RECEIPT-06` | `P-REC-03` | yes |
| `AIF-049` | Test Execution Evidence (evaluation case cannot pass without observed execution) | `RED-022`, `EVAL-01`, `EVAL-06`, **`EVAL-A049`** | `P-TEST-01` | yes |
| `AIF-050` | Oracle Independence (oracle never derives expected truth from skill output) | `EVAL-07`, **`EVAL-A050`** | `P-01` | yes |
| `AIF-051` | Corpus Integrity (results bound to `case_corpus_digest` and `oracle_digest`) | `EVAL-01`, `EVAL-09`, **`EVAL-A051`** | — | yes |
| `AIF-052` | Regression Reproducibility (same snapshot + corpus + oracle + evaluator $\Rightarrow$ equivalent result) | `EVAL-09`, **`EVAL-A052`** | `P-07` | yes |
| `AIF-053` | Mutation Sensitivity (critical invariant suite detects contract-breaking mutations) | `RED-020`, `RED-028`, `RED-041`, `TEST-07`, `COMPLETE-06`, `EVAL-10`, **`EVAL-A053`** | — | yes |
| `AIF-054` | Trigger Correctness (`SHOULD TRIGGER` vs `SHOULD NOT TRIGGER` & trigger pressure) | `EVAL-12`, **`EVAL-A054`** | `P-08` | yes |
| `AIF-055` | Test Non-Vacuity (`PASS` requires `execution_occurred + observation_produced + oracle_matched`) | `EVAL-06`, **`EVAL-A055`** | `P-03` | yes |




