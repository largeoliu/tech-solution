# Technical Solution Weak Model Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework `create-technical-solution` so every intermediate analysis artifact is locked to the active template structure, which makes weaker models more stable without changing the external output path or prerequisite rules.

**Architecture:** Start by extending the contract tests so the new workflow is explicit and regression-safe. Then replace the old template-agnostic expert/convergence contracts with a template-slot pipeline: `范围冻结 -> 模板任务单 -> 专家按模板逐槽位分析 -> 按模板逐槽位协作收敛 -> 严格模板成稿`. Keep the current prerequisite checks, template-first ordering, overwrite confirmation, and minimum semantic coverage, but express them through template-native slots instead of a template-external schema.

**Tech Stack:** Markdown skill docs, Python 3 `unittest`, `rg`, `git diff --check`

---

## File Structure

- Modify: `skills/create-technical-solution/SKILL.md` - swap the old expert/convergence workflow for the new template-locked five-stage pipeline while preserving existing hard-stop and save-path rules.
- Modify: `skills/create-technical-solution/references/solution-process.md` - define the new canonical intermediate artifacts: `模板任务单`, `专家按模板逐槽位分析`, and `按模板逐槽位协作收敛`.
- Modify: `skills/create-technical-solution/references/template-adaptation.md` - strengthen the rule that the active template is the only information architecture for the whole chain, not just final rendering.
- Modify: `skills/create-technical-solution/references/progress-transparency.md` - align phase boundaries, visible artifacts, and rollback rules with the new template-slot workflow.
- Modify: `tests/skill_validation/helpers.py` - expose `progress-transparency.md` to the create-solution contract loader.
- Modify: `tests/skill_validation/test_create_technical_solution_contracts.py` - add regression assertions for template-locked workflow, template-slot artifacts, zero-new-content behavior, and template-change rollback.
- Read: `docs/superpowers/specs/2026-03-27-technical-solution-weak-model-quality-design.md` - approved design to implement fully.

### Task 1: Lock the Main Skill Workflow Contract

**Files:**
- Modify: `tests/skill_validation/test_create_technical_solution_contracts.py`
- Modify: `skills/create-technical-solution/SKILL.md`

- [ ] **Step 1: Write the failing main-workflow test**

```python
def test_main_skill_enforces_template_locked_workflow(self) -> None:
    require_snippets_in_order(
        self,
        self.sources["main"],
        (
            "必须先读取当前生效模板，再判断方案类型，再选择参与成员。",
            "### 7. 生成模板任务单",
            "### 8. 组织专家按模板逐槽位分析",
            "### 9. 按模板逐槽位协作收敛",
            "### 10. 严格模板成稿并保存结果",
        ),
    )
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_main_skill_enforces_template_locked_workflow -v`
Expected: FAIL because the new workflow headings are missing from `skills/create-technical-solution/SKILL.md`

- [ ] **Step 3: Rewrite the main workflow and completion contract**

Replace the old member-input and convergence workflow in `skills/create-technical-solution/SKILL.md` with this structure:

```md
## 完成标准

- 主题、目标、非目标、约束、影响范围已经明确。
- 参与成员选择与方案类型一致，且至少包含系统架构师。
- 共享上下文已覆盖原则、现状、已有实现、关键约束和当前生效模板结构。
- `模板任务单` 已完成，并按当前模板原始顺序定义槽位语义、参与成员、每位专家必答问题、禁止越界项和阻塞信息。
- 分阶段中间产物已按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示：每位参与成员各 1 份按模板槽位组织的 `专家产物`，以及 1 份按模板槽位组织的 `协作收敛纪要`；这些中间产物默认不作为侧车文档落盘。
- 最终内容只填写当前生效模板已有位置，不新增模板外可见内容，并且保存行为符合覆盖确认规则。

### 7. 生成模板任务单

在当前模板结构、章节语义、表格列和占位说明都已理解后，先生成 `模板任务单`。它必须按模板原始顺序列出每个已有槽位，并为每个槽位明确：槽位语义、可填写边界、参与成员、每位专家必答问题、禁止越界项和阻塞信息。

### 8. 组织专家按模板逐槽位分析

要求每个参与成员只基于 `范围冻结` 与 `模板任务单` 独立分析。专家产物必须按模板槽位顺序输出，不得以模板外的统一标题重新组织内容。每个成员完成后，立即按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示该成员的结构化 `专家产物`。

### 9. 按模板逐槽位协作收敛

把专家输入按模板槽位收敛为共同结论、分歧点、选定写法、未采纳理由和仍待决策，并在最终成稿前先展示 1 份结构化 `协作收敛纪要`。如果用户在展示后新增约束、修正目标或调整范围，先说明失效范围，再从最近受影响的阶段边界重进。

### 10. 严格模板成稿并保存结果

仅把上游已经收敛的结论填写回当前模板已有位置；如果某个必要信息没有模板内合法落点，立即停止并向用户确认。若三个关键文件齐全但 `.architecture/technical-solutions/` 缺失，则自动创建该目录后继续。

## 行为契约

1. 先读取当前生效模板。
2. 再判断方案类型。
3. 再选择参与成员。
4. 先生成 `模板任务单`。
5. 再展示按模板逐槽位组织的 `专家产物` 与 `协作收敛纪要`。
6. 最终只把已收敛内容写回当前模板已有位置。
7. 缺少语义前置、无法展示稳定中间产物或无法安全落位时停止并确认。
```

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_main_skill_enforces_template_locked_workflow -v`
Expected: PASS

- [ ] **Step 5: Commit the main workflow slice**

```bash
git add tests/skill_validation/test_create_technical_solution_contracts.py skills/create-technical-solution/SKILL.md
git commit -m "feat(skill): lock create solution workflow to template stages"
```

### Task 2: Replace Generic Expert Schema with Template-Slot Contracts

**Files:**
- Modify: `tests/skill_validation/test_create_technical_solution_contracts.py`
- Modify: `skills/create-technical-solution/references/solution-process.md`

- [ ] **Step 1: Write the failing solution-process test**

```python
def test_solution_process_requires_template_slot_artifacts(self) -> None:
    require_snippets_in_order(
        self,
        self.sources["solution_process"],
        (
            "## 3. 模板任务单",
            "`槽位标识`",
            "`每位专家必答问题`",
            "## 4. 专家按模板逐槽位分析",
            "`是否参与该槽位`",
            "`建议写法或建议内容`",
            "## 5. 按模板逐槽位协作收敛",
            "`共同结论`",
            "`未采纳理由`",
        ),
    )


def test_solution_process_forbids_generic_expert_shells(self) -> None:
    require_snippets_in_order(
        self,
        self.sources["solution_process"],
        (
            "专家不能再以 `设计目标`、`关键约束`、`主要风险`、`关键权衡` 等通用标题组织自己的主结构。",
            "只能围绕模板已有槽位回答。",
            "如果某个槽位与该专家无关，应明确标记无贡献，而不是自由发挥到别的结构里。",
        ),
    )
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_solution_process_requires_template_slot_artifacts tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_solution_process_forbids_generic_expert_shells -v`
Expected: FAIL because `solution-process.md` still defines the old template-agnostic expert and convergence schema

- [ ] **Step 3: Rewrite the canonical process document around template slots**

Replace the current expert/convergence sections in `skills/create-technical-solution/references/solution-process.md` with this content:

```md
## 2. 文档职责与共享展示规则

本文件补充 `skills/create-technical-solution/SKILL.md`，只展开产出细则，不定义顶层执行顺序，也不替代主 skill 的权威入口角色。本文负责：

- `模板任务单` 的 canonical schema
- `专家按模板逐槽位分析` 的 canonical schema
- `按模板逐槽位协作收敛` 的 canonical schema
- 最低语义义务与完整质量门槛
- 阶段回退或重新进入时必须保留的产物字段要求

适用于全部用户可见产物的共享规则如下：

- `模板任务单`、`专家产物`、`协作收敛纪要`、`变更影响说明` 都必须先补齐本文件要求的必填字段，再对用户展示。
- 所有用户可见产物都必须保持当前模板顺序，不得改写成模板外的统一标题结构。
- 长内容都采用摘要优先的展示组织方式，先给稳定结论，再补充支撑细节。

## 3. 模板任务单

`模板任务单` 是整条链路的 canonical planning artifact。它不是新的正文模板，也不是最终文档草稿；它只把当前模板拆成后续可执行的槽位任务。

推荐格式如下：

```markdown
## 模板任务单

### [槽位顺序]. [槽位标识]

- `槽位语义`：[这个槽位在当前模板里承载什么]
- `可填写边界`：[允许写什么，不允许写什么]
- `参与专家`：[系统架构师, 安全架构师]
- `每位专家必答问题`：
  - `系统架构师`：[该专家在这个槽位必须回答什么]
  - `安全架构师`：[该专家在这个槽位必须回答什么]
- `禁止越界项`：[该槽位不能偷偷承担的内容]
- `依赖槽位`：[和哪些槽位有前后依赖或一致性关系]
- `缺口或阻塞项`：[当前无法合法填写、需要停机补问的信息]
```

要求：

- 必须严格沿用当前模板的原始顺序。
- 用户提出的“专家罗盘”内嵌在 `每位专家必答问题` 中，不单独长出模板外层级。
- 任何槽位如果没有足够语义支撑，必须标记为阻塞并停止后续自动成稿。

## 4. 专家按模板逐槽位分析

每位专家只接收 `范围冻结` 和 `模板任务单`，并且必须按模板槽位顺序输出。专家不能再以 `设计目标`、`关键约束`、`主要风险`、`关键权衡` 等通用标题组织自己的主结构。只能围绕模板已有槽位回答。

推荐格式如下：

```markdown
### [参与成员名称] - [角色头衔]

#### [槽位顺序]. [槽位标识]

- `是否参与该槽位`：[是 / 否]
- `建议写法或建议内容`：[该专家建议写进这个槽位的内容]
- `支撑理由`：[为什么这样写]
- `与其他槽位的依赖或冲突`：[需要和哪些槽位一起看]
- `仍需补证的信息`：[缺什么信息才能稳定落笔]
```

要求：

- 如果某个槽位与该专家无关，应明确标记无贡献，而不是自由发挥到别的结构里。
- 专家阶段只做本角色判断，不提前替其他角色收敛。
- 如发现某个必要信息没有模板内合法落点，必须标记阻塞并停止继续补写。

## 5. 按模板逐槽位协作收敛

全部专家输入完成后，必须按模板槽位顺序收敛，而不是退回模板外的统一纪要结构。

推荐格式如下：

```markdown
## 协作收敛

### [槽位顺序]. [槽位标识]

- `共同结论`：[团队一致认可的写法]
- `分歧点`：[仍然存在的争议]
- `选定写法`：[最终采用的槽位内容]
- `未采纳理由`：[为什么不采用其他写法]
- `仍待决策`：[还缺什么信息、由谁补齐]
```

要求：

- 被否决写法和未采纳理由必须保留。
- 如果该槽位语义不承载某项元数据，明确写“不适用”，而不是硬塞内容。
- 协作收敛完成后才能进入最终成稿。
```

- [ ] **Step 4: Update rollback and minimum-semantic sections to match the new pipeline**

Change the rollback section and the standard-information-block introduction in `skills/create-technical-solution/references/solution-process.md` to this wording:

```md
### 最近受影响的阶段边界

- 如果变化只影响最终模板落位，不改变槽位语义、专家供给和收敛结论，则最近受影响的阶段边界为最终成稿阶段。
- 如果变化影响单个或多个槽位的共同结论、选定写法、未采纳理由或仍待决策，则最近受影响的阶段边界为按模板逐槽位协作收敛阶段。
- 如果变化影响某个槽位下专家是否参与、建议写法、支撑理由或补证需求，则最近受影响的阶段边界为专家按模板逐槽位分析阶段。
- 如果变化影响模板结构、槽位语义、参与成员分配、每位专家必答问题或禁止越界项，则最近受影响的阶段边界为模板任务单阶段。

## 6. 最低语义义务

虽然中间产物不再按模板外的“标准信息块”组织，但最终技术方案正文仍必须覆盖以下最低语义义务。这些义务是语义检查清单，不是新的中间结构，也不是允许脱离当前模板单独展开的章节体系。
```

- [ ] **Step 5: Run the focused tests to verify they pass**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_solution_process_requires_template_slot_artifacts tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_solution_process_forbids_generic_expert_shells -v`
Expected: PASS

- [ ] **Step 6: Commit the process-contract slice**

```bash
git add tests/skill_validation/test_create_technical_solution_contracts.py skills/create-technical-solution/references/solution-process.md
git commit -m "feat(skill): make solution process template-slot based"
```

### Task 3: Align Template Adaptation and Progress Transparency with the New Chain

**Files:**
- Modify: `tests/skill_validation/helpers.py`
- Modify: `tests/skill_validation/test_create_technical_solution_contracts.py`
- Modify: `skills/create-technical-solution/references/template-adaptation.md`
- Modify: `skills/create-technical-solution/references/progress-transparency.md`

- [ ] **Step 1: Write the failing cross-reference test**

```python
def test_template_chain_is_locked_in_adaptation_and_progress_docs(self) -> None:
    require_snippets_in_order(
        self,
        self.sources["template_adaptation"],
        (
            "当前 `.architecture/templates/technical-solution-template.md` 是唯一正文骨架来源。",
            "当前模板不仅是最终正文骨架，也是整条分析链唯一的信息架构。",
            "不允许在任何阶段引入模板外的章节层级。",
            "如果某个必要信息在当前模板内没有合法落点，应停止并向用户确认。",
        ),
    )
    require_snippets_in_order(
        self,
        self.sources["progress_transparency"],
        (
            "模板任务单阶段",
            "专家按模板逐槽位分析阶段",
            "按 `references/solution-process.md` 的模板逐槽位字段顺序展示",
            "按模板逐槽位协作收敛阶段",
            "模板发生变化时，至少回退到 `模板任务单`。",
        ),
    )
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_template_chain_is_locked_in_adaptation_and_progress_docs -v`
Expected: FAIL with `KeyError: 'progress_transparency'` or missing-snippet assertions

- [ ] **Step 3: Expose the progress-transparency source to the test loader**

Update `tests/skill_validation/helpers.py` like this:

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
        "analysis_guide": read_repo_text(
            "skills/create-technical-solution/references/solution-analysis-guide.md"
        ),
    }
```

- [ ] **Step 4: Strengthen template-adaptation and transparency docs**

Apply these edits:

```md
# skills/create-technical-solution/references/template-adaptation.md

## 基本原则

- 当前 `.architecture/templates/technical-solution-template.md` 是唯一正文骨架来源。
- 当前生效模板可能是默认模板，也可能是用户替换后的自定义模板。
- 当前模板不仅是最终正文骨架，也是整条分析链唯一的信息架构。
- 先理解当前模板的语义和层级，再决定信息块落位。
- 不允许在任何阶段引入模板外的章节层级。
- 不允许新增用户模板没有定义的一级章节。
- 如果某个必要信息在当前模板内没有合法落点，应停止并向用户确认。
```

```md
# skills/create-technical-solution/references/progress-transparency.md

## 2. 阶段边界

阶段性播报只在以下阶段边界触发：

1. 模板任务单阶段：当前模板的槽位语义、参与专家、必答问题和阻塞项稳定后，才允许进入专家分析。
2. 专家按模板逐槽位分析阶段：单个专家补齐当前模板槽位的必填分析后，立即展示该专家的 `专家产物`。
3. 按模板逐槽位协作收敛阶段：全部专家输入完成后，统一展示一份按模板槽位组织的 `协作收敛纪要`。
4. 严格模板成稿阶段：用户看过收敛结果后，再把已收敛内容填写回当前模板已有位置。

### 失效处理

- 如果模板发生变化时，至少回退到 `模板任务单`。
- 如果变化影响槽位下的专家判断，则回到相应专家产物阶段。
- 如果变化影响槽位收敛结论，则至少回到协作收敛阶段。

## 3. 专家产物

### 专家产物：展示契约

`专家产物` 是对 `references/solution-process.md` 中“专家按模板逐槽位分析”的对话内展示包装。字段级定义、必填项和内容约束以 `references/solution-process.md` 为准；本文件只定义用户可见形态和展示时机。

对用户展示时，至少应包含：

- 专家身份：专家名称与角色头衔
- 结构化主体：按 `references/solution-process.md` 的模板逐槽位字段顺序展示

## 4. 协作收敛纪要

`协作收敛纪要` 是 `references/solution-process.md` 中“按模板逐槽位协作收敛”结构的对话内展示形态。

- 收敛主体：按 `references/solution-process.md` 的模板逐槽位字段顺序渲染
- 被否决写法和未采纳理由必须显式保留
```

- [ ] **Step 5: Run the focused test to verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_template_chain_is_locked_in_adaptation_and_progress_docs -v`
Expected: PASS

- [ ] **Step 6: Commit the supporting-contract slice**

```bash
git add tests/skill_validation/helpers.py tests/skill_validation/test_create_technical_solution_contracts.py skills/create-technical-solution/references/template-adaptation.md skills/create-technical-solution/references/progress-transparency.md
git commit -m "feat(skill): align template and progress contracts"
```

### Task 4: Run the Full Contract Suite and Clean Up Wording Drift

**Files:**
- Modify: `tests/skill_validation/test_create_technical_solution_contracts.py`
- Modify: `skills/create-technical-solution/SKILL.md`
- Modify: `skills/create-technical-solution/references/solution-process.md`
- Modify: `skills/create-technical-solution/references/template-adaptation.md`
- Modify: `skills/create-technical-solution/references/progress-transparency.md`

- [ ] **Step 1: Add the final zero-new-content regression test**

```python
def test_contracts_require_zero_new_visible_content_and_safe_stop(self) -> None:
    require_snippets_in_order(
        self,
        self.sources["main"],
        (
            "最终只把已收敛内容写回当前模板已有位置。",
            "缺少语义前置、无法展示稳定中间产物或无法安全落位时停止并确认。",
        ),
    )
    require_snippets_in_order(
        self,
        self.sources["template_adaptation"],
        (
            "不允许在任何阶段引入模板外的章节层级。",
            "不允许新增用户模板没有定义的一级章节。",
            "如果某个必要信息在当前模板内没有合法落点，应停止并向用户确认。",
        ),
    )
```

- [ ] **Step 2: Run the full contract test file to verify remaining gaps**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts -v`
Expected: FAIL only if wording drift remains in the edited docs

- [ ] **Step 3: Fix any wording drift by normalizing the final docs**

Ensure these exact phrases exist after the final edit pass:

```md
# skills/create-technical-solution/SKILL.md
- 最终只把已收敛内容写回当前模板已有位置。
- 缺少语义前置、无法展示稳定中间产物或无法安全落位时停止并确认。

# skills/create-technical-solution/references/solution-process.md
- 任何槽位如果没有足够语义支撑，必须标记为阻塞并停止后续自动成稿。
- 如果某个槽位与该专家无关，应明确标记无贡献，而不是自由发挥到别的结构里。

# skills/create-technical-solution/references/template-adaptation.md
- 不允许在任何阶段引入模板外的章节层级。
- 如果某个必要信息在当前模板内没有合法落点，应停止并向用户确认。

# skills/create-technical-solution/references/progress-transparency.md
- 模板发生变化时，至少回退到 `模板任务单`。
```

- [ ] **Step 4: Run the full validation and whitespace checks**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts -v`
Expected: PASS with all create-solution contract tests green

Run: `git diff --check`
Expected: no output

- [ ] **Step 5: Commit the final validation pass**

```bash
git add tests/skill_validation/test_create_technical_solution_contracts.py skills/create-technical-solution/SKILL.md skills/create-technical-solution/references/solution-process.md skills/create-technical-solution/references/template-adaptation.md skills/create-technical-solution/references/progress-transparency.md tests/skill_validation/helpers.py
git commit -m "test: lock create solution template-only contracts"
```
