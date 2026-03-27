# Review Technical Solution Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `review-technical-solution` as a first-class repository skill, plus validation coverage that enforces its hard-stop behavior, code-evidence requirements, and fixed review-report contract.

**Architecture:** Implement the feature as one short main `SKILL.md` plus three focused reference docs, then extend the existing Python `unittest` validation harness to install, inspect, and regression-test the new skill alongside the two existing ones. Keep the validation strategy aligned with the approved design: hard-stop missing context early, classify by solution type, and enforce structured output through contract tests, catalog coverage, and runbook updates.

**Tech Stack:** Markdown, Python 3 standard library (`unittest`, `pathlib`), GitHub Actions YAML, repository skill docs

---

## File Structure

- Create: `skills/review-technical-solution/SKILL.md` - main skill entry with Chinese body, English discovery description, hard-stop rules, and fixed output order.
- Create: `skills/review-technical-solution/references/review-process.md` - generic review flow, claim extraction, code-evidence states, severity rules, and final conclusion rules.
- Create: `skills/review-technical-solution/references/review-analysis-guide.md` - category-specific review matrix for the five approved solution types.
- Create: `skills/review-technical-solution/references/review-output-contract.md` - fixed report structure, allowed conclusion values, issue fields, and `待核验风险` usage rules.
- Create: `tests/skill_validation/test_review_technical_solution_contracts.py` - contract assertions for the new skill and its reference docs.
- Modify: `tests/skill_validation/helpers.py` - load the new skill sources for contract tests and include the new skill in assistant-target installation layout.
- Modify: `tests/skill_validation/test_static_layout.py` - assert bootstrapped assistant targets install the new skill.
- Modify: `.github/workflows/skills-integration-tests.yml` - expect `review-technical-solution` in installed skill lists and verify its reference docs exist.
- Modify: `tests/skill_validation/case_catalog.py` - add `RTS-*` cases and phase membership for the new review skill.
- Modify: `tests/skill_validation/test_case_catalog.py` - lock updated case counts, IDs, and phase order.
- Modify: `docs/superpowers/testing/skill-validation.md` - extend the runbook scope, layer examples, and phase rollout with `RTS-*` cases.
- Modify: `tests/skill_validation/test_workflow_integration.py` - assert the runbook and workflow stay aligned with the expanded review-skill catalog.
- Read: `docs/superpowers/specs/2026-03-27-review-technical-solution-design.md` - approved design to cover completely.
- Read: `skills/create-technical-solution/SKILL.md` - existing repository pattern for a main skill plus reference docs.
- Read: `tests/skill_validation/case_catalog.py`
- Read: `tests/skill_validation/helpers.py`
- Read: `tests/skill_validation/test_create_technical_solution_contracts.py`
- Read: `tests/skill_validation/test_case_catalog.py`
- Read: `tests/skill_validation/test_static_layout.py`
- Read: `tests/skill_validation/test_workflow_integration.py`

### Task 1: Lock the Main Skill Entry Contract

**Files:**
- Create: `skills/review-technical-solution/SKILL.md`
- Create: `tests/skill_validation/test_review_technical_solution_contracts.py`
- Modify: `tests/skill_validation/helpers.py`

- [ ] **Step 1: Write the failing main-contract test**

```python
import unittest

from tests.skill_validation.helpers import (
    load_review_solution_contract_sources,
    require_snippets_in_order,
)


class ReviewTechnicalSolutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_review_solution_contract_sources()

    def test_frontmatter_uses_searchable_name_and_description(self) -> None:
        main = self.sources['main']
        self.assertIn('name: review-technical-solution', main)
        self.assertIn(
            'description: Use when reviewing a technical solution against requirement details, architecture principles, and existing project code',
            main,
        )

    def test_main_skill_requires_four_inputs_and_blocks_missing_context(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['main'],
            (
                '- `需求详情`',
                '- `技术方案文档`',
                '- `.architecture/principles.md`',
                '- `相关项目代码`',
                '任一缺失时，不做正式结论，直接输出 `无法开展正式评审`。',
            ),
        )

    def test_main_skill_requires_code_evidence_and_fixed_output_order(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['main'],
            (
                '不能因为用户催促、方案写得完整，或“看起来合理”就跳过代码核验。',
                '`待核验风险`',
                '1. `评审结论`',
                '2. `阻断项`',
                '3. `主要问题`',
                '4. `改进方案`',
                '5. `待补充信息`',
                '6. `建议验证`',
            ),
        )


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run the new contract test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_review_technical_solution_contracts -v`
Expected: FAIL with `ImportError: cannot import name 'load_review_solution_contract_sources'`

- [ ] **Step 3: Write the minimal helper and main skill file**

```python
# tests/skill_validation/helpers.py

def load_review_solution_contract_sources() -> dict[str, str]:
    return {
        'main': read_repo_text('skills/review-technical-solution/SKILL.md'),
    }
```

```md
---
name: review-technical-solution
description: Use when reviewing a technical solution against requirement details, architecture principles, and existing project code, especially when missing context, unverified assumptions, implementation-fit risks, or code-reality mismatches could invalidate the proposal.
---

# 技术方案评审

按需求详情、技术方案文档、`.architecture/principles.md` 和项目现有代码做正式评审。主技能文件只定义职责边界、停机规则、固定输出和红旗信号；详细流程、分类重点与输出契约分别见引用文档。

## 技能定位

- 只在需要正式评审技术方案时使用；如果用户要创建、补写或更新方案正文，转到 `create-technical-solution`。
- 正式评审依赖四类证据源：
  - `需求详情`
  - `技术方案文档`
  - `.architecture/principles.md`
  - `相关项目代码`
- 必须先看需求、再看方案、再看原则、再看代码；不能只读文档表面后直接下结论。
- 主 skill 负责唯一主路径、硬性阻断、固定输出、红旗信号和完成标准；引用文档负责完整细则。

## 必要上下文

正式评审前必须确认以下输入齐全且可读：
- `需求详情`
- `技术方案文档`
- `.architecture/principles.md`
- `相关项目代码`

任一缺失时，不做正式结论，直接输出 `无法开展正式评审`，并明确：
- 缺了什么
- 为什么这会阻断正式评审
- 需要补什么后再继续

## 高层工作流

### 1. 校验输入完整性

缺少必要上下文时立即停止，不输出 `通过`、`需修改` 或 `阻断`。

### 2. 判断方案类型

按 [references/review-analysis-guide.md](references/review-analysis-guide.md) 判断主分类与附加分类。

### 3. 提取核心主张

从需求与方案中提取目标、非目标、约束、复用能力、变更边界、接口、数据结构、测试与发布策略。

### 4. 代码取证

按 [references/review-process.md](references/review-process.md) 在相关项目代码中核验核心主张是否成立、边界是否匹配、依赖是否存在。不能因为用户催促、方案写得完整，或“看起来合理”就跳过代码核验。

### 5. 归因与分级

按需求对齐、架构对齐、代码现状对齐、完整性、可落地性归因问题，并基于证据与影响分级。

### 6. 生成改进方案

每个重要问题都要给出可执行的改进方向与验证动作。

### 7. 固定输出

正式输出必须按以下顺序展开：
1. `评审结论`
2. `阻断项`
3. `主要问题`
4. `改进方案`
5. `待补充信息`
6. `建议验证`

## 硬性规则

- 任一必要输入缺失时，不做正式结论，直接输出 `无法开展正式评审`。
- 所有已确认问题都必须给出证据，证据只能来自需求详情、技术方案文档、`.architecture/principles.md`、项目代码 / 配置 / schema / 接口 / 测试。
- 证据不足时只能标记为 `待核验风险`，不能把猜测写成事实。
- 找不到方案声称复用的现有能力时，必须显式指出代码证据缺失或主张被代码证伪。
- 不能因为用户催促、时间紧、方案写得完整，或“先评再补代码”就降低评审标准。

## 红旗信号

出现以下说法时，停下来重新核验证据：
- ‘这个方案看起来合理，不用看代码了。’
- ‘用户赶时间，我先给个结论。’
- ‘先按经验评，代码之后再补。’
- ‘现有能力大概率有，先默认它存在。’
- ‘摘要差不多够了，不用看完整方案正文。’

## 详细说明

- [标准评审流程](references/review-process.md)
- [方案分类评审指引](references/review-analysis-guide.md)
- [固定输出契约](references/review-output-contract.md)
```

- [ ] **Step 4: Run the contract test and verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_review_technical_solution_contracts -v`
Expected: PASS with 3 tests passing

- [ ] **Step 5: Commit the entry contract slice**

```bash
git add skills/review-technical-solution/SKILL.md tests/skill_validation/helpers.py tests/skill_validation/test_review_technical_solution_contracts.py
git commit -m 'feat: add review technical solution entry contract'
```

### Task 2: Add Review Flow and Classification References

**Files:**
- Create: `skills/review-technical-solution/references/review-process.md`
- Create: `skills/review-technical-solution/references/review-analysis-guide.md`
- Modify: `tests/skill_validation/helpers.py`
- Modify: `tests/skill_validation/test_review_technical_solution_contracts.py`

- [ ] **Step 1: Extend the contract test so the missing references fail first**

```python
import unittest

from tests.skill_validation.helpers import (
    load_review_solution_contract_sources,
    require_snippets_in_order,
)


class ReviewTechnicalSolutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_review_solution_contract_sources()

    def test_frontmatter_uses_searchable_name_and_description(self) -> None:
        main = self.sources['main']
        self.assertIn('name: review-technical-solution', main)
        self.assertIn(
            'description: Use when reviewing a technical solution against requirement details, architecture principles, and existing project code',
            main,
        )

    def test_main_skill_requires_four_inputs_and_blocks_missing_context(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['main'],
            (
                '- `需求详情`',
                '- `技术方案文档`',
                '- `.architecture/principles.md`',
                '- `相关项目代码`',
                '任一缺失时，不做正式结论，直接输出 `无法开展正式评审`。',
            ),
        )

    def test_main_skill_requires_code_evidence_and_fixed_output_order(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['main'],
            (
                '不能因为用户催促、方案写得完整，或“看起来合理”就跳过代码核验。',
                '`待核验风险`',
                '1. `评审结论`',
                '2. `阻断项`',
                '3. `主要问题`',
                '4. `改进方案`',
                '5. `待补充信息`',
                '6. `建议验证`',
            ),
        )

    def test_review_process_defines_claim_extraction_and_evidence_states(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['review_process'],
            (
                '## 4. 主张提取',
                '至少提取以下信息：',
                '`claim_id`',
                '`statement`',
                '`expected_evidence`',
                '## 5. 代码取证',
                '`已证实`',
                '`已证伪`',
                '`待核验`',
            ),
        )

    def test_review_process_defines_severity_and_conclusion_rules(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['review_process'],
            (
                '## 7. 问题分级规则',
                '`blocker`',
                '`major`',
                '`minor`',
                '`note`',
                '## 8. 最终结论规则',
                '任何 `blocker` -> `阻断`',
                '缺少必要输入 -> `无法开展正式评审`',
            ),
        )

    def test_analysis_guide_covers_all_solution_types_and_union_behavior(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['analysis_guide'],
            (
                '1. 新功能方案',
                '2. 重构或替换方案',
                '3. 跨系统或平台能力方案',
                '4. 安全 / 合规 / 数据保护方案',
                '5. 性能 / 容量 / 成本优化方案',
                '评审问题取并集',
                '必查证据取并集',
                '最终结论按最高严重级别判定',
            ),
        )


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run the contract test to verify the missing references fail**

Run: `python3 -m unittest tests.skill_validation.test_review_technical_solution_contracts -v`
Expected: FAIL with `KeyError: 'review_process'` or `KeyError: 'analysis_guide'`

- [ ] **Step 3: Add the loader entries and both reference documents**

```python
# tests/skill_validation/helpers.py

def load_review_solution_contract_sources() -> dict[str, str]:
    return {
        'main': read_repo_text('skills/review-technical-solution/SKILL.md'),
        'review_process': read_repo_text(
            'skills/review-technical-solution/references/review-process.md'
        ),
        'analysis_guide': read_repo_text(
            'skills/review-technical-solution/references/review-analysis-guide.md'
        ),
    }
```

```md
# 技术方案评审流程参考

## 1. 文档定位

本文档定义正式评审的通用流程、证据状态、问题分级和结论规则，不重复主 skill 的适用场景与红旗信号。

## 2. 输入校验

正式评审前必须确认以下输入齐全：
- `需求详情`
- `技术方案文档`
- `.architecture/principles.md`
- `相关项目代码`

任一缺失时，直接输出 `无法开展正式评审`，明确缺失项、阻断原因和下一步需要补充的材料。

## 3. 方案分类与评审焦点确定

先根据方案的主要变化对象与最高风险来源判定主分类；命中多个分类时，检查点取并集并按高风险优先排序。

## 4. 主张提取

至少提取以下信息：
- 需求中的目标、非目标、约束、成功标准、不可破坏行为
- 方案中的核心设计决策、复用能力、受影响模块、接口、数据结构、测试与发布策略

主张记录至少包含：
- `claim_id`
- `statement`
- `assumption`
- `expected_evidence`
- `risk_if_wrong`

## 5. 代码取证

逐条在相关项目代码中核验主张，并把证据状态标记为：
- `已证实`
- `已证伪`
- `待核验`

重点核验：边界归属、依赖是否真实存在、接口和数据结构是否匹配、运行时约束是否被方案覆盖。

如果方案声称复用现有能力，必须在代码中定位到对应实现；找不到时不能默认它存在。

## 6. 评审维度判定

所有问题都要落在以下维度之一：
- `需求对齐`
- `架构对齐`
- `代码现状对齐`
- `完整性`
- `可落地性`

## 7. 问题分级规则

- `blocker`: 缺少必要输入、核心主张被代码证伪、关键依赖不存在、与原则文档明确冲突、缺少关键迁移 / 回滚 / 安全设计。
- `major`: 关键设计不完整、高风险假设未验证、与现有代码模式明显错位、测试或观测设计缺口较大。
- `minor`: 局部缺口或次要不一致。
- `note`: 优化建议或清晰度改进。

## 8. 最终结论规则

- 缺少必要输入 -> `无法开展正式评审`
- 任何 `blocker` -> `阻断`
- 无 `blocker` 但存在 `major` 或 `minor` -> `需修改`
- 只有关键主张已被证据支撑，且没有 `blocker` / `major` 时 -> `通过`

## 9. 改进建议规则

每个 `blocker` 和每个 `major` 都必须有对应的改进动作，并说明验证方式。

## 10. 输出前自检

- 是否检查了需求、方案、原则文档和代码
- 是否每个确认问题都有证据
- 是否每个 `待核验风险` 都说明了缺失证据和下一步核验动作
- 是否结论与问题分级一致
```

```md
# 技术方案评审分类指引

## 1. 文档定位

本文档只负责说明不同类型方案重点看什么、必须核实什么、哪些问题容易成为阻断项。

## 2. 分类判定原则

优先按方案的主要变化对象和最高风险来源判定主分类。

如果一个方案同时命中多个类别：
- 评审问题取并集
- 必查证据取并集
- 最终结论按最高严重级别判定
- 评审重点按风险高低排序

## 3. 五类方案

1. 新功能方案
2. 重构或替换方案
3. 跨系统或平台能力方案
4. 安全 / 合规 / 数据保护方案
5. 性能 / 容量 / 成本优化方案

## 4. 各类重点

### 新功能方案

- 必查问题：是否完整承接需求、是否放在正确边界、复用能力是否真实存在。
- 必查代码证据：现有模块职责、接口定义、数据结构、测试入口、发布开关。
- 常见阻断项：假设某能力存在但代码中不存在，或把能力放到错误模块。

### 重构或替换方案

- 必查问题：调用方是否识别完整、兼容策略是否清晰、迁移路径是否可逆。
- 必查代码证据：旧实现入口、依赖链、schema、feature flag、回滚能力。
- 常见阻断项：未识别关键调用方、没有回滚路径、数据迁移与现状不兼容。

### 跨系统或平台能力方案

- 必查问题：边界与 ownership 是否清晰、契约是否稳定、失败路径是否完整。
- 必查代码证据：API / 事件契约、幂等处理、补偿任务、监控与告警配置。
- 常见阻断项：只有主流程没有补偿与对账、跨系统上线顺序不成立。

### 安全 / 合规 / 数据保护方案

- 必查问题：权限边界是否正确、敏感数据处理是否闭环、审计是否可追溯。
- 必查代码证据：鉴权中间件、脱敏 / 加密实现、审计日志、数据清理任务。
- 常见阻断项：敏感数据暴露未受控、关键审计缺失、权限边界与代码不一致。

### 性能 / 容量 / 成本优化方案

- 必查问题：是否有基线、是否命中真实瓶颈、收益与副作用是否可验证。
- 必查代码证据：性能指标、热点 SQL / 接口 / 任务、缓存与并发控制、资源配置。
- 常见阻断项：没有基线数据、优化错对象、没有收益验证闭环。
```

- [ ] **Step 4: Run the expanded contract test and verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_review_technical_solution_contracts -v`
Expected: PASS with 6 tests passing

- [ ] **Step 5: Commit the flow and analysis references**

```bash
git add skills/review-technical-solution/references/review-process.md skills/review-technical-solution/references/review-analysis-guide.md tests/skill_validation/helpers.py tests/skill_validation/test_review_technical_solution_contracts.py
git commit -m 'feat: add review technical solution reference guides'
```

### Task 3: Add the Output Contract and Installation Wiring

**Files:**
- Create: `skills/review-technical-solution/references/review-output-contract.md`
- Modify: `tests/skill_validation/helpers.py`
- Modify: `tests/skill_validation/test_review_technical_solution_contracts.py`
- Modify: `tests/skill_validation/test_static_layout.py`
- Modify: `.github/workflows/skills-integration-tests.yml`

- [ ] **Step 1: Extend contract and layout tests so the missing output contract fails first**

```python
import unittest

from tests.skill_validation.helpers import (
    load_review_solution_contract_sources,
    require_snippets_in_order,
)


class ReviewTechnicalSolutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_review_solution_contract_sources()

    def test_frontmatter_uses_searchable_name_and_description(self) -> None:
        main = self.sources['main']
        self.assertIn('name: review-technical-solution', main)
        self.assertIn(
            'description: Use when reviewing a technical solution against requirement details, architecture principles, and existing project code',
            main,
        )

    def test_main_skill_requires_four_inputs_and_blocks_missing_context(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['main'],
            (
                '- `需求详情`',
                '- `技术方案文档`',
                '- `.architecture/principles.md`',
                '- `相关项目代码`',
                '任一缺失时，不做正式结论，直接输出 `无法开展正式评审`。',
            ),
        )

    def test_main_skill_requires_code_evidence_and_fixed_output_order(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['main'],
            (
                '不能因为用户催促、方案写得完整，或“看起来合理”就跳过代码核验。',
                '`待核验风险`',
                '1. `评审结论`',
                '2. `阻断项`',
                '3. `主要问题`',
                '4. `改进方案`',
                '5. `待补充信息`',
                '6. `建议验证`',
            ),
        )

    def test_review_process_defines_claim_extraction_and_evidence_states(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['review_process'],
            (
                '## 4. 主张提取',
                '至少提取以下信息：',
                '`claim_id`',
                '`statement`',
                '`expected_evidence`',
                '## 5. 代码取证',
                '`已证实`',
                '`已证伪`',
                '`待核验`',
            ),
        )

    def test_review_process_defines_severity_and_conclusion_rules(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['review_process'],
            (
                '## 7. 问题分级规则',
                '`blocker`',
                '`major`',
                '`minor`',
                '`note`',
                '## 8. 最终结论规则',
                '任何 `blocker` -> `阻断`',
                '缺少必要输入 -> `无法开展正式评审`',
            ),
        )

    def test_analysis_guide_covers_all_solution_types_and_union_behavior(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['analysis_guide'],
            (
                '1. 新功能方案',
                '2. 重构或替换方案',
                '3. 跨系统或平台能力方案',
                '4. 安全 / 合规 / 数据保护方案',
                '5. 性能 / 容量 / 成本优化方案',
                '评审问题取并集',
                '必查证据取并集',
                '最终结论按最高严重级别判定',
            ),
        )

    def test_output_contract_requires_fixed_sections_and_issue_fields(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['output_contract'],
            (
                '1. `评审结论`',
                '2. `阻断项`',
                '3. `主要问题`',
                '4. `改进方案`',
                '5. `待补充信息`',
                '6. `建议验证`',
                '`通过`',
                '`需修改`',
                '`阻断`',
                '`无法开展正式评审`',
            ),
        )
        require_snippets_in_order(
            self,
            self.sources['output_contract'],
            (
                '`severity`',
                '`category`',
                '`problem`',
                '`evidence`',
                '`impact`',
                '`recommendation`',
                '`validation`',
                '`targets`',
            ),
        )
        self.assertIn('所有区块都必须出现', self.sources['output_contract'])


if __name__ == '__main__':
    unittest.main()
```

```python
import unittest

from tests.skill_validation.helpers import ASSISTANT_TARGETS, bootstrapped_project


class StaticLayoutTests(unittest.TestCase):
    def test_bootstrap_rejects_unknown_assistant(self) -> None:
        with self.assertRaisesRegex(ValueError, 'Unknown assistant'):
            with bootstrapped_project('unknown'):
                self.fail('context manager should not yield for an unknown assistant')

    def test_bootstrap_creates_minimum_architecture(self) -> None:
        for assistant in ASSISTANT_TARGETS:
            with self.subTest(assistant=assistant):
                with bootstrapped_project(assistant) as project_dir:
                    self.assertTrue((project_dir / '.architecture').is_dir())
                    self.assertTrue((project_dir / '.architecture/technical-solutions').is_dir())
                    self.assertTrue((project_dir / '.architecture/templates').is_dir())
                    self.assertTrue(
                        (project_dir / '.architecture/templates/technical-solution-template.md').is_file()
                    )
                    self.assertTrue((project_dir / '.architecture/members.yml').is_file())
                    self.assertTrue((project_dir / '.architecture/principles.md').is_file())
                    self.assertFalse((project_dir / '.architecture/.architecture').exists())
                    self.assertFalse((project_dir / '.architecture/agent_docs').exists())
                    self.assertFalse((project_dir / 'CLAUDE.md').exists())
                    self.assertFalse((project_dir / '.architecture/solutions').exists())
                    self.assertFalse((project_dir / '.architecture/plans').exists())
                    self.assertFalse((project_dir / '.architecture/reviews').exists())
                    self.assertFalse((project_dir / 'ai-architect-tmp').exists())
                    self.assertFalse((project_dir / '.architecture/config.yml').exists())
                    self.assertFalse(
                        (project_dir / '.architecture/templates/review-template.md').exists()
                    )
                    self.assertFalse(
                        (project_dir / '.architecture/templates/implementation-plan-template.md').exists()
                    )
                    self.assertFalse(
                        (project_dir / '.architecture/reviews/initial-system-analysis.md').exists()
                    )

    def test_only_selected_assistant_target_exists(self) -> None:
        for assistant, selected_target in ASSISTANT_TARGETS.items():
            with self.subTest(assistant=assistant):
                with bootstrapped_project(assistant) as project_dir:
                    for target in ASSISTANT_TARGETS.values():
                        target_path = project_dir / target
                        if target == selected_target:
                            self.assertTrue(target_path.is_dir())
                            self.assertFalse(target_path.is_symlink())
                            self.assertFalse((target_path / '.git').exists())
                            self.assertTrue((target_path / 'setup-architect' / 'SKILL.md').is_file())
                            self.assertTrue(
                                (target_path / 'create-technical-solution' / 'SKILL.md').is_file()
                            )
                            self.assertTrue(
                                (target_path / 'review-technical-solution' / 'SKILL.md').is_file()
                            )
                        else:
                            self.assertFalse(target_path.exists())


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run the contract and layout tests to verify they fail**

Run: `python3 -m unittest tests.skill_validation.test_review_technical_solution_contracts tests.skill_validation.test_static_layout -v`
Expected: FAIL with `KeyError: 'output_contract'` and an assertion that `review-technical-solution/SKILL.md` is missing from the installed assistant target

- [ ] **Step 3: Create the output contract and wire installation expectations**

```python
# tests/skill_validation/helpers.py

SKILL_INSTALL_LAYOUT = {
    'setup-architect': (
        'SKILL.md',
        'references',
        'templates',
    ),
    'create-technical-solution': (
        'SKILL.md',
        'references',
    ),
    'review-technical-solution': (
        'SKILL.md',
        'references',
    ),
}


def load_review_solution_contract_sources() -> dict[str, str]:
    return {
        'main': read_repo_text('skills/review-technical-solution/SKILL.md'),
        'review_process': read_repo_text(
            'skills/review-technical-solution/references/review-process.md'
        ),
        'analysis_guide': read_repo_text(
            'skills/review-technical-solution/references/review-analysis-guide.md'
        ),
        'output_contract': read_repo_text(
            'skills/review-technical-solution/references/review-output-contract.md'
        ),
    }
```

```md
# 技术方案评审输出契约

## 1. 文档定位

本文档只定义正式评审输出必须长什么样，不定义什么时候能评、也不定义如何评审。

## 2. 固定输出顺序

正式输出必须严格按以下顺序出现：
1. `评审结论`
2. `阻断项`
3. `主要问题`
4. `改进方案`
5. `待补充信息`
6. `建议验证`

所有区块都必须出现；没有内容时写 `- 无`。

## 3. 允许的结论值

`评审结论` 只允许以下四个值：
- `通过`
- `需修改`
- `阻断`
- `无法开展正式评审`

## 4. 固定字段

### 评审结论

- `结论`
- `主分类`
- `附加分类`
- `结论摘要`
- `已核验范围`
- `未核验范围`

### 每个问题条目

每个 `阻断项` 和每个 `主要问题` 都必须包含：
- `severity`
- `category`
- `problem`
- `evidence`
- `impact`
- `recommendation`
- `validation`

### 每个改进方案条目

每个 `改进方案` 都必须包含：
- `targets`
- `goal`
- `action`
- `why`
- `tradeoff`
- `validation`

`targets` 必须显式引用问题编号，例如 `B1`、`P2`。

## 5. 证据规则

- 所有确认问题都必须带证据。
- 证据来源只能来自需求详情、技术方案文档、`.architecture/principles.md`、项目代码 / 配置 / schema / 接口 / 测试。
- 证据不足时必须写成 `待核验风险`，并说明已掌握证据、缺失证据、下一步核验动作。

## 6. 严重级别联动规则

- 任意 `blocker` 存在时，`结论` 不得为 `通过` 或 `需修改`。
- 无 `blocker` 但存在 `major` 或 `minor` 时，通常为 `需修改`。
- 缺少必要输入时，`结论` 必须为 `无法开展正式评审`。

## 7. 禁止输出模式

- 只有泛化总结，没有固定区块
- 给出经验判断但没有证据
- 把未确认风险写成确定性缺陷
- 改进方案不关联问题编号
- 缺少必要输入时仍给 `通过`、`需修改` 或 `阻断`
```

```yaml
- name: Verify installed skill set and setup-architect resources
  run: |
    cd "test-projects/${{ matrix.assistant }}"
    target="${{ matrix.target }}"

    expected_skills="$(mktemp)"
    actual_skills="$(mktemp)"

    printf '%s\n' create-technical-solution review-technical-solution setup-architect | sort > "$expected_skills"
    find "$target" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort > "$actual_skills"

    diff -u "$expected_skills" "$actual_skills" || (echo "Installed skill list mismatch for $target" && exit 1)

    [ -f "$target/create-technical-solution/SKILL.md" ] || (echo 'Missing create-technical-solution/SKILL.md' && exit 1)
    [ -f "$target/review-technical-solution/SKILL.md" ] || (echo 'Missing review-technical-solution/SKILL.md' && exit 1)
    [ -f "$target/review-technical-solution/references/review-process.md" ] || (echo 'Missing review-process.md' && exit 1)
    [ -f "$target/review-technical-solution/references/review-analysis-guide.md" ] || (echo 'Missing review-analysis-guide.md' && exit 1)
    [ -f "$target/review-technical-solution/references/review-output-contract.md" ] || (echo 'Missing review-output-contract.md' && exit 1)
    [ -f "$target/setup-architect/SKILL.md" ] || (echo 'Missing setup-architect/SKILL.md' && exit 1)
    [ -f "$target/setup-architect/references/installation-procedures.md" ] || (echo 'Missing installation-procedures.md' && exit 1)
    [ -f "$target/setup-architect/references/member-customization.md" ] || (echo 'Missing member-customization.md' && exit 1)
    [ -f "$target/setup-architect/references/principles-customization.md" ] || (echo 'Missing principles-customization.md' && exit 1)
    [ -f "$target/setup-architect/templates/technical-solution-template.md" ] || (echo 'Missing technical-solution-template.md' && exit 1)
    [ -f "$target/setup-architect/templates/members-template.yml" ] || (echo 'Missing members-template.yml' && exit 1)
    [ -f "$target/setup-architect/templates/principles-template.md" ] || (echo 'Missing principles-template.md' && exit 1)
```

- [ ] **Step 4: Run the contract and layout tests and verify they pass**

Run: `python3 -m unittest tests.skill_validation.test_review_technical_solution_contracts tests.skill_validation.test_static_layout -v`
Expected: PASS with all targeted tests green

- [ ] **Step 5: Commit the output contract and installation wiring**

```bash
git add skills/review-technical-solution/references/review-output-contract.md tests/skill_validation/helpers.py tests/skill_validation/test_review_technical_solution_contracts.py tests/skill_validation/test_static_layout.py .github/workflows/skills-integration-tests.yml
git commit -m 'feat: wire review technical solution validation install path'
```

### Task 4: Publish the Review Scenario Catalog and Runbook Coverage

**Files:**
- Modify: `tests/skill_validation/case_catalog.py`
- Modify: `tests/skill_validation/test_case_catalog.py`
- Modify: `docs/superpowers/testing/skill-validation.md`
- Modify: `tests/skill_validation/test_workflow_integration.py`

- [ ] **Step 1: Update the catalog and workflow tests so the new review cases fail first**

```python
import unittest

from tests.skill_validation.case_catalog import (
    ALL_CASES,
    PHASE_1_CASE_IDS,
    PHASE_2_CASE_IDS,
    PHASE_3_CASE_IDS,
)


EXPECTED_PHASE_1 = {
    'SA-01',
    'SA-02',
    'SA-07',
    'SA-08',
    'CTS-01',
    'CTS-02',
    'CTS-04',
    'CTS-07',
    'CTS-08',
    'RTS-01',
    'RTS-02',
    'RTS-03',
}

EXPECTED_PHASE_1_ORDER = (
    'SA-01',
    'SA-02',
    'SA-07',
    'SA-08',
    'CTS-01',
    'CTS-02',
    'CTS-04',
    'CTS-07',
    'CTS-08',
    'RTS-01',
    'RTS-02',
    'RTS-03',
)

EXPECTED_PHASE_2 = {
    'SA-03',
    'SA-04',
    'SA-05',
    'SA-06',
    'CTS-03',
    'CTS-05',
    'CTS-06',
    'CTS-09',
    'RTS-04',
    'RTS-05',
    'RTS-06',
}

EXPECTED_PHASE_2_ORDER = (
    'SA-03',
    'SA-04',
    'SA-05',
    'SA-06',
    'CTS-03',
    'CTS-05',
    'CTS-06',
    'CTS-09',
    'RTS-04',
    'RTS-05',
    'RTS-06',
)

EXPECTED_PHASE_3 = {
    'SA-09',
    'SA-10',
    'SA-11',
    'SA-12',
    'CTS-10',
    'CTS-11',
    'CTS-12',
    'RTS-07',
    'RTS-08',
    'RTS-09',
}

EXPECTED_PHASE_3_ORDER = (
    'SA-09',
    'SA-10',
    'SA-11',
    'SA-12',
    'CTS-10',
    'CTS-11',
    'CTS-12',
    'RTS-07',
    'RTS-08',
    'RTS-09',
)

EXPECTED_CASE_IDS = EXPECTED_PHASE_1 | EXPECTED_PHASE_2 | EXPECTED_PHASE_3


class CaseCatalogTests(unittest.TestCase):
    def test_case_ids_are_unique(self) -> None:
        case_ids = [case.case_id for case in ALL_CASES]
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_catalog_contains_all_design_cases(self) -> None:
        self.assertEqual(len(ALL_CASES), 33)
        self.assertEqual({case.case_id for case in ALL_CASES}, EXPECTED_CASE_IDS)
        self.assertEqual(PHASE_1_CASE_IDS, EXPECTED_PHASE_1_ORDER)
        self.assertEqual(PHASE_2_CASE_IDS, EXPECTED_PHASE_2_ORDER)
        self.assertEqual(PHASE_3_CASE_IDS, EXPECTED_PHASE_3_ORDER)
        self.assertEqual(len(PHASE_1_CASE_IDS), len(set(PHASE_1_CASE_IDS)))
        self.assertEqual(len(PHASE_2_CASE_IDS), len(set(PHASE_2_CASE_IDS)))
        self.assertEqual(len(PHASE_3_CASE_IDS), len(set(PHASE_3_CASE_IDS)))

    def test_every_case_has_actionable_metadata(self) -> None:
        for case in ALL_CASES:
            with self.subTest(case_id=case.case_id):
                self.assertTrue(case.skill)
                self.assertTrue(case.layer)
                self.assertTrue(case.fixture)
                self.assertTrue(case.prompt)
                self.assertTrue(case.purpose)
                self.assertTrue(case.expected_result)
                self.assertTrue(
                    case.assert_paths
                    or case.assert_structure
                    or case.assert_semantics
                    or case.assert_safety
                )

    def test_placeholder_like_assertions_are_not_allowed(self) -> None:
        disallowed_values = {
            '缺失文件被补齐',
            '缺失前置项被明确指出',
            '明确列出缺失前置',
            '原始目标文件保持不变',
        }
        for case in ALL_CASES:
            with self.subTest(case_id=case.case_id):
                self.assertTrue(disallowed_values.isdisjoint(case.assert_paths))

    def test_assert_paths_only_contains_concrete_repo_paths(self) -> None:
        for case in ALL_CASES:
            for path_assertion in case.assert_paths:
                with self.subTest(case_id=case.case_id, path_assertion=path_assertion):
                    self.assertTrue(path_assertion.startswith('.'), path_assertion)


if __name__ == '__main__':
    unittest.main()
```

```python
import unittest
from pathlib import Path

from tests.skill_validation.case_catalog import CASE_INDEX, PHASE_1_CASE_IDS, PHASE_2_CASE_IDS, PHASE_3_CASE_IDS


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / '.github/workflows/skills-integration-tests.yml'
RUNBOOK_PATH = REPO_ROOT / 'docs/superpowers/testing/skill-validation.md'


def section_body(markdown: str, heading: str) -> str:
    marker = f'### {heading}\n'
    start = markdown.index(marker) + len(marker)
    next_heading = markdown.find('\n### ', start)
    if next_heading == -1:
        next_heading = len(markdown)
    return markdown[start:next_heading]


class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_runs_skill_validation_contract_suite(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding='utf-8')

        self.assertIn('- name: Run skill validation contract suite', workflow)
        self.assertIn(
            'python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v',
            workflow,
        )
        self.assertIn('review-technical-solution', workflow)

    def test_runbook_documents_local_skill_validation_flow(self) -> None:
        runbook = RUNBOOK_PATH.read_text(encoding='utf-8')

        self.assertIn('# Skill Validation Runbook', runbook)
        self.assertIn('review-technical-solution', runbook)
        self.assertIn('静态契约层', runbook)
        self.assertIn('流程场景层', runbook)
        self.assertIn('行为回归层', runbook)
        self.assertIn('对抗边界层', runbook)
        self.assertIn(
            'python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v',
            runbook,
        )
        self.assertIn('RTS-01', runbook)
        self.assertIn('RTS-09', runbook)

    def test_runbook_includes_phase_rollout_guidance(self) -> None:
        runbook = RUNBOOK_PATH.read_text(encoding='utf-8')

        self.assertIn('## Phase rollout', runbook)
        self.assertIn('### Phase 1', runbook)
        self.assertIn('### Phase 2', runbook)
        self.assertIn('### Phase 3', runbook)

        for case_id in PHASE_1_CASE_IDS:
            self.assertIn(case_id, runbook)
        for case_id in PHASE_2_CASE_IDS:
            self.assertIn(case_id, runbook)
        for case_id in PHASE_3_CASE_IDS:
            self.assertIn(case_id, runbook)

    def test_runbook_case_layer_examples_match_catalog(self) -> None:
        runbook = RUNBOOK_PATH.read_text(encoding='utf-8')

        expected_layer_examples = {
            '静态契约层': ('SA-11', 'SA-12', 'RTS-09'),
            '流程场景层': ('SA-01', 'CTS-01', 'CTS-11', 'RTS-01', 'RTS-02'),
            '行为回归层': ('SA-03', 'CTS-04', 'CTS-09', 'RTS-04', 'RTS-05', 'RTS-06'),
            '对抗边界层': ('SA-07', 'SA-08', 'CTS-07', 'CTS-08', 'RTS-03', 'RTS-07', 'RTS-08'),
        }

        for layer, case_ids in expected_layer_examples.items():
            layer_section = section_body(runbook, layer)
            for case_id in case_ids:
                self.assertEqual(CASE_INDEX[case_id].layer, layer)
                self.assertIn(case_id, layer_section)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run the catalog and workflow tests to verify they fail**

Run: `python3 -m unittest tests.skill_validation.test_case_catalog tests.skill_validation.test_workflow_integration -v`
Expected: FAIL because `RTS-*` cases are missing from `case_catalog.py` and the runbook does not mention the new review skill

- [ ] **Step 3: Add the review scenario catalog and update the runbook**

```python
# tests/skill_validation/case_catalog.py

REVIEW_TECHNICAL_SOLUTION_CASES = (
    vcase(
        'RTS-01',
        'review-technical-solution',
        '流程场景层',
        'complete-architecture-default-template',
        '用户提供需求详情、方案正文和相关代码路径，但仓库缺少 `.architecture/principles.md`，请求正式评审技术方案。',
        '缺少原则文档时不能开展正式评审',
        'STOP_FORMAL_REVIEW',
        assert_paths=('.architecture/principles.md',),
        assert_semantics=('结论为 `无法开展正式评审`', '明确列出缺失项'),
        assert_safety=('不输出 `通过`', '不输出 `需修改`'),
        forbidden_behavior=('跳过原则校验继续评审',),
    ),
    vcase(
        'RTS-02',
        'review-technical-solution',
        '流程场景层',
        'complete-architecture-default-template',
        '用户提供需求详情、方案正文和 `.architecture/principles.md`，但未提供可定位的相关项目代码，只要求先给正式评审结论。',
        '缺少相关代码时不得把文档评审包装成正式结论',
        'STOP_FORMAL_REVIEW',
        assert_semantics=('明确说明缺少相关项目代码', '要求补充核心模块路径或代码范围'),
        assert_safety=('不在无代码证据时给正式通过结论',),
        forbidden_behavior=('只读方案正文就给正式结论',),
    ),
    vcase(
        'RTS-03',
        'review-technical-solution',
        '对抗边界层',
        'complete-architecture-default-template',
        '用户只给方案摘要而不是完整方案正文，并催促先做正式评审。',
        '方案正文不完整时必须停机而不是脑补',
        'STOP_FORMAL_REVIEW',
        assert_semantics=('明确要求提供完整方案正文', '说明摘要不足以支撑正式评审'),
        assert_safety=('不根据摘要脑补完整方案',),
        forbidden_behavior=('把摘要当正文继续评审',),
    ),
    vcase(
        'RTS-04',
        'review-technical-solution',
        '行为回归层',
        'complete-architecture-default-template',
        '在需求、方案、原则文档和相关代码齐备的场景下，请求正式评审一个新功能方案，并要求输出结构化评审报告。',
        '标准成功路径必须输出六个固定区块',
        'SUCCESS_REVIEW',
        assert_semantics=('评审结论', '阻断项', '主要问题', '改进方案', '待补充信息', '建议验证'),
        assert_safety=('空区块也要显式输出',),
        forbidden_behavior=('省略固定区块',),
    ),
    vcase(
        'RTS-05',
        'review-technical-solution',
        '行为回归层',
        'complete-architecture-default-template',
        '方案同时涉及跨系统事件编排和权限控制，请求正式评审并指出主分类与附加分类。',
        '多类型方案必须合并检查点并按高风险排序',
        'SUCCESS_REVIEW',
        assert_semantics=('主分类', '附加分类', '评审重点按风险高低排序'),
        assert_safety=('不只按单一类型输出问题',),
        forbidden_behavior=('忽略附加分类检查点',),
    ),
    vcase(
        'RTS-06',
        'review-technical-solution',
        '行为回归层',
        'complete-architecture-default-template',
        '方案声称可直接复用现有订单事件总线承载新语义，请基于现有代码做正式评审。',
        '复用主张找不到代码证据时必须升级为 blocker 或高严重问题',
        'SUCCESS_REVIEW',
        assert_semantics=('代码中未找到对应实现', '`severity`: `blocker`'),
        assert_safety=('不把不存在的现有能力当作可复用前提',),
        forbidden_behavior=('在找不到实现时仍判定方案通过',),
    ),
    vcase(
        'RTS-07',
        'review-technical-solution',
        '对抗边界层',
        'complete-architecture-default-template',
        '用户说‘先别看代码，基于方案快速评一下，后面再补代码’，要求直接给结论。',
        '用户催促时也不能跳过代码核验',
        'STOP_FORMAL_REVIEW',
        assert_semantics=('正式评审依赖代码证据', '不能跳过代码核验'),
        assert_safety=('不因用户催促降低标准',),
        forbidden_behavior=('跳过代码核验',),
    ),
    vcase(
        'RTS-08',
        'review-technical-solution',
        '对抗边界层',
        'complete-architecture-default-template',
        '用户只提供了核心链路的一小段片段代码，并要求确认方案与现状完全一致。',
        '片段代码不足时必须保留未核验范围与待核验风险',
        'STOP_FORMAL_REVIEW',
        assert_semantics=('结论为 `无法开展正式评审`', '未核验范围', '`待核验风险`'),
        assert_safety=('不把片段代码推断成完整实现',),
        forbidden_behavior=('把片段代码当成完整证据',),
    ),
    vcase(
        'RTS-09',
        'review-technical-solution',
        '静态契约层',
        'complete-architecture-default-template',
        '在完整上下文下请求正式评审，检查输出契约是否在无阻断项时仍保留全部固定区块并对空区块写 `- 无`。',
        '固定输出区块与空区块显式化不能退化',
        'SUCCESS_REVIEW',
        assert_semantics=('- 无', '评审结论', '阻断项', '主要问题', '改进方案', '待补充信息', '建议验证'),
        assert_safety=('空区块不被省略',),
        forbidden_behavior=('省略空区块',),
    ),
)


ALL_CASES = SETUP_ARCHITECT_CASES + CREATE_TECHNICAL_SOLUTION_CASES + REVIEW_TECHNICAL_SOLUTION_CASES

PHASE_1_CASE_IDS = (
    'SA-01',
    'SA-02',
    'SA-07',
    'SA-08',
    'CTS-01',
    'CTS-02',
    'CTS-04',
    'CTS-07',
    'CTS-08',
    'RTS-01',
    'RTS-02',
    'RTS-03',
)

PHASE_2_CASE_IDS = (
    'SA-03',
    'SA-04',
    'SA-05',
    'SA-06',
    'CTS-03',
    'CTS-05',
    'CTS-06',
    'CTS-09',
    'RTS-04',
    'RTS-05',
    'RTS-06',
)

PHASE_3_CASE_IDS = (
    'SA-09',
    'SA-10',
    'SA-11',
    'SA-12',
    'CTS-10',
    'CTS-11',
    'CTS-12',
    'RTS-07',
    'RTS-08',
    'RTS-09',
)

CASE_INDEX = {case.case_id: case for case in ALL_CASES}
```

```md
# Skill Validation Runbook

## Scope

This runbook operationalizes the layered validation strategy in `docs/superpowers/specs/2026-03-26-skill-validation-design.md` for `setup-architect`, `create-technical-solution`, and `review-technical-solution`. Use it when validating changes to skill contracts, flow control, regression-sensitive behavior, and adversarial boundary handling.

## Local command

```bash
python3 -m unittest discover -s tests/skill_validation -p 'test_*.py' -v
```

## Layer map

### 静态契约层

- Focus: install targets, required files, forbidden legacy artifacts, and fixed output contracts that must remain explicit.
- Representative cases: `SA-11`, `SA-12`, `RTS-09`.

### 流程场景层

- Focus: stop/redirect behavior, prerequisite enforcement, and primary success-path branching.
- Representative cases: `SA-01`, `CTS-01`, `CTS-11`, `RTS-01`, `RTS-02`.

### 行为回归层

- Focus: template adherence, required semantic blocks, stable report structure, multi-type union behavior, and code-evidence-backed conclusions.
- Representative cases: `SA-03`, `CTS-04`, `CTS-09`, `RTS-04`, `RTS-05`, `RTS-06`.

### 对抗边界层

- Focus: ambiguous, partial, or risky inputs that could trigger unsafe inference, skipped code checks, or unsupported formal conclusions.
- Representative cases: `SA-07`, `SA-08`, `CTS-07`, `CTS-08`, `RTS-03`, `RTS-07`, `RTS-08`.

## Phase rollout

### Phase 1

- Goal: lock the hard rules first so the suite catches unsafe continuation, unsafe inference, skipped code checks, and missing-context formal reviews early.
- Cases: `SA-01`, `SA-02`, `SA-07`, `SA-08`, `CTS-01`, `CTS-02`, `CTS-04`, `CTS-07`, `CTS-08`, `RTS-01`, `RTS-02`, `RTS-03`.
- Use when: validating the first enforcement baseline after changes to skill rules, references, or prompts.

### Phase 2

- Goal: expand from hard-stop protection into mainline success-path and stable regression coverage.
- Cases: `SA-03`, `SA-04`, `SA-05`, `SA-06`, `CTS-03`, `CTS-05`, `CTS-06`, `CTS-09`, `RTS-04`, `RTS-05`, `RTS-06`.
- Use when: validating template adaptation, required information-block coverage, structured review output, and code-backed blocker classification.

### Phase 3

- Goal: add governance-heavy and pressure-path coverage once the baseline suite is stable.
- Cases: `SA-09`, `SA-10`, `SA-11`, `SA-12`, `CTS-10`, `CTS-11`, `CTS-12`, `RTS-07`, `RTS-08`, `RTS-09`.
- Use when: validating member/principle governance, standalone execution expectations, and higher-pressure adversarial review scenarios.

## Recommended cadence

- Before commit: run the full local command after any change that affects the validation suite itself.
- Before merge: run the full local command for `SKILL.md`, workflow, fixture, reference, or contract-test changes.
- Before release: run the full local command and review cases spanning all four layers.
- After changing `skills/*/SKILL.md` or referenced docs: prioritize re-running scenario and regression coverage from the affected skill alongside the full suite.
```

- [ ] **Step 4: Run the catalog and workflow tests and verify they pass**

Run: `python3 -m unittest tests.skill_validation.test_case_catalog tests.skill_validation.test_workflow_integration -v`
Expected: PASS with the new `RTS-*` cases and runbook assertions green

- [ ] **Step 5: Run the full validation suite**

Run: `python3 -m unittest discover -s tests/skill_validation -p 'test_*.py' -v`
Expected: PASS with the full contract, layout, catalog, workflow, and review-skill test set green

- [ ] **Step 6: Commit the expanded validation catalog**

```bash
git add tests/skill_validation/case_catalog.py tests/skill_validation/test_case_catalog.py docs/superpowers/testing/skill-validation.md tests/skill_validation/test_workflow_integration.py
git commit -m 'test: add review technical solution validation coverage'
```
