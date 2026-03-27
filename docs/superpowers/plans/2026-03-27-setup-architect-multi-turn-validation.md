---
# setup-architect 多轮验证建模实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标**：在不引入真实模型调用和 CLI E2E 的前提下，为 `setup-architect` 的 skill validation 体系补上可复用的多轮对话建模能力，锁定“初始化尾声必须先询问是否定制技术方案模板，并在收到回答前停止”的流程契约。

**架构**：增量扩展现有 `ValidationCase` 体系，增加可选的 `turns` 字段用于多轮 case；新增专用多轮测试模块消费 `turns`；同步收紧 skill 文档硬规则。

**技术栈**：Python unittest, dataclass, existing helpers in `tests/skill_validation/`

---

## Task 1: 收紧 setup-architect 文档硬规则

**Files:**
- Modify: `skills/setup-architect/SKILL.md:57-65`
- Modify: `skills/setup-architect/references/technical-solution-template-customization.md:47-65`

- [ ] **Step 1: 收紧 SKILL.md 第 6 步的停顿语义**

修改 `skills/setup-architect/SKILL.md` 中 `### 6. 确认当前生效模板并收尾` 部分，将：

```markdown
- 先询问用户是否需要定制技术方案模板。
- 若回答“不需要”，保留当前 `.architecture/templates/technical-solution-template.md`；
- 若回答“需要”，先校验...（保留现有规则）
```

替换为：

```markdown
- 先询问用户是否需要定制技术方案模板。
- 若用户尚未回答，本轮结果为 STOP_AND_ASK；必须在此停止并等待用户回答。
- 未收到用户回答前，不得输出“Tech Solution 设置完成”初始化摘要。
- 若回答“不需要”，保留当前 `.architecture/templates/technical-solution-template.md`；
- 若回答“需要”，先校验 `.architecture/templates/technical-solution-template.md`、`.architecture/members.yml`、`.architecture/principles.md` 已存在；若 setup 不完整，则必须停止，并要求用户先完成完整初始化。
- 只接受完整 Markdown、文件路径或链接地址。
- 只允许整体替换 `.architecture/templates/technical-solution-template.md`。
- 不允许自动生成模板、局部编辑或内容合并。
- 只有在用户明确回答“不需要”，或已完成合法整体替换后，才能输出初始化摘要。
```

- [ ] **Step 2: 收紧 reference 文档场景 A 的未回答状态**

修改 `skills/setup-architect/references/technical-solution-template-customization.md` 中 `## 场景 A：初始化收尾时确认模板是否定制` 部分，在现有内容后追加：

```markdown
- 若用户尚未回答是否需要定制技术方案模板，本轮结果为 STOP_AND_ASK。
- 在该状态下，只输出询问，不得附带初始化完成摘要。
- 只有在用户明确回答“不需要”，或已完成合法模板整体替换后，才能输出“初始化场景摘要”。
```

- [ ] **Step 3: 提交更改**

```bash
git add skills/setup-architect/SKILL.md skills/setup-architect/references/technical-solution-template-customization.md
git commit -m "fix(setup-architect): add STOP_AND_ASK boundary before init summary"
```

---

## Task 2: 扩展 case_catalog.py schema 并新增多轮 case

**Files:**
- Modify: `tests/skill_validation/case_catalog.py:1-50`
- Modify: `tests/skill_validation/case_catalog.py:240-250`

- [ ] **Step 1: 在 case_catalog.py 顶部添加 ConversationTurn 数据结构**

在 `from dataclasses import dataclass` 之后、`@dataclass(frozen=True) class ValidationCase` 之前，添加：

```python
@dataclass(frozen=True)
class ConversationTurn:
    user_input: str
    expected_result: str
    assert_paths: Tuple[str, ...] = ()
    assert_structure: Tuple[str, ...] = ()
    assert_semantics: Tuple[str, ...] = ()
    assert_safety: Tuple[str, ...] = ()
    forbidden_behavior: Tuple[str, ...] = ()
```

- [ ] **Step 2: 给 ValidationCase 增加可选 turns 字段**

修改 `@dataclass(frozen=True) class ValidationCase:` 的字段定义，在最后添加：

```python
    turns: Tuple[ConversationTurn, ...] = ()
```

- [ ] **Step 3: 更新 vcase 函数签名**

修改 `def vcase(...)` 的参数列表，在 `forbidden_behavior` 参数后添加：

```python
    turns: Tuple[ConversationTurn, ...] = (),
```

并修改 `return ValidationCase(...)` 调用，添加 `turns=turns` 字段。

- [ ] **Step 4: 新增 SA-13 和 SA-14 多轮 case**

在 `SETUP_ARCHITECT_CASES` 末尾（在 SA-12 之后）添加：

```python
    vcase(
        "SA-13",
        "setup-architect",
        "流程场景层",
        "complete-architecture-default-template",
        "完整初始化完成后，尚未收到用户对是否需要定制技术方案模板的回答。",
        "模板定制确认未回答时必须先停下来询问",
        "STOP_AND_ASK",
        assert_paths=(".architecture/templates/technical-solution-template.md",),
        assert_semantics=("询问是否需要定制技术方案模板",),
        assert_safety=("未收到回答前不输出初始化完成摘要", "不默认保留或替换模板"),
        forbidden_behavior=("直接输出 Tech Solution 设置完成", "跳过模板确认直接收尾"),
        turns=(
            ConversationTurn(
                user_input="请求完整执行 setup-architect",
                expected_result="STOP_AND_ASK",
                assert_semantics=("明确询问是否需要定制技术方案模板",),
                assert_safety=("未收到回答前不输出初始化完成摘要",),
                forbidden_behavior=("直接输出 Tech Solution 设置完成",),
            ),
            ConversationTurn(
                user_input="不需要，保留当前模板",
                expected_result="SUCCESS_INIT",
                assert_semantics=("模板最终状态明确为保留当前模板",),
            ),
        ),
    ),
    vcase(
        "SA-14",
        "setup-architect",
        "行为回归层",
        "template-replacement-inputs",
        "完整初始化完成后，用户第二轮提供完整模板并要求替换。",
        "多轮等待后进入合法模板替换成功路径",
        "SUCCESS_REPLACE_TEMPLATE",
        assert_paths=(".architecture/templates/technical-solution-template.md",),
        assert_safety=("整体替换，不做局部 merge",),
        turns=(
            ConversationTurn(
                user_input="请求完整执行 setup-architect",
                expected_result="STOP_AND_ASK",
                assert_semantics=("明确询问是否需要定制技术方案模板",),
                forbidden_behavior=("跳过确认直接收尾",),
            ),
            ConversationTurn(
                user_input="提供完整 Markdown 模板内容或合法路径/链接",
                expected_result="SUCCESS_REPLACE_TEMPLATE",
                assert_paths=(".architecture/templates/technical-solution-template.md",),
                assert_safety=("整体替换，不做局部 merge",),
            ),
        ),
    ),
```

- [ ] **Step 5: 更新 PHASE_1_CASE_IDS 和 PHASE_2_CASE_IDS**

修改 `PHASE_1_CASE_IDS`（在 `SA-02` 后插入 `SA-13`）：

```python
PHASE_1_CASE_IDS = (
    "SA-01",
    "SA-02",
    "SA-13",  # 新增
    "SA-07",
    "SA-08",
    ...
)
```

修改 `PHASE_2_CASE_IDS`（在末尾追加 `SA-14`）：

```python
PHASE_2_CASE_IDS = (
    "SA-03",
    "SA-04",
    "SA-05",
    "SA-06",
    "SA-14",  # 新增
    ...
)
```

- [ ] **Step 6: 运行测试验证 schema 扩展正确**

Run: `python3 -m unittest tests.skill_validation.test_case_catalog -v`
Expected: PASS（case count 从 33 变为 35）

- [ ] **Step 7: 提交更改**

```bash
git add tests/skill_validation/case_catalog.py
git commit -m "feat(validation): add ConversationTurn and SA-13/SA-14 multi-turn cases"
```

---

## Task 3: 更新 test_case_catalog.py 校验多轮元数据

**Files:**
- Modify: `tests/skill_validation/test_case_catalog.py:100-130`

- [ ] **Step 1: 新增多轮元数据校验测试**

在 `test_placeholder_like_assertions_are_not_allowed` 方法之后添加：

```python
    def test_multi_turn_cases_have_at_least_two_turns(self) -> None:
        for case in ALL_CASES:
            if case.turns:
                with self.subTest(case_id=case.case_id):
                    self.assertGreaterEqual(
                        len(case.turns), 2,
                        f"{case.case_id} must have at least 2 turns"
                    )

    def test_multi_turn_cases_first_turn_is_stop_and_ask(self) -> None:
        for case in ALL_CASES:
            if case.turns:
                with self.subTest(case_id=case.case_id):
                    self.assertEqual(
                        case.turns[0].expected_result,
                        "STOP_AND_ASK",
                        f"{case.case_id} first turn must be STOP_AND_ASK"
                    )

    def test_phase_1_has_sa_13(self) -> None:
        self.assertIn("SA-13", PHASE_1_CASE_IDS)

    def test_phase_2_has_sa_14(self) -> None:
        self.assertIn("SA-14", PHASE_2_CASE_IDS)

    def test_total_case_count_updated(self) -> None:
        self.assertEqual(len(ALL_CASES), 35)
```

- [ ] **Step 2: 运行测试验证多轮校验通过**

Run: `python3 -m unittest tests.skill_validation.test_case_catalog -v`
Expected: PASS（包括新的多轮校验测试）

- [ ] **Step 3: 提交更改**

```bash
git add tests/skill_validation/test_case_catalog.py
git commit -m "test(validation): add multi-turn metadata checks for SA-13/SA-14"
```

---

## Task 4: 更新 test_setup_architect_contracts.py 补充顺序断言

**Files:**
- Modify: `tests/skill_validation/test_setup_architect_contracts.py:1-50`
- Modify: `tests/skill_validation/test_setup_architect_contracts.py:90-94`

- [ ] **Step 1: 导入 require_snippets_in_order**

在 `from tests.skill_validation.helpers import load_setup_contract_sources, require_all_snippets` 中添加 `require_snippets_in_order`：

```python
from tests.skill_validation.helpers import (
    load_setup_contract_sources,
    require_all_snippets,
    require_snippets_in_order,
)
```

- [ ] **Step 2: 新增主 skill 顺序断言测试**

在文件末尾（`test_principles_customization_preserves_core_principles_and_coverage` 之后）添加：

```python
    def test_main_skill_waits_for_template_answer_before_summary(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "先询问用户是否需要定制技术方案模板。",
                "若用户尚未回答，本轮结果为 STOP_AND_ASK；必须在此停止并等待用户回答。",
                "未收到用户回答前，不得输出“Tech Solution 设置完成”初始化摘要。",
                "初始化摘要：",
            ),
        )

    def test_reference_scene_a_requires_stop_and_wait(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["template_customization"],
            (
                "若用户尚未回答是否需要定制技术方案模板，本轮结果为 STOP_AND_ASK。",
                "在该状态下，只输出询问，不得附带初始化完成摘要。",
                "初始化场景摘要：",
            ),
        )
```

- [ ] **Step 3: 运行测试验证顺序断言通过**

Run: `python3 -m unittest tests.skill_validation.test_setup_architect_contracts -v`
Expected: PASS（包括新的顺序断言测试）

- [ ] **Step 4: 提交更改**

```bash
git add tests/skill_validation/test_setup_architect_contracts.py
git commit -m "test(contracts): add ordered assertions for ask->stop->no-summary"
```

---

## Task 5: 新增多轮 case 消费器 test_setup_architect_conversation_simulation.py

**Files:**
- Create: `tests/skill_validation/test_setup_architect_conversation_simulation.py`

- [ ] **Step 1: 创建多轮 case 消费器测试文件**

创建 `tests/skill_validation/test_setup_architect_conversation_simulation.py`：

```python
import unittest
from tests.skill_validation.case_catalog import SETUP_ARCHITECT_CASES, CASE_INDEX


class SetupArchitectConversationSimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.multi_turn_cases = [
            case for case in SETUP_ARCHITECT_CASES if case.turns
        ]

    def test_multi_turn_cases_exist(self) -> None:
        self.assertGreaterEqual(
            len(self.multi_turn_cases), 2,
            "Should have at least SA-13 and SA-14 as multi-turn cases"
        )

    def test_sa_13_has_correct_turn_structure(self) -> None:
        case = CASE_INDEX["SA-13"]
        self.assertEqual(len(case.turns), 2)
        self.assertEqual(case.turns[0].expected_result, "STOP_AND_ASK")
        self.assertEqual(case.turns[1].expected_result, "SUCCESS_INIT")
        self.assertIn("不需要，保留当前模板", case.turns[1].user_input)

    def test_sa_14_has_correct_turn_structure(self) -> None:
        case = CASE_INDEX["SA-14"]
        self.assertEqual(len(case.turns), 2)
        self.assertEqual(case.turns[0].expected_result, "STOP_AND_ASK")
        self.assertEqual(case.turns[1].expected_result, "SUCCESS_REPLACE_TEMPLATE")
        self.assertIn("完整 Markdown", case.turns[1].user_input)

    def test_first_turn_always_asks_template_customization(self) -> None:
        for case in self.multi_turn_cases:
            with self.subTest(case_id=case.case_id):
                first_turn = case.turns[0]
                self.assertEqual(first_turn.expected_result, "STOP_AND_ASK")
                semantics_found = any(
                    "定制技术方案模板" in s or "模板" in s
                    for s in first_turn.assert_semantics
                )
                self.assertTrue(
                    semantics_found,
                    f"{case.case_id} first turn must ask about template customization"
                )

    def test_multi_turn_cases_forbidden_behavior_defined(self) -> None:
        for case in self.multi_turn_cases:
            with self.subTest(case_id=case.case_id):
                for turn in case.turns:
                    if turn.forbidden_behavior:
                        self.assertTrue(
                            len(turn.forbidden_behavior) > 0,
                            f"{case.case_id} turn {case.turns.index(turn)} has forbidden behavior defined"
                        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试验证多轮消费器正确**

Run: `python3 -m unittest tests.skill_validation.test_setup_architect_conversation_simulation -v`
Expected: PASS

- [ ] **Step 3: 提交更改**

```bash
git add tests/skill_validation/test_setup_architect_conversation_simulation.py
git commit -m "test(validation): add multi-turn case consumer for setup-architect"
```

---

## Task 6: 同步 runbook 和设计文档

**Files:**
- Modify: `docs/superpowers/testing/skill-validation.md:39-52`
- Modify: `docs/superpowers/specs/2026-03-26-skill-validation-design.md:195-210`

- [ ] **Step 1: 更新 runbook Phase 1 和 Phase 2 列表**

修改 `docs/superpowers/testing/skill-validation.md`：
- 在 `### Phase 1` 列表中，在 `SA-02` 后添加 `SA-13`
- 在 `### Phase 2` 列表末尾添加 `SA-14`
- 在 `### 流程场景层` 列表中添加 `SA-13` 作为代表 case

- [ ] **Step 2: 更新 runbook 说明多轮 case**

在 `## Layer map` 之后添加说明：

```markdown
> **注**：部分 catalog case（如 `SA-13`、`SA-14`）使用多轮 `turns` 定义来表达回合边界。这些 case 的第一轮必须是 `STOP_AND_ASK`，第二轮才进入成功分支。
```

- [ ] **Step 3: 更新设计文档**

在 `docs/superpowers/specs/2026-03-26-skill-validation-design.md` 的用例矩阵部分，添加 `SA-13` 和 `SA-14` 的描述，说明它们是新增的多轮 case。

- [ ] **Step 4: 提交更改**

```bash
git add docs/superpowers/testing/skill-validation.md docs/superpowers/specs/2026-03-26-skill-validation-design.md
git commit -m "docs: update runbook and design with SA-13/SA-14 multi-turn cases"
```

---

## Task 7: 最终验证全量测试通过

**Files:**
- Run: 全量测试

- [ ] **Step 1: 运行全量 skill_validation 测试**

Run: `python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v`
Expected: 全部 PASS

- [ ] **Step 2: 如有失败，定位并修复**

如果测试失败，检查失败原因并回溯修复。

- [ ] **Step 3: 提交最终更改**

```bash
git add .
git commit -m "feat: complete setup-architect multi-turn validation modeling"
```

---

## 验证检查清单

完成所有任务后，确认：

- [ ] `skills/setup-architect/SKILL.md` 包含明确的 `STOP_AND_ASK` 停顿语义
- [ ] `skills/setup-architect/references/technical-solution-template-customization.md` 包含场景 A 的未回答状态定义
- [ ] `tests/skill_validation/case_catalog.py` 包含 `ConversationTurn` 数据结构和 `SA-13`、`SA-14`
- [ ] `tests/skill_validation/test_case_catalog.py` 包含多轮元数据校验
- [ ] `tests/skill_validation/test_setup_architect_contracts.py` 包含顺序断言
- [ ] `tests/skill_validation/test_setup_architect_conversation_simulation.py` 存在并通过
- [ ] `docs/superpowers/testing/skill-validation.md` 已同步更新
- [ ] `docs/superpowers/specs/2026-03-26-skill-validation-design.md` 已同步更新
- [ ] 全量测试 `python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v` 全部通过
---
