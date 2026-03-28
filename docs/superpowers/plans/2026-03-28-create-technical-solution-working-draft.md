# Create Technical Solution Working Draft Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single working-draft workflow to `create-technical-solution` so every stage writes full canonical artifacts to `.architecture/technical-solutions/working-drafts/` before showing concise conversation summaries.

**Architecture:** Introduce `references/working-draft-protocol.md` as the canonical contract for path, block identifiers, lifecycle, write-before-display, invalidation, and absorb/delete behavior. Then wire that contract through `solution-process.md`, `progress-transparency.md`, and `SKILL.md`, and lock the behavior with focused `unittest` contract checks that load the new reference source and verify the full working-draft round trip.

**Tech Stack:** Markdown skill docs, Python `unittest` validation suite

---

## File Map

- Create: `skills/create-technical-solution/references/working-draft-protocol.md` — canonical working-draft contract for path, block IDs, lifecycle, references, invalidation, and absorb/delete rules.
- Modify: `skills/create-technical-solution/references/solution-process.md` — require every canonical artifact to be written to the working draft before user-visible summaries and before downstream consumption.
- Modify: `skills/create-technical-solution/references/progress-transparency.md` — switch user-visible stage rendering from full artifact dumps to summary-first rendering plus `WD-*` references.
- Modify: `skills/create-technical-solution/SKILL.md` — integrate working-draft path creation, per-stage writes, absorb/delete checks, and updated completion/output wording.
- Modify: `tests/skill_validation/helpers.py` — load the new working-draft reference alongside the existing create-solution sources.
- Modify: `tests/skill_validation/test_create_technical_solution_contracts.py` — add focused contract tests for the new protocol and cross-doc wiring.

### Task 1: Add Working-Draft Protocol Coverage

**Files:**
- Create: `skills/create-technical-solution/references/working-draft-protocol.md`
- Modify: `tests/skill_validation/helpers.py`
- Modify: `tests/skill_validation/test_create_technical_solution_contracts.py`
- Test: `tests/skill_validation/test_create_technical_solution_contracts.py`

- [ ] **Step 1: Write the failing test and source loader**

```python
def load_create_solution_contract_sources() -> dict[str, str]:
    return {
        "main": read_repo_text("skills/create-technical-solution/SKILL.md"),
        "solution_process": read_repo_text(
            "skills/create-technical-solution/references/solution-process.md"
        ),
        "template_adaptation": read_repo_text(
            "skills/create-technical-solution/references/template-adaptation.md"
        ),
        "progress_transparency": read_repo_text(
            "skills/create-technical-solution/references/progress-transparency.md"
        ),
        "working_draft_protocol": read_repo_text(
            "skills/create-technical-solution/references/working-draft-protocol.md"
        ),
        "analysis_guide": read_repo_text(
            "skills/create-technical-solution/references/solution-analysis-guide.md"
        ),
    }
```

```python
    def test_working_draft_protocol_defines_single_draft_path_blocks_and_lifecycle(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["working_draft_protocol"],
            (
                "`.architecture/technical-solutions/working-drafts/[slug].working.md`",
                "整个一次技术方案生成过程只维护一份 working draft。",
                "## WD-CTX 共享上下文清单",
                "## WD-TASK 模板任务单",
                "## WD-EXP-[expert-slug] 专家产物",
                "## WD-SYN 协作收敛纪要",
                "## WD-IMPACT-[n] 变更影响说明",
                "每个阶段完成后，必须先把完整 canonical schema 写入 working draft，再对用户展示摘要。",
                "working draft 不保存 scratchpad、原始推理链路或聊天记录。",
                "吸收检查通过后，删除 working draft。",
            ),
        )
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_working_draft_protocol_defines_single_draft_path_blocks_and_lifecycle -v`
Expected: FAIL with `FileNotFoundError` for `skills/create-technical-solution/references/working-draft-protocol.md` or with missing-snippet assertions because the protocol file does not exist yet.

- [ ] **Step 3: Write the minimal working-draft protocol document**

```markdown
# 技术方案 working draft 协议

## 1. 路径与定位

- working draft 固定路径：`.architecture/technical-solutions/working-drafts/[slug].working.md`
- 其中 `[slug]` 与主 skill 中的 `[主题-短横线文件名]` 指向同一个清洗结果。
- 整个一次技术方案生成过程只维护一份 working draft。

## 2. 稳定区块

## WD-CTX 共享上下文清单
- `上下文编号`
- `来源`
- `结论或约束`
- `适用槽位`
- `可信度或缺口`

## WD-TASK 模板任务单
- `槽位标识`
- `槽位语义`
- `本槽位必须消费的共享上下文`
- `参与专家`
- `缺失即停止的上下文`

## WD-EXP-[expert-slug] 专家产物
- `是否参与该槽位`
- `建议写法或建议内容`
- `已使用的共享上下文编号`
- `结论是否超出上下文支持`

## WD-SYN 协作收敛纪要
- `共同结论`
- `选定写法`
- `本槽位已核销的共享上下文`
- `仍缺哪条共享上下文`

## WD-IMPACT-[n] 变更影响说明
- `触发变更`
- `受影响内容`
- `最近受影响的阶段边界`
- `保持有效的内容`
- `下一步动作`

## 3. 写入与消费规则

- 每个阶段完成后，必须先把完整 canonical schema 写入 working draft，再对用户展示摘要。
- 下游阶段只能消费 working draft 中已存在的稳定区块；未写入则视为不存在。
- working draft 不保存 scratchpad、原始推理链路或聊天记录。

## 4. 吸收与删除

- 最终文档生成后，必须先执行吸收检查。
- 吸收检查通过后，删除 working draft。
```

- [ ] **Step 4: Run the targeted test to verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_working_draft_protocol_defines_single_draft_path_blocks_and_lifecycle -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/skill_validation/helpers.py tests/skill_validation/test_create_technical_solution_contracts.py skills/create-technical-solution/references/working-draft-protocol.md
git commit -m "docs(skill): add create-solution working draft protocol"
```

### Task 2: Wire Write-Before-Display Into Reference Docs

**Files:**
- Modify: `skills/create-technical-solution/references/solution-process.md`
- Modify: `skills/create-technical-solution/references/progress-transparency.md`
- Modify: `tests/skill_validation/test_create_technical_solution_contracts.py`
- Test: `tests/skill_validation/test_create_technical_solution_contracts.py`

- [ ] **Step 1: Write the failing contract tests for the two reference docs**

```python
    def test_solution_process_requires_working_draft_before_user_display(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["solution_process"],
            (
                "适用于全部用户可见产物的共享规则如下：",
                "`共享上下文清单`、`模板任务单`、`专家按模板逐槽位分析`、`按模板逐槽位协作收敛`、`变更影响说明` 都必须先补齐本文件要求的必填字段，再写入 working draft，再对用户展示。",
                "对外展示时，默认只展示稳定摘要，并使用 `详见 working draft：WD-CTX（共享上下文清单）` 这类稳定引用指向完整内容。",
                "阶段回退或重算时，先更新 working draft 中对应区块，再对外展示 `变更影响说明`。",
                "最终文档生成后，先执行吸收检查，再删除 working draft。",
            ),
        )

    def test_progress_transparency_switches_to_summary_plus_working_draft_references(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["progress_transparency"],
            (
                "中间产物必须先写入 working draft，再对用户展示摘要。",
                "`详见 working draft：WD-CTX（共享上下文清单）`",
                "`详见 working draft：WD-TASK（模板任务单）`",
                "`详见 working draft：WD-EXP-system-architect（系统架构师专家产物）`",
                "`详见 working draft：WD-SYN（协作收敛纪要）`",
            ),
        )
        self.assertNotIn(
            "中间产物默认只在当前对话中展示，不新增正式文档或侧车文件。",
            self.sources["progress_transparency"],
        )
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_solution_process_requires_working_draft_before_user_display tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_progress_transparency_switches_to_summary_plus_working_draft_references -v`
Expected: FAIL because the current references still describe conversation-only display and do not yet require working-draft writes or `WD-*` references.

- [ ] **Step 3: Add the minimal reference-doc wording to make the tests pass**

```markdown
适用于全部用户可见产物的共享规则如下：

- `共享上下文清单`、`模板任务单`、`专家按模板逐槽位分析`、`按模板逐槽位协作收敛`、`变更影响说明` 都必须先补齐本文件要求的必填字段，再写入 working draft，再对用户展示。
- 对外展示时，默认只展示稳定摘要，并使用 `详见 working draft：WD-CTX（共享上下文清单）` 这类稳定引用指向完整内容。
- 阶段回退或重算时，先更新 working draft 中对应区块，再对外展示 `变更影响说明`。
- 最终文档生成后，先执行吸收检查，再删除 working draft。
```

```markdown
### 边界

- 中间产物必须先写入 working draft，再对用户展示摘要。
- 对话内默认只展示稳定摘要，并使用 `详见 working draft：WD-CTX（共享上下文清单）` 这类稳定引用指向完整内容。
- working draft 不是正式技术方案正文，也不是第二份正式交付物。

共享上下文来源、约束、适用槽位和缺口稳定后，先将完整 `共享上下文清单` 写入 `WD-CTX`，再展示摘要。

摘要末尾附：`详见 working draft：WD-CTX（共享上下文清单）`

模板槽位、参与专家、必答问题和阻塞条件稳定后，先将完整 `模板任务单` 写入 `WD-TASK`，再展示摘要。

摘要末尾附：`详见 working draft：WD-TASK（模板任务单）`

单个专家补齐必填字段后，先将完整专家产物写入 `WD-EXP-system-architect` 这类专家区块，再展示摘要。

摘要末尾附：`详见 working draft：WD-EXP-system-architect（系统架构师专家产物）`

全部专家输入完成后，先将完整 `协作收敛纪要` 写入 `WD-SYN`，再展示摘要。

摘要末尾附：`详见 working draft：WD-SYN（协作收敛纪要）`
```

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_solution_process_requires_working_draft_before_user_display tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_progress_transparency_switches_to_summary_plus_working_draft_references -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/create-technical-solution/references/solution-process.md skills/create-technical-solution/references/progress-transparency.md tests/skill_validation/test_create_technical_solution_contracts.py
git commit -m "docs(skill): require working draft before summary display"
```

### Task 3: Integrate The Working-Draft Lifecycle Into The Main Skill

**Files:**
- Modify: `skills/create-technical-solution/SKILL.md`
- Modify: `tests/skill_validation/test_create_technical_solution_contracts.py`
- Test: `tests/skill_validation/test_create_technical_solution_contracts.py`

- [ ] **Step 1: Write the failing main-skill contract test**

```python
    def test_main_skill_requires_working_draft_round_trip(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "`.architecture/technical-solutions/working-drafts/[主题-短横线文件名].working.md`",
                "完成后，必须先按 [references/working-draft-protocol.md](references/working-draft-protocol.md) 将 `共享上下文清单` 写入 `WD-CTX`，再按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示摘要。",
                "完成后，必须先按 [references/working-draft-protocol.md](references/working-draft-protocol.md) 将这份 `模板任务单` 写入 `WD-TASK`，再在对话中展示摘要。",
                "每个成员完成独立输入后，先写入对应 `WD-EXP-[expert-slug]` 区块，再展示摘要。",
                "完成收敛后、生成最终文档前，必须先将 `协作收敛纪要` 写入 `WD-SYN`，再在对话中展示摘要。",
                "过程可见产物：已写入 1 份 working draft，并摘要展示 1 份共享上下文清单、1 份模板任务单、[成员数] 份专家产物与 1 份协作收敛纪要",
                "生成最终文档后，先执行吸收检查；通过后删除 working draft。",
            ),
        )
        self.assertNotIn("这些中间产物默认不作为侧车文档落盘", self.sources["main"])
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_main_skill_requires_working_draft_round_trip -v`
Expected: FAIL because `SKILL.md` still describes conversation-only staged artifacts and does not yet mention the working-draft path or absorb/delete lifecycle.

- [ ] **Step 3: Update `SKILL.md` with the minimal working-draft lifecycle text**

```markdown
- [working draft 协议](references/working-draft-protocol.md)

- 分阶段中间产物已先写入 `.architecture/technical-solutions/working-drafts/[主题-短横线文件名].working.md`，再按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中摘要展示。
- 生成最终文档后已完成吸收检查，working draft 已删除。

先明确：问题、目标与非目标、约束与依赖、影响范围、相关需求。主题模糊时先澄清，再生成安全的短横线风格文件名，并预留 working draft 路径 `.architecture/technical-solutions/working-drafts/[主题-短横线文件名].working.md`。

完成后，必须先按 [references/working-draft-protocol.md](references/working-draft-protocol.md) 将 `共享上下文清单` 写入 `WD-CTX`，再按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示摘要。

完成后，必须先按 [references/working-draft-protocol.md](references/working-draft-protocol.md) 将这份 `模板任务单` 写入 `WD-TASK`，再在对话中展示摘要。

每个成员完成独立输入后，先写入对应 `WD-EXP-[expert-slug]` 区块，再展示摘要。

完成收敛后、生成最终文档前，必须先将 `协作收敛纪要` 写入 `WD-SYN`，再在对话中展示摘要。

过程可见产物：已写入 1 份 working draft，并摘要展示 1 份共享上下文清单、1 份模板任务单、[成员数] 份专家产物与 1 份协作收敛纪要

生成最终文档后，先执行吸收检查；通过后删除 working draft。

6. `共享上下文清单`、`模板任务单`、各份 `专家产物`、`协作收敛纪要` 和 `变更影响说明` 都必须先写入单一 working draft，再按阶段展示摘要。
7. 最终保持当前模板现有结构，不新增任何模板外可见结构；最终只把已收敛内容写回当前模板已有位置。
8. 缺少语义前置、无法展示稳定中间产物、无法安全落位，或任一槽位缺少可回溯的共享上下文编号时停止并确认。
9. 生成最终文档后必须执行吸收检查，通过后删除 working draft。
```

- [ ] **Step 4: Run the targeted test to verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_main_skill_requires_working_draft_round_trip -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/create-technical-solution/SKILL.md tests/skill_validation/test_create_technical_solution_contracts.py
git commit -m "docs(skill): add working draft lifecycle to create-solution"
```

### Task 4: Run The Full Validation Suite And Resolve Contract Drift

**Files:**
- Test: `tests/skill_validation/test_*.py`

- [ ] **Step 1: Run the full validation suite**

Run: `python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v`
Expected: PASS with the new working-draft contract tests green and no regressions in the existing setup, create-solution, or review-solution suites.

- [ ] **Step 2: If an assertion still reflects pre-working-draft wording, align it to the new contract immediately**

```python
require_snippets_in_order(
    self,
    self.sources["main"],
    (
        "### 6. 构建共享上下文",
        "写入 `WD-CTX`",
        "### 7. 生成模板任务单",
        "写入 `WD-TASK`",
        "### 9. 按模板逐槽位协作收敛",
        "写入 `WD-SYN`",
        "### 10. 严格模板成稿并保存结果",
        "先执行吸收检查；通过后删除 working draft。",
    ),
)
```

- [ ] **Step 3: Re-run the full validation suite**

Run: `python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add skills/create-technical-solution/SKILL.md skills/create-technical-solution/references/working-draft-protocol.md skills/create-technical-solution/references/solution-process.md skills/create-technical-solution/references/progress-transparency.md tests/skill_validation/helpers.py tests/skill_validation/test_create_technical_solution_contracts.py
git commit -m "feat(skill): enforce working draft flow in create-technical-solution"
```
