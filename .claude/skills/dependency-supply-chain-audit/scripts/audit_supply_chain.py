#!/usr/bin/env python3
"""
audit_supply_chain.py — Deterministic Phase 8 Dependency Supply-Chain Auditor for
.claude/skills/dependency-supply-chain-audit (Component C-03, AIF-0.1.0).

Enforces Sections 8.1-8.18:
  NO_KNOWN_VULNERABILITIES != SUPPLY_CHAIN_ESTABLISHED
  LOCKFILE_MISSING != VULNERABLE
  AUDIT_UNAVAILABLE != AUDIT_PASSED
  DECLARED != RESOLVED != INSTALLED != USED_IN_BUILD
  AIF-034..AIF-040
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def is_semver_range_compatible(requested_range: str, resolved_version: str) -> bool:
    """Distinguish valid semver range resolution (foo ^1.0 -> 1.9.4) from manifest/lock drift."""
    req = requested_range.strip()
    res = resolved_version.strip().lstrip("v")
    if not req or not res:
        return True
    if req == res or req == "*" or req == "latest":
        return True
    res_parts = res.split(".")
    if req.startswith("^"):
        base = req[1:].strip().split(".")
        return res_parts[0] == base[0]
    if req.startswith("~"):
        base = req[1:].strip().split(".")
        return len(base) >= 2 and res_parts[:2] == base[:2]
    return req == res


def audit_supply_chain(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate the 10-stage supply-chain lifecycle across DependencyManifestRecord,
    LockfileRecord, ResolutionRecord, SourceRecord, IntegrityRecord, InstallRecord,
    BuildRecord, ArtifactRecord, vulnerability audit status, and DependencyEvidenceCoverage.
    """
    target_snapshot = payload.get("target_snapshot", "S1")
    manifest: Optional[Dict[str, Any]] = payload.get("manifest_record")
    lockfile: Optional[Dict[str, Any]] = payload.get("lockfile_record")
    resolution: Optional[Dict[str, Any]] = payload.get("resolution_record")
    sources: List[Dict[str, Any]] = payload.get("source_records", [])
    integrities: List[Dict[str, Any]] = payload.get("integrity_records", [])
    install_rec: Optional[Dict[str, Any]] = payload.get("install_record")
    build_rec: Optional[Dict[str, Any]] = payload.get("build_record")
    artifacts: List[Dict[str, Any]] = payload.get("artifact_records", [])
    vuln_audit: Optional[Dict[str, Any]] = payload.get("vulnerability_audit")

    # Pressure / governance flags
    agent_inference: Optional[str] = payload.get("agent_inference")
    attempted_mutation_command: Optional[str] = payload.get("attempted_mutation_command")
    agent_created_lockfile_in_audit: bool = payload.get("agent_created_lockfile_in_audit", False)
    dependency_mutated_between_resolution_and_build: bool = payload.get(
        "dependency_mutated_between_resolution_and_build", False
    )

    findings: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    limitations: List[str] = []

    def add_finding(code: str, category: str, proposition: str, invariant: str = "AIF-034") -> None:
        findings.append(
            {
                "finding_id": f"find-sc-{len(findings) + 1:03d}",
                "code": code,
                "category": category,
                "invariant": invariant,
                "proposition": proposition,
                "remediation_authorized": False,
            }
        )

    # P-DEP-02: Agent runs mutating command (npm audit fix / npm install) during audit
    if attempted_mutation_command:
        add_finding(
            "UNAUTHORIZED_MUTATION",
            "SUPPLY_CHAIN_GOVERNANCE",
            f"Audit attempted mutating command '{attempted_mutation_command}' without authorization (AIF-010).",
            "AIF-010",
        )
        return {
            "target_snapshot": target_snapshot,
            "status": "UNAUTHORIZED_MUTATION",
            "findings": findings,
            "evidence": [],
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # P-DEP-03: No lockfile, agent creates one to make audit complete
    if agent_created_lockfile_in_audit:
        add_finding(
            "SCOPE_VIOLATION",
            "SUPPLY_CHAIN_GOVERNANCE",
            "Agent created a lockfile during a read-only audit instead of reporting LOCKFILE = MISSING (P-DEP-03, AIF-010).",
            "AIF-010",
        )
        return {
            "target_snapshot": target_snapshot,
            "status": "SCOPE_VIOLATION",
            "findings": findings,
            "evidence": [],
            "mutates_repository": False,
            "authority": False,
            "completion": False,
        }

    # Stage 1: Manifest
    manifest_status = "PRESENT" if manifest else "MISSING"
    manifest_snap = (manifest or {}).get("subject_snapshot", target_snapshot)

    # Stage 2: Lockfile (PRESENT | MISSING | UNREADABLE | UNSUPPORTED | MULTIPLE | UNKNOWN)
    if lockfile is not None:
        lockfile_status = lockfile.get("status", "PRESENT")
        lockfile_snap = lockfile.get("subject_snapshot", target_snapshot)
    else:
        lockfile_status = "MISSING"
        lockfile_snap = target_snapshot

    if lockfile_status == "MISSING":
        add_finding(
            "LOCKFILE_MISSING",
            "SUPPLY_CHAIN_LOCKFILE",
            "Lockfile status is MISSING (LOCKFILE_MISSING != VULNERABLE; resolution not established, AIF-034).",
            "AIF-034",
        )
        limitations.append("Lockfile is MISSING; concrete dependency resolution is NOT_ESTABLISHED")
    elif lockfile_status == "PRESENT":
        add_finding(
            "LOCKFILE_PRESENT",
            "SUPPLY_CHAIN_LOCKFILE",
            "Lockfile is PRESENT (does not prove INSTALL_EXECUTED, BUILD_EXECUTED, or ARTIFACT_BOUND, AIF-035, AIF-036).",
            "AIF-035",
        )

    # Stage 3: Resolution & Drift / Range check (DEP-SC-03 & P-DEP-05)
    resolution_status = "NOT_ESTABLISHED"
    resolution_outcome = "NOT_ESTABLISHED"
    resolution_snap = target_snapshot
    if resolution:
        resolution_status = resolution.get("status", "RESOLVED")
        resolution_snap = resolution.get("subject_snapshot", target_snapshot)
        if resolution.get("registry_configuration"):
            # DEP-SC-06: Alternate registry observed (configuration != execution)
            add_finding(
                "REGISTRY_OBSERVED",
                "SUPPLY_CHAIN_SOURCE",
                f"Registry configuration '{resolution.get('registry_configuration')}' observed (configuration != execution).",
                "AIF-039",
            )
        drifted = False
        for pkg in resolution.get("resolved_packages", []):
            req_range = pkg.get("requested_range", "")
            res_ver = pkg.get("resolved_version", "")
            if not is_semver_range_compatible(req_range, res_ver):
                drifted = True
                add_finding(
                    "MANIFEST_LOCK_DRIFT",
                    "SUPPLY_CHAIN_RESOLUTION",
                    f"Package '{pkg.get('name')}' manifest range '{req_range}' is incompatible with lock resolution '{res_ver}' (DEP-SC-03).",
                    "AIF-034",
                )
        resolution_outcome = "MANIFEST_LOCK_DRIFT" if drifted else "VALID_RESOLUTION"

    # P-DEP-04: Snapshot mismatch on manifest/lockfile/resolution/audit
    audit_snap = (vuln_audit or {}).get("subject_snapshot", target_snapshot)
    snapshot_match = (
        manifest_snap == target_snapshot
        and lockfile_snap == target_snapshot
        and resolution_snap == target_snapshot
        and audit_snap == target_snapshot
    )
    if not snapshot_match:
        add_finding(
            "SNAPSHOT_MISMATCH",
            "SUPPLY_CHAIN_SNAPSHOT",
            f"Supply-chain evidence snapshot does not match target snapshot '{target_snapshot}' (AIF-040).",
            "AIF-040",
        )

    # Stage 4: Source provenance (AIF-039: source_type = UNKNOWN remains UNKNOWN)
    source_status = "UNKNOWN"
    if sources:
        types = {s.get("source_type", "UNKNOWN") for s in sources}
        source_status = "UNKNOWN" if "UNKNOWN" in types else sorted(types)[0]

    # Stage 5: Integrity (VERIFIED | MISMATCH | NOT_AVAILABLE | NOT_CHECKED | UNKNOWN)
    integrity_status = "NOT_CHECKED"
    if integrities:
        for irec in integrities:
            exp_d = irec.get("expected_digest")
            obs_d = irec.get("observed_digest")
            res_i = irec.get("result")
            if res_i == "MISMATCH" or (exp_d and obs_d and exp_d != obs_d):
                integrity_status = "MISMATCH"
                add_finding(
                    "INTEGRITY_MISMATCH",
                    "SUPPLY_CHAIN_INTEGRITY",
                    f"Dependency '{irec.get('dependency')}' expected digest '{exp_d}' != observed digest '{obs_d}' (DEP-SC-08).",
                    "AIF-008A",
                )
            elif res_i == "VERIFIED" and integrity_status != "MISMATCH":
                integrity_status = "VERIFIED"

    # Stage 6: Installation (SUCCESS | FAILURE | PARTIAL | INTERRUPTED | UNKNOWN | NOT_EXECUTED)
    install_status = "NOT_EXECUTED"
    if install_rec:
        install_status = install_rec.get("result", "SUCCESS")
        if install_rec.get("install_script_executed"):
            # DEP-SC-07: postinstall script observed -> behavioral evidence, not automatically MALICIOUS
            add_finding(
                "INSTALL_SCRIPT_EXECUTED",
                "SUPPLY_CHAIN_INSTALLATION",
                "Lifecycle/postinstall script executed during installation (behavioral evidence, not automatically MALICIOUS).",
                "AIF-035",
            )

    # Stage 7: Build & Stage 8: Artifact provenance (DEP-SC-09 & DEP-SC-10)
    build_status = "NOT_EXECUTED"
    if build_rec:
        build_status = build_rec.get("result", "SUCCESS")
        if dependency_mutated_between_resolution_and_build or (
            build_rec.get("dependency_resolution_snapshot")
            and build_rec.get("dependency_resolution_snapshot") != build_rec.get("build_snapshot", target_snapshot)
        ):
            # DEP-SC-10: Build at S2 after dependency mutation since S1 resolution
            add_finding(
                "RESOLUTION_BUILD_SNAPSHOT_MISMATCH",
                "SUPPLY_CHAIN_BUILD",
                "Dependencies were resolved at S1, mutated, and built at S2; S1 resolution cannot certify S2 build (AIF-014, AIF-028, AIF-040).",
                "AIF-040",
            )
            snapshot_match = False

    artifact_status = "NONE"
    build_provenance = "UNKNOWN"
    if artifacts:
        for art in artifacts:
            if art.get("build_id") and build_rec and art.get("build_id") == build_rec.get("build_id") and snapshot_match:
                artifact_status = "ARTIFACT_BOUND"
                build_provenance = "PROVEN"
            else:
                # DEP-SC-09: dist/app.js exists without build evidence
                artifact_status = "ARTIFACT_OBSERVED"
                build_provenance = "UNKNOWN"
                add_finding(
                    "ARTIFACT_OBSERVED",
                    "SUPPLY_CHAIN_ARTIFACT",
                    f"Artifact '{art.get('path')}' observed without proven BuildRecord binding (BUILD_PROVENANCE = UNKNOWN, AIF-037).",
                    "AIF-037",
                )

    # Stage 9: Vulnerability Audit (DEP-SC-04, DEP-SC-05, P-DEP-01)
    vuln_status = "NOT_CHECKED"
    if vuln_audit:
        v_raw = vuln_audit.get("status", "CLEAN")
        if v_raw == "UNAVAILABLE":
            # DEP-SC-05: Tool unavailable -> AUDIT_UNAVAILABLE, never AUDIT_PASSED
            vuln_status = "AUDIT_UNAVAILABLE"
            add_finding(
                "AUDIT_UNAVAILABLE",
                "SUPPLY_CHAIN_VULNERABILITY",
                "Vulnerability audit mechanism was unavailable (AUDIT_UNAVAILABLE != AUDIT_PASSED, AIF-008, AIF-039).",
                "AIF-039",
            )
        else:
            vuln_status = v_raw

    # P-DEP-01: Agent claims "npm audit passed, therefore dependencies are safe."
    if agent_inference and "dependencies are safe" in agent_inference.lower():
        add_finding(
            "REJECTED_INFERENCE",
            "SUPPLY_CHAIN_SCOPE",
            "Rejected overclaim 'dependencies are safe' from 'npm audit passed' (NO_KNOWN_VULNERABILITIES != SUPPLY_CHAIN_ESTABLISHED, AIF-038).",
            "AIF-038",
        )

    # Overall DependencyEvidenceCoverage completeness
    if (
        manifest_status == "PRESENT"
        and lockfile_status == "PRESENT"
        and resolution_status == "RESOLVED"
        and integrity_status == "VERIFIED"
        and install_status == "SUCCESS"
        and build_status == "SUCCESS"
        and artifact_status == "ARTIFACT_BOUND"
        and snapshot_match
    ):
        completeness = "COMPLETE"
    elif lockfile_status == "MISSING" or resolution_status == "NOT_ESTABLISHED":
        completeness = "NOT_ESTABLISHED"
    else:
        completeness = "PARTIAL"

    coverage = {
        "manifest": manifest_status,
        "lockfile": lockfile_status,
        "resolution": resolution_status,
        "source": source_status,
        "integrity": integrity_status,
        "installation": install_status,
        "build": build_status,
        "artifact": artifact_status,
        "build_provenance": build_provenance,
        "vulnerability_audit": vuln_status,
        "snapshot_match": snapshot_match,
        "completeness": completeness,
        "limitations": limitations,
    }

    return {
        "target_snapshot": target_snapshot,
        "status": "SNAPSHOT_MISMATCH"
        if not snapshot_match
        else ("REJECTED_INFERENCE" if agent_inference else completeness),
        "resolution_outcome": resolution_outcome,
        "coverage": coverage,
        "forbidden_inferences": [
            "dependencies are insecure",
            "dependencies are safe",
            "SUPPLY_CHAIN_ESTABLISHED (from vulnerability scan alone)",
        ],
        "findings": findings,
        "evidence": evidence,
        "mutates_repository": False,
        "authority": False,
        "completion": False,
    }


def run_self_tests() -> int:
    """Execute the 16-case Phase 8 supply-chain test suite (DEP-SC-01..10 + P-DEP-01..05 + StreamForge check)."""
    passed = 0
    failed = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if cond:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}: {detail}", file=sys.stderr)
            failed += 1

    base_manifest = {"manifest_id": "m1", "path": "package.json", "package_manager": "npm", "subject_snapshot": "S1"}
    base_lock = {"lockfile_id": "l1", "path": "package-lock.json", "status": "PRESENT", "subject_snapshot": "S1"}

    # DEP-SC-01: manifest without lockfile
    r01 = audit_supply_chain({"manifest_record": base_manifest, "lockfile_record": None})
    check(
        "DEP-SC-01 (manifest without lockfile -> MANIFEST=PRESENT, LOCKFILE=MISSING, RESOLUTION=NOT_ESTABLISHED)",
        r01["coverage"]["manifest"] == "PRESENT"
        and r01["coverage"]["lockfile"] == "MISSING"
        and r01["coverage"]["resolution"] == "NOT_ESTABLISHED"
        and "dependencies are insecure" in r01["forbidden_inferences"]
        and "dependencies are safe" in r01["forbidden_inferences"],
        str(r01),
    )

    # DEP-SC-02: lockfile present -> LOCKFILE_PRESENT, does not prove INSTALL_EXECUTED / BUILD_EXECUTED / ARTIFACT_BOUND
    r02 = audit_supply_chain({"manifest_record": base_manifest, "lockfile_record": base_lock})
    check(
        "DEP-SC-02 (lockfile present -> LOCKFILE_PRESENT; installation=NOT_EXECUTED, build=NOT_EXECUTED)",
        any(f["code"] == "LOCKFILE_PRESENT" for f in r02["findings"])
        and r02["coverage"]["installation"] == "NOT_EXECUTED"
        and r02["coverage"]["build"] == "NOT_EXECUTED"
        and r02["coverage"]["artifact"] != "ARTIFACT_BOUND",
        str(r02),
    )

    # DEP-SC-03: manifest/lock drift
    r03 = audit_supply_chain(
        {
            "manifest_record": base_manifest,
            "lockfile_record": base_lock,
            "resolution_record": {
                "status": "RESOLVED",
                "resolved_packages": [{"name": "foo", "requested_range": "^2.0.0", "resolved_version": "1.9.4"}],
            },
        }
    )
    check(
        "DEP-SC-03 (manifest/lock incompatible version -> MANIFEST_LOCK_DRIFT finding)",
        r03["resolution_outcome"] == "MANIFEST_LOCK_DRIFT"
        and any(f["code"] == "MANIFEST_LOCK_DRIFT" for f in r03["findings"]),
        str(r03),
    )

    # DEP-SC-04: vulnerability scanner clean -> VULNERABILITY_AUDIT=CLEAN, SUPPLY_CHAIN=NOT_ESTABLISHED
    r04 = audit_supply_chain({"manifest_record": base_manifest, "vulnerability_audit": {"status": "CLEAN"}})
    check(
        "DEP-SC-04 (npm audit clean -> VULNERABILITY_AUDIT=CLEAN, completeness=NOT_ESTABLISHED)",
        r04["coverage"]["vulnerability_audit"] == "CLEAN" and r04["coverage"]["completeness"] == "NOT_ESTABLISHED",
        str(r04),
    )

    # DEP-SC-05: audit unavailable -> AUDIT_UNAVAILABLE, never AUDIT_PASSED
    r05 = audit_supply_chain({"manifest_record": base_manifest, "vulnerability_audit": {"status": "UNAVAILABLE"}})
    check(
        "DEP-SC-05 (audit unavailable -> AUDIT_UNAVAILABLE, never AUDIT_PASSED)",
        r05["coverage"]["vulnerability_audit"] == "AUDIT_UNAVAILABLE",
        str(r05),
    )

    # DEP-SC-06: alternate registry -> REGISTRY_OBSERVED (configuration != execution)
    r06 = audit_supply_chain(
        {
            "manifest_record": base_manifest,
            "lockfile_record": base_lock,
            "resolution_record": {"status": "RESOLVED", "registry_configuration": "https://npm.internal.example"},
            "source_records": [{"dependency": "foo", "source_type": "UNKNOWN"}],
        }
    )
    check(
        "DEP-SC-06 (alternate registry -> REGISTRY_OBSERVED & source_type=UNKNOWN preserved)",
        any(f["code"] == "REGISTRY_OBSERVED" for f in r06["findings"]) and r06["coverage"]["source"] == "UNKNOWN",
        str(r06),
    )

    # DEP-SC-07: install script observed -> INSTALL_SCRIPT_EXECUTED (not automatically MALICIOUS)
    r07 = audit_supply_chain(
        {
            "manifest_record": base_manifest,
            "lockfile_record": base_lock,
            "install_record": {"result": "SUCCESS", "install_script_executed": True},
        }
    )
    check(
        "DEP-SC-07 (postinstall script -> INSTALL_SCRIPT_EXECUTED finding, not MALICIOUS)",
        any(f["code"] == "INSTALL_SCRIPT_EXECUTED" for f in r07["findings"]),
        str(r07),
    )

    # DEP-SC-08: integrity mismatch -> INTEGRITY_MISMATCH
    r08 = audit_supply_chain(
        {
            "manifest_record": base_manifest,
            "lockfile_record": base_lock,
            "integrity_records": [
                {"dependency": "foo", "expected_digest": "sha512:aaa", "observed_digest": "sha512:bbb"}
            ],
        }
    )
    check(
        "DEP-SC-08 (expected digest != observed digest -> INTEGRITY_MISMATCH)",
        r08["coverage"]["integrity"] == "MISMATCH"
        and any(f["code"] == "INTEGRITY_MISMATCH" for f in r08["findings"]),
        str(r08),
    )

    # DEP-SC-09: artifact without build evidence -> ARTIFACT_OBSERVED, BUILD_PROVENANCE=UNKNOWN
    r09 = audit_supply_chain(
        {
            "manifest_record": base_manifest,
            "lockfile_record": base_lock,
            "artifact_records": [{"artifact_id": "art-1", "path": "dist/app.js"}],
        }
    )
    check(
        "DEP-SC-09 (dist/app.js without BuildRecord -> ARTIFACT_OBSERVED & BUILD_PROVENANCE=UNKNOWN)",
        r09["coverage"]["artifact"] == "ARTIFACT_OBSERVED"
        and r09["coverage"]["build_provenance"] == "UNKNOWN",
        str(r09),
    )

    # DEP-SC-10: build after dependency mutation -> S1 resolution cannot certify S2 build
    r10 = audit_supply_chain(
        {
            "target_snapshot": "S2",
            "manifest_record": dict(base_manifest, subject_snapshot="S2"),
            "lockfile_record": dict(base_lock, subject_snapshot="S2"),
            "resolution_record": {"status": "RESOLVED", "subject_snapshot": "S1"},
            "build_record": {
                "build_id": "b1",
                "result": "SUCCESS",
                "dependency_resolution_snapshot": "S1",
                "build_snapshot": "S2",
            },
            "dependency_mutated_between_resolution_and_build": True,
        }
    )
    check(
        "DEP-SC-10 (dependencies resolved at S1, mutated, built at S2 -> SNAPSHOT_MISMATCH / AIF-040)",
        r10["status"] == "SNAPSHOT_MISMATCH"
        and any(f["code"] == "RESOLUTION_BUILD_SNAPSHOT_MISMATCH" for f in r10["findings"]),
        str(r10),
    )

    # P-DEP-01: "npm audit passed, therefore dependencies are safe." -> REJECTED_INFERENCE
    p01 = audit_supply_chain(
        {
            "manifest_record": base_manifest,
            "vulnerability_audit": {"status": "CLEAN"},
            "agent_inference": "npm audit passed, therefore dependencies are safe.",
        }
    )
    check(
        "P-DEP-01 ('npm audit passed, therefore dependencies are safe' -> REJECTED_INFERENCE, VULNERABILITY_AUDIT=CLEAN)",
        p01["status"] == "REJECTED_INFERENCE" and p01["coverage"]["vulnerability_audit"] == "CLEAN",
        str(p01),
    )

    # P-DEP-02: Agent runs npm audit fix during an audit -> UNAUTHORIZED_MUTATION
    p02 = audit_supply_chain({"attempted_mutation_command": "npm audit fix"})
    check(
        "P-DEP-02 (agent runs 'npm audit fix' during audit -> UNAUTHORIZED_MUTATION)",
        p02["status"] == "UNAUTHORIZED_MUTATION",
        str(p02),
    )

    # P-DEP-03: No lockfile, agent creates one to make audit complete -> SCOPE_VIOLATION
    p03 = audit_supply_chain({"agent_created_lockfile_in_audit": True})
    check(
        "P-DEP-03 (agent creates lockfile during audit -> SCOPE_VIOLATION)",
        p03["status"] == "SCOPE_VIOLATION",
        str(p03),
    )

    # P-DEP-04: Dependency audit executed against commit A, current repo is commit B -> SNAPSHOT_MISMATCH
    p04 = audit_supply_chain(
        {
            "target_snapshot": "commit-B",
            "manifest_record": dict(base_manifest, subject_snapshot="commit-B"),
            "lockfile_record": dict(base_lock, subject_snapshot="commit-B"),
            "vulnerability_audit": {"status": "CLEAN", "subject_snapshot": "commit-A"},
        }
    )
    check(
        "P-DEP-04 (dependency audit executed against commit A, current is commit B -> SNAPSHOT_MISMATCH)",
        p04["status"] == "SNAPSHOT_MISMATCH",
        str(p04),
    )

    # P-DEP-05: Manifest says foo ^1.0, lockfile resolves foo 1.9.4 -> VALID_RESOLUTION
    p05 = audit_supply_chain(
        {
            "manifest_record": base_manifest,
            "lockfile_record": base_lock,
            "resolution_record": {
                "status": "RESOLVED",
                "resolved_packages": [{"name": "foo", "requested_range": "^1.0", "resolved_version": "1.9.4"}],
            },
        }
    )
    check(
        "P-DEP-05 (manifest 'foo ^1.0' vs lockfile 'foo 1.9.4' -> VALID_RESOLUTION, not drift)",
        p05["resolution_outcome"] == "VALID_RESOLUTION"
        and not any(f["code"] == "MANIFEST_LOCK_DRIFT" for f in p05["findings"]),
        str(p05),
    )

    # Section 8.16 StreamForge check: do not infer remaining dependency state from package.json alone
    sf = audit_supply_chain({"manifest_record": base_manifest, "lockfile_record": base_lock})
    check(
        "Section 8.16 StreamForge (package.json + package-lock.json alone -> PARTIAL/NOT_ESTABLISHED for install/build/vuln)",
        sf["coverage"]["manifest"] == "PRESENT"
        and sf["coverage"]["lockfile"] == "PRESENT"
        and sf["coverage"]["installation"] == "NOT_EXECUTED"
        and sf["coverage"]["vulnerability_audit"] == "NOT_CHECKED",
        str(sf),
    )

    print(f"\ndependency-supply-chain-audit Self-Test Summary: {passed} passed, {failed} failed")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit 10-stage dependency supply chain under AIF-0.1.0 (read-only)."
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to JSON file containing supply-chain audit input.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the 16-case Phase 8 supply-chain test suite (DEP-SC-01..10 + P-DEP-01..05 + StreamForge check).",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_tests()

    if not args.input_path:
        parser.error("Provide an input JSON path or --self-test")

    payload = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
    result = audit_supply_chain(payload)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
