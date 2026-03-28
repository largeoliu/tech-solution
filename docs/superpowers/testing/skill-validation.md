# Skill Validation Runbook

## Scope

This runbook operationalizes the layered validation strategy in `docs/superpowers/specs/2026-03-26-skill-validation-design.md` for `setup-architect` and `create-technical-solution`, plus `docs/superpowers/specs/2026-03-27-review-technical-solution-design.md` for `review-technical-solution`. Use it when validating changes to skill contracts, flow control, regression-sensitive behavior, and adversarial boundary handling.

## Local command

```bash
python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v
```

## Layer map

### 静态契约层

- Focus: install targets, required files, forbidden legacy artifacts, minimum `.architecture/` layout, and fixed review output contracts.
- Representative cases: `SA-11`, `SA-12`, `RTS-09`.

### 流程场景层

- Focus: stop/redirect behavior, prerequisite enforcement, and primary success-path branching.
- Representative cases: `SA-01`, `SA-13`, `SA-15`, `SA-16`, `SA-17`, `CTS-01`, `CTS-11`, `RTS-01`, `RTS-02`.

### 行为回归层

- Focus: fixed prompts and fixtures that verify template adherence, required semantic blocks, non-overwrite behavior, and stable review-report semantics over time.
- Representative cases: `SA-03`, `CTS-04`, `CTS-09`, `RTS-04`, `RTS-05`, `RTS-06`.

### 对抗边界层

- Focus: ambiguous, partial, or risky inputs that could trigger unsafe inference, unsafe overwrite, invalid template expansion, or lowered review standards.
- Representative cases: `SA-07`, `SA-08`, `CTS-07`, `CTS-08`, `CTS-13`, `RTS-03`, `RTS-07`, `RTS-08`.

## Phase rollout

- Note: some catalog cases now use multi-turn `turns` definitions to express turn boundaries.

### Phase 1

- Goal: lock the hard rules first so the suite catches unsafe continuation, unsafe inference, silent overwrite behavior, and invalid formal review starts early.
- Cases: `SA-01`, `SA-02`, `SA-07`, `SA-08`, `SA-13`, `SA-15`, `SA-16`, `SA-17`, `CTS-01`, `CTS-02`, `CTS-04`, `CTS-07`, `CTS-08`, `RTS-01`, `RTS-02`, `RTS-03`.
- Use when: validating the first enforcement baseline for contract and boundary-sensitive behavior after changes to skill rules, references, or prompts.

### Phase 2

- Goal: expand from hard-stop protection into mainline success-path and stable regression coverage.
- Cases: `SA-03`, `SA-04`, `SA-05`, `SA-06`, `SA-14`, `CTS-03`, `CTS-05`, `CTS-06`, `CTS-09`, `RTS-04`, `RTS-05`, `RTS-06`.
- Use when: validating template adaptation, required information-block coverage, and non-destructive behavior on established paths.

### Phase 3

- Goal: add governance-heavy and pressure-path coverage once the baseline suite is stable.
- Cases: `SA-09`, `SA-10`, `SA-11`, `SA-12`, `CTS-10`, `CTS-11`, `CTS-12`, `CTS-13`, `RTS-07`, `RTS-08`, `RTS-09`.
- Use when: validating member/principle governance, standalone execution expectations, shared-context traceability, and higher-pressure adversarial scenarios.

## Recommended cadence

- Before commit: run the full local command after any change that affects the validation suite itself.
- Before merge: run the full local command for `SKILL.md`, workflow, fixture, reference, or contract-test changes.
- Before release: run the full local command and review cases spanning all four layers.
- After changing `skills/*/SKILL.md` or referenced docs: prioritize re-running scenario and regression coverage from the affected skill alongside the full suite.

## Open contract questions

- If `.architecture/members.yml`, `.architecture/principles.md`, and `.architecture/templates/technical-solution-template.md` exist but `.architecture/technical-solutions/` is missing, should `create-technical-solution` create the output directory or stop and ask for setup completion?
- How strict should slug normalization be for `.architecture/technical-solutions/<slug>.md`, and which normalization rules must be fixed to keep path assertions stable?
