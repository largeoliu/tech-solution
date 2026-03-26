# Skill Validation Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a durable validation suite for `setup-architect` and `create-technical-solution` that turns the approved design into executable catalog, contract, fixture, and CI checks.

**Architecture:** Keep the existing GitHub Actions shell layout checks as the static-contract base, then add a Python `unittest` suite under `tests/skill_validation/` for case catalog coverage, repository contract assertions, fixture preparation, and workflow integration. The suite stays dependency-free by using only the Python standard library, so local runs and CI stay lightweight.

**Tech Stack:** Markdown, Python 3 standard library (`unittest`, `pathlib`, `tempfile`, `shutil`, `contextlib`), GitHub Actions YAML, repository skill documents

---

## File Structure

- Create: `tests/__init__.py` - marks `tests/` as an importable package for `unittest` discovery.
- Create: `tests/skill_validation/__init__.py` - marks the validation suite as a package.
- Create: `tests/skill_validation/case_catalog.py` - durable source of truth for all `SA-*` and `CTS-*` cases, phases, fixtures, and expected results.
- Create: `tests/skill_validation/helpers.py` - shared repo readers, heading extraction helpers, and temporary project bootstrap helpers.
- Create: `tests/skill_validation/test_case_catalog.py` - verifies the catalog covers the approved design and stays internally consistent.
- Create: `tests/skill_validation/test_static_layout.py` - regression checks for assistant-target installation layout and `.architecture/` bootstrap invariants.
- Create: `tests/skill_validation/test_setup_architect_contracts.py` - asserts the formal `setup-architect` contract is explicit across main and reference docs.
- Create: `tests/skill_validation/test_create_technical_solution_contracts.py` - asserts the formal `create-technical-solution` contract is explicit across main and reference docs.
- Create: `tests/skill_validation/test_workflow_integration.py` - asserts CI and local runbook wiring stay aligned.
- Create: `tests/skill_validation/testdata/custom-template.md` - valid custom template fixture with a clearly different top-level structure.
- Create: `tests/skill_validation/testdata/ambiguous-template.md` - deliberately sparse template fixture for ambiguous placement scenarios.
- Create: `tests/skill_validation/testdata/template-fragment.md` - invalid partial template input fixture for replacement-boundary tests.
- Create: `docs/superpowers/testing/skill-validation.md` - operator runbook for layers, commands, phases, and known open contract decisions.
- Modify: `.github/workflows/skills-integration-tests.yml` - add Python validation suite execution after existing layout checks.
- Read: `docs/superpowers/specs/2026-03-26-skill-validation-design.md` - approved design spec to cover completely.
- Read: `skills/setup-architect/SKILL.md`
- Read: `skills/setup-architect/references/installation-procedures.md`
- Read: `skills/setup-architect/references/member-customization.md`
- Read: `skills/setup-architect/references/principles-customization.md`
- Read: `skills/setup-architect/references/technical-solution-template-customization.md`
- Read: `skills/create-technical-solution/SKILL.md`
- Read: `skills/create-technical-solution/references/solution-process.md`
- Read: `skills/create-technical-solution/references/template-adaptation.md`
- Read: `skills/create-technical-solution/references/solution-analysis-guide.md`

### Task 1: Publish the Validation Case Catalog

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/skill_validation/__init__.py`
- Create: `tests/skill_validation/case_catalog.py`
- Create: `tests/skill_validation/test_case_catalog.py`
- Read: `docs/superpowers/specs/2026-03-26-skill-validation-design.md`

- [ ] **Step 1: Write the failing catalog coverage test**

```python
import unittest

from tests.skill_validation.case_catalog import (
    ALL_CASES,
    PHASE_1_CASE_IDS,
    PHASE_2_CASE_IDS,
    PHASE_3_CASE_IDS,
)


EXPECTED_PHASE_1 = {
    "SA-01",
    "SA-02",
    "SA-07",
    "SA-08",
    "CTS-01",
    "CTS-02",
    "CTS-04",
    "CTS-07",
    "CTS-08",
}

EXPECTED_PHASE_2 = {
    "SA-03",
    "SA-04",
    "SA-05",
    "SA-06",
    "CTS-03",
    "CTS-05",
    "CTS-06",
    "CTS-09",
}

EXPECTED_PHASE_3 = {
    "SA-09",
    "SA-10",
    "SA-11",
    "SA-12",
    "CTS-10",
    "CTS-11",
    "CTS-12",
}


class CaseCatalogTests(unittest.TestCase):
    def test_case_ids_are_unique(self) -> None:
        case_ids = [case.case_id for case in ALL_CASES]
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_catalog_contains_all_design_cases(self) -> None:
        self.assertEqual(len(ALL_CASES), 24)
        self.assertEqual(set(PHASE_1_CASE_IDS), EXPECTED_PHASE_1)
        self.assertEqual(set(PHASE_2_CASE_IDS), EXPECTED_PHASE_2)
        self.assertEqual(set(PHASE_3_CASE_IDS), EXPECTED_PHASE_3)

    def test_every_case_has_actionable_metadata(self) -> None:
        for case in ALL_CASES:
            with self.subTest(case_id=case.case_id):
                self.assertTrue(case.skill)
                self.assertTrue(case.layer)
                self.assertTrue(case.fixture)
                self.assertTrue(case.purpose)
                self.assertTrue(case.expected_result)
                self.assertTrue(
                    case.assert_paths
                    or case.assert_structure
                    or case.assert_semantics
                    or case.assert_safety
                )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the catalog test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_case_catalog -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tests.skill_validation.case_catalog'`

- [ ] **Step 3: Create the package markers and full case catalog**

```python
# tests/__init__.py
```

```python
# tests/skill_validation/__init__.py
```

```python
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ValidationCase:
    case_id: str
    skill: str
    layer: str
    fixture: str
    purpose: str
    expected_result: str
    assert_paths: Tuple[str, ...] = ()
    assert_structure: Tuple[str, ...] = ()
    assert_semantics: Tuple[str, ...] = ()
    assert_safety: Tuple[str, ...] = ()
    forbidden_behavior: Tuple[str, ...] = ()


def vcase(
    case_id: str,
    skill: str,
    layer: str,
    fixture: str,
    purpose: str,
    expected_result: str,
    *,
    assert_paths: Tuple[str, ...] = (),
    assert_structure: Tuple[str, ...] = (),
    assert_semantics: Tuple[str, ...] = (),
    assert_safety: Tuple[str, ...] = (),
    forbidden_behavior: Tuple[str, ...] = (),
) -> ValidationCase:
    return ValidationCase(
        case_id=case_id,
        skill=skill,
        layer=layer,
        fixture=fixture,
        purpose=purpose,
        expected_result=expected_result,
        assert_paths=assert_paths,
        assert_structure=assert_structure,
        assert_semantics=assert_semantics,
        assert_safety=assert_safety,
        forbidden_behavior=forbidden_behavior,
    )


SETUP_ARCHITECT_CASES = (
    vcase(
        "SA-01",
        "setup-architect",
        "流程场景层",
        "empty-project",
        "锁定最基础的 setup 成功路径",
        "SUCCESS_INIT",
        assert_paths=(
            ".architecture/technical-solutions/",
            ".architecture/templates/",
            ".architecture/templates/technical-solution-template.md",
            ".architecture/members.yml",
            ".architecture/principles.md",
        ),
        assert_structure=(".architecture 最小结构完整",),
        assert_safety=("只创建最小必需结构",),
        forbidden_behavior=("写入 legacy 路径",),
    ),
    vcase(
        "SA-02",
        "setup-architect",
        "流程场景层",
        "complete-architecture-default-template",
        "防止重复 setup 产生重复目录和副产物",
        "SUCCESS_INIT",
        assert_paths=(".architecture/",),
        assert_structure=("不生成 .architecture/.architecture", "不生成重复模板"),
        assert_safety=("不引入 legacy 或临时副产物",),
        forbidden_behavior=("嵌套 .architecture", "重复模板副本"),
    ),
    vcase(
        "SA-03",
        "setup-architect",
        "行为回归层",
        "partial-architecture-missing-one-file",
        "只补缺失项，不覆盖已有项",
        "SUCCESS_INIT",
        assert_paths=("缺失文件被补齐",),
        assert_structure=("现有文件保持原位",),
        assert_safety=("已有内容不被无提示覆盖",),
        forbidden_behavior=("重写无缺失文件",),
    ),
    vcase(
        "SA-04",
        "setup-architect",
        "行为回归层",
        "complete-architecture-default-template",
        "用户拒绝定制模板时保留当前模板",
        "SUCCESS_INIT",
        assert_paths=(".architecture/templates/technical-solution-template.md",),
        assert_structure=("模板路径不变",),
        assert_semantics=("模板最终状态明确为保留当前模板",),
        assert_safety=("不发生模板替换",),
        forbidden_behavior=("无用户请求时覆盖模板",),
    ),
    vcase(
        "SA-05",
        "setup-architect",
        "行为回归层",
        "template-replacement-inputs",
        "初始化尾声允许整文件替换模板",
        "SUCCESS_REPLACE_TEMPLATE",
        assert_paths=(".architecture/templates/technical-solution-template.md",),
        assert_structure=("整体替换单个目标文件",),
        assert_safety=("不做局部 merge",),
        forbidden_behavior=("局部编辑", "内容合并"),
    ),
    vcase(
        "SA-06",
        "setup-architect",
        "行为回归层",
        "complete-architecture-default-template",
        "安装后仅替换模板时跳过完整 setup",
        "SUCCESS_REPLACE_TEMPLATE",
        assert_paths=(".architecture/templates/technical-solution-template.md",),
        assert_structure=("只走模板替换分支",),
        assert_safety=("不重跑初始化流程",),
        forbidden_behavior=("重新安装 .architecture 基础结构",),
    ),
    vcase(
        "SA-07",
        "setup-architect",
        "对抗边界层",
        "partial-architecture-missing-one-file",
        "模板替换前置不满足时必须停机",
        "STOP_AND_REDIRECT",
        assert_paths=("缺失前置项被明确指出",),
        assert_safety=("要求先完成完整 setup", "不静默补文件"),
        forbidden_behavior=("边补环境边替换模板",),
    ),
    vcase(
        "SA-08",
        "setup-architect",
        "对抗边界层",
        "template-replacement-inputs",
        "拒绝模板片段和口头描述输入",
        "STOP_AND_ASK",
        assert_semantics=("继续索要完整 Markdown、路径或链接",),
        assert_safety=("不自动生成模板", "不做局部编辑", "不做内容合并"),
        forbidden_behavior=("根据片段脑补完整模板",),
    ),
    vcase(
        "SA-09",
        "setup-architect",
        "行为回归层",
        "complete-architecture-default-template",
        "成员定制必须保留核心成员",
        "SUCCESS_INIT",
        assert_semantics=("保留系统架构师", "保留领域专家", "保留安全专家", "保留性能专家", "保留可维护性专家"),
        assert_safety=("允许增补专家，不允许替换核心成员",),
        forbidden_behavior=("删除核心成员",),
    ),
    vcase(
        "SA-10",
        "setup-architect",
        "行为回归层",
        "complete-architecture-default-template",
        "原则定制必须保留核心原则和最低覆盖范围",
        "SUCCESS_INIT",
        assert_semantics=(
            "保留核心原则",
            "覆盖模块边界与依赖方向",
            "覆盖 API / 事件 / 数据边界",
            "覆盖测试和验证基线",
            "覆盖安全与合规底线",
            "覆盖技术方案和实施计划的决策标准",
        ),
        assert_safety=("不删除核心原则",),
        forbidden_behavior=("删除核心原则",),
    ),
    vcase(
        "SA-11",
        "setup-architect",
        "静态契约层",
        "complete-architecture-default-template",
        "最终总结前结构必须已验证",
        "SUCCESS_INIT",
        assert_paths=(
            ".architecture/technical-solutions/",
            ".architecture/templates/",
            ".architecture/templates/technical-solution-template.md",
            ".architecture/members.yml",
            ".architecture/principles.md",
        ),
        assert_safety=("无 legacy 目录",),
        forbidden_behavior=("保留 .architecture/solutions", ".architecture/plans", ".architecture/reviews"),
    ),
    vcase(
        "SA-12",
        "setup-architect",
        "静态契约层",
        "empty-project",
        "安装和初始化不应引入无关产物",
        "SUCCESS_INIT",
        assert_structure=("assistant 目标目录唯一",),
        assert_safety=("无 CLAUDE.md", "无 agent_docs", "无嵌套 .git", "无随机 temp 目录"),
        forbidden_behavior=("生成无关安装副产物",),
    ),
)


CREATE_TECHNICAL_SOLUTION_CASES = (
    vcase(
        "CTS-01",
        "create-technical-solution",
        "流程场景层",
        "empty-project",
        "前置全缺失时立即停止并回指 setup-architect",
        "STOP_AND_REDIRECT",
        assert_paths=("明确列出缺失前置",),
        assert_safety=("不自动创建 .architecture/*", "不继续生成技术方案"),
        forbidden_behavior=("伪造初始化产物",),
    ),
    vcase(
        "CTS-02",
        "create-technical-solution",
        "流程场景层",
        "partial-architecture-missing-one-file",
        "任一关键前置缺失都必须停机",
        "STOP_AND_REDIRECT",
        assert_paths=(
            ".architecture/members.yml",
            ".architecture/principles.md",
            ".architecture/templates/technical-solution-template.md",
        ),
        assert_safety=("不允许半继续执行",),
        forbidden_behavior=("跳过缺失项继续生成",),
    ),
    vcase(
        "CTS-03",
        "create-technical-solution",
        "行为回归层",
        "complete-architecture-default-template",
        "标准成功路径把结果写到正式目录",
        "SUCCESS_CREATE",
        assert_paths=(".architecture/technical-solutions/payment-pipeline-rework.md",),
        assert_structure=("生成正式技术方案文档",),
        assert_safety=("不写入其他目录",),
        forbidden_behavior=("输出聊天式说明替代文档",),
    ),
    vcase(
        "CTS-04",
        "create-technical-solution",
        "行为回归层",
        "complete-architecture-custom-template",
        "结果必须遵循当前自定义模板，而不是默认模板",
        "SUCCESS_CREATE",
        assert_structure=("保留当前模板顶层结构",),
        assert_semantics=("先读取当前模板",),
        assert_safety=("不回退默认模板结构",),
        forbidden_behavior=("发明默认顶层章节",),
    ),
    vcase(
        "CTS-05",
        "create-technical-solution",
        "行为回归层",
        "complete-architecture-custom-template",
        "允许加小节但禁止新增模板外一级章节",
        "SUCCESS_CREATE",
        assert_structure=("一级结构保持不变",),
        assert_safety=("只在现有章节内细化",),
        forbidden_behavior=("新增用户模板没有定义的一级章节",),
    ),
    vcase(
        "CTS-06",
        "create-technical-solution",
        "行为回归层",
        "complete-architecture-default-template",
        "所有必填信息块都必须被覆盖",
        "SUCCESS_CREATE",
        assert_semantics=(
            "问题与背景",
            "目标与非目标",
            "约束与依赖",
            "推荐方案",
            "备选方案与权衡",
            "详细设计",
            "风险与缓解",
            "实施建议",
            "评审关注点",
            "未决问题",
        ),
        assert_safety=("不遗漏强制信息块",),
        forbidden_behavior=("只输出零散结论",),
    ),
    vcase(
        "CTS-07",
        "create-technical-solution",
        "对抗边界层",
        "complete-architecture-custom-template",
        "模板无法安全承载信息块时必须停下来询问",
        "STOP_AND_ASK",
        assert_semantics=("明确说明无法安全落位的信息块",),
        assert_safety=("不擅自新增一级章节",),
        forbidden_behavior=("猜测模板语义继续生成",),
    ),
    vcase(
        "CTS-08",
        "create-technical-solution",
        "对抗边界层",
        "existing-solution-file",
        "目标文件已存在时必须先确认覆盖或另存",
        "STOP_AND_ASK",
        assert_paths=(".architecture/technical-solutions/payment-pipeline-rework.md",),
        assert_safety=("没有未经确认覆盖已有文件",),
        forbidden_behavior=("静默覆盖既有文档",),
    ),
    vcase(
        "CTS-09",
        "create-technical-solution",
        "行为回归层",
        "existing-solution-file",
        "用户拒绝覆盖时保留原文件并等待另存决策",
        "SUCCESS_SAVE_AS",
        assert_paths=("原始目标文件保持不变",),
        assert_safety=("停止覆盖原文件",),
        forbidden_behavior=("继续写回原路径",),
    ),
    vcase(
        "CTS-10",
        "create-technical-solution",
        "对抗边界层",
        "complete-architecture-default-template",
        "多类型主题按成员并集参与，且始终包含系统架构师",
        "SUCCESS_CREATE",
        assert_semantics=("成员取并集并去重", "系统架构师始终参与"),
        assert_safety=("不遗漏高风险主题所需成员",),
        forbidden_behavior=("只按单一类型裁剪成员",),
    ),
    vcase(
        "CTS-11",
        "create-technical-solution",
        "流程场景层",
        "complete-architecture-default-template",
        "前置齐全时应能独立执行，不依赖刚跑过 setup",
        "SUCCESS_CREATE",
        assert_paths=(".architecture/technical-solutions/payment-pipeline-rework.md",),
        assert_semantics=("仅依赖既有 .architecture 契约",),
        assert_safety=("不要求 setup 继续参与",),
        forbidden_behavior=("回头猜安装过程上下文",),
    ),
    vcase(
        "CTS-12",
        "create-technical-solution",
        "对抗边界层",
        "partial-architecture-missing-one-file",
        "前置不完整时不得脑补成员、原则或模板",
        "STOP_AND_REDIRECT",
        assert_safety=("不边补环境边写 solution",),
        forbidden_behavior=("伪造 members.yml", "伪造 principles.md", "伪造模板文件"),
    ),
)


ALL_CASES = SETUP_ARCHITECT_CASES + CREATE_TECHNICAL_SOLUTION_CASES

PHASE_1_CASE_IDS = (
    "SA-01",
    "SA-02",
    "SA-07",
    "SA-08",
    "CTS-01",
    "CTS-02",
    "CTS-04",
    "CTS-07",
    "CTS-08",
)

PHASE_2_CASE_IDS = (
    "SA-03",
    "SA-04",
    "SA-05",
    "SA-06",
    "CTS-03",
    "CTS-05",
    "CTS-06",
    "CTS-09",
)

PHASE_3_CASE_IDS = (
    "SA-09",
    "SA-10",
    "SA-11",
    "SA-12",
    "CTS-10",
    "CTS-11",
    "CTS-12",
)

CASE_INDEX = {case.case_id: case for case in ALL_CASES}
```

- [ ] **Step 4: Run the catalog test to verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_case_catalog -v`
Expected: PASS with 3 tests run and 0 failures

- [ ] **Step 5: Commit the catalog milestone**

```bash
git add tests/__init__.py tests/skill_validation/__init__.py tests/skill_validation/case_catalog.py tests/skill_validation/test_case_catalog.py
git commit -m "test: add skill validation case catalog"
```

### Task 2: Add Shared Helpers and Static Layout Regression Tests

**Files:**
- Create: `tests/skill_validation/helpers.py`
- Create: `tests/skill_validation/test_static_layout.py`
- Read: `.github/workflows/skills-integration-tests.yml`
- Read: `skills/setup-architect/templates/technical-solution-template.md`
- Read: `skills/setup-architect/templates/members-template.yml`
- Read: `skills/setup-architect/templates/principles-template.md`

- [ ] **Step 1: Write the failing static layout test**

```python
import unittest

from tests.skill_validation.helpers import ASSISTANT_TARGETS, bootstrapped_project


class StaticLayoutTests(unittest.TestCase):
    def test_bootstrap_creates_minimum_architecture(self) -> None:
        for assistant in ASSISTANT_TARGETS:
            with self.subTest(assistant=assistant):
                with bootstrapped_project(assistant) as project_dir:
                    self.assertTrue((project_dir / ".architecture").is_dir())
                    self.assertTrue((project_dir / ".architecture/technical-solutions").is_dir())
                    self.assertTrue((project_dir / ".architecture/templates").is_dir())
                    self.assertTrue(
                        (project_dir / ".architecture/templates/technical-solution-template.md").is_file()
                    )
                    self.assertTrue((project_dir / ".architecture/members.yml").is_file())
                    self.assertTrue((project_dir / ".architecture/principles.md").is_file())

    def test_only_selected_assistant_target_exists(self) -> None:
        for assistant, selected_target in ASSISTANT_TARGETS.items():
            with self.subTest(assistant=assistant):
                with bootstrapped_project(assistant) as project_dir:
                    for target in ASSISTANT_TARGETS.values():
                        target_path = project_dir / target
                        if target == selected_target:
                            self.assertTrue(target_path.is_dir())
                            self.assertFalse(target_path.is_symlink())
                            self.assertFalse((target_path / ".git").exists())
                        else:
                            self.assertFalse(target_path.exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the static layout test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_static_layout -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tests.skill_validation.helpers'`

- [ ] **Step 3: Implement the shared helpers and layout regression test**

```python
from contextlib import contextmanager
from pathlib import Path
import shutil
import tempfile
from typing import Iterable, Iterator


REPO_ROOT = Path(__file__).resolve().parents[2]

ASSISTANT_TARGETS = {
    "claude": ".claude/skills",
    "qoder": ".qoder/skills",
    "lingma": ".lingma/skills",
    "generic": ".agents/skills",
}


def repo_path(*parts: str) -> Path:
    return REPO_ROOT.joinpath(*parts)


def read_repo_text(relative_path: str) -> str:
    return repo_path(relative_path).read_text(encoding="utf-8")


def testdata_path(name: str) -> Path:
    return repo_path("tests", "skill_validation", "testdata", name)


def top_level_headings(markdown: str) -> list[str]:
    headings: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            headings.append(line[3:].strip())
    return headings


def require_all_snippets(testcase, text: str, snippets: Iterable[str]) -> None:
    for snippet in snippets:
        testcase.assertIn(snippet, text)


@contextmanager
def bootstrapped_project(assistant: str) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir_name:
        project_dir = Path(temp_dir_name) / assistant
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "README.md").write_text("# Skill-only test project\n", encoding="utf-8")

        selected_target = project_dir / ASSISTANT_TARGETS[assistant]
        selected_target.parent.mkdir(parents=True, exist_ok=True)

        shutil.copytree(repo_path("skills", "setup-architect"), selected_target / "setup-architect")
        shutil.copytree(
            repo_path("skills", "create-technical-solution"),
            selected_target / "create-technical-solution",
        )

        skill_root = selected_target / "setup-architect"
        (project_dir / ".architecture" / "technical-solutions").mkdir(parents=True, exist_ok=True)
        (project_dir / ".architecture" / "templates").mkdir(parents=True, exist_ok=True)

        shutil.copyfile(
            skill_root / "templates" / "technical-solution-template.md",
            project_dir / ".architecture" / "templates" / "technical-solution-template.md",
        )
        shutil.copyfile(
            skill_root / "templates" / "members-template.yml",
            project_dir / ".architecture" / "members.yml",
        )
        shutil.copyfile(
            skill_root / "templates" / "principles-template.md",
            project_dir / ".architecture" / "principles.md",
        )

        yield project_dir
```

```python
import unittest

from tests.skill_validation.helpers import ASSISTANT_TARGETS, bootstrapped_project


class StaticLayoutTests(unittest.TestCase):
    def test_bootstrap_creates_minimum_architecture(self) -> None:
        for assistant in ASSISTANT_TARGETS:
            with self.subTest(assistant=assistant):
                with bootstrapped_project(assistant) as project_dir:
                    self.assertTrue((project_dir / ".architecture").is_dir())
                    self.assertTrue((project_dir / ".architecture/technical-solutions").is_dir())
                    self.assertTrue((project_dir / ".architecture/templates").is_dir())
                    self.assertTrue(
                        (project_dir / ".architecture/templates/technical-solution-template.md").is_file()
                    )
                    self.assertTrue((project_dir / ".architecture/members.yml").is_file())
                    self.assertTrue((project_dir / ".architecture/principles.md").is_file())
                    self.assertFalse((project_dir / ".architecture/.architecture").exists())
                    self.assertFalse((project_dir / ".architecture/agent_docs").exists())
                    self.assertFalse((project_dir / "CLAUDE.md").exists())
                    self.assertFalse((project_dir / ".architecture/solutions").exists())
                    self.assertFalse((project_dir / ".architecture/plans").exists())
                    self.assertFalse((project_dir / ".architecture/reviews").exists())

    def test_only_selected_assistant_target_exists(self) -> None:
        for assistant, selected_target in ASSISTANT_TARGETS.items():
            with self.subTest(assistant=assistant):
                with bootstrapped_project(assistant) as project_dir:
                    for target in ASSISTANT_TARGETS.values():
                        target_path = project_dir / target
                        if target == selected_target:
                            self.assertTrue(target_path.is_dir())
                            self.assertFalse(target_path.is_symlink())
                            self.assertFalse((target_path / ".git").exists())
                            self.assertTrue((target_path / "setup-architect" / "SKILL.md").is_file())
                            self.assertTrue(
                                (target_path / "create-technical-solution" / "SKILL.md").is_file()
                            )
                        else:
                            self.assertFalse(target_path.exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run the static layout test to verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_static_layout -v`
Expected: PASS with 2 tests run and 0 failures

- [ ] **Step 5: Commit the helper milestone**

```bash
git add tests/skill_validation/helpers.py tests/skill_validation/test_static_layout.py
git commit -m "test: add skill validation layout helpers"
```

### Task 3: Add `setup-architect` Contract Tests

**Files:**
- Create: `tests/skill_validation/test_setup_architect_contracts.py`
- Modify: `tests/skill_validation/helpers.py`
- Read: `skills/setup-architect/SKILL.md`
- Read: `skills/setup-architect/references/installation-procedures.md`
- Read: `skills/setup-architect/references/member-customization.md`
- Read: `skills/setup-architect/references/principles-customization.md`
- Read: `skills/setup-architect/references/technical-solution-template-customization.md`

- [ ] **Step 1: Write the failing `setup-architect` contract test**

```python
import unittest

from tests.skill_validation.helpers import load_setup_contract_sources, require_all_snippets


class SetupArchitectContractTests(unittest.TestCase):
    def test_main_skill_exposes_install_and_template_only_paths(self) -> None:
        sources = load_setup_contract_sources()
        require_all_snippets(
            self,
            sources["main"],
            (
                "### 2. 安装架构框架",
                "### 6. 最后确认技术方案模板并收尾",
                "## 安装后定制技术方案模板",
                "不要重跑上述初始安装流程",
            ),
        )

    def test_template_customization_requires_complete_setup_and_full_input(self) -> None:
        sources = load_setup_contract_sources()
        require_all_snippets(
            self,
            sources["template_customization"],
            (
                "若任一校验失败，则视为 setup 不完整，应停止并要求用户先执行完整初始化；不要静默补文件。",
                "接受用户直接提供的完整 Markdown 模板内容、文件路径或者链接地址。",
                "收到后整体替换 `.architecture/templates/technical-solution-template.md`。",
                "不支持自动生成模板、局部编辑或内容合并。",
            ),
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the `setup-architect` contract test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_setup_architect_contracts -v`
Expected: FAIL with `ImportError: cannot import name 'load_setup_contract_sources'`

- [ ] **Step 3: Implement the helper extension and full `setup-architect` contract suite**

```python
def load_setup_contract_sources() -> dict[str, str]:
    return {
        "main": read_repo_text("skills/setup-architect/SKILL.md"),
        "installation": read_repo_text("skills/setup-architect/references/installation-procedures.md"),
        "member_customization": read_repo_text(
            "skills/setup-architect/references/member-customization.md"
        ),
        "principles_customization": read_repo_text(
            "skills/setup-architect/references/principles-customization.md"
        ),
        "template_customization": read_repo_text(
            "skills/setup-architect/references/technical-solution-template-customization.md"
        ),
    }
```

```python
import unittest

from tests.skill_validation.helpers import load_setup_contract_sources, require_all_snippets


class SetupArchitectContractTests(unittest.TestCase):
    def test_main_skill_exposes_install_and_template_only_paths(self) -> None:
        sources = load_setup_contract_sources()
        require_all_snippets(
            self,
            sources["main"],
            (
                "### 2. 安装架构框架",
                "### 6. 最后确认技术方案模板并收尾",
                "## 安装后定制技术方案模板",
                "不要重跑上述初始安装流程",
            ),
        )

    def test_installation_reference_creates_minimum_structure(self) -> None:
        sources = load_setup_contract_sources()
        require_all_snippets(
            self,
            sources["installation"],
            (
                "mkdir -p .architecture/technical-solutions",
                "mkdir -p .architecture/templates",
                ".architecture/templates/technical-solution-template.md",
                ".architecture/members.yml",
                ".architecture/principles.md",
            ),
        )

    def test_template_customization_requires_complete_setup_and_full_input(self) -> None:
        sources = load_setup_contract_sources()
        require_all_snippets(
            self,
            sources["template_customization"],
            (
                "若任一校验失败，则视为 setup 不完整，应停止并要求用户先执行完整初始化；不要静默补文件。",
                "接受用户直接提供的完整 Markdown 模板内容、文件路径或者链接地址。",
                "收到后整体替换 `.architecture/templates/technical-solution-template.md`。",
                "不支持恢复默认模板。",
                "不支持自动生成模板、局部编辑或内容合并。",
            ),
        )

    def test_template_customization_keeps_both_scenario_branches_explicit(self) -> None:
        sources = load_setup_contract_sources()
        require_all_snippets(
            self,
            sources["template_customization"],
            (
                "若回答“不需要”，保留当前 `.architecture/templates/technical-solution-template.md`。",
                "直接要求用户提供完整 Markdown 模板内容，不存在“保留当前模板”的分支。",
            ),
        )

    def test_member_customization_preserves_core_members(self) -> None:
        sources = load_setup_contract_sources()
        require_all_snippets(
            self,
            sources["member_customization"],
            (
                "系统架构师",
                "领域专家",
                "安全专家",
                "性能专家",
                "可维护性专家",
                "添加技术专家，不要替换核心成员。",
            ),
        )

    def test_principles_customization_preserves_core_principles_and_minimum_coverage(self) -> None:
        sources = load_setup_contract_sources()
        require_all_snippets(
            self,
            sources["principles_customization"],
            (
                "不要删除下方“核心原则（保留这些）”中的基础原则",
                "至少覆盖模块边界与依赖方向、API / 事件 / 数据边界、测试和验证基线、安全与合规底线，以及技术方案和实施计划的决策标准",
                "宜居代码",
                "清晰优于炫技",
                "关注点分离",
                "可演化性",
                "可观测性",
                "设计即安全",
                "领域中心设计",
                "务实的简洁性",
                "变更影响意识",
            ),
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run the `setup-architect` contract test to verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_setup_architect_contracts -v`
Expected: PASS with 6 tests run and 0 failures

- [ ] **Step 5: Commit the `setup-architect` contract suite**

```bash
git add tests/skill_validation/helpers.py tests/skill_validation/test_setup_architect_contracts.py
git commit -m "test: add setup-architect contract checks"
```

### Task 4: Add `create-technical-solution` Contract Tests and Behavior Fixtures

**Files:**
- Create: `tests/skill_validation/test_create_technical_solution_contracts.py`
- Create: `tests/skill_validation/testdata/custom-template.md`
- Create: `tests/skill_validation/testdata/ambiguous-template.md`
- Create: `tests/skill_validation/testdata/template-fragment.md`
- Read: `skills/create-technical-solution/SKILL.md`
- Read: `skills/create-technical-solution/references/solution-process.md`
- Read: `skills/create-technical-solution/references/template-adaptation.md`
- Read: `skills/create-technical-solution/references/solution-analysis-guide.md`

- [ ] **Step 1: Write the failing `create-technical-solution` contract test**

```python
import unittest

from tests.skill_validation.helpers import (
    load_create_solution_contract_sources,
    require_all_snippets,
    testdata_path,
)


class CreateTechnicalSolutionContractTests(unittest.TestCase):
    def test_main_skill_requires_current_template_and_redirects_on_missing_prereqs(self) -> None:
        sources = load_create_solution_contract_sources()
        require_all_snippets(
            self,
            sources["main"],
            (
                "始终先读取当前 `.architecture/templates/technical-solution-template.md`",
                ".architecture/members.yml",
                ".architecture/principles.md",
                ".architecture/templates/technical-solution-template.md",
                "任一缺失时立即停止，明确说明初始化未完成，并引导用户先使用 `setup-architect`。",
            ),
        )

    def test_behavior_fixture_files_exist(self) -> None:
        self.assertTrue(testdata_path("custom-template.md").is_file())
        self.assertTrue(testdata_path("ambiguous-template.md").is_file())
        self.assertTrue(testdata_path("template-fragment.md").is_file())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the `create-technical-solution` contract test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts -v`
Expected: FAIL with `ImportError: cannot import name 'load_create_solution_contract_sources'`

- [ ] **Step 3: Add behavior fixtures and the full `create-technical-solution` contract suite**

```markdown
# 支付链路改造方案

## 决策摘要

## 当前痛点与目标

## 候选路径比较

## 详细设计

## 风险与发布

## 未决事项
```

```markdown
# 极简方案记录

## 主体

这里刻意只保留一个模糊章节，用来验证“无法安全落位时必须停下来问用户”。
```

```markdown
## 仅有局部片段

这里只是替换模板时的无效片段输入，不是完整模板。
```

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
        "analysis_guide": read_repo_text(
            "skills/create-technical-solution/references/solution-analysis-guide.md"
        ),
    }
```

```python
import unittest

from tests.skill_validation.helpers import (
    load_create_solution_contract_sources,
    require_all_snippets,
    testdata_path,
    top_level_headings,
)


class CreateTechnicalSolutionContractTests(unittest.TestCase):
    def test_main_skill_requires_current_template_and_redirects_on_missing_prereqs(self) -> None:
        sources = load_create_solution_contract_sources()
        require_all_snippets(
            self,
            sources["main"],
            (
                "始终先读取当前 `.architecture/templates/technical-solution-template.md`",
                ".architecture/members.yml",
                ".architecture/principles.md",
                ".architecture/templates/technical-solution-template.md",
                "任一缺失时立即停止，明确说明初始化未完成，并引导用户先使用 `setup-architect`。",
            ),
        )

    def test_main_skill_requires_output_path_and_overwrite_confirmation(self) -> None:
        sources = load_create_solution_contract_sources()
        require_all_snippets(
            self,
            sources["main"],
            (
                "将最终文档写入 `.architecture/technical-solutions/[主题-短横线文件名].md`。",
                "先确认覆盖还是另存；不要静默覆盖无关文档。",
                "没有未经确认覆盖已有文件。",
            ),
        )

    def test_solution_process_defines_slug_rules_and_mandatory_information_blocks(self) -> None:
        sources = load_create_solution_contract_sources()
        require_all_snippets(
            self,
            sources["solution_process"],
            (
                "将空格、下划线和常见分隔符折叠为 `-`",
                "如果清洗结果为空，要求用户提供更明确的标题",
                "### 问题与背景",
                "### 目标与非目标",
                "### 约束与依赖",
                "### 推荐方案",
                "### 备选方案与权衡",
                "### 详细设计",
                "### 风险与缓解",
                "### 实施建议",
                "### 评审关注点",
                "### 未决问题",
            ),
        )

    def test_template_adaptation_forbids_new_top_level_sections_and_requires_stop_on_ambiguity(self) -> None:
        sources = load_create_solution_contract_sources()
        require_all_snippets(
            self,
            sources["template_adaptation"],
            (
                "不允许新增用户模板没有定义的一级章节。",
                "不要猜测，直接停止并向用户确认：",
                "哪个信息块无法安全落位",
                "当前有哪些可能归宿",
                "为什么继续自动放置风险高",
            ),
        )

    def test_solution_analysis_requires_system_architect_and_multi_type_union(self) -> None:
        sources = load_create_solution_contract_sources()
        require_all_snippets(
            self,
            sources["analysis_guide"],
            (
                "系统架构师始终参与",
                "参与成员取并集并去重",
                "必答问题取并集",
                "易漏风险取并集",
                "评审重点按风险高低排序",
            ),
        )

    def test_behavior_testdata_is_distinct_for_valid_and_ambiguous_templates(self) -> None:
        custom_text = testdata_path("custom-template.md").read_text(encoding="utf-8")
        ambiguous_text = testdata_path("ambiguous-template.md").read_text(encoding="utf-8")
        fragment_text = testdata_path("template-fragment.md").read_text(encoding="utf-8")

        self.assertGreaterEqual(len(top_level_headings(custom_text)), 5)
        self.assertEqual(top_level_headings(ambiguous_text), ["主体"])
        self.assertEqual(top_level_headings(fragment_text), ["仅有局部片段"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run the `create-technical-solution` contract test to verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts -v`
Expected: PASS with 6 tests run and 0 failures

- [ ] **Step 5: Commit the `create-technical-solution` contract suite**

```bash
git add tests/skill_validation/test_create_technical_solution_contracts.py tests/skill_validation/testdata/custom-template.md tests/skill_validation/testdata/ambiguous-template.md tests/skill_validation/testdata/template-fragment.md
git commit -m "test: add create-technical-solution contract checks"
```

### Task 5: Wire the Suite into CI and Add the Local Runbook

**Files:**
- Create: `tests/skill_validation/test_workflow_integration.py`
- Create: `docs/superpowers/testing/skill-validation.md`
- Modify: `.github/workflows/skills-integration-tests.yml`
- Read: `docs/superpowers/specs/2026-03-26-skill-validation-design.md`

- [ ] **Step 1: Write the failing workflow integration test**

```python
import unittest

from tests.skill_validation.helpers import read_repo_text, require_all_snippets


class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_runs_the_skill_validation_suite(self) -> None:
        workflow = read_repo_text(".github/workflows/skills-integration-tests.yml")
        require_all_snippets(
            self,
            workflow,
            (
                "- name: Run skill validation contract suite",
                'python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v',
            ),
        )

    def test_runbook_documents_layers_and_local_commands(self) -> None:
        runbook = read_repo_text("docs/superpowers/testing/skill-validation.md")
        require_all_snippets(
            self,
            runbook,
            (
                "# Skill Validation Runbook",
                "静态契约层",
                "流程场景层",
                "行为回归层",
                "对抗边界层",
                'python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v',
                "SA-01",
                "CTS-08",
            ),
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the workflow integration test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_workflow_integration -v`
Expected: FAIL with `FileNotFoundError` for `docs/superpowers/testing/skill-validation.md` or an assertion failure because the workflow step is missing

- [ ] **Step 3: Add the runbook, workflow step, and workflow integration test**

```markdown
# Skill Validation Runbook

## Scope

本运行手册对应 `docs/superpowers/specs/2026-03-26-skill-validation-design.md`，覆盖 `setup-architect` 与 `create-technical-solution` 的长期验证流程。

## 本地执行命令

```bash
python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v
```

## 分层说明

### 静态契约层

- 关注 assistant 安装目标、`.architecture/` 最小结构、禁止产物
- 代表 case：`SA-01`、`SA-02`、`SA-11`、`SA-12`

### 流程场景层

- 关注缺前置时的停机和回指、独立运行路径
- 代表 case：`CTS-01`、`CTS-02`、`CTS-11`

### 行为回归层

- 关注当前模板优先、必填信息块、分支行为
- 代表 case：`SA-03`、`SA-04`、`SA-05`、`SA-06`、`CTS-03`、`CTS-04`、`CTS-05`、`CTS-06`、`CTS-09`

### 对抗边界层

- 关注模板片段输入、已有目标文件、模板语义冲突、多类型主题
- 代表 case：`SA-07`、`SA-08`、`CTS-07`、`CTS-08`、`CTS-10`、`CTS-12`

## 推荐执行节奏

- 提交前：运行完整本地命令，并重点检查本次改动触及的 layer
- 合并前：确保 CI 中的 `Skills Integration Tests` 已通过
- 修改 `SKILL.md` 或 references 后：至少重跑 `python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v`

## 待确认契约

- 当 `.architecture/members.yml`、`.architecture/principles.md`、`.architecture/templates/technical-solution-template.md` 已存在而 `.architecture/technical-solutions/` 缺失时，`create-technical-solution` 是自动创建目录还是停机提示
- 主题到短横线文件名的规范化规则是否需要进一步收紧到单一实现
```

```yaml
      - name: Run skill validation contract suite
        run: python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v
```

```python
import unittest

from tests.skill_validation.helpers import read_repo_text, require_all_snippets


class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_runs_the_skill_validation_suite(self) -> None:
        workflow = read_repo_text(".github/workflows/skills-integration-tests.yml")
        require_all_snippets(
            self,
            workflow,
            (
                "- name: Run skill validation contract suite",
                'python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v',
            ),
        )

    def test_runbook_documents_layers_and_local_commands(self) -> None:
        runbook = read_repo_text("docs/superpowers/testing/skill-validation.md")
        require_all_snippets(
            self,
            runbook,
            (
                "# Skill Validation Runbook",
                "静态契约层",
                "流程场景层",
                "行为回归层",
                "对抗边界层",
                'python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v',
                "SA-01",
                "CTS-08",
            ),
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run the workflow integration test and then the full suite**

Run: `python3 -m unittest tests.skill_validation.test_workflow_integration -v && python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v`
Expected: PASS for the workflow integration module, then PASS for the full validation suite with 0 failures

- [ ] **Step 5: Commit the CI wiring and runbook**

```bash
git add tests/skill_validation/test_workflow_integration.py docs/superpowers/testing/skill-validation.md .github/workflows/skills-integration-tests.yml
git commit -m "test: wire skill validation suite into ci"
```

## Self-Review Checklist

- [ ] Confirm every requirement in `docs/superpowers/specs/2026-03-26-skill-validation-design.md` maps to at least one test module or catalog case.
- [ ] Search the plan implementation for placeholder terms with `rg -n "TBD|TODO|implement later|fill in details" tests/skill_validation docs/superpowers/testing .github/workflows/skills-integration-tests.yml` and fix any matches.
- [ ] Re-run `python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v` after the final task and confirm the output shows 0 failures.
