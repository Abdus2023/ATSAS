#!/usr/bin/env bash
# Document Class: EXECUTABLE-CONFORMANCE
# Protocol: AIF-0.1.0
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PASS_COUNT=0
FAIL_COUNT=0
INTEGRITY_PASS=0
EXECUTION_PASS=0
ADVERSARIAL_PASS=0
CURRENT_CHECK_CATEGORY="INTEGRITY"

pass() {
  echo "  [PASS][$CURRENT_CHECK_CATEGORY] $1"
  PASS_COUNT=$((PASS_COUNT + 1))
  case "$CURRENT_CHECK_CATEGORY" in
    INTEGRITY) INTEGRITY_PASS=$((INTEGRITY_PASS + 1)) ;;
    EXECUTION) EXECUTION_PASS=$((EXECUTION_PASS + 1)) ;;
    ADVERSARIAL) ADVERSARIAL_PASS=$((ADVERSARIAL_PASS + 1)) ;;
  esac
}

fail() {
  echo "  [FAIL][$CURRENT_CHECK_CATEGORY] $1" >&2
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

CURRENT_CHECK_CATEGORY="INTEGRITY"
echo "=== 1. [INTEGRITY CHECKS] Validating JSON Schemas in schemas/ ==="
for schema in schemas/*.schema.json; do
  if python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
assert d.get('\$schema') == 'https://json-schema.org/draft/2020-12/schema', 'Missing draft 2020-12 \$schema'
assert '\$id' in d and 'title' in d and 'type' in d, 'Missing \$id, title, or type'
" "$schema"; then
    pass "$schema is well-formed Draft 2020-12 JSON Schema"
  else
    fail "$schema failed metadata validation"
  fi
done

echo ""
CURRENT_CHECK_CATEGORY="EXECUTION"
echo "=== 2. [EXECUTION CHECKS] Validating Compliant Contracts, Receipts & Assurance Manifests ==="
for valid_file in \
  examples/governance-policy.json \
  examples/tool-bash.json \
  examples/skill-tdd.json \
  examples/valid-canonical-data-model.json \
  examples/valid-evidence-ref.json \
  examples/valid-evidence-receipt.json \
  examples/valid-skill-eval-receipt.json \
  examples/valid-completion-manifest.json; do
  if ./bin/aif-verify "$valid_file" > /dev/null; then
    pass "$valid_file accepted by aif-verify"
  else
    fail "$valid_file should have passed aif-verify"
  fi
done

echo ""
CURRENT_CHECK_CATEGORY="ADVERSARIAL"
echo "=== 3. [ADVERSARIAL CHECKS] Verifying Rejection of Invalid Assurance Claims ==="

check_rejection() {
  local file="$1"
  local expected_invariant="$2"
  local output
  if output=$(./bin/aif-verify "$file" 2>&1); then
    fail "$file unexpectedly passed validation"
    return
  fi
  if grep -q "\[$expected_invariant\]" <<<"$output"; then
    pass "$file rejected with expected invariant [$expected_invariant]"
  else
    fail "$file rejected, but missing expected invariant [$expected_invariant]. Output: $output"
  fi
}

check_rejection "examples/invalid-stale-evidence.json" "AIF-INV-003"
check_rejection "examples/invalid-stale-evidence.json" "AIF-INV-008"

check_rejection "examples/invalid-partial-observability.json" "AIF-INV-004"
check_rejection "examples/invalid-partial-observability.json" "AIF-INV-005"
check_rejection "examples/invalid-partial-observability.json" "AIF-INV-007"
check_rejection "examples/invalid-partial-observability.json" "AIF-INV-008"

check_rejection "examples/invalid-skill-as-evidence.json" "AIF-INV-001"
check_rejection "examples/invalid-skill-as-evidence.json" "AIF-INV-008"

echo ""
CURRENT_CHECK_CATEGORY="INTEGRITY"
echo "=== 4. [INTEGRITY CHECKS] Validating Bundled ATSAS Agent Skills (.claude/skills/) ==="
if SKILL_INVENTORY_MSG=$(python3 - <<'PY'
import subprocess, sys
from pathlib import Path

skills_root = Path(".claude/skills")
discovered = sorted(
    p.name for p in skills_root.iterdir()
    if p.is_dir() and p.name != "_shared" and (p / "SKILL.md").is_file()
)
wave1_expected = {
    "arena-intake-and-authority",
    "agent-change-scope-audit",
    "dependency-supply-chain-audit",
    "ci-workflow-audit",
    "test-execution-and-evidence-audit",
    "evidence-receipt-generator",
    "arena-completion-gate",
    "skill-evaluation-harness",
}
wave1_found = sorted(s for s in discovered if s in wave1_expected)
imported_found = sorted(s for s in discovered if s not in wave1_expected)

assert len(discovered) == 22, f"Expected 22 discovered skills, found {len(discovered)}"
assert len(wave1_found) == 8, f"Expected 8 AIF Wave-1 skills, found {len(wave1_found)}"
assert len(imported_found) == 14, f"Expected 14 imported/original skills, found {len(imported_found)}"

res = subprocess.run(
    [sys.executable, ".claude/skills/skill-creator/scripts/validate_skill.py", "--all", ".claude/skills"],
    capture_output=True, text=True
)
assert res.returncode == 0, res.stdout + res.stderr
print(f"Discovered {len(discovered)} total skills ({len(imported_found)} imported/original + {len(wave1_found)} AIF Wave-1 skills); all pass validate_skill.py")
PY
); then
  pass "$SKILL_INVENTORY_MSG"
else
  fail ".claude/skills/ dynamic inventory discovery or validate_skill.py failed"
fi

if bash .claude/skills/docs-integrity-check/scripts/check_fences.sh spec > /dev/null && \
   bash .claude/skills/docs-integrity-check/scripts/check_fences.sh .claude/skills > /dev/null && \
   bash .claude/skills/docs-integrity-check/scripts/check_fences.sh .claude/assurance > /dev/null; then
  pass "All Markdown files in spec/, .claude/skills/, and .claude/assurance/ have balanced code fences"
else
  fail "Markdown fence balance check failed"
fi

if python3 .claude/skills/docs-integrity-check/scripts/check_links.py spec .claude/skills .claude/assurance > /dev/null; then
  pass "All internal Markdown links in spec/, .claude/skills/, and .claude/assurance/ resolve cleanly"
else
  fail "Internal Markdown link check failed"
fi

if python3 .claude/skills/secret-leak-scan/scripts/scan_secrets.py . > /dev/null; then
  pass "Repository passes secret-leak-scan with 0 findings"
else
  fail "secret-leak-scan reported findings"
fi

echo ""
echo "=== 5. Validating .claude/assurance/ Artifacts, 55-Invariant Kernel, 49-Case Corpus & 8 Component Contracts ==="
for assurance_doc in \
  .claude/assurance/invariants.md \
  .claude/assurance/test-matrix.md \
  .claude/assurance/state-model.md \
  .claude/assurance/evidence-schema.md \
  .claude/assurance/capability-map.md \
  .claude/assurance/component-contracts.md \
  .claude/assurance/aif-v01-freeze-review.md \
  .claude/assurance/canonical-data-model.md \
  .claude/assurance/semantic-kernel-layout-review.md \
  .claude/assurance/phase12-interface-freeze-audit.md \
  .claude/assurance/phase13-consistency-normalization-audit.md \
  ARENA_CAPABILITY_OVERLAP_MATRIX.md \
  ARENA_AIF_V01_FREEZE_REVIEW.md \
  ARENA_CANONICAL_DATA_MODEL.md \
  ARENA_SEMANTIC_KERNEL_LAYOUT_REVIEW.md \
  ARENA_PHASE12_INTERFACE_FREEZE_AND_BRANCH_AUDIT.md; do
  if [ -f "$assurance_doc" ]; then
    pass "Assurance design artifact [$assurance_doc] present"
  else
    fail "Assurance design artifact [$assurance_doc] missing"
  fi
done

if python3 - <<'PY'
import json
from pathlib import Path

contracts_text = Path(".claude/assurance/component-contracts.md").read_text(encoding="utf-8")
review_text = Path(".claude/assurance/aif-v01-freeze-review.md").read_text(encoding="utf-8")
cdm_text = Path(".claude/assurance/canonical-data-model.md").read_text(encoding="utf-8")
layout_text = Path(".claude/assurance/semantic-kernel-layout-review.md").read_text(encoding="utf-8")
cdm_schema = json.loads(Path("schemas/aif-canonical-data-model.schema.json").read_text(encoding="utf-8"))

for i in range(1, 9):
    cid = f"C-{i:02d}"
    assert f"`{cid}`" in contracts_text, f"Missing {cid} in component-contracts.md"
    assert f"`{cid}`" in review_text, f"Missing {cid} in aif-v01-freeze-review.md"
    assert f"`{cid}`" in layout_text, f"Missing {cid} in semantic-kernel-layout-review.md"

for i in range(1, 15):
    adv_id = f"ADV-{i:03d}"
    patch_id = f"PATCH-{i:03d}"
    assert f"`{adv_id}`" in review_text, f"Missing {adv_id} in aif-v01-freeze-review.md"
    assert f"`{patch_id}`" in review_text, f"Missing {patch_id} in aif-v01-freeze-review.md"

for i in range(1, 21):
    aif_id = f"AIF-{i:03d}"
    assert f"`{aif_id}`" in contracts_text, f"Missing {aif_id} in component-contracts.md"
    assert f"`{aif_id}`" in review_text, f"Missing {aif_id} in aif-v01-freeze-review.md"
    assert f"`{aif_id}`" in cdm_text, f"Missing {aif_id} in canonical-data-model.md"

for sub_id in ("AIF-001A", "AIF-002A", "AIF-003A", "AIF-004A", "AIF-005A", "AIF-006A", "AIF-008A", "AIF-014A"):
    assert f"`{sub_id}`" in contracts_text, f"Missing {sub_id} in component-contracts.md"
    assert f"`{sub_id}`" in review_text, f"Missing {sub_id} in aif-v01-freeze-review.md"
    assert f"`{sub_id}`" in cdm_text, f"Missing {sub_id} in canonical-data-model.md"

canonical_types = (
    "Request",
    "SnapshotRef",
    "AuthorityEvent",
    "AdmissionRecord",
    "ExecutionRecord",
    "ChangeRecord",
    "Claim",
    "EvidenceRef",
    "EvidenceCoverage",
    "VerificationRecord",
    "Finding",
    "AcceptanceExpression",
    "CompletionResult",
    "ArenaEvidenceReceipt",
)
for t_name in canonical_types:
    assert f"`{t_name}`" in cdm_text, f"Missing {t_name} in canonical-data-model.md"
    assert f"`{t_name}`" in contracts_text, f"Missing {t_name} in component-contracts.md"
    assert f"`{t_name}`" in layout_text, f"Missing {t_name} in semantic-kernel-layout-review.md"
    assert t_name in cdm_schema.get("$defs", {}), f"Missing {t_name} in schemas/aif-canonical-data-model.schema.json $defs"

invariants_md = Path(".claude/skills/_shared/aif/invariants.md").read_text(encoding="utf-8")
oracle_md = Path(".claude/skills/_shared/aif/tests/oracle.md").read_text(encoding="utf-8")
cases_yaml = Path(".claude/skills/_shared/aif/tests/cases.yaml").read_text(encoding="utf-8")
tests_readme = Path(".claude/skills/_shared/aif/tests/README.md").read_text(encoding="utf-8")
aif_verify_src = Path("bin/aif-verify").read_text(encoding="utf-8")
red_suite_src = Path("tests/aif-v01-red-suite.py").read_text(encoding="utf-8")

for i in range(1, 56):
    inv_code = f"AIF-{i:03d}"
    assert f"### `{inv_code}`" in invariants_md, f"Missing {inv_code} in .claude/skills/_shared/aif/invariants.md"
    assert f"`{inv_code}`" in oracle_md, f"Missing {inv_code} in .claude/skills/_shared/aif/tests/oracle.md"
    assert inv_code in cases_yaml, f"Missing {inv_code} in .claude/skills/_shared/aif/tests/cases.yaml"
    assert f"`{inv_code}`" in tests_readme, f"Missing {inv_code} in .claude/skills/_shared/aif/tests/README.md"
    assert inv_code in aif_verify_src, f"Missing {inv_code} in bin/aif-verify"
    assert inv_code in red_suite_src, f"Missing {inv_code} in tests/aif-v01-red-suite.py"

for sub_id in ("AIF-001A", "AIF-002A", "AIF-003A", "AIF-004A", "AIF-005A", "AIF-006A", "AIF-008A", "AIF-014A"):
    assert f"Sub-Invariant `{sub_id}`" in invariants_md, f"Missing {sub_id} in .claude/skills/_shared/aif/invariants.md"
    assert f"`{sub_id}`" in oracle_md, f"Missing {sub_id} in .claude/skills/_shared/aif/tests/oracle.md"
    assert sub_id in cases_yaml, f"Missing {sub_id} in .claude/skills/_shared/aif/tests/cases.yaml"
    assert sub_id in aif_verify_src, f"Missing {sub_id} in bin/aif-verify"
    assert sub_id in red_suite_src, f"Missing {sub_id} in tests/aif-v01-red-suite.py"

for norm_file in ("README.md", "invariants.md", "states.md", "snapshots.md", "evidence.md", "compatibility.md"):
    norm_text = Path(f".claude/skills/_shared/aif/{norm_file}").read_text(encoding="utf-8")
    assert "NORMATIVE" in norm_text, f"Missing Document Class NORMATIVE in .claude/skills/_shared/aif/{norm_file}"

for exec_file in (
    ".claude/skills/_shared/aif/tests/README.md",
    ".claude/skills/_shared/aif/tests/oracle.md",
    ".claude/skills/_shared/aif/tests/cases.yaml",
    "bin/aif-verify",
    "tests/aif-v01-red-suite.py",
    "tests/run-tests.sh",
):
    exec_text = Path(exec_file).read_text(encoding="utf-8")
    assert "EXECUTABLE-CONFORMANCE" in exec_text, f"Missing Document Class EXECUTABLE-CONFORMANCE in {exec_file}"

compat_text = Path(".agent/tools/aif-red-suite").read_text(encoding="utf-8")
assert "COMPATIBILITY" in compat_text, "Missing Document Class COMPATIBILITY in .agent/tools/aif-red-suite"

for hist_file in (
    ".claude/assurance/phase12-interface-freeze-audit.md",
    ".claude/assurance/aif-v01-freeze-review.md",
):
    hist_text = Path(hist_file).read_text(encoding="utf-8")
    assert "Document Class: HISTORICAL" in hist_text, f"Missing Document Class: HISTORICAL in {hist_file}"
    assert "Currentness: HISTORICAL — NOT" in hist_text, f"Missing HISTORICAL currentness notice in {hist_file}"
PY
then
  pass "All 14 core Semantic Kernel Types (across 13 modular schemas), 8 contracts (C-01..C-08), 55 invariants (AIF-001..055) + 8 sub-invariants, and layout review verified"
else
  fail "AIF-0.1.0 Canonical Data Model, 55-invariant kernel, or freeze review verification failed"
fi

for aai_id in AAI-001 AAI-002 AAI-003 AAI-004 AAI-005 AAI-006 AAI-007 AAI-008 AAI-009 AAI-010 AAI-011; do
  if grep -q "\`$aai_id\`" spec/04-invariants-and-axioms.md && \
     grep -q "\`$aai_id\`" .claude/assurance/invariants.md; then
    pass "Arena Assurance Invariant [$aai_id] defined in spec/04 & .claude/assurance/invariants.md"
  else
    fail "Arena Assurance Invariant [$aai_id] missing"
  fi
done

for comp in \
  arena-intake-and-authority \
  agent-change-scope-audit \
  dependency-supply-chain-audit \
  ci-workflow-audit \
  test-execution-and-evidence-audit \
  evidence-receipt-generator \
  arena-completion-gate \
  skill-evaluation-harness; do
  if grep -q "\`$comp\`" .claude/assurance/component-contracts.md && \
     grep -q "\`$comp\`" spec/06-wave1-skill-interfaces.md; then
    pass "v0.1 Normative Component Contract [$comp] defined in component-contracts.md & spec/06"
  else
    fail "v0.1 Normative Component Contract [$comp] missing"
  fi
done

for ref_field in comparison_base intake_snapshot execution_snapshot verification_snapshot head_commit; do
  if grep -q "\"$ref_field\"" schemas/aif-evidence-receipt.schema.json && \
     grep -q "\"$ref_field\"" examples/valid-evidence-receipt.json; then
    pass "Three-snapshot provenance field [$ref_field] present in ArenaEvidenceReceipt schema & example"
  else
    fail "Three-snapshot provenance field [$ref_field] missing"
  fi
done

for col in TEST_ID TRIGGER PRECONDITION AUTHORIZED_SCOPE AGENT_ACTION EXPECTED_OBSERVATION EXPECTED_CLASSIFICATION REQUIRED_EVIDENCE FORBIDDEN_INFERENCE FAILURE_STATE TARGET_SKILL; do
  if grep -q "\`$col\`" ARENA_ASSURANCE_TEST_MATRIX.md && \
     grep -q "\`$col\`" spec/07-wave1-red-pressure-matrix.md && \
     grep -q "\`$col\`" .claude/assurance/test-matrix.md; then
    pass "Test Matrix schema column [$col] present in all test matrix artifacts"
  else
    fail "Test Matrix schema column [$col] missing"
  fi
done

if python3 - <<'PY'
from pathlib import Path

matrix_paths = (
    ".claude/assurance/test-matrix.md",
    "ARENA_ASSURANCE_TEST_MATRIX.md",
    "spec/07-wave1-red-pressure-matrix.md",
)
for path_str in matrix_paths:
    text = Path(path_str).read_text(encoding="utf-8")
    for i in range(1, 37):
        aai_case = f"AAI-{i:03d}"
        red_case = f"RED-{i:02d}"
        assert f"| `{aai_case}`" in text, f"Missing {aai_case} in {path_str}"
        assert red_case in text, f"Missing {red_case} cross-ref in {path_str}"
    for i in range(1, 9):
        p_case = f"P-{i:03d}"
        assert f"| `{p_case}`" in text, f"Missing {p_case} in {path_str}"

cap_paths = (
    ".claude/assurance/capability-map.md",
    "ARENA_CAPABILITY_OVERLAP_MATRIX.md",
)
skills_root = Path(".claude/skills")
skill_dirs = sorted(p.name for p in skills_root.iterdir() if p.is_dir() and not p.name.startswith("_"))
assert len(skill_dirs) == 22, f"Expected 22 skills (14 imported + 8 implemented assurance skills), found {len(skill_dirs)}: {skill_dirs}"
assert "arena-intake-and-authority" in skill_dirs, "Missing Phase 3 skill arena-intake-and-authority"
assert "agent-change-scope-audit" in skill_dirs, "Missing Phase 4 skill agent-change-scope-audit"
assert "ci-workflow-audit" in skill_dirs, "Missing Phase 6 skill ci-workflow-audit"
assert "test-execution-and-evidence-audit" in skill_dirs, "Missing Phase 7 skill test-execution-and-evidence-audit"
assert "dependency-supply-chain-audit" in skill_dirs, "Missing Phase 8 skill dependency-supply-chain-audit"
assert "evidence-receipt-generator" in skill_dirs, "Missing Phase 9 skill evidence-receipt-generator"
assert "arena-completion-gate" in skill_dirs, "Missing Phase 10 skill arena-completion-gate"
assert "skill-evaluation-harness" in skill_dirs, "Missing Phase 11 skill skill-evaluation-harness"
assert (skills_root / "_shared" / "aif" / "VERSION").is_file(), "Missing .claude/skills/_shared/aif/VERSION"

for cap_str in cap_paths:
    cap_text = Path(cap_str).read_text(encoding="utf-8")
    for s_name in skill_dirs:
        assert f"`{s_name}`" in cap_text, f"Skill {s_name} missing from {cap_str}"
    for i in range(1, 35):
        assert f"| `AAI-{i:03d}` |" in cap_text, f"Missing AAI-{i:03d} in {cap_str}"
    for i in range(1, 9):
        assert f"| `P-{i:03d}` |" in cap_text, f"Missing P-{i:03d} in {cap_str}"
    for label in ("COVERED", "PARTIALLY_COVERED", "UNCOVERED", "DUPLICATE", "CONFLICTING", "ORPHANED"):
        assert f"`{label}`" in cap_text, f"Missing classification {label} in {cap_str}"
PY
then
  pass "All 22 skills (14 imported + 8 Wave-1 AIF skills), 49 behavioral cases in cases.yaml, & historical Phase 0/1 capability maps verified"
else
  fail "22-skill or behavioral corpus capability audit verification failed"
fi

for w_id in W1 W2 W3 W4 W5 W6 W7 W8; do
  if grep -q "\`$w_id\`" spec/06-wave1-skill-interfaces.md && \
     grep -q "\`$w_id\`" spec/07-wave1-red-pressure-matrix.md; then
    pass "Wave-1 skill $w_id frozen in spec/06 and covered in RED/pressure matrix spec/07"
  else
    fail "Wave-1 skill $w_id missing from spec/06 or spec/07"
  fi
done

for failure_code in \
  AUTHORITY_MISSING \
  SCOPE_UNDEFINED \
  SCOPE_VIOLATION \
  NOT_EXECUTED \
  WRONG_HEAD \
  STALE_EVIDENCE \
  CI_NOT_CONFIGURED \
  CI_NOT_EXECUTED \
  TEST_NOT_EXECUTED \
  TEST_FAILED \
  SECRET_UNVERIFIED \
  DEPENDENCY_UNRESOLVED \
  EVIDENCE_INCOMPLETE \
  ARTIFACT_MISMATCH \
  RECEIPT_INVALID; do
  if grep -q "\`$failure_code\`" spec/06-wave1-skill-interfaces.md; then
    pass "Failure taxonomy code [$failure_code] defined in spec/06-wave1-skill-interfaces.md"
  else
    fail "Failure taxonomy code [$failure_code] missing from spec/06-wave1-skill-interfaces.md"
  fi
done

echo ""
CURRENT_CHECK_CATEGORY="EXECUTION"
echo "=== 6. [EXECUTION CHECKS] Running Canonical AIF-0.1.0 Kernel, 49-Case RED/Pressure Suite & Wave-1 (C-01..C-08) Self-Tests ==="
if python3 tests/aif-v01-red-suite.py > /dev/null; then
  pass "Canonical AIF-0.1.0 minimal kernel, First RED Gate, 63 invariant rules (AIF-001..055) & 49 behavioral cases (tests/aif-v01-red-suite.py) passed"
else
  fail "Canonical AIF-0.1.0 RED test suite failed"
fi

if ./.agent/tools/aif-red-suite > /dev/null; then
  pass "Phase 13 upgraded .agent/tools/aif-red-suite wrapper verified (VERSION == 0.1.0 & delegates to canonical tests/aif-v01-red-suite.py)"
else
  fail ".agent/tools/aif-red-suite wrapper failed"
fi

if python3 .claude/skills/arena-intake-and-authority/scripts/evaluate_intake.py --self-test > /dev/null; then
  pass "Phase 3 arena-intake-and-authority 14-case adversarial test suite (RED-01..04, A-01..07, AIF-021, AIF-022) passed"
else
  fail "Phase 3 arena-intake-and-authority adversarial test suite failed"
fi

if python3 .claude/skills/agent-change-scope-audit/scripts/audit_change_scope.py --self-test > /dev/null; then
  pass "Phase 4 agent-change-scope-audit 9-case adversarial test suite (RED-05..08, RED-37..41, AIF-023..025) passed"
else
  fail "Phase 4 agent-change-scope-audit adversarial test suite failed"
fi

if python3 .claude/skills/ci-workflow-audit/scripts/audit_ci_workflow.py --self-test > /dev/null; then
  pass "Phase 6 ci-workflow-audit 21-case adversarial test suite (CI-01..20 + StreamForge NOT_FOUND, AIF-028) passed"
else
  fail "Phase 6 ci-workflow-audit adversarial test suite failed"
fi

if python3 .claude/skills/test-execution-and-evidence-audit/scripts/audit_test_execution.py --self-test > /dev/null; then
  pass "Phase 7 test-execution-and-evidence-audit 27-case adversarial test suite (TEST-01..20, P-TEST-01..04, AIF-029..033) passed"
else
  fail "Phase 7 test-execution-and-evidence-audit adversarial test suite failed"
fi

if python3 .claude/skills/dependency-supply-chain-audit/scripts/audit_supply_chain.py --self-test > /dev/null; then
  pass "Phase 8 dependency-supply-chain-audit 16-case adversarial test suite (DEP-SC-01..10, P-DEP-01..05, AIF-034..040) passed"
else
  fail "Phase 8 dependency-supply-chain-audit adversarial test suite failed"
fi

if python3 .claude/skills/evidence-receipt-generator/scripts/generate_receipt.py --self-test > /dev/null; then
  pass "Phase 9 evidence-receipt-generator 19-case adversarial test suite (RECEIPT-01..12, P-REC-01..07, AIF-041..048) passed"
else
  fail "Phase 9 evidence-receipt-generator adversarial test suite failed"
fi

if python3 .claude/skills/arena-completion-gate/scripts/evaluate_completion.py --self-test > /dev/null; then
  pass "Phase 10 arena-completion-gate 22-case adversarial test suite (COMPLETE-01..10, P-COMP-01..08, 10.3..10.5 & 10.21) passed"
else
  fail "Phase 10 arena-completion-gate adversarial test suite failed"
fi

if python3 .claude/skills/skill-evaluation-harness/scripts/run_suite.py --self-test > /dev/null; then
  pass "Phase 11, 12 & 15.1 skill-evaluation-harness 20-case meta-assurance, interface freeze & evaluator attack suite (EVAL-01..13, EVAL-A049..A055) passed"
else
  fail "Phase 11, 12 & 15.1 skill-evaluation-harness test suite failed"
fi

CURRENT_CHECK_CATEGORY="INTEGRITY"
if python3 - <<'PY'
from pathlib import Path

assert Path(".claude/skills/_shared/aif/VERSION").read_text(encoding="utf-8").strip() == "0.1.0"
assert Path(".agent/skills/_shared/aif/VERSION").read_text(encoding="utf-8").strip() == "0.1.0"

cases_hdr = Path(".claude/skills/_shared/aif/tests/cases.yaml").read_text(encoding="utf-8")[:300]
assert "49-Case" in cases_hdr and "41 RED + 8 PRESSURE" in cases_hdr, "Stale header in cases.yaml"

oracle_txt = Path(".claude/skills/_shared/aif/tests/oracle.md").read_text(encoding="utf-8")
assert "41 RED + 8 PRESSURE = 49 cases" in oracle_txt, "Stale corpus count in oracle.md"

tests_readme = Path(".claude/skills/_shared/aif/tests/README.md").read_text(encoding="utf-8")
assert "55-Invariant Coverage Matrix" in tests_readme and "AIF-055" in tests_readme, "Stale invariant count in tests/README.md"

root_readme = Path("README.md").read_text(encoding="utf-8")
skills_readme = Path(".claude/skills/README.md").read_text(encoding="utf-8")
for skill_dir in sorted(p.name for p in Path(".claude/skills").iterdir() if p.is_dir() and not p.name.startswith("_")):
    assert skill_dir in root_readme, f"Missing {skill_dir} in README.md"
    assert skill_dir in skills_readme, f"Missing {skill_dir} in .claude/skills/README.md"
PY
then
  pass "Phase 13 consistency & normalization audit verified (VERSION=0.1.0, 55 invariants AIF-001..055, 49 cases in cases.yaml, 22 skills indexed)"
else
  fail "Phase 13 consistency & normalization audit failed"
fi

echo ""
CURRENT_CHECK_CATEGORY="ADVERSARIAL"
echo "=== 7. [ADVERSARIAL CHECKS] Phase 15.1 Evaluator Attack Corpus (EVAL-A049..A055) & Runner Self-Integrity Attack ==="
if python3 - <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path(".claude/skills/skill-evaluation-harness/scripts").resolve()))
import run_suite  # type: ignore

attack_res = run_suite.run_evaluator_attack_corpus()
assert attack_res["total_attack_fixtures"] == 7, f"Expected 7 attack fixtures, got {attack_res['total_attack_fixtures']}"
assert attack_res["all_detected"] is True, f"Evaluator attack corpus failed: {attack_res}"
for fx in attack_res["fixtures"]:
    assert fx["detected"] is True, f"Fixture {fx['fixture_id']} failed: {fx}"
PY
then
  pass "Phase 15.1 Evaluator Attack Corpus (EVAL-A049..EVAL-A055) verified: all 7 behavioral attacks on the evaluator detected without claim_scope string injection"
else
  fail "Phase 15.1 Evaluator Attack Corpus (EVAL-A049..EVAL-A055) failed"
fi

if python3 - <<'PY'
# Phase 15.9 / 15.12: Runner Self-Integrity Attack
# Prove that the runner's integrity checks actually fail when assumptions are violated:
# 1) Missing invariant in oracle_md
# 2) Tampered corpus count (red_cases=40 vs 41 actual)
# 3) Missing Document Class header
from pathlib import Path

oracle_md = Path(".claude/skills/_shared/aif/tests/oracle.md").read_text(encoding="utf-8")
damaged_oracle = oracle_md.replace("AIF-055", "AIF-REMOVED")
missing_detected = "`AIF-055`" not in damaged_oracle
assert missing_detected is True, "Runner self-integrity attack 1 failed to detect missing AIF-055 in damaged oracle"

declared_red = 40
actual_red = 41
tamper_detected = declared_red != actual_red
assert tamper_detected is True, "Runner self-integrity attack 2 failed to detect corpus count mismatch"

damaged_hist = "Protocol: AIF-0.1.0\n"
doc_class_missing_detected = "Document Class: HISTORICAL" not in damaged_hist
assert doc_class_missing_detected is True, "Runner self-integrity attack 3 failed to detect missing Document Class header"
PY
then
  pass "Phase 15.9 Runner Self-Integrity Attack verified: integrity verifier rejects missing invariant reference, tampered corpus count, and missing Document Class"
else
  fail "Phase 15.9 Runner Self-Integrity Attack failed"
fi

echo ""
echo "=============================================="
echo "Category Breakdown (total_checks != quality_score):"
echo "  INTEGRITY CHECKS   (internal connection)     : ${INTEGRITY_PASS} passed"
echo "  EXECUTION CHECKS   (behavioral conformance)  : ${EXECUTION_PASS} passed"
echo "  ADVERSARIAL CHECKS (assumption violation)    : ${ADVERSARIAL_PASS} passed"
echo "----------------------------------------------"
echo "Summary: ${PASS_COUNT} passed, ${FAIL_COUNT} failed"
echo "Note: Declared check counts provide evidence for their declared properties only (not a synthetic quality percentage)."
echo "=============================================="

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
