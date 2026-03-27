# Host Project Principles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shift `setup-architect` from a generic `principles.md` starter to a host-project judgment baseline that directly supports technical-solution writing and review.

**Architecture:** Extend the existing setup-architect contract tests first, then rewrite the principles template and customization guide to use the approved seven-section host-project structure plus principle mapping. Keep the main `setup-architect` flow stable; only tighten its wording so `.architecture/principles.md` is framed as a required project-context baseline for later solution work.

**Tech Stack:** Markdown, Python 3 standard library (`unittest`, `pathlib`), repository skill docs

---

## File Structure

- Modify: `tests/skill_validation/helpers.py` - expose `skills/setup-architect/templates/principles-template.md` to setup-architect contract tests.
- Modify: `tests/skill_validation/test_setup_architect_contracts.py` - add regression tests for the new host-project template structure and guidance wording.
- Modify: `skills/setup-architect/templates/principles-template.md` - replace the quote-heavy generic template plus HTML-comment customization block with the approved seven-section host-project baseline template and `原则映射表`.
- Modify: `skills/setup-architect/references/principles-customization.md` - replace the HTML-comment copy workflow with chapter-based host-project editing guidance.
- Modify: `skills/setup-architect/SKILL.md` - minimally reword the principles step so it positions `.architecture/principles.md` as a required judgment baseline.
- Read: `docs/superpowers/specs/2026-03-27-host-project-principles-design.md`
- Read: `skills/setup-architect/templates/principles-template.md`
- Read: `skills/setup-architect/references/principles-customization.md`
- Read: `tests/skill_validation/helpers.py`
- Read: `tests/skill_validation/test_setup_architect_contracts.py`

### Task 1: Lock the Host-Project Template Contract

**Files:**
- Modify: `tests/skill_validation/helpers.py`
- Modify: `tests/skill_validation/test_setup_architect_contracts.py`
- Modify: `skills/setup-architect/templates/principles-template.md`

- [ ] **Step 1: Write the failing template contract tests**

```python
from tests.skill_validation.helpers import (
    load_setup_contract_sources,
    require_all_snippets,
    top_level_headings,
)


class SetupArchitectContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_setup_contract_sources()

    def test_principles_template_uses_host_project_baseline_sections(self) -> None:
        self.assertEqual(
            top_level_headings(self.sources["principles_template"]),
            [
                "文档目的与使用方式",
                "业务域与项目语义",
                "模块边界与依赖方向",
                "数据、接口与事件边界",
                "质量属性与治理底线",
                "当前必须尊重的项目现实",
                "方案编写与评审准绳",
                "原则映射表",
            ],
        )

    def test_principles_template_embeds_inline_host_project_guidance_and_mapping(self) -> None:
        template = self.sources["principles_template"]
        require_all_snippets(
            self,
            template,
            (
                "本文档用于为后续技术方案编写与评审提供项目上下文和判断基线。",
                "### 本项目事实",
                "### 为什么重要",
                "### 对方案与评审的要求",
                "核心原则必须保留，但要翻译成当前项目里的具体判断规则。",
                "| 核心原则 | 主要落点章节 | 本项目中的约束含义 |",
            ),
        )
        self.assertNotIn("复制下方模板，在上方合适位置新增项目特定原则", template)
```

- [ ] **Step 2: Run the setup contract test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_setup_architect_contracts -v`
Expected: FAIL with `KeyError: 'principles_template'`

- [ ] **Step 3: Write the minimal helper change and rewrite the principles template**

```python
# tests/skill_validation/helpers.py

def load_setup_contract_sources() -> dict[str, str]:
    return {
        "main": read_repo_text("skills/setup-architect/SKILL.md"),
        "installation": read_repo_text(
            "skills/setup-architect/references/installation-procedures.md"
        ),
        "member_customization": read_repo_text(
            "skills/setup-architect/references/member-customization.md"
        ),
        "principles_customization": read_repo_text(
            "skills/setup-architect/references/principles-customization.md"
        ),
        "principles_template": read_repo_text(
            "skills/setup-architect/templates/principles-template.md"
        ),
        "template_customization": read_repo_text(
            "skills/setup-architect/references/technical-solution-template-customization.md"
        ),
    }
```

```md
# 架构原则

本文档用于为后续技术方案编写与评审提供项目上下文和判断基线。
只记录会影响方案选型、边界判断、风险识别和评审结论的项目事实与规则；不要把它写成 README、系统清单或运维手册。
核心原则必须保留，但要翻译成当前项目里的具体判断规则。

## 文档目的与使用方式

**相关原则**：宜居代码、清晰优于炫技

### 本项目事实
- 用 2-4 条规则写清本文档服务于谁，以及哪些方案决策和评审场景必须参考本文档。
- 写清本文档沉淀的是长期稳定的判断基线，不是高频变化的实现细节。
- 写清本文档与 README、ADR、运行手册的边界，避免职责重叠。

### 为什么重要
- 解释为什么后续技术方案必须先理解项目语义、边界和约束，再讨论实现细节。
- 解释为什么判断基线缺失会导致方案选型、评审尺度或实施计划漂移。

### 对方案与评审的要求
- 明确哪些类型的方案必须引用本文档中的边界、底线和现实约束。
- 明确评审时优先判断“是否符合项目基线”，而不是“是否抽象上看起来合理”。

## 业务域与项目语义

**相关原则**：领域中心设计

### 本项目事实
- 列出项目的核心业务域、支撑域和关键术语，只保留会影响设计判断的内容。
- 写清统一语言里最容易被误解的概念，以及它们在当前项目中的精确定义。

### 为什么重要
- 解释错误的领域划分会怎样误导模块拆分、接口设计和职责归属。

### 对方案与评审的要求
- 新方案必须先说明自己落在哪个业务域，复用或扩展了哪些现有概念。
- 不允许只按技术层或框架层命名能力，却回避业务语义和责任边界。

## 模块边界与依赖方向

**相关原则**：宜居代码、清晰优于炫技、关注点分离

### 本项目事实
- 列出关键模块、子系统或目录的职责边界。
- 写清允许的依赖方向、禁止的反向依赖，以及必须通过接口隔离的跨边界协作。
- 标出当前已经过载或风险较高的模块，避免新方案继续堆责。

### 为什么重要
- 解释边界不清会如何放大耦合、增加认知负担并降低可维护性。

### 对方案与评审的要求
- 新增能力优先落在既有边界内，只有当现有边界已被证明失效时才允许新建边界。
- 新抽象必须说明比直接复用现有结构多解决了什么问题。
- 禁止把领域逻辑、接口编排、存储细节和跨系统集成塞进同一个模块。

## 数据、接口与事件边界

**相关原则**：关注点分离、可演化性

### 本项目事实
- 写清关键数据模型、对外接口、内部事件和跨系统契约的边界。
- 写清兼容性要求、版本策略、幂等约束和必须保留的历史包袱。

### 为什么重要
- 解释为什么接口和数据边界往往决定迁移成本、联调风险和发布顺序。

### 对方案与评审的要求
- 方案必须说明新增或变更的数据、接口、事件会影响哪些消费者。
- 方案必须说明兼容策略、迁移路径、灰度方式和回滚条件。
- 禁止把跨边界契约变化隐藏在“内部改造”表述里。

## 质量属性与治理底线

**相关原则**：可演化性、可观测性、设计即安全

### 本项目事实
- 写清性能、可靠性、可观测性、安全、合规、测试和发布的最低要求。
- 写清关键链路必须具备的日志、指标、追踪、审计或告警能力。

### 为什么重要
- 解释哪些治理底线一旦缺失，会让方案即使功能正确也无法上线或无法稳定运行。

### 对方案与评审的要求
- 方案必须说明验证方式、监控补齐、失败处理、权限控制和敏感数据保护。
- 禁止把观测、安全或验证要求留到“上线前再补”。

## 当前必须尊重的项目现实

**相关原则**：务实的简洁性、变更影响意识

### 本项目事实
- 写清当前遗留模块、迁移阶段、组织边界、上线窗口或外部依赖等现实约束。
- 写清哪些问题已知存在但短期不能一次性解决。

### 为什么重要
- 解释为什么忽略这些现实会让方案变成理想化终态，而不是可落地路径。

### 对方案与评审的要求
- 方案必须说明自己尊重了哪些现实约束，以及哪些问题被刻意延后。
- 方案必须显式说明影响范围、可逆性、协作成本和失败半径。

## 方案编写与评审准绳

**相关原则**：清晰优于炫技、变更影响意识

### 本项目事实
- 写清本项目判断技术方案是否合格时最看重的决策标准。
- 写清哪些风险或缺项会直接导致方案退回重写或补证据。

### 为什么重要
- 解释为什么统一的方案准绳能减少评审分歧和返工。

### 对方案与评审的要求
- 方案必须写清目标、非目标、影响边界、依赖变化、验证策略和回滚策略。
- 评审必须区分“已证实问题”“待核验风险”和“超出当前范围的建议”。
- 禁止用抽象价值判断替代基于项目边界和代码现实的结论。

## 原则映射表

| 核心原则 | 主要落点章节 | 本项目中的约束含义 |
| --- | --- | --- |
| 宜居代码 | 文档目的与使用方式；模块边界与依赖方向 | 优先降低认知负担，避免继续把职责堆进已过载模块。 |
| 清晰优于炫技 | 模块边界与依赖方向；方案编写与评审准绳 | 优先选择边界清晰、易解释的方案，新增抽象必须自证收益。 |
| 关注点分离 | 模块边界与依赖方向；数据、接口与事件边界 | 领域、接口、存储、集成职责必须分层，不允许跨层偷塞。 |
| 可演化性 | 数据、接口与事件边界；质量属性与治理底线 | 方案必须交代兼容、迁移、灰度和回滚。 |
| 可观测性 | 质量属性与治理底线 | 关键链路必须可监控、可追踪、可审计。 |
| 设计即安全 | 质量属性与治理底线 | 权限、敏感数据和合规约束必须进入方案正文，不能后补。 |
| 领域中心设计 | 业务域与项目语义 | 先解释业务语义和责任边界，再讨论技术拆分。 |
| 务实的简洁性 | 当前必须尊重的项目现实 | 方案必须尊重遗留约束和阶段性禁区，不写理想化终态。 |
| 变更影响意识 | 当前必须尊重的项目现实；方案编写与评审准绳 | 每个方案都要说明影响范围、可逆性、协作成本和失败半径。 |
```

- [ ] **Step 4: Run the setup contract test and verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_setup_architect_contracts -v`
Expected: PASS with 10 tests passing

- [ ] **Step 5: Commit the template contract slice**

```bash
git add tests/skill_validation/helpers.py tests/skill_validation/test_setup_architect_contracts.py skills/setup-architect/templates/principles-template.md
git commit -m 'test: lock host project principles template contract'
```

### Task 2: Align Customization Guidance and Main Skill Wording

**Files:**
- Modify: `tests/skill_validation/test_setup_architect_contracts.py`
- Modify: `skills/setup-architect/references/principles-customization.md`
- Modify: `skills/setup-architect/SKILL.md`

- [ ] **Step 1: Write the failing guidance and main-skill tests**

```python
from tests.skill_validation.helpers import (
    load_setup_contract_sources,
    require_all_snippets,
    require_snippets_in_order,
    top_level_headings,
)


class SetupArchitectContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_setup_contract_sources()

    def test_principles_customization_requires_host_project_baseline_rules(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["principles_customization"],
            (
                "`.architecture/principles.md` 的主要作用，是为宿主项目后续的技术方案编写与架构评审提供项目上下文和判断基线。",
                "按七个主章节填写宿主项目事实、边界、底线和当前现实。",
                "核心原则必须保留，但必须翻译成宿主项目语境下的判断规则。",
                "只保留会影响技术方案和评审判断的内容。",
                "不要写成 README、系统清单、接口总表或运维手册。",
            ),
        )

    def test_main_skill_positions_principles_as_required_judgment_baseline(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "### 4. 定制架构原则",
                "按 [references/principles-customization.md](references/principles-customization.md) 把 `.architecture/principles.md` 定制成宿主项目的上下文和判断基线；",
                "后续技术方案编写与架构评审会将这些原则作为必需输入。",
            ),
        )
```

- [ ] **Step 2: Run the setup contract test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_setup_architect_contracts -v`
Expected: FAIL with `AssertionError` because the customization guide and main skill still use the old wording

- [ ] **Step 3: Rewrite the customization guide and tighten the main skill wording**

```md
# 定制架构原则

`.architecture/principles.md` 的主要作用，是为宿主项目后续的技术方案编写与架构评审提供项目上下文和判断基线。

## 编辑目标

- 保留项目的稳定基线：业务语义、模块边界、依赖方向、接口约束、治理底线和决策标准。
- 补充当前必须被方案尊重的最小现实：遗留约束、迁移阶段、组织边界和短期不可突破的限制。
- 只保留会影响技术方案和评审判断的内容。

## 编辑步骤

1. 先复制 [../templates/principles-template.md](../templates/principles-template.md) 初始化 `.architecture/principles.md`。
2. 按七个主章节填写宿主项目事实、边界、底线和当前现实。
3. 在每个章节里分别写清“本项目事实”“为什么重要”“对方案与评审的要求”。
4. 在文末补全 `原则映射表`，说明每条核心原则在当前项目中的落点和约束含义。

## 写作规则

- 核心原则必须保留，但必须翻译成宿主项目语境下的判断规则。
- 同时覆盖稳定基线和最小必要的当前现实，不要只写其中一类。
- 多用 `必须`、`优先`、`禁止`、`仅在……时允许` 这类明确规则句。
- 只保留会影响技术方案和评审判断的内容。

## 最低覆盖范围

- 模块边界与依赖方向
- API / 事件 / 数据边界
- 测试和验证基线
- 安全与合规底线
- 技术方案和实施计划的决策标准

## 不该写什么

- 不要写成 README、系统清单、接口总表或运维手册。
- 不要罗列高频变动的临时事实。
- 不要只保留抽象价值观，却不写它们在当前项目里的具体约束。

## 核心原则（保留这些）

- **宜居代码**：围绕长期维护和开发体验设计代码库。
- **清晰优于炫技**：优先选择简单清晰的设计。
- **关注点分离**：明确组件职责边界和依赖关系。
- **可演化性**：支持系统随时间安全演进。
- **可观测性**：为运行行为、性能和状态提供可见性。
- **设计即安全**：将安全作为架构内建约束。
- **领域中心设计**：让架构反映并服务于问题领域。
- **务实的简洁性**：优先选择实用、可工作的方案。
- **变更影响意识**：在决策前显式评估影响范围、可逆性和时机。
```

```md
### 4. 定制架构原则

按 [references/principles-customization.md](references/principles-customization.md) 把 `.architecture/principles.md` 定制成宿主项目的上下文和判断基线；后续技术方案编写与架构评审会将这些原则作为必需输入。
```

- [ ] **Step 4: Run the setup contract test and verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_setup_architect_contracts -v`
Expected: PASS with 12 tests passing

- [ ] **Step 5: Commit the guidance slice**

```bash
git add tests/skill_validation/test_setup_architect_contracts.py skills/setup-architect/references/principles-customization.md skills/setup-architect/SKILL.md
git commit -m 'docs: align setup architect principles baseline'
```

### Task 3: Run Final Validation and Diff Checks

**Files:**
- Test: `tests/skill_validation/test_setup_architect_contracts.py`
- Test: `tests/skill_validation/`

- [ ] **Step 1: Run the whitespace and patch safety check**

Run: `git diff --check`
Expected: no output

- [ ] **Step 2: Re-run the targeted setup contract test**

Run: `python3 -m unittest tests.skill_validation.test_setup_architect_contracts -v`
Expected: PASS with 12 tests passing

- [ ] **Step 3: Run the full skill-validation suite**

Run: `python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v`
Expected: PASS with 47 tests passing
