# create-technical-solution Architecture Closeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the `create-technical-solution` runtime so it has one canonical state contract, one WD submission pipeline, one public recovery surface, and one public execution path.

**Architecture:** This is a boundary-tightening change, not a workflow rewrite. First centralize all runtime defaults and path resolution into a single script-side contract, then replace step 7-10 raw Markdown submission with structured payloads rendered by scripts, then collapse recovery onto one public executor, and only after that clean the docs and tests to match the new path.

**Tech Stack:** Python runtime scripts, YAML workflow/state contracts, Markdown skill docs, pytest evals

---

## Step 0 Findings

### What already exists

- `skills/create-technical-solution/scripts/protocol_runtime.py` already owns the strongest version of repo-relative path helpers and workflow lookup; this should become the single contract source rather than introducing a new parallel runtime layer.
- `skills/create-technical-solution/scripts/run-step.py` already acts as the public orchestrator; the closeout should reinforce that role, not create a second top-level command surface.
- `skills/create-technical-solution/scripts/validate-state.py` already emits machine-readable `repair_plan`, but the current actions are too generic and still force the model to interpret prose.
- `skills/create-technical-solution/scripts/upsert-draft-block.py` already owns WD block file writes; it should be upgraded into a structured renderer path rather than replaced by a second writer.
- `skills/create-technical-solution/scripts/render-final-document.py` already renders final output from working draft artifacts; keep this model, but make upstream WD inputs more deterministic.
- Existing eval coverage in `evals/create-technical-solution/test_run_step.py`, `evals/create-technical-solution/test_validate_state.py`, and `evals/create-technical-solution/test_docs_alignment.py` already catches many step-local issues. The missing piece is stronger regression coverage by error class.

### Scope challenge

- This work touches more than 8 files, but it is still the minimum credible closeout because the same boundary leak currently appears in runtime, writer, validator, docs, and tests. Trying to do only one layer would leave the public path inconsistent.
- The real minimum is 5 execution packages, not 7. "Single WD write path" and "structured WD submission protocol" must ship together or the same interfaces will be redesigned twice.
- No new infrastructure is needed. This is a boring-technology cleanup inside the existing script stack. Good.
- Search unavailable for framework best-practice lookup in this review path, proceeding with in-distribution knowledge only.

### Complexity guardrails

- Do not rewrite the workflow engine.
- Do not add a second public command surface.
- Do not add new artifact types.
- Do not move final document generation out of `render-final-document.py`.
- Do not turn `runtime_doctor.py` into a public recovery path.

## NOT in scope

- Reworking the 12-step workflow structure, the goal is boundary cleanup, not process redesign.
- Introducing a new state storage format, YAML remains the source format.
- Adding new WD artifact families beyond `WD-CTX`, `WD-TASK`, `WD-EXP-SLOT-*`, and `WD-SYN-SLOT-*`.
- Changing the technical solution template mechanism itself, only the way the runtime reads and renders around it.
- Expanding `runtime_doctor.py` into a second supported user entrypoint.

## Canonical target model

The end state after this plan is:

```text
model submits business payload only
            |
            v
run-step.py is the only public executor
            |
            v
single runtime contract resolves paths/defaults/step defs
            |
            v
structured WD payload -> script renderer -> WD files -> artifact registry
            |
            v
validator diagnoses drift and returns typed recovery action
            |
            v
run-step.py executes the only public repair path
```

## Migration strategy

The WD protocol migration is staged on purpose.

```text
Phase 1: land canonical state contract + add structured WD schema support
Phase 2: switch public docs/examples/run-step responses to structured payloads
Phase 3: remove raw Markdown as a public step 7-10 submission path
```

- During Phase 1, old raw Markdown may remain as an internal compatibility shim if needed for tests.
- During Phase 2, all public docs and examples must stop teaching raw Markdown submission.
- During Phase 3, tests should only preserve legacy upgrade coverage, not legacy main-path behavior.

## Worktree parallelization strategy

| Step | Modules touched | Depends on |
|------|-----------------|------------|
| Canonical state contract | `skills/create-technical-solution/scripts/`, `evals/create-technical-solution/` | — |
| Structured WD submission pipeline | `skills/create-technical-solution/scripts/`, `skills/create-technical-solution/protocol/`, `evals/create-technical-solution/` | Canonical state contract |
| Single recovery surface | `skills/create-technical-solution/scripts/`, `evals/create-technical-solution/` | Structured WD submission pipeline |
| Public interface cleanup | `skills/create-technical-solution/`, `evals/create-technical-solution/` | Single recovery surface |
| Error-class verification + external run | `evals/create-technical-solution/`, external runtime verification | Public interface cleanup |

Parallel lanes:

- Lane A: Canonical state contract -> Structured WD submission pipeline -> Single recovery surface
- Lane B: Public interface cleanup (prepare drafts only, merge after Lane A contract stabilizes)
- Lane C: Error-class verification -> external tmux run

Execution order:

- Launch only Lane A first.
- Lane B can prepare draft doc/test edits once WD payload shapes are stable, but should not merge before Lane A is done.
- Launch Lane C after A + B land.

Conflict flags:

- Lanes A and B both touch `skills/create-technical-solution/` and `evals/create-technical-solution/`, so careless parallel execution will cause merge conflicts. Prefer sequential merge order even if exploration is parallel.

### Task 1: Centralize the canonical runtime contract

**Files:**
- Modify: `skills/create-technical-solution/scripts/protocol_runtime.py`
- Modify: `skills/create-technical-solution/scripts/run-step.py`
- Modify: `skills/create-technical-solution/scripts/initialize-state.py`
- Modify: `skills/create-technical-solution/scripts/runtime_snapshot.py`
- Modify: `skills/create-technical-solution/scripts/validate-state.py`
- Modify: `skills/create-technical-solution/scripts/render-final-document.py`
- Test: `evals/create-technical-solution/test_run_step.py`
- Test: `evals/create-technical-solution/test_validate_state.py`

- [ ] **Step 1: Extract the shared runtime contract API**

Add or extend helper functions in `skills/create-technical-solution/scripts/protocol_runtime.py` so this module becomes the single source for:

```python
DEFAULT_TEMPLATE_PATH = ".architecture/templates/technical-solution-template.md"
DEFAULT_MEMBERS_PATH = ".architecture/members.yml"
DEFAULT_PRINCIPLES_PATH = ".architecture/principles.md"

def build_canonical_state_payload(*, state_path: Path, slug: str | None = None) -> dict[str, Any]:
    ...

def canonical_repo_paths_for_slug(*, repo_root: Path, slug: str) -> dict[str, Path]:
    ...

def canonical_state_paths_for_slug(slug: str) -> dict[str, str]:
    ...

def canonical_step_defs() -> dict[int, dict[str, Any]]:
    ...
```

- [ ] **Step 2: Remove duplicated default field assembly from `run-step.py`**

Replace local state bootstrap logic so `skills/create-technical-solution/scripts/run-step.py` no longer hardcodes:

```python
"members_path": ".architecture/members.yml"
"principles_path": ".architecture/principles.md"
"template_path": ".architecture/templates/technical-solution-template.md"
```

and instead consumes the canonical contract helper.

- [ ] **Step 3: Remove duplicated default field assembly from `initialize-state.py`**

Replace `setdefault(...)` path bootstrapping in `skills/create-technical-solution/scripts/initialize-state.py` with canonical contract consumption so the file no longer invents its own minimum state shape.

- [ ] **Step 4: Remove duplicated fallback path logic from snapshot/validator/render code**

Update:

- `skills/create-technical-solution/scripts/runtime_snapshot.py`
- `skills/create-technical-solution/scripts/validate-state.py`
- `skills/create-technical-solution/scripts/render-final-document.py`

so they resolve paths through the shared runtime contract instead of each carrying their own fallback default logic.

- [ ] **Step 5: Add bootstrap convergence regression tests**

Add test coverage proving that these inputs converge to the same canonical state shape:

```text
- empty state via run-step --advance
- legacy prepare path / compatibility bootstrap
- installed-copy path expectations
- external skill copy path expectations
```

- [ ] **Step 6: Run the focused bootstrap test subset**

Run:

```bash
python -m pytest evals/create-technical-solution/test_run_step.py -k "bootstrap or canonical or initial_state" -q
python -m pytest evals/create-technical-solution/test_validate_state.py -k "path or canonical" -q
```

Expected: passing tests that prove path/default convergence and no duplicated truth source behavior remains.

- [ ] **Step 7: Gate A review**

Confirm these statements are now true before moving on:

```text
- all default state/path fields come from one runtime contract
- bootstrap entrypoints converge to the same minimal state shape
- snapshot, validator, and renderer do not carry their own independent default path truth
```

### Task 2: Replace step 7-10 raw Markdown submission with a structured WD pipeline

**Files:**
- Modify: `skills/create-technical-solution/scripts/run-step.py`
- Modify: `skills/create-technical-solution/scripts/upsert-draft-block.py`
- Modify: `skills/create-technical-solution/scripts/validate-state.py`
- Modify: `skills/create-technical-solution/protocol/block-contracts.yaml`
- Modify: `skills/create-technical-solution/REFERENCE.md`
- Test: `evals/create-technical-solution/test_run_step.py`
- Test: `evals/create-technical-solution/test_validate_state.py`

- [ ] **Step 1: Define canonical WD payload schemas**

Define one explicit structured input per creative step:

```text
step 7  -> CTX entry array
step 8  -> slot task array
step 9  -> per-slot expert analysis payload
step 10 -> per-slot synthesis payload
```

Write the schema shape into code and protocol docs before changing the writer.

- [ ] **Step 2: Change `run-step.py --advance` to advertise schemas, not raw body examples**

Update the creative-step entry payload so the contract reads like:

```json
{
  "artifact": "WD-CTX",
  "required_output_shape": {"type": "array", "item_schema": "ctx_entry"},
  "next_action": "submit_structured_payload"
}
```

not a heredoc-style freeform body instruction.

- [ ] **Step 3: Change creative completion to parse structured payloads**

Update `skills/create-technical-solution/scripts/run-step.py` so step 7-10 completion paths accept structured payloads and hand them to a script-side renderer. Do not keep raw Markdown as the main path.

- [ ] **Step 4: Upgrade the WD writer into a renderer path**

Change `skills/create-technical-solution/scripts/upsert-draft-block.py` so it owns:

```text
payload -> markdown render -> file write -> artifact registry sync
```

instead of treating raw Markdown block bodies as the canonical user input.

- [ ] **Step 5: Tighten validator expectations around rendered structure**

Update `skills/create-technical-solution/scripts/validate-state.py` so schema/render agreement becomes the main contract. Validator should check rendered output against payload-derived rules, not act like a post-hoc Markdown format repair system.

- [ ] **Step 6: Preserve a short migration shim only if required**

If old raw Markdown inputs are needed temporarily to avoid a giant flag day, keep them only as internal compatibility behavior with clear tests. Do not document them as a public path.

- [ ] **Step 7: Add structured WD pipeline regression tests**

Add tests covering:

```text
- valid structured step 7 payload renders WD-CTX
- valid structured step 8 payload renders WD-TASK
- valid structured step 9 payload renders WD-EXP-SLOT-*
- valid structured step 10 payload renders WD-SYN-SLOT-*
- invalid schema fails before write
- repeated payload renders stable output
```

- [ ] **Step 8: Run the focused WD pipeline test subset**

Run:

```bash
python -m pytest evals/create-technical-solution/test_run_step.py -k "WD or scaffold or complete" -q
python -m pytest evals/create-technical-solution/test_validate_state.py -k "WD or ctx or syn or task" -q
```

Expected: green tests proving structured payloads are now the primary step 7-10 submission path.

- [ ] **Step 9: Gate B review**

Confirm these statements are now true before moving on:

```text
- step 7-10 canonical input is structured payload, not raw Markdown
- Markdown is now a script-rendered artifact
- WD file placement and registry sync happen inside one controlled write path
```

### Task 3: Collapse recovery onto one public surface

**Files:**
- Modify: `skills/create-technical-solution/scripts/validate-state.py`
- Modify: `skills/create-technical-solution/scripts/run-step.py`
- Modify: `skills/create-technical-solution/scripts/protocol_runtime.py`
- Test: `evals/create-technical-solution/test_run_step.py`
- Test: `evals/create-technical-solution/test_validate_state.py`

- [ ] **Step 1: Separate diagnosis from public execution**

Refactor the recovery contract so:

```text
validate-state.py -> diagnosis + typed action recommendation
run-step.py       -> only supported public repair executor
```

Do not leave validator JSON as a competing public repair path.

- [ ] **Step 2: Replace generic repair actions with finite typed actions**

Convert generic actions like `rerun_run_step` into a finite set such as:

```text
refresh_ticket
rebuild_from_step_3
rebuild_from_step_7
rebuild_from_step_8
rollback_to_step_10
rerender_final_document
```

Each action should carry typed parameters, not rely primarily on a shell command string.

- [ ] **Step 3: Make `run-step.py --advance` the only public repair entrypoint**

Update user-facing failure output so recovery always routes back through `run-step.py`, even when diagnosis came from the validator.

- [ ] **Step 4: Downgrade prose recovery guidance to supporting detail**

Keep `repair_guidance` only as explanation. The machine-readable action must be sufficient on its own.

- [ ] **Step 5: Add drift and recovery regressions by error class**

Add tests covering unique recovery actions for:

```text
- ticket drift
- artifact drift
- slot/template truth mismatch
- final document drift
- CTX dangling reference
```

- [ ] **Step 6: Run the focused recovery test subset**

Run:

```bash
python -m pytest evals/create-technical-solution/test_validate_state.py -k "repair or drift or rollback or ticket" -q
python -m pytest evals/create-technical-solution/test_run_step.py -k "repair or ticket or advance" -q
```

Expected: every major failure mode maps to one public recovery surface.

- [ ] **Step 7: Gate C review**

Confirm these statements are now true before moving on:

```text
- validator diagnoses but does not compete as a public executor
- recovery actions are finite and typed
- users and models only need run-step.py to recover
```

### Task 4: Clean the public interface and documentation

**Files:**
- Modify: `skills/create-technical-solution/SKILL.md`
- Modify: `skills/create-technical-solution/REFERENCE.md`
- Modify: `skills/create-technical-solution/steps/07-构建共享上下文.md`
- Modify: `skills/create-technical-solution/steps/08-生成模板任务单.md`
- Modify: `skills/create-technical-solution/steps/09-组织专家按模板逐槽位分析.md`
- Modify: `skills/create-technical-solution/steps/10-按模板逐槽位协作收敛.md`
- Test: `evals/create-technical-solution/test_docs_alignment.py`

- [ ] **Step 1: Rewrite the public path in SKILL.md**

Document only the supported path:

```text
status via run-step.py
advance via run-step.py --advance
structured submission via run-step.py --complete --ticket ...
```

Low-level flags may still exist internally, but they must stop appearing as user-operable guidance.

- [ ] **Step 2: Rewrite step 7-10 cards around schemas**

Update step cards so they describe business payload shapes and business constraints, not freeform Markdown body composition.

- [ ] **Step 3: Reduce internal protocol leakage in REFERENCE.md**

Keep enough detail for implementation and debugging, but remove or soften unnecessary public emphasis on:

```text
--prepare
--mark-step-card-read
manual ticket repair
manual state repair
validator JSON as a second public recovery path
```

- [ ] **Step 4: Add docs alignment assertions for the new public path**

Extend `evals/create-technical-solution/test_docs_alignment.py` so it proves:

```text
- docs teach one public path
- step 7-10 describe structured payloads
- low-level flags are not presented as main-path commands
```

- [ ] **Step 5: Run docs alignment tests**

Run:

```bash
python -m pytest evals/create-technical-solution/test_docs_alignment.py -q
```

Expected: docs, step cards, and protocol references now tell the same story.

- [ ] **Step 6: Gate D review**

Confirm these statements are now true before moving on:

```text
- only one public execution path is documented
- only one public recovery path is documented
- step 7-10 public instructions talk about schemas, not raw Markdown bodies
```

### Task 5: Finish regression coverage by error class and run end-to-end verification

**Files:**
- Modify: `evals/create-technical-solution/test_run_step.py`
- Modify: `evals/create-technical-solution/test_validate_state.py`
- Modify: `evals/create-technical-solution/test_docs_alignment.py`

- [ ] **Step 1: Reorganize missing regressions around error classes**

Add or rename tests so these classes are first-class regression buckets:

```text
state bootstrap inconsistency
direct artifact write
ticket drift recovery
CTX dangling reference
slot/template truth mismatch
empty or invalid synthesis
public path ambiguity
```

- [ ] **Step 2: Add direct artifact write prevention coverage**

Prove that direct out-of-band writes to these artifacts are rejected or treated as drift:

```text
WD-CTX
WD-TASK
WD-EXP-SLOT-*
WD-SYN-SLOT-*
final document before official render
```

- [ ] **Step 3: Run the full CTS local suite**

Run:

```bash
python -m pytest evals/create-technical-solution/test_run_step.py -q
python -m pytest evals/create-technical-solution/test_validate_state.py -q
python -m pytest evals/create-technical-solution/test_docs_alignment.py -q
```

Expected: full local green across runtime, validator, and docs alignment.

- [ ] **Step 4: Perform an external tmux run from empty state**

Manually run the skill through an external UGC tmux session from empty state and record:

```text
- whether the public path stays on run-step.py
- whether step 7-10 use structured payloads cleanly
- whether drift recovery avoids manual YAML/file edits
```

- [ ] **Step 5: Force at least two drift scenarios during the external run**

During the tmux exercise, deliberately trigger at least two failures, such as:

```text
- ticket invalidation after state drift
- WD artifact drift after out-of-band write
```

Confirm the system returns one repair action instead of encouraging manual repair invention.

- [ ] **Step 6: Capture final acceptance against the closeout standard**

Record whether all of these are true:

```text
- one canonical state generation strategy
- one WD write path
- one public recovery surface
- one public main path
- model only fills business payloads, scripts own flow/state/render/recovery
```

## Failure modes to watch during implementation

| New codepath | Likely production failure | Test required | Error handling required | User-visible result |
|--------------|---------------------------|---------------|-------------------------|---------------------|
| canonical bootstrap | legacy state upgrades to inconsistent path fields | yes | yes | should stop with explicit path mismatch, not silently continue |
| structured WD submit | payload shape accepted but renderer drops a field | yes | yes | clear validation failure, not silent malformed WD file |
| artifact registry sync | file written but registry not updated atomically | yes | yes | drift surfaced on next check, not silent false pass |
| typed recovery action | diagnosis maps to wrong rebuild step | yes | yes | clear single repair action, not looping retry |
| docs/public path | docs still teach side-door commands | yes | n/a | user confusion, path ambiguity |

Any failure mode that ends up with no test, no error handling, and a silent pass is a critical gap. Do not ship past it.

## Completion summary template

Use this when the implementation is done:

- Step 0: Scope Challenge — accepted as-is / reduced
- Architecture Review: closeout plan implemented across 5 packages
- Code Quality Review: duplicated contract sources removed / remaining hotspots listed
- Test Review: error-class coverage completed, gap count recorded
- Performance Review: not expected to be the primary risk, but note any regressions
- NOT in scope: preserved
- What already exists: reused, not rebuilt in parallel
- TODOS.md updates: list any deferred follow-ups discovered during implementation
- Failure modes: critical gaps count
- Parallelization: note actual execution lane usage
- Lake Score: record how many complete options were chosen over shortcuts
