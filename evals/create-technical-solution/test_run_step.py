# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "pytest>=8.0"]
# ///
"""create-technical-solution runner/protocol regression tests."""

from __future__ import annotations

import argparse
import copy
import importlib.util
from pathlib import Path

import pytest
import yaml


skill_root = Path(__file__).parent.parent.parent / "skills" / "create-technical-solution"
protocol_root = skill_root / "protocol"
scripts_root = skill_root / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), scripts_root / f"{name}.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


vs = load_script("validate-state")
run_step = load_script("run-step")


def load_protocol(name: str) -> dict:
    path = protocol_root / name
    assert path.exists(), f"missing protocol file: {path}"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    assert isinstance(data, dict), f"protocol file must load as mapping: {path}"
    return data


@pytest.fixture()
def workspace(tmp_path: Path) -> dict[str, Path]:
    repo = tmp_path / "sample-project"
    arch = repo / ".architecture"
    state_dir = arch / ".state" / "create-technical-solution"
    template_dir = arch / "templates"
    solution_root = arch / "technical-solutions"

    state_dir.mkdir(parents=True)
    template_dir.mkdir(parents=True)
    solution_root.mkdir(parents=True)

    template_path = template_dir / "technical-solution-template.md"
    template_path.write_text(
        """# 技术方案文档

## 一、背景

### 1.1 需求概述

### 1.2 核心目标

## 二、设计

### 2.1 方案设计

### 2.2 风险与验证
""",
        encoding="utf-8",
    )
    members_path = arch / "members.yml"
    members_path.write_text("members:\n  - id: systems_architect\n", encoding="utf-8")
    principles_path = arch / "principles.md"
    principles_path.write_text("# principles\n", encoding="utf-8")

    return {
        "repo": repo,
        "arch": arch,
        "state_path": state_dir / "sample-solution.yaml",
        "working_draft_path": state_dir / "sample-solution.working.md",
        "template_path": template_path,
        "members_path": members_path,
        "principles_path": principles_path,
        "content_file": repo / "wd-exp-systems-architect.md",
    }


def make_step9_state(workspace: dict[str, Path]) -> dict:
    state = {
        "current_step": 9,
        "completed_steps": [1, 2, 3, 4, 5, 6, 7, 8],
        "skipped_steps": [],
        "pending_questions": [],

        "required_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP-*"],
        "produced_artifacts": ["WD-CTX", "WD-TASK"],
        "gate_receipt": {"step": 9, "state_fingerprint": "", "validated_at": ""},
        "solution_root": ".architecture/technical-solutions",
        "template_path": ".architecture/templates/technical-solution-template.md",
        "members_path": ".architecture/members.yml",
        "principles_path": ".architecture/principles.md",
        "repowiki_path": ".qoder/repowiki",
        "working_draft_path": ".architecture/.state/create-technical-solution/sample-solution.working.md",
        "final_document_path": ".architecture/technical-solutions/sample-solution.md",
        "checkpoints": {
            "step-1": {"summary": "完成；slug=sample-solution", "slug": "sample-solution", "scope_ready": True},
            "step-2": {"summary": "完成；检查前置文件", "prerequisites_checked": True},
            "step-3": {"summary": "完成；模板已加载", "template_loaded": True, "template_fingerprint": "", "slot_count": 4},
            "step-4": {"summary": "完成；类型已判定", "solution_type": "新功能方案"},
            "step-5": {"summary": "完成；成员已选择", "members_checked": True, "selected_members": ["systems_architect"], "selected_member_count": 1},
            "step-6": {"summary": "完成；repowiki 不存在", "repowiki_checked": True, "repowiki_exists": False, "repowiki_source_count": 0},
            "step-7": {"summary": "完成；写入 WD-CTX", "wd_ctx_written": True, "ctx_count": 1},
            "step-8": {"summary": "完成；写入 WD-TASK", "wd_task_written": True, "task_slot_count": 4},
            "step-9": {"summary": "进行中", "skipped": False, "reason": "", "wd_exp_count": 0},
            "step-10": {"summary": "", "wd_syn_written": False, "syn_slot_count": 0},
            "step-11": {"summary": "等待成稿", "final_document_written": False, "absorbed_slot_count": 0, "rendered_via_script": False},
            "step-12": {"summary": "", "validator_passed": False, "working_draft_deleted": False, "state_file_deleted": False},
        },
        "can_enter_step_8": True,
        "can_enter_step_9": True,
        "can_enter_step_10": False,
        "can_enter_step_11": False,
        "can_enter_step_12": False,
        "absorption_check_passed": False,
        "cleanup_allowed": False,
    }
    headings = vs.extract_slot_headings(workspace["template_path"].read_text(encoding="utf-8"))
    state["checkpoints"]["step-3"]["template_fingerprint"] = vs.compute_template_fingerprint(
        workspace["template_path"].read_text(encoding="utf-8"),
        headings,
    )
    state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
    return state


def make_step11_state(workspace: dict[str, Path]) -> dict:
    state = {
        "current_step": 11,
        "completed_steps": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "skipped_steps": [],
        "pending_questions": [],
        "required_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP-*", "WD-SYN"],
        "produced_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP-*", "WD-SYN"],
        "gate_receipt": {"step": 11, "state_fingerprint": "", "validated_at": "2026-04-08T09:31:00"},
        "solution_root": ".architecture/technical-solutions",
        "template_path": ".architecture/templates/technical-solution-template.md",
        "members_path": ".architecture/members.yml",
        "principles_path": ".architecture/principles.md",
        "repowiki_path": ".qoder/repowiki",
        "working_draft_path": ".architecture/.state/create-technical-solution/sample-solution.working.md",
        "final_document_path": ".architecture/technical-solutions/sample-solution.md",
        "checkpoints": {
            "step-1": {"summary": "完成；slug=sample-solution", "slug": "sample-solution", "scope_ready": True},
            "step-2": {"summary": "完成；检查前置文件", "prerequisites_checked": True},
            "step-3": {"summary": "完成；模板已加载", "template_loaded": True, "template_fingerprint": "", "slot_count": 4},
            "step-4": {"summary": "完成；类型已判定", "solution_type": "新功能方案"},
            "step-5": {"summary": "完成；成员已选择", "members_checked": True, "selected_members": ["systems_architect"], "selected_member_count": 1},
            "step-6": {"summary": "完成；repowiki 不存在", "repowiki_checked": True, "repowiki_exists": False, "repowiki_source_count": 0},
            "step-7": {"summary": "完成；写入 WD-CTX", "wd_ctx_written": True, "ctx_count": 1},
            "step-8": {"summary": "完成；写入 WD-TASK", "wd_task_written": True, "task_slot_count": 4},
            "step-9": {"summary": "完成；写入 WD-EXP-*", "wd_exp_written": True, "wd_exp_count": 1},
            "step-10": {"summary": "完成；写入 WD-SYN", "wd_syn_written": True, "syn_slot_count": 4},
            "step-11": {"summary": "等待成稿", "final_document_written": False, "absorbed_slot_count": 0, "rendered_via_script": False},
            "step-12": {"summary": "", "validator_passed": False, "working_draft_deleted": False, "state_file_deleted": False},
        },
        "can_enter_step_8": True,
        "can_enter_step_9": True,
        "can_enter_step_10": True,
        "can_enter_step_11": True,
        "can_enter_step_12": False,
        "absorption_check_passed": False,
        "cleanup_allowed": False,
    }
    template_text = workspace["template_path"].read_text(encoding="utf-8")
    headings = vs.extract_slot_headings(template_text)
    state["checkpoints"]["step-3"]["template_fingerprint"] = vs.compute_template_fingerprint(template_text, headings)
    state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
    return state


def make_step9_moderate_state(workspace: dict[str, Path]) -> dict:
    state = make_step9_state(workspace)
    state["required_artifacts"] = ["WD-CTX", "WD-TASK", "WD-SYN"]
    state["gate_receipt"] = {
        "step": 9,
        "state_fingerprint": "",
        "validated_at": "2026-04-08T09:31:00",
    }
    state["checkpoints"]["step-4"] = {
        "summary": "完成；类型已判定",
        "solution_type": "现有资产改造",
    }
    state["checkpoints"]["step-9"] = {"summary": "待跳过", "skipped": False, "reason": "", "wd_exp_count": 0}
    state["can_enter_step_9"] = False
    state["can_enter_step_10"] = False
    state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
    return state


def make_step4_state(workspace: dict[str, Path]) -> dict:
    template_text = workspace["template_path"].read_text(encoding="utf-8")
    slot_headings = vs.extract_slot_headings(template_text)
    state = {
        "current_step": 4,
        "completed_steps": [1, 2, 3],
        "skipped_steps": [],
        "pending_questions": [],
        "required_artifacts": [],
        "produced_artifacts": [],
        "gate_receipt": {
            "step": 4,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        },
        "solution_root": ".architecture/technical-solutions",
        "template_path": ".architecture/templates/technical-solution-template.md",
        "members_path": ".architecture/members.yml",
        "principles_path": ".architecture/principles.md",
        "repowiki_path": ".qoder/repowiki",
        "working_draft_path": ".architecture/.state/create-technical-solution/sample-solution.working.md",
        "final_document_path": ".architecture/technical-solutions/sample-solution.md",
        "checkpoints": {
            "step-1": {"summary": "主题已确定", "slug": "sample-solution", "scope_ready": True},
            "step-2": {"summary": "前置文件通过", "prerequisites_checked": True},
            "step-3": {
                "summary": "模板已读取",
                "template_loaded": True,
                "template_fingerprint": vs.compute_template_fingerprint(template_text, slot_headings),
                "slot_count": len(slot_headings),
            },
            "step-4": {"summary": "", "solution_type": ""},
            "step-5": {"summary": "", "members_checked": False, "selected_members": [], "selected_member_count": 0},
            "step-6": {"summary": "", "repowiki_checked": False, "repowiki_exists": False, "repowiki_source_count": 0},
            "step-7": {"summary": "", "wd_ctx_written": False, "ctx_entry_count": 0, "repowiki_consumed": False},
            "step-8": {"summary": "", "wd_task_written": False, "task_slot_count": 0},
            "step-9": {"summary": "", "skipped": False, "reason": "", "wd_exp_count": 0},
            "step-10": {"summary": "", "wd_syn_written": False, "syn_slot_count": 0},
            "step-11": {"summary": "", "final_document_written": False, "absorbed_slot_count": 0, "rendered_via_script": False},
            "step-12": {"summary": "", "validator_passed": False, "working_draft_deleted": False, "state_file_deleted": False},
        },
        "can_enter_step_8": False,
        "can_enter_step_9": False,
        "can_enter_step_10": False,
        "can_enter_step_11": False,
        "can_enter_step_12": False,
        "absorption_check_passed": False,
        "cleanup_allowed": False,
    }
    state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
    return state


def make_step5_state(workspace: dict[str, Path]) -> dict:
    state = make_step4_state(workspace)
    state["current_step"] = 5
    state["completed_steps"] = [1, 2, 3, 4]
    state["required_artifacts"] = ["WD-CTX", "WD-TASK", "WD-EXP-*", "WD-SYN"]
    state["skipped_steps"] = []
    state["checkpoints"]["step-4"] = {
        "summary": "类型判定完成",
        "solution_type": "新功能方案",
    }
    state["gate_receipt"] = {
        "step": 5,
        "state_fingerprint": "",
        "validated_at": "2026-04-08T09:31:00",
    }
    state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
    return state


def make_step3_state(workspace: dict[str, Path]) -> dict:
    state = make_step4_state(workspace)
    state["current_step"] = 3
    state["completed_steps"] = [1, 2]
    state["gate_receipt"] = {
        "step": 3,
        "state_fingerprint": "",
        "validated_at": "2026-04-08T09:31:00",
    }
    state["checkpoints"]["step-3"] = {
        "summary": "",
        "template_loaded": False,
        "template_fingerprint": "",
        "slot_count": 0,
    }
    state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
    return state


def write_state(workspace: dict[str, Path], state: dict) -> None:
    workspace["state_path"].write_text(vs.yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_step9_draft(workspace: dict[str, Path]) -> None:
    workspace["working_draft_path"].write_text(
        """# Working Draft: sample-solution

## WD-CTX

### CTX-01
来源: code

## WD-TASK

### 1.1 需求概述
必须消费的共享上下文: CTX-01

### 1.2 核心目标
必须消费的共享上下文: CTX-01

### 2.1 方案设计
必须消费的共享上下文: CTX-01

### 2.2 风险与验证
必须消费的共享上下文: CTX-01
""",
        encoding="utf-8",
    )


def write_step11_draft(workspace: dict[str, Path]) -> None:
    workspace["working_draft_path"].write_text(
        """# Working Draft: sample-solution

## WD-CTX

### CTX-01
来源: code

## WD-TASK

### 1.1 需求概述
必须消费的共享上下文: CTX-01

### 1.2 核心目标
必须消费的共享上下文: CTX-01

### 2.1 方案设计
必须消费的共享上下文: CTX-01

### 2.2 风险与验证
必须消费的共享上下文: CTX-01

## WD-SYN

### 槽位：1.1 需求概述
#### 目标能力
- 明确需求边界与改造目标。
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- 路径: 改造
- 选定写法: 在现有实现上扩展。
- 关键证据引用: CTX-01
- 建议落位槽位: 1.1 需求概述
- 模板承载缺口: 无
- 未决问题: 无

### 槽位：1.2 核心目标
#### 目标能力
- 收敛核心目标与验收标准。
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- 路径: 改造
- 选定写法: 保留目标结构并补齐约束。
- 关键证据引用: CTX-01
- 建议落位槽位: 1.2 核心目标
- 模板承载缺口: 无
- 未决问题: 无

### 槽位：2.1 方案设计
#### 目标能力
- 收敛实现路径与关键设计点。
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- 路径: 改造
- 选定写法: 在现有骨架上补充实现细节。
- 关键证据引用: CTX-01
- 建议落位槽位: 2.1 方案设计
- 模板承载缺口: 无
- 未决问题: 无

### 槽位：2.2 风险与验证
#### 目标能力
- 明确风险与验证手段。
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- 路径: 改造
- 选定写法: 沿用现有验证流程并补足检查项。
- 关键证据引用: CTX-01
- 建议落位槽位: 2.2 风险与验证
- 模板承载缺口: 无
- 未决问题: 无
""",
        encoding="utf-8",
    )


FINAL_DOC = """# 技术方案文档

## 一、背景

### 1.1 需求概述

内容

### 1.2 核心目标

内容

## 二、设计

### 2.1 方案设计

内容

### 2.2 风险与验证

内容
"""


WD_CTX_BODY = """### CTX-01
来源: code
"""


WD_TASK_BODY = """### 1.1 需求概述
必须消费的共享上下文: CTX-01

### 1.2 核心目标
必须消费的共享上下文: CTX-01

### 2.1 方案设计
必须消费的共享上下文: CTX-01

### 2.2 风险与验证
必须消费的共享上下文: CTX-01
"""


WD_EXP_BODY = """### 参与槽位
- 2.1 方案设计

### 决策类型
- 改造

### 核心理由
- 复用现有骨架并补齐专家分析。

### 关键证据引用
- CTX-01

### 未决点
- 无
"""


WD_SYN_BODY = """### 槽位：1.1 需求概述
#### 目标能力
- 明确需求边界与改造目标。
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- 路径: 改造
- 选定写法: 在现有实现上扩展。
- 关键证据引用: CTX-01
- 建议落位槽位: 1.1 需求概述
- 模板承载缺口: 无
- 未决问题: 无

### 槽位：1.2 核心目标
#### 目标能力
- 收敛核心目标与验收标准。
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- 路径: 改造
- 选定写法: 保留目标结构并补齐约束。
- 关键证据引用: CTX-01
- 建议落位槽位: 1.2 核心目标
- 模板承载缺口: 无
- 未决问题: 无

### 槽位：2.1 方案设计
#### 目标能力
- 收敛实现路径与关键设计点。
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- 路径: 改造
- 选定写法: 在现有骨架上补充实现细节。
- 关键证据引用: CTX-01
- 建议落位槽位: 2.1 方案设计
- 模板承载缺口: 无
- 未决问题: 无

### 槽位：2.2 风险与验证
#### 目标能力
- 明确风险与验证手段。
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- 路径: 改造
- 选定写法: 沿用现有验证流程并补足检查项。
- 关键证据引用: CTX-01
- 建议落位槽位: 2.2 风险与验证
- 模板承载缺口: 无
- 未决问题: 无
"""


WD_SYN_LIGHT_BODY = """### 槽位：1.1 需求概述
- 延续现有结构，只做小范围调整。

### 槽位：1.2 核心目标
- 保持现有边界并补齐说明。

### 槽位：2.1 方案设计
- 在现有模块内完成实现。

### 槽位：2.2 风险与验证
- 增加回归验证并控制改动范围。
"""


def make_args(
    state_path: Path,
    summary: str,
    *,
    slug: str | None = None,
    # flow_tier removed - all flows are full
    solution_type: str | None = None,
    signal: list[str] | None = None,
    member: list[str] | None = None,
    content_file: list[str] | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        state=str(state_path),
        complete=True,
        summary=summary,
        slug=slug,
        solution_type=solution_type,
        signal=signal or [],
        member=member or [],
        content_file=content_file or [],
    )


def write_content_file(workspace: dict[str, Path], name: str, content: str) -> str:
    path = workspace["repo"] / name
    path.write_text(content, encoding="utf-8")
    return str(path)


class TestProtocolContracts:
    def test_workflow_contract_defines_full_step_sequence(self) -> None:
        workflow = load_protocol("workflow.yaml")
        steps = workflow.get("steps")
        assert isinstance(steps, list)
        assert [step["id"] for step in steps] == list(range(1, 13))

        step7 = steps[6]
        step8 = steps[7]
        step9 = steps[8]
        step10 = steps[9]

        assert step7["produces"] == ["WD-CTX"]
        assert step8["produces"] == ["WD-TASK"]
        assert step9["produces_pattern"] == "WD-EXP-*"

    def test_workflow_contract_exposes_runner_metadata(self) -> None:
        workflow = load_protocol("workflow.yaml")
        steps = {step["id"]: step for step in workflow["steps"]}

        assert steps[7]["name"] == "构建共享上下文 (WD-CTX)"
        assert steps[7]["content_block"] == "WD-CTX"
        assert steps[8]["name"] == "生成模板任务单 (WD-TASK)"
        assert steps[8]["content_block"] == "WD-TASK"
        assert steps[10]["name"] == "协作收敛 (WD-SYN)"

    def test_block_contract_defines_wd_exp_minimum_shape(self) -> None:
        contracts = load_protocol("block-contracts.yaml")
        blocks = contracts.get("blocks")
        assert isinstance(blocks, dict)

        wd_exp = blocks["WD-EXP"]
        assert wd_exp["heading_pattern"] == r"WD-EXP-[A-Z0-9_-]+"
        assert wd_exp["required_sections"] == [
            "参与槽位",
            "决策类型",
            "核心理由",
            "关键证据引用",
            "未决点",
        ]


class TestRunStepBehavior:
    def test_main_emit_scaffold_mode_keeps_summary_optional(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, object] = {}

        def fake_emit_scaffold(state_path: Path, members: list[str] | None = None) -> int:
            captured["state_path"] = state_path
            captured["members"] = members
            return 0

        monkeypatch.setattr(run_step, "emit_scaffold", fake_emit_scaffold)
        monkeypatch.setattr(
            "sys.argv",
            ["run-step.py", "--state", str(workspace["state_path"]), "--emit-scaffold"],
        )

        assert run_step.main() == 0
        assert captured == {
            "state_path": workspace["state_path"].resolve(),
            "members": [],
        }

    def test_main_rejects_emit_scaffold_with_complete(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "run-step.py",
                "--state",
                str(workspace["state_path"]),
                "--emit-scaffold",
                "--complete",
                "--summary",
                "noop",
            ],
        )

        with pytest.raises(SystemExit) as exc_info:
            run_step.main()

        assert exc_info.value.code == 2

    def test_main_preserves_public_cli_flags_for_complete_mode(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, object] = {}

        def fake_complete_step(args: argparse.Namespace) -> int:
            captured["state"] = args.state
            captured["complete"] = args.complete
            captured["summary"] = args.summary
            captured["slug"] = args.slug
            captured["solution_type"] = args.solution_type
            captured["member"] = args.member
            captured["content_file"] = args.content_file
            return 0

        monkeypatch.setattr(run_step, "complete_step", fake_complete_step)
        monkeypatch.setattr(
            "sys.argv",
            [
                "run-step.py",
                "--state",
                str(workspace["state_path"]),
                "--complete",
                "--summary",
                "专家分析完成",
                "--slug",
                "sample-solution",
                "--solution-type",
                "新功能方案",
                "--member",
                "SYSTEMS_ARCHITECT",
                "--content-file",
                "/tmp/wd-exp-systems_architect.md",
            ],
        )

        assert run_step.main() == 0
        assert captured == {
            "state": str(workspace["state_path"]),
            "complete": True,
            "summary": "专家分析完成",
            "slug": "sample-solution",
            "solution_type": "新功能方案",
            "member": ["SYSTEMS_ARCHITECT"],
            "content_file": ["/tmp/wd-exp-systems_architect.md"],
        }

    def test_main_status_mode_keeps_summary_optional(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, Path] = {}

        def fake_print_status(state_path: Path) -> int:
            captured["state_path"] = state_path
            return 0

        monkeypatch.setattr(run_step, "print_status", fake_print_status)
        monkeypatch.setattr(
            "sys.argv",
            ["run-step.py", "--state", str(workspace["state_path"])],
        )

        assert run_step.main() == 0
        assert captured["state_path"] == workspace["state_path"].resolve()

    def test_emit_scaffold_does_not_mutate_state_or_draft(self, workspace: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        before_state = workspace["state_path"].read_text(encoding="utf-8")
        before_draft = workspace["working_draft_path"].read_text(encoding="utf-8")

        exit_code = run_step.emit_scaffold(workspace["state_path"])

        assert exit_code == 0
        output = capsys.readouterr().out
        assert "## WD-EXP-SYSTEMS_ARCHITECT" in output
        assert "### 参与槽位" in output
        assert workspace["state_path"].read_text(encoding="utf-8") == before_state
        assert workspace["working_draft_path"].read_text(encoding="utf-8") == before_draft

    def test_emit_scaffold_step9_member_filter_limits_output(self, workspace: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
        state = make_step9_state(workspace)
        state["checkpoints"]["step-5"]["selected_members"] = ["systems_architect", "domain_expert"]
        state["checkpoints"]["step-5"]["selected_member_count"] = 2
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step9_draft(workspace)

        exit_code = run_step.emit_scaffold(workspace["state_path"], members=["domain_expert"])

        assert exit_code == 0
        output = capsys.readouterr().out
        assert "## WD-EXP-DOMAIN_EXPERT" in output
        assert "## WD-EXP-SYSTEMS_ARCHITECT" not in output

    def test_emit_scaffold_uses_stdout_instead_of_complete_path(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)

        def forbid_complete(*_args, **_kwargs):
            raise AssertionError("emit_scaffold should not call complete path")

        monkeypatch.setattr(run_step, "complete_creative_step", forbid_complete)

        exit_code = run_step.emit_scaffold(workspace["state_path"])

        assert exit_code == 0
        assert "WD-EXP" in capsys.readouterr().out

    def test_run_step_reads_names_and_default_blocks_from_workflow(self) -> None:
        assert run_step.get_step_name(7) == "构建共享上下文 (WD-CTX)"
        assert run_step.get_step_name(10) == "协作收敛 (WD-SYN)"
        assert run_step.default_block_for_step(7) == "WD-CTX"
        assert run_step.default_block_for_step(8) == "WD-TASK"
        assert run_step.default_block_for_step(10) == "WD-SYN"
        assert run_step.get_step_card_path(9).name == "09-组织专家按模板逐槽位分析.md"

    def test_complete_creative_step_uses_in_process_validator_and_writer(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        workspace["content_file"].write_text(
            """### 参与槽位
- 2.1 方案设计

### 决策类型
- 改造

### 核心理由
- 复用现有骨架并补齐专家分析。

### 关键证据引用
- CTX-01

### 未决点
- 无
""",
            encoding="utf-8",
        )

        def forbid_subprocess(*_args, **_kwargs):
            raise AssertionError("complete_creative_step should not use subprocess")

        monkeypatch.setattr(run_step, "run_script", forbid_subprocess)

        code, message = run_step.complete_creative_step(
            workspace["state_path"],
            "专家分析完成",
            9,
            [str(workspace["content_file"])],
        )

        assert code == 0, message
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 10
        assert new_state["checkpoints"]["step-9"]["wd_exp_count"] == 1
        assert new_state["can_enter_step_10"] is True

    def test_complete_creative_step_batch_step9_is_atomic_on_success(self, workspace: dict[str, Path]) -> None:
        state = make_step9_state(workspace)
        state["checkpoints"]["step-5"]["selected_members"] = ["systems_architect", "domain_expert"]
        state["checkpoints"]["step-5"]["selected_member_count"] = 2
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step9_draft(workspace)

        first_file = workspace["repo"] / "wd-exp-systems_architect.md"
        second_file = workspace["repo"] / "wd-exp-domain_expert.md"
        first_file.write_text(
            "### 参与槽位\n- 2.1 方案设计\n\n### 决策类型\n- 改造\n\n### 核心理由\n- 保持核心骨架。\n\n### 关键证据引用\n- CTX-01\n\n### 未决点\n- 无\n",
            encoding="utf-8",
        )
        second_file.write_text(
            "### 参与槽位\n- 2.2 风险与验证\n\n### 决策类型\n- 新建\n\n### 核心理由\n- 独立补强风险控制。\n\n### 关键证据引用\n- CTX-01\n\n### 未决点\n- 无\n",
            encoding="utf-8",
        )

        code, message = run_step.complete_creative_step(
            workspace["state_path"],
            "专家分析完成",
            9,
            [str(first_file), str(second_file)],
        )

        assert code == 0, message
        new_state = vs.load_state(workspace["state_path"])
        updated_draft = workspace["working_draft_path"].read_text(encoding="utf-8")
        assert new_state["current_step"] == 10
        assert new_state["gate_receipt"]["step"] == 10
        assert new_state["checkpoints"]["step-9"]["wd_exp_count"] == 2
        assert updated_draft.count("## WD-EXP-") == 2
        assert "## WD-EXP-SYSTEMS_ARCHITECT" in updated_draft
        assert "## WD-EXP-DOMAIN_EXPERT" in updated_draft

    def test_complete_creative_step_batch_step9_rolls_back_on_partial_failure(self, workspace: dict[str, Path]) -> None:
        state = make_step9_state(workspace)
        before_state = copy.deepcopy(state)
        write_state(workspace, state)
        write_step9_draft(workspace)
        before_draft = workspace["working_draft_path"].read_text(encoding="utf-8")

        valid_file = workspace["repo"] / "wd-exp-systems_architect.md"
        invalid_file = workspace["repo"] / "wd-exp-domain_expert.md"
        valid_file.write_text(
            "### 参与槽位\n- 2.1 方案设计\n\n### 决策类型\n- 改造\n\n### 核心理由\n- 保持核心骨架。\n\n### 关键证据引用\n- CTX-01\n\n### 未决点\n- 无\n",
            encoding="utf-8",
        )
        invalid_file.write_text(
            "### 参与槽位\n- 2.2 风险与验证\n\n### 决策类型\n- 新建\n\n### 核心理由\n- 结构错误。\n\n## WD-EXP-OTHER\n\n### 关键证据引用\n- CTX-01\n\n### 未决点\n- 无\n",
            encoding="utf-8",
        )

        code, message = run_step.complete_creative_step(
            workspace["state_path"],
            "专家分析完成",
            9,
            [str(valid_file), str(invalid_file)],
        )

        assert code != 0
        assert message.startswith("upsert-draft-block.py 失败:\n")
        assert "WD-EXP" in message or "嵌套" in message
        assert workspace["working_draft_path"].read_text(encoding="utf-8") == before_draft
        assert "## WD-EXP-SYSTEMS_ARCHITECT" not in workspace["working_draft_path"].read_text(encoding="utf-8")
        assert vs.load_state(workspace["state_path"]) == before_state

    def test_step9_rejects_nested_wd_exp_heading_in_content_file(self, workspace: dict[str, Path]) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        workspace["content_file"].write_text(
            """### 参与槽位
- 2.1 方案设计

### 决策类型
- 改造

### 核心理由
- 先写一段正常内容。

## WD-EXP-OTHER_EXPERT

### 关键证据引用
- CTX-01

### 未决点
- 无
""",
            encoding="utf-8",
        )

        code, message = run_step.complete_creative_step(
            workspace["state_path"],
            "专家分析完成",
            9,
            [str(workspace["content_file"])],
        )

        assert code != 0
        assert "WD-EXP" in message or "嵌套" in message

    def test_complete_step_11_uses_in_process_renderer(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        state = make_step11_state(workspace)
        write_state(workspace, state)
        write_step11_draft(workspace)

        def forbid_subprocess(*_args, **_kwargs):
            raise AssertionError("complete_step_11 should not use subprocess")

        monkeypatch.setattr(run_step, "run_script", forbid_subprocess)

        code, message = run_step.complete_step_11(workspace["state_path"], "成稿完成")

        assert code == 0, message
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 12
        assert new_state["checkpoints"]["step-11"]["rendered_via_script"] is True
        final_document_path = workspace["repo"] / new_state["final_document_path"]
        assert final_document_path.exists()
        assert "## 一、背景" in final_document_path.read_text(encoding="utf-8")

    def test_complete_step_12_uses_in_process_cleanup(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        state = make_step11_state(workspace)
        state["current_step"] = 12
        state["completed_steps"] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        state["can_enter_step_12"] = True
        state["checkpoints"]["step-11"] = {
            "summary": "完成；final_document=1；absorbed_slots=4；gate: step-12 ready",
            "final_document_written": True,
            "absorbed_slot_count": 4,
            "rendered_via_script": True,
        }
        state["checkpoints"]["step-12"] = {
            "summary": "完成；validator_passed=true；deleted=0",
            "validator_passed": False,
            "working_draft_deleted": False,
            "state_file_deleted": False,
        }
        state["gate_receipt"] = {
            "step": 12,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step11_draft(workspace)
        final_document_path = workspace["repo"] / state["final_document_path"]
        final_document_path.write_text(FINAL_DOC, encoding="utf-8")

        def forbid_subprocess(*_args, **_kwargs):
            raise AssertionError("complete_step_12 should not use subprocess")

        monkeypatch.setattr(run_step, "run_script", forbid_subprocess)

        code, message = run_step.complete_step_12(workspace["state_path"], "清理完成")

        assert code == 0, message
        assert not workspace["state_path"].exists()
        assert not workspace["working_draft_path"].exists()




    def test_complete_step_5_uses_in_process_state_advance(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        state = make_step5_state(workspace)
        write_state(workspace, state)

        def forbid_subprocess(*_args, **_kwargs):
            raise AssertionError("complete_step_5 should not use subprocess")

        monkeypatch.setattr(run_step, "run_script", forbid_subprocess)

        code, message = run_step.complete_step_5(
            workspace["state_path"],
            "成员选定完成",
            members=["SYSTEMS_ARCHITECT", "DOMAIN_EXPERT"],
        )

        assert code == 0, message
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 6
        assert new_state["checkpoints"]["step-5"]["selected_members"] == ["SYSTEMS_ARCHITECT", "DOMAIN_EXPERT"]
        assert new_state["checkpoints"]["step-5"]["selected_member_count"] == 2

    def test_complete_step_1_uses_in_process_initializer(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def forbid_subprocess(*_args, **_kwargs):
            raise AssertionError("complete_step_1 should not use subprocess")

        monkeypatch.setattr(run_step, "run_script", forbid_subprocess)

        code, message = run_step.complete_step_1(
            workspace["state_path"],
            "定题完成",
            slug="sample-solution",
        )

        assert code == 0, message
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 2
        assert new_state["gate_receipt"]["step"] == 2
        assert new_state["checkpoints"]["step-1"]["slug"] == "sample-solution"

    def test_complete_step_3_uses_in_process_template_snapshot(self, workspace: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
        state = make_step3_state(workspace)
        write_state(workspace, state)

        def forbid_subprocess(*_args, **_kwargs):
            raise AssertionError("complete_step_3 should not use subprocess")

        monkeypatch.setattr(run_step, "run_script", forbid_subprocess)

        code, message = run_step.complete_step_3(workspace["state_path"], "模板读取完成")

        assert code == 0, message
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 4
        assert new_state["checkpoints"]["step-3"]["template_loaded"] is True
        assert workspace["working_draft_path"].exists()
        assert new_state["working_draft_path"] == ".architecture/.state/create-technical-solution/sample-solution.working.md"

    def test_complete_step_3_ignores_tampered_external_working_draft_path(self, workspace: dict[str, Path]) -> None:
        state = make_step3_state(workspace)
        external_draft_path = workspace["repo"].parent / "tampered" / "sample-solution.working.md"
        state["working_draft_path"] = str(external_draft_path.resolve())
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)

        code, message = run_step.complete_step_3(workspace["state_path"], "模板读取完成")

        assert code == 0, message
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 4
        assert new_state["working_draft_path"] == ".architecture/.state/create-technical-solution/sample-solution.working.md"
        assert workspace["working_draft_path"].exists()
        assert not external_draft_path.exists()

    def test_print_status_shows_public_repair_hint_and_next_command(self, workspace: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
        state = make_step9_state(workspace)
        state["working_draft_path"] = ".architecture/technical-solutions/working-drafts/sample-solution.working.md"
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)

        exit_code = run_step.print_status(workspace["state_path"])

        assert exit_code == 0
        output = capsys.readouterr().out
        assert "working_draft_path 必须固定为 .architecture/.state/create-technical-solution/sample-solution.working.md" in output
        assert "回到步骤 3，重新生成 .architecture/.state/create-technical-solution/[slug].working.md" in output
        assert "--complete --summary \"<专家分析完成>\" --content-file /tmp/wd-exp-systems_architect.md" in output

    def test_light_sample_flow_end_to_end(self, workspace: dict[str, Path]) -> None:
        ctx_file = write_content_file(workspace, "wd-ctx.md", WD_CTX_BODY)
        task_file = write_content_file(workspace, "wd-task.md", WD_TASK_BODY)
        exp_file = write_content_file(workspace, "wd-exp-systems_architect.md", WD_EXP_BODY)
        syn_file = write_content_file(workspace, "wd-syn.md", WD_SYN_BODY)

        assert run_step.complete_step(
            make_args(workspace["state_path"], "定题完成", slug="sample-solution")
        ) == 0
        assert run_step.complete_step(make_args(workspace["state_path"], "前置文件检查通过")) == 0
        assert run_step.complete_step(make_args(workspace["state_path"], "模板读取完成")) == 0
        assert run_step.complete_step(
            make_args(
                workspace["state_path"],
                "类型判定完成",
                solution_type="新功能方案",
                signal=["introduces-core-capability"],
            )
        ) == 0
        assert run_step.complete_step(
            make_args(workspace["state_path"], "成员选定完成", member=["SYSTEMS_ARCHITECT"])
        ) == 0
        assert run_step.complete_step(make_args(workspace["state_path"], "repowiki 检查完成")) == 0
        assert run_step.complete_step(
            make_args(workspace["state_path"], "WD-CTX 完成", content_file=[ctx_file])
        ) == 0
        assert run_step.complete_step(
            make_args(workspace["state_path"], "WD-TASK 完成", content_file=[task_file])
        ) == 0

        state_after_task = vs.load_state(workspace["state_path"])
        assert state_after_task["current_step"] == 9

        assert run_step.complete_step(
            make_args(workspace["state_path"], "专家分析完成", content_file=[exp_file])
        ) == 0
        assert run_step.complete_step(
            make_args(workspace["state_path"], "WD-SYN 完成", content_file=[syn_file])
        ) == 0

        state_after_syn = vs.load_state(workspace["state_path"])
        assert state_after_syn["current_step"] == 11

        assert run_step.complete_step(make_args(workspace["state_path"], "成稿完成")) == 0
        assert run_step.complete_step(make_args(workspace["state_path"], "清理完成")) == 0

        assert not workspace["state_path"].exists()
        assert not workspace["working_draft_path"].exists()
        final_document = workspace["arch"] / "technical-solutions" / "sample-solution.md"
        assert final_document.exists()
        assert "### 2.1 方案设计" in final_document.read_text(encoding="utf-8")
