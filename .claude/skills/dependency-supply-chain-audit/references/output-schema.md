# `dependency-supply-chain-audit` Output Schema (`output-schema.md`)

```json
{
  "target_snapshot": "S1",
  "manifest_record": {
    "manifest_id": "man-001",
    "path": "package.json",
    "package_manager": "npm",
    "status": "PRESENT",
    "subject_snapshot": "S1"
  },
  "lockfile_record": {
    "lockfile_id": "lock-001",
    "path": "package-lock.json",
    "package_manager": "npm",
    "format_version": 3,
    "subject_snapshot": "S1",
    "status": "PRESENT"
  },
  "coverage": {
    "manifest": "PRESENT",
    "lockfile": "PRESENT",
    "resolution": "RESOLVED",
    "source": "REGISTRY",
    "integrity": "VERIFIED",
    "installation": "NOT_EXECUTED",
    "build": "NOT_EXECUTED",
    "artifact": "UNKNOWN",
    "vulnerability_audit": "CLEAN",
    "snapshot_match": true,
    "completeness": "PARTIAL",
    "limitations": [
      "Installation and build stages were not executed"
    ]
  },
  "findings": [],
  "evidence": [],
  "verifications": [],
  "mutates_repository": false,
  "authority": false,
  "completion": false
}
```
