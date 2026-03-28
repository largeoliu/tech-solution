# Install Target Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Codify runtime-based install target routing so project installs choose the current assistant's directory deterministically, include Trae in the supported target matrix, and fail instead of guessing when runtime identity is missing or conflicting.

**Architecture:** Treat `INSTALLATION.md` as the normative installation contract, then lock that contract with focused `unittest` coverage. Extend the shared assistant-target registry, bootstrap tests, and GitHub Actions workflow so Trae participates in the same routing matrix as Claude, Qoder, Lingma, and generic installs.

**Tech Stack:** Markdown, Python 3 standard library (`unittest`, `pathlib`), GitHub Actions YAML

---

## File Structure

- Create: `tests/skill_validation/test_installation_contracts.py` - contract tests that pin Stage 1 runtime-routing rules, fail-fast behavior, and acceptance examples in `INSTALLATION.md`.
- Modify: `INSTALLATION.md` - replace directory-guessing wording with runtime-based `assistant_id + scope` routing rules, Trae project target mapping, and explicit failure conditions.
- Modify: `tests/skill_validation/helpers.py` - add `trae` to the shared `ASSISTANT_TARGETS` registry used by bootstrap helpers and static layout tests.
- Modify: `tests/skill_validation/test_static_layout.py` - add direct Trae assertions so bootstrap coverage fails loudly if Trae support regresses.
- Modify: `.github/workflows/skills-integration-tests.yml` - extend the assistant matrix and candidate-directory invariant loop to include `.trae/skills`.
- Modify: `tests/skill_validation/test_workflow_integration.py` - assert the workflow keeps Trae in the install matrix and candidate list.
- Read: `docs/superpowers/specs/2026-03-28-install-target-routing-design.md` - approved design to cover completely.
- Read: `INSTALLATION.md`
- Read: `tests/skill_validation/helpers.py`
- Read: `tests/skill_validation/test_static_layout.py`
- Read: `.github/workflows/skills-integration-tests.yml`
- Read: `tests/skill_validation/test_workflow_integration.py`

### Task 1: Lock the Installation Routing Contract

**Files:**
- Create: `tests/skill_validation/test_installation_contracts.py`
- Modify: `INSTALLATION.md`
- Read: `docs/superpowers/specs/2026-03-28-install-target-routing-design.md`

- [ ] **Step 1: Write the failing installation contract test file**

```python
import unittest
from pathlib import Path

from tests.skill_validation.helpers import require_all_snippets, require_snippets_in_order


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLATION_PATH = REPO_ROOT / "INSTALLATION.md"


class InstallationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.installation = INSTALLATION_PATH.read_text(encoding="utf-8")

    def test_stage1_routes_from_runtime_not_project_directories(self) -> None:
        require_snippets_in_order(
            self,
            self.installation,
            (
                "### Stage 1: 识别当前助手并解析目标目录",
                "`assistant_id` 只能来自当前 AI 助手宿主或运行时环境。",
                "不能根据项目里是否存在 `.qoder/`、`.trae/`、`.claude/` 等目录推断当前助手。",
                "若无法唯一识别当前助手，则停止安装并输出诊断。",
            ),
        )

    def test_stage1_keeps_project_target_registry_including_trae(self) -> None:
        require_all_snippets(
            self,
            self.installation,
            (
                "`claude -> .claude/skills`",
                "`qoder -> .qoder/skills`",
                "`lingma -> .lingma/skills`",
                "`trae -> .trae/skills`",
                "`generic -> .agents/skills`",
            ),
        )

    def test_stage1_documents_conflict_failures_and_acceptance_examples(self) -> None:
        require_all_snippets(
            self,
            self.installation,
            (
                "如果宿主显式信号与宿主特征识别结果冲突，也必须停止安装。",
                "`Trae runtime + existing .qoder/ -> .trae/skills`",
                "`Qoder runtime + existing .trae/ -> .qoder/skills`",
                "`unrecognized runtime + multiple assistant directories -> fail without guessing`",
            ),
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new installation contract test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_installation_contracts -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tests.skill_validation.test_installation_contracts'`

- [ ] **Step 3: Replace `INSTALLATION.md` with the runtime-routing contract**

```md
## 安装步骤

### Stage 1: 识别当前助手并解析目标目录

先识别当前 AI 助手运行环境，并把结果规范化为 `assistant_id`。

`assistant_id` 只能来自当前 AI 助手宿主或运行时环境。

不能根据项目里是否存在 `.qoder/`、`.trae/`、`.claude/` 等目录推断当前助手。

项目目录只能说明这个仓库曾经被哪些助手使用过，不能说明当前是谁在执行安装。

本安装说明默认讨论项目级安装，即 `scope=project`。

若调用方明确要求全局安装，也必须先识别同一个 `assistant_id`，再解析对应的全局目标；如果该助手没有定义合法的全局目标，则停止安装，不要猜。

当 `scope=project` 时，目标目录固定通过统一映射表解析：

- `claude -> .claude/skills`
- `qoder -> .qoder/skills`
- `lingma -> .lingma/skills`
- `trae -> .trae/skills`
- `generic -> .agents/skills`

识别顺序固定如下：

1. 优先读取宿主直接暴露的显式身份信号。
2. 如果没有显式信号，再根据宿主进程、启动器、可执行路径、宿主元数据等运行环境特征识别。
3. 将结果规范化为统一的 `assistant_id`。
4. 使用 `TARGETS[assistant_id][scope]` 解析目标目录。

一旦上层已经给出明确身份，下层只能用于校验或补充诊断，不能改写结果。

如果宿主显式信号与宿主特征识别结果冲突，也必须停止安装。

若无法唯一识别当前助手，则停止安装并输出诊断。

诊断至少应说明：读到了哪些宿主信号、这些信号各自指向什么助手、为什么结果被判定为缺失/冲突/未知、因此未执行安装。

不要把项目目录扫描保留为低优先级回退逻辑，也不要因为仓库里已经存在某个助手目录就覆盖运行时识别结果。

验收示例：

- `Trae runtime + existing .qoder/ -> .trae/skills`
- `Qoder runtime + existing .trae/ -> .qoder/skills`
- `unrecognized runtime + multiple assistant directories -> fail without guessing`

### Stage 2: 安装 skills 到目标目录

Stage 2 必须将仓库 `skills/` 目录下当前存在的全部一级 skill 目录完整复制到目标目录。

不要只复制后续将要执行的某一个 skill。

执行以下指令：

```bash
mkdir -p "$TARGET"
git clone https://github.com/largeoliu/tech-solution.git ./tech-solution-tmp
cp -r ./tech-solution-tmp/skills/* "$TARGET"/

for skill_dir in ./tech-solution-tmp/skills/*; do
  [ -d "$skill_dir" ] || continue
  skill_name="$(basename "$skill_dir")"
  [ -f "$TARGET/$skill_name/SKILL.md" ] || (echo "Missing $skill_name/SKILL.md" && exit 1)
done

rm -rf ./tech-solution-tmp
```

### Stage 3: 在同一次流程内完成项目初始化

确认 Stage 2 已将 `skills/` 下当前全部一级 skill 目录安装到目标目录后，继续读取并执行本地 `setup-architect` 的初始化流程，不要等待用户追加输入。

这里指定的是安装完成后的下一步执行入口，不是 Stage 2 的安装范围。

必须基于以下目录下的文件完成当前项目初始化：

- `"$TARGET/setup-architect"`

完成标准：

- 创建 `.architecture/technical-solutions`、`.architecture/templates`
- 生成 `.architecture/members.yml`、`.architecture/principles.md`
- 生成 `.architecture/templates/technical-solution-template.md`，并在初始化结束前确认该文件最终保留默认模板还是被用户提供的完整 Markdown 整体替换
```

- [ ] **Step 4: Run the installation-contract tests and the existing Stage 2 integration guard**

Run: `python3 -m unittest tests.skill_validation.test_installation_contracts tests.skill_validation.test_workflow_integration.WorkflowIntegrationTests.test_installation_doc_keeps_skill_copy_scope_generic -v`
Expected: PASS with three `InstallationContractTests` cases and the existing Stage 2 scope test all green

- [ ] **Step 5: Commit the installation routing contract**

```bash
git add INSTALLATION.md tests/skill_validation/test_installation_contracts.py
git commit -m "docs: codify runtime-based install target routing"
```

### Task 2: Add Trae to the Shared Assistant Target Registry

**Files:**
- Modify: `tests/skill_validation/helpers.py`
- Modify: `tests/skill_validation/test_static_layout.py`

- [ ] **Step 1: Add failing Trae-specific static layout assertions**

```python
class StaticLayoutTests(unittest.TestCase):
    def test_validate_assistant_supports_trae_target(self) -> None:
        self.assertEqual(skill_helpers.validate_assistant("trae"), ".trae/skills")

    def test_bootstrap_supports_trae_project_target(self) -> None:
        with bootstrapped_project("trae") as project_dir:
            self.assertTrue((project_dir / ".trae/skills").is_dir())
            self.assertFalse((project_dir / ".qoder/skills").exists())
            self.assertFalse((project_dir / ".claude/skills").exists())
```

- [ ] **Step 2: Run the Trae static-layout tests to verify they fail**

Run: `python3 -m unittest tests.skill_validation.test_static_layout.StaticLayoutTests.test_validate_assistant_supports_trae_target tests.skill_validation.test_static_layout.StaticLayoutTests.test_bootstrap_supports_trae_project_target -v`
Expected: FAIL with `ValueError: Unknown assistant 'trae'`

- [ ] **Step 3: Add Trae to `ASSISTANT_TARGETS` in the shared helper**

```python
ASSISTANT_TARGETS = {
    "claude": ".claude/skills",
    "qoder": ".qoder/skills",
    "lingma": ".lingma/skills",
    "trae": ".trae/skills",
    "generic": ".agents/skills",
}
```

- [ ] **Step 4: Re-run the Trae static-layout tests and the full static layout module**

Run: `python3 -m unittest tests.skill_validation.test_static_layout -v`
Expected: PASS with the new Trae tests plus the existing bootstrap/layout cases all green

- [ ] **Step 5: Commit the shared Trae target support**

```bash
git add tests/skill_validation/helpers.py tests/skill_validation/test_static_layout.py
git commit -m "test: add trae assistant target coverage"
```

### Task 3: Extend the CI Install Matrix to Cover Trae

**Files:**
- Modify: `.github/workflows/skills-integration-tests.yml`
- Modify: `tests/skill_validation/test_workflow_integration.py`

- [ ] **Step 1: Add a failing workflow integration test for Trae coverage**

```python
class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_matrix_covers_trae_target(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("- assistant: trae", workflow)
        self.assertIn("target: .trae/skills", workflow)
        self.assertIn(
            "for candidate in .claude/skills .qoder/skills .lingma/skills .trae/skills .agents/skills; do",
            workflow,
        )
```

- [ ] **Step 2: Run the new workflow integration test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_workflow_integration.WorkflowIntegrationTests.test_workflow_matrix_covers_trae_target -v`
Expected: FAIL because the current matrix and candidate loop do not mention Trae

- [ ] **Step 3: Update the workflow matrix and candidate-directory loop**

```yaml
strategy:
  matrix:
    include:
      - assistant: claude
        target: .claude/skills
      - assistant: qoder
        target: .qoder/skills
      - assistant: lingma
        target: .lingma/skills
      - assistant: trae
        target: .trae/skills
      - assistant: generic
        target: .agents/skills
```

```yaml
for candidate in .claude/skills .qoder/skills .lingma/skills .trae/skills .agents/skills; do
  if [ "$candidate" = "${{ matrix.target }}" ]; then
    [ -d "$candidate" ] || (echo "Missing $candidate" && exit 1)
    [ ! -L "$candidate" ] || (echo "$candidate must not be symlink" && exit 1)
    [ ! -d "$candidate/.git" ] || (echo "Nested .git should be cleaned from $candidate" && exit 1)
  else
    [ ! -d "$candidate" ] || (echo "$candidate should not exist" && exit 1)
  fi
done
```

- [ ] **Step 4: Re-run the workflow integration module**

Run: `python3 -m unittest tests.skill_validation.test_workflow_integration -v`
Expected: PASS with the new Trae workflow test and the existing workflow/runbook assertions all green

- [ ] **Step 5: Commit the CI matrix update**

```bash
git add .github/workflows/skills-integration-tests.yml tests/skill_validation/test_workflow_integration.py
git commit -m "ci: add trae install matrix coverage"
```

### Task 4: Verify the Full Routing Validation Slice

**Files:**
- Test: `tests/skill_validation/test_installation_contracts.py`
- Test: `tests/skill_validation/test_static_layout.py`
- Test: `tests/skill_validation/test_workflow_integration.py`
- Test: `tests/skill_validation/*`

- [ ] **Step 1: Run the focused routing-related validation slice**

Run: `python3 -m unittest tests.skill_validation.test_installation_contracts tests.skill_validation.test_static_layout tests.skill_validation.test_workflow_integration -v`
Expected: PASS with the installation contract, Trae bootstrap, and workflow matrix coverage all green

- [ ] **Step 2: Run the full skill validation suite**

Run: `python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v`
Expected: PASS with no regressions in the existing setup/create/review validation suite

- [ ] **Step 3: Inspect the final working tree before handing off**

Run: `git status --short`
Expected: clean working tree if all three commits succeeded, or only the intended files listed if you intentionally deferred commits

- [ ] **Step 4: Capture the resulting diff for reviewer context**

Run: `git log --oneline -3 && git diff --stat HEAD~3..HEAD`
Expected: the top section shows the three new commit SHAs, and the diff stat covers `INSTALLATION.md`, the new installation contract test, Trae helper/static-layout updates, and the workflow integration changes

- [ ] **Step 5: Stop and hand off for execution choice or review**

No new code in this step. Report the completed validation commands, the three commit SHAs, and whether the working tree is clean.
