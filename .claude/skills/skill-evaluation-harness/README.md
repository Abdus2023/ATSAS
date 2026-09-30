# `skill-evaluation-harness` (`C-08`)

Behavioral, adversarial, mutation, trigger, and regression evaluation harness for ATSAS and AIF-0.1.0 Agent Skills.

## Directory Layout (`11.2`)

```text
.claude/skills/skill-evaluation-harness/
├── SKILL.md
├── README.md
├── scripts/
│   ├── discover_cases.py
│   ├── run_case.py
│   ├── run_suite.py
│   ├── compare_result.py
│   └── generate_report.py
└── references/
    ├── test-model.md
    ├── oracle-model.md
    ├── case-format.md
    ├── regression.md
    └── adversarial-testing.md
```

## Quick Commands

```bash
# Discover content-addressed evaluation corpus (aif-eval-corpus-0.2)
python3 .claude/skills/skill-evaluation-harness/scripts/discover_cases.py

# Run Phase 11 & Phase 12 comprehensive self-test suite
python3 .claude/skills/skill-evaluation-harness/scripts/run_suite.py --self-test

# Generate raw human-readable evaluation report
python3 .claude/skills/skill-evaluation-harness/scripts/generate_report.py
```
