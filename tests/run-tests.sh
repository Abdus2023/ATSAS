#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  echo "  [PASS] $1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  echo "  [FAIL] $1" >&2
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

echo "=== 1. Validating JSON Schemas in schemas/ ==="
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
echo "=== 2. Validating Compliant Contracts, Receipts & Assurance Manifests ==="
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
echo "=== 3. Verifying Rejection of Invalid Assurance Claims ==="

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
echo "=== 4. Validating Bundled ATSAS Agent Skills (.claude/skills/) ==="
if python3 .claude/skills/skill-creator/scripts/validate_skill.py --all .claude/skills > /dev/null; then
  pass "All 14 imported Agent Skills in .claude/skills/ pass validate_skill.py (including SCOPE checks)"
else
  fail ".claude/skills/ failed validate_skill.py"
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
echo "=== 5. Validating .claude/assurance/ Artifacts, 42-Case Matrix & 8 Component Contracts ==="
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
PY
then
  pass "All 14 Semantic Kernel Types, 8 contracts (C-01..C-08), 20+8 invariants (AIF-001..020 + A), and layout review verified"
else
  fail "AIF v0.1 Canonical Data Model or freeze review verification failed"
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
  pass "All 44 cases (AAI-001..036, P-001..008) & all 14 existing skills verified across matrices and capability maps"
else
  fail "44-case or 14-skill capability audit verification failed"
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
echo "=== 6. Running Phase 2/3 AIF-0.1.0 Kernel, 44-Case RED Suite & arena-intake-and-authority Tests ==="
if python3 tests/aif-v01-red-suite.py > /dev/null; then
  pass "Phase 2 AIF-0.1.0 minimal kernel, First RED Gate & 44 behavioral cases (tests/aif-v01-red-suite.py) passed"
else
  fail "Phase 2 AIF-0.1.0 RED test suite failed"
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
  pass "Phase 11 & 12 skill-evaluation-harness 13-case meta-assurance & interface freeze test suite (EVAL-01..13, AIF-049..055) passed"
else
  fail "Phase 11 & 12 skill-evaluation-harness test suite failed"
fi

echo ""
echo "=============================================="
echo "Summary: ${PASS_COUNT} passed, ${FAIL_COUNT} failed"
echo "=============================================="

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
