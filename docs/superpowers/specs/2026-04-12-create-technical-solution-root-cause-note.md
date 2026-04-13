# Create Technical Solution Root Cause Note

## Background

This note records the root causes exposed during a real `create-technical-solution` run in the `qoder` tmux session, plus the design changes made to pull the workflow back onto a single low-ambiguity path.

The failure pattern was not a single parser bug. It was a workflow design problem: the skill still required the model to coordinate protocol details that should have been owned by scripts.

## What Failed

The observed run exposed three recurring symptoms:

1. Step 9 summary submissions were rejected even when they matched the documented checkpoint examples.
2. Creative steps required a valid `ticket`, but the main `--advance` path did not return that ticket as first-class structured output.
3. Steps 9 and 10 required a full one-shot JSON payload, but the helper path only emitted Markdown scaffolds, so the model had to hand-build large arrays.

These symptoms pushed the execution off the happy path and into repair behavior: repeated ticket retrieval, state-file inspection, and trial-and-error summary changes.

## Root Causes

### 1. Protocol truth was split across docs and validators

Step cards and `REFERENCE.md` documented step 9 summaries like `完成；写入 WD-EXP-SLOT-*；slots={N}；gate: step-10 ready`, while `validate-state.py` rejected summaries containing `WD-EXP`.

That meant a user or model following the docs could still fail validation. This is not model error. It is protocol self-contradiction.

### 2. Ticket ownership existed internally, but not on the public path

The workflow internally generated and tracked `pending_ticket`, but the creative-step `--advance` response did not include the ticket. The CLI printed a submit template with `<ticket>` placeholders, which is fine for humans but weak for agents.

This forced the executor to infer or recover protocol state from secondary outputs or the state file. Once that happens, the "single high-level entrypoint" promise is gone.

### 3. Structure generation was delegated to the model

For steps 7-10, the protocol expected structured JSON payloads. But helper output was biased toward Markdown scaffolds. For steps 9 and 10 in particular, that meant the model had to synthesize large array payloads from scratch.

That is exactly the kind of workflow structure the script should own.

## Design Principles Reinforced

These fixes align with the repository guidance in `AGENTS.md`:

- Script-driven workflows should define the path, not validators alone.
- The model should fill business values, not reconstruct protocol skeletons.
- Workflow truth should live in one place, with docs, helpers, and validators derived from the same contract.

In short: script sets the form, model fills the form.

## Changes Made

### Summary contract alignment

- Removed the hard-coded `WD-EXP` summary rejection.
- Updated step 9 and step 10 examples to use artifact-type summaries like `写入专家分析` and `写入协作收敛` rather than artifact wildcard names.
- Added regression tests to ensure documented summary examples pass validation.

### Ticket contract surfaced on the main path

- Creative `--advance` responses now return:
  - `ticket`
  - `allowed_block_pattern`
  - `submit_command`
  - `json_scaffold_command`
  - `json_scaffold_preview`

This removes the need to read `state.yaml` to continue the flow.

### JSON scaffold support for creative steps

- Added `--emit-json-scaffold` for steps 7, 8, 9, and 10.
- Added matching scaffold generators that emit valid structured arrays instead of Markdown-only draft templates.
- 后续进一步收口 public surface，只保留 `--emit-json-scaffold` 作为创作步骤的只读辅助入口。

### Draft path and runtime alignment

- Brought runtime, validators, and tests into agreement on the canonical draft location under `.architecture/.state/create-technical-solution/<slug>/draft`.
- Ensured template snapshot generation initializes the draft skeleton instead of only mutating state.
- Ensured staging writes create parent directories before attempting atomic draft replacement.

## Why `json_scaffold_preview` Exists

Returning only a command is better than returning nothing, but it still leaves a small orchestration gap. The executor must issue another command before seeing the structure.

`json_scaffold_preview` closes that last gap for common cases:

- `--advance` explains the task
- returns the ticket
- returns the exact submit command
- returns the exact scaffold command
- and includes a preview of the expected JSON shape

That gives the executor the protocol, the structure, and the next action in one response.

## Validation Evidence

The repaired workflow is covered by regression tests in:

- `evals/create-technical-solution/test_validate_state.py`
- `evals/create-technical-solution/test_run_step.py`

Verification command:

```bash
python3 -m pytest evals/create-technical-solution/test_validate_state.py evals/create-technical-solution/test_run_step.py
```

Latest result after the fixes:

- `151 passed`

## Remaining Follow-Ups

These are worthwhile, but no longer blockers for the main execution path:

1. Add doc-consistency tests that parse public examples from step cards and `REFERENCE.md` directly.
2. Consider deriving public protocol examples from one script-owned source to reduce future drift.
3. Consider shrinking `json_scaffold_preview` for very large templates if payload size becomes noisy.

## Review Follow-Ups

After the first merge, a code review identified two important issues that were addressed in a follow-up commit (`1f91867`).

### Issue 1: Step 9 JSON scaffold ignored member filtering

The `build_exp_json_scaffold` function computed `_resolved_members` but never used it, producing one flat entry per slot regardless of how many members were selected. The test `test_emit_json_scaffold_step9_respects_member_filter` had a misleading name — it asserted shape but not filtering behavior.

Fix: rewrote `build_exp_json_scaffold` to expand entries per `slot × member` pair, added a `member` field to each entry, and updated the test to assert member values appear in output. Also added a second test confirming that two selected members produce double the entries.

### Issue 2: Over-broad `WD-*` summary rejection

Replacing the removed `WD-EXP` single-pattern with `re.compile(r"WD-[A-Z]+(?:-[A-Z0-9*]+)*")` was too aggressive — it rejected all `WD-*` strings, including the legitimate short summaries `WD-CTX 完成` and `WD-TASK 完成` used by steps 7 and 8.

Fix: narrowed the pattern to only block internal wildcard artifact identifiers:

```python
re.compile(r"WD-(?:EXP|SYN)-[A-Z0-9*\-]+")
```

This allows `WD-CTX` and `WD-TASK` in summaries while still catching `WD-EXP-SLOT-*` and `WD-SYN-SLOT-*`. A regression test `test_validator_rejects_generic_wd_artifact_identifier_in_summary` was added to lock in the narrowing.

### Lesson

Both issues were caught by having tests that named the wrong thing (member filter) or by testing at the wrong granularity (blocking all `WD-*` instead of just the internal artifact wildcard forms). The review process paid for itself twice.

## Bottom Line

The run failed because the workflow still leaked protocol assembly work to the model.

The fix was not "tell the model better." The fix was to move summary rules, ticket delivery, and JSON skeleton generation back into the script layer.

That is the durable path.
