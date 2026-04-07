# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "pytest>=8.0"]
# ///
"""validate-state.py 单元测试"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

scripts_path = Path(__file__).parent.parent.parent / "skills" / "create-technical-solution" / "scripts"
spec = importlib.util.spec_from_file_location("validate_state", scripts_path / "validate-state.py")
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)

cleanup_spec = importlib.util.spec_from_file_location("finalize_cleanup", scripts_path / "finalize-cleanup.py")
fc = importlib.util.module_from_spec(cleanup_spec)
cleanup_spec.loader.exec_module(fc)

tier_spec = importlib.util.spec_from_file_location("set_flow_tier", scripts_path / "set-flow-tier.py")
sft = importlib.util.module_from_spec(tier_spec)
tier_spec.loader.exec_module(sft)

skip_spec = importlib.util.spec_from_file_location("mark_step_skipped", scripts_path / "mark-step-skipped.py")
mss = importlib.util.module_from_spec(skip_spec)
skip_spec.loader.exec_module(mss)


DEFAULT_TEMPLATE = """# 技术方案文档

## 一、背景

### 1.1 需求概述

### 1.2 核心目标

## 二、设计

### 2.1 方案设计

### 2.2 风险与验证
"""


UGC_REAL_RUN_TEMPLATE = """# 技术方案文档

## 一、需求背景与综合评估

### 1.1 需求概述

### 1.2 核心目标

### 1.3 影响范围

### 1.4 风险等级

### 1.5 发布环境

## 二、总体设计

### 2.1 业务流程梳理

### 2.2 术语表

### 2.3 涉及组件

## 三、详细设计

### 3.1 数据库设计

### 3.2 HTTP接口设计

### 3.3 RPC接口设计

### 3.4 配置与依赖

## 四、测试方案&数据兼容

### 4.1 历史数据处理

### 4.2 重点测试场景

## 五、上线方案

### 5.1 发布顺序

### 5.2 可观察性

### 5.3 可灰度

### 5.4 可回滚与应急预案

### 5.5 服务上线检查项清单
"""


@pytest.fixture()
def workspace(tmp_path: Path) -> dict[str, Path]:
    repo = tmp_path / "sample-project"
    arch = repo / ".architecture"
    state_dir = arch / ".state" / "create-technical-solution"
    template_dir = arch / "templates"
    solution_root = arch / "technical-solutions"
    working_drafts = solution_root / "working-drafts"

    state_dir.mkdir(parents=True)
    template_dir.mkdir(parents=True)
    working_drafts.mkdir(parents=True)

    template_path = template_dir / "technical-solution-template.md"
    template_path.write_text(DEFAULT_TEMPLATE, encoding="utf-8")

    return {
        "repo": repo,
        "arch": arch,
        "state_dir": state_dir,
        "template_path": template_path,
        "solution_root": solution_root,
        "working_draft_path": working_drafts / "sample-solution.working.md",
        "final_document_path": solution_root / "sample-solution.md",
        "state_path": state_dir / "sample-solution.yaml",
    }


def make_template_snapshot(template_path: Path) -> dict:
    headings = vs.extract_slot_headings(template_path.read_text(encoding="utf-8"))
    return {
        "path": str(template_path),
        "slot_level": headings[0]["level"] if headings else None,
        "headings": headings,
        "captured_at": "2026-04-07T12:00:00Z",
    }


def make_template_snapshot_with_level(template_path: Path, level: int) -> dict:
    headings = vs.extract_slot_headings(template_path.read_text(encoding="utf-8"), slot_level=level)
    return {
        "path": str(template_path),
        "slot_level": level,
        "headings": headings,
        "captured_at": "2026-04-07T12:00:00Z",
    }


def render_custom_template(sections: list[tuple[str, list[str]]]) -> str:
    lines = ["# 自定义技术方案", ""]
    for section_title, slots in sections:
        lines.append(f"## {section_title}")
        lines.append("")
        for slot in slots:
            lines.append(f"### {slot}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def make_state(workspace: dict[str, Path], **overrides) -> dict:
    state = {
        "skill": "create-technical-solution",
        "slug": "sample-solution",
        "topic_summary": "为样例项目生成技术方案",
        "current_step": 10,
        "step_status": "in_progress",
        "started_at": "2026-04-07T12:00:00Z",
        "updated_at": "2026-04-07T12:10:00Z",
        "solution_root": str(workspace["solution_root"]),
        "working_draft_path": str(workspace["working_draft_path"]),
        "final_document_path": str(workspace["final_document_path"]),
        "template_snapshot": make_template_snapshot(workspace["template_path"]),
        "completed_steps": [1, 2, 3, 4, 5, 6, 7, 8],
        "blocked": False,
        "block_reason": None,
        "checkpoints": {
            "step-2": {"summary": "前置文件检查完成", "prerequisites_checked": True},
            "step-3": {"summary": "模板快照已提取", "template_loaded": True},
            "step-4": {"summary": "方案类型完成", "solution_type": "现有资产改造", "flow_tier": "moderate"},
            "step-6": {"summary": "repowiki 检测完成", "repowiki_checked": True, "repowiki_exists": False},
            "step-9": {"summary": "因流程级别跳过 step-9", "skipped": True, "reason": "moderate 跳过 step-9"},
        },
        "active_references": [],
        "flow_tier": "moderate",
        "required_artifacts": ["WD-CTX", "WD-TASK", "WD-SYN"],
        "produced_artifacts": ["WD-CTX", "WD-TASK"],
        "selected_members": ["systems_architect", "domain_expert"],
        "template_slots": [item["title"] for item in make_template_snapshot(workspace["template_path"])["headings"]],
        "blocked_slots": [],
        "skipped_steps": [9],
        "can_enter_step_8": True,
        "can_enter_step_9": False,
        "can_enter_step_10": True,
        "can_enter_step_11": True,
        "can_enter_step_12": False,
        "absorption_check_passed": False,
        "cleanup_allowed": False,
    }
    state.update(overrides)
    return state


def make_validator(state: dict, workspace: dict[str, Path]) -> vs.GateValidator:
    workspace["state_path"].write_text("state: fixture\n", encoding="utf-8")
    return vs.GateValidator(state, workspace["state_path"])


class TestSchema:
    def test_step_2_string_checkpoint_reports_schema_mismatch(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, current_step=2, completed_steps=[1], checkpoints={"step-2": "done"})
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_2("moderate", errors)
        assert any(error["code"] == "schema_mismatch" for error in errors)
        assert any(error["field"] == "checkpoints.step-2" for error in errors)

    def test_step_11_premature_cleanup_flags_fail(self, workspace: dict[str, Path]) -> None:
        state = make_state(
            workspace,
            current_step=11,
            completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 10],
            produced_artifacts=["WD-CTX", "WD-TASK", "WD-SYN"],
            can_enter_step_11=True,
            absorption_check_passed=True,
        )
        workspace["working_draft_path"].write_text("## WD-CTX\n\n## WD-TASK\n\n## WD-SYN\n", encoding="utf-8")
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11("moderate", errors)
        assert any(error["code"] == "premature_cleanup_flags" for error in errors)


class TestStateScripts:
    def test_set_flow_tier_script_updates_contract_atomically(self, workspace: dict[str, Path]) -> None:
        state = make_state(
            workspace,
            current_step=4,
            completed_steps=[1, 2, 3],
            flow_tier="full",
            required_artifacts=[],
            skipped_steps=[],
            checkpoints={
                "step-2": {"summary": "前置文件检查完成", "prerequisites_checked": True},
                "step-3": {"summary": "模板快照已提取", "template_loaded": True},
                "step-4": {"summary": "", "solution_type": "", "flow_tier": ""},
                "step-6": {"summary": "repowiki 检测完成", "repowiki_checked": True, "repowiki_exists": False},
            },
        )
        workspace["state_path"].write_text(vs.yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
        payload = sft.set_flow_tier(
            state_path=workspace["state_path"],
            flow_tier="moderate",
            solution_type="现有资产改造",
            summary="方案类型：现有资产改造；flow_tier=moderate",
            next_step=5,
            append_completed=True,
        )
        updated = vs.yaml.safe_load(workspace["state_path"].read_text(encoding="utf-8"))
        assert payload["flow_tier"] == "moderate"
        assert updated["flow_tier"] == "moderate"
        assert updated["checkpoints"]["step-4"]["flow_tier"] == "moderate"
        assert updated["required_artifacts"] == ["WD-CTX", "WD-TASK", "WD-SYN"]
        assert updated["skipped_steps"] == [9]
        assert updated["current_step"] == 5
        assert 4 in updated["completed_steps"]

    def test_mark_step_skipped_removes_step_from_completed_steps(self, workspace: dict[str, Path]) -> None:
        state = make_state(
            workspace,
            current_step=9,
            completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 9],
            skipped_steps=[],
        )
        workspace["state_path"].write_text(vs.yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
        payload = mss.mark_step_skipped(
            state_path=workspace["state_path"],
            step=9,
            summary="因流程级别跳过 step-9",
            reason="moderate 无需 WD-EXP-*",
            next_step=10,
        )
        updated = vs.yaml.safe_load(workspace["state_path"].read_text(encoding="utf-8"))
        assert payload["skipped_step"] == 9
        assert 9 not in updated["completed_steps"]
        assert 9 in updated["skipped_steps"]
        assert updated["checkpoints"]["step-9"]["skipped"] is True
        assert updated["current_step"] == 10


class TestWorkingDraft:
    def test_step_10_moderate_passes_with_working_draft_blocks(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text("## WD-CTX\n\n## WD-TASK\n", encoding="utf-8")
        state = make_state(workspace)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10("moderate", errors)
        assert errors == []

    def test_step_10_moderate_missing_wd_task_block(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text("## WD-CTX\n", encoding="utf-8")
        state = make_state(workspace)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10("moderate", errors)
        assert any(error["code"] == "missing_working_draft_block" for error in errors)
        assert any(error.get("missing_artifacts") == ["WD-TASK"] for error in errors)


class TestTemplateDrivenValidation:
    def test_step_4_detects_flow_tier_state_mismatch(self, workspace: dict[str, Path]) -> None:
        state = make_state(
            workspace,
            current_step=4,
            completed_steps=[1, 2, 3],
            flow_tier="moderate",
            required_artifacts=["WD-CTX", "WD-TASK", "WD-SYN", "WD-EXP-SYSTEMS_ARCHITECT"],
            checkpoints={
                "step-2": {"summary": "前置文件检查完成", "prerequisites_checked": True},
                "step-3": {"summary": "模板快照已提取", "template_loaded": True},
                "step-4": {"summary": "方案类型完成", "solution_type": "现有资产改造", "flow_tier": "full"},
                "step-6": {"summary": "repowiki 检测完成", "repowiki_checked": True, "repowiki_exists": False},
            },
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_4("moderate", errors)
        assert any(error["code"] == "flow_tier_state_mismatch" for error in errors)

    def test_step_3_fails_when_snapshot_uses_wrong_granularity(self, workspace: dict[str, Path]) -> None:
        custom_template = render_custom_template(
            [
                ("A. 背景", ["A1 需求概述", "A2 核心目标"]),
                ("B. 设计", ["B1 组件设计", "B2 接口设计", "B3 风险控制"]),
            ]
        )
        workspace["template_path"].write_text(custom_template, encoding="utf-8")
        bad_snapshot = make_template_snapshot_with_level(workspace["template_path"], level=2)
        state = make_state(workspace, current_step=3, completed_steps=[1, 2], template_snapshot=bad_snapshot, template_slots=[item["title"] for item in bad_snapshot["headings"]])
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_3("full", errors)
        assert any(error["code"] == "template_changed_since_snapshot" for error in errors)

    def test_step_12_passes_for_custom_template(self, workspace: dict[str, Path]) -> None:
        custom_template = """# 自定义方案\n\n## A\n\n### A1 目标\n\n### A2 范围\n\n## B\n\n### B1 设计\n\n### B2 验证\n"""
        workspace["template_path"].write_text(custom_template, encoding="utf-8")
        workspace["working_draft_path"].write_text("## WD-CTX\n\n## WD-TASK\n\n## WD-SYN\n", encoding="utf-8")
        workspace["final_document_path"].write_text(
            "# 自定义方案\n\n## A\n\n### A1 目标\n\n内容\n\n### A2 范围\n\n内容\n\n## B\n\n### B1 设计\n\n内容\n\n### B2 验证\n\n内容\n",
            encoding="utf-8",
        )
        state = make_state(
            workspace,
            current_step=12,
            completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 10, 11],
            can_enter_step_12=True,
            produced_artifacts=["WD-CTX", "WD-TASK", "WD-SYN"],
            template_snapshot=make_template_snapshot(workspace["template_path"]),
            template_slots=[item["title"] for item in make_template_snapshot(workspace["template_path"])["headings"]],
            checkpoints={
                "step-2": {"summary": "前置文件检查完成", "prerequisites_checked": True},
                "step-3": {"summary": "模板快照已提取", "template_loaded": True},
                "step-4": {"summary": "方案类型完成", "solution_type": "现有资产改造", "flow_tier": "moderate"},
                "step-6": {"summary": "repowiki 检测完成", "repowiki_checked": True, "repowiki_exists": False},
                "step-9": {"summary": "因流程级别跳过 step-9", "skipped": True, "reason": "moderate 跳过 step-9"},
                "step-12": {"summary": "吸收检查通过，待清理", "working_draft_deleted": False, "state_file_deleted": False},
            },
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_12("moderate", errors)
        assert errors == []

    def test_step_12_fails_when_final_document_breaks_template_order(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text("## WD-CTX\n\n## WD-TASK\n\n## WD-SYN\n", encoding="utf-8")
        workspace["final_document_path"].write_text(
            "# 技术方案文档\n\n## 一、背景\n\n### 1.2 核心目标\n\n### 1.1 需求概述\n\n## 二、设计\n\n### 2.1 方案设计\n\n### 2.2 风险与验证\n",
            encoding="utf-8",
        )
        state = make_state(
            workspace,
            current_step=12,
            completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 10, 11],
            can_enter_step_12=True,
            produced_artifacts=["WD-CTX", "WD-TASK", "WD-SYN"],
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_12("moderate", errors)
        assert any(error["code"] == "final_document_headings_mismatch" for error in errors)

    def test_step_4_detects_template_change_since_snapshot(self, workspace: dict[str, Path]) -> None:
        old_snapshot = make_template_snapshot(workspace["template_path"])
        workspace["template_path"].write_text(DEFAULT_TEMPLATE + "\n### 2.3 新增章节\n", encoding="utf-8")
        state = make_state(workspace, current_step=4, completed_steps=[1, 2, 3], template_snapshot=old_snapshot)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_4("moderate", errors)
        assert any(error["code"] == "template_changed_since_snapshot" for error in errors)


class TestPathPolicy:
    def test_step_3_rejects_legacy_solution_root_for_new_writes(self, workspace: dict[str, Path]) -> None:
        legacy_root = workspace["arch"] / "solutions"
        (legacy_root / "working-drafts").mkdir(parents=True)
        state = make_state(
            workspace,
            current_step=3,
            completed_steps=[1, 2],
            solution_root=str(legacy_root),
            working_draft_path=str(legacy_root / "working-drafts" / "sample-solution.working.md"),
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_3("moderate", errors)
        assert any(error["code"] == "legacy_path_detected" for error in errors)


class TestRealRunRegression:
    def test_step_8_detects_task_slots_incomplete(self, workspace: dict[str, Path]) -> None:
        workspace["template_path"].write_text(UGC_REAL_RUN_TEMPLATE, encoding="utf-8")
        workspace["working_draft_path"].write_text(
            "## WD-CTX\n\n内容\n\n## WD-TASK\n\n### 一、需求背景与综合评估\n\n粗粒度任务\n",
            encoding="utf-8",
        )
        snapshot = make_template_snapshot(workspace["template_path"])
        state = make_state(
            workspace,
            current_step=8,
            completed_steps=[1, 2, 3, 4, 5, 6, 7],
            flow_tier="full",
            can_enter_step_8=True,
            template_snapshot=snapshot,
            template_slots=[item["title"] for item in snapshot["headings"]],
            produced_artifacts=["WD-CTX", "WD-TASK"],
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_8("full", errors)
        assert any(error["code"] == "task_slots_incomplete" for error in errors)

    def test_step_10_detects_missing_per_expert_blocks(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text(
            "## WD-CTX\n\n内容\n\n## WD-TASK\n\n### 1.1 需求概述\n\n任务\n\n## WD-EXP\n\n总块，不是逐专家块\n",
            encoding="utf-8",
        )
        state = make_state(
            workspace,
            current_step=10,
            completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 9],
            flow_tier="full",
            selected_members=["systems_architect", "domain_expert"],
            produced_artifacts=["WD-CTX", "WD-TASK", "WD-EXP-SYSTEMS_ARCHITECT", "WD-EXP-DOMAIN_EXPERT"],
            can_enter_step_10=True,
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10("full", errors)
        assert any(error["code"] == "missing_working_draft_block" and error["missing_artifacts"] == ["WD-EXP-SYSTEMS_ARCHITECT"] for error in errors)
        assert any(error["code"] == "missing_working_draft_block" and error["missing_artifacts"] == ["WD-EXP-DOMAIN_EXPERT"] for error in errors)

    def test_step_11_detects_final_document_created_before_step_10_completion(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text("## WD-CTX\n\n## WD-TASK\n\n## WD-SYN\n", encoding="utf-8")
        workspace["final_document_path"].write_text(
            "# 技术方案文档\n\n## 一、背景\n\n### 1.1 需求概述\n\n内容\n\n### 1.2 核心目标\n\n内容\n\n## 二、设计\n\n### 2.1 方案设计\n\n内容\n\n### 2.2 风险与验证\n\n内容\n",
            encoding="utf-8",
        )
        state = make_state(
            workspace,
            current_step=11,
            completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 10],
            produced_artifacts=["WD-CTX", "WD-TASK", "WD-SYN"],
            checkpoints={
                "step-2": {"summary": "前置文件检查完成", "prerequisites_checked": True},
                "step-3": {"summary": "模板快照已提取", "template_loaded": True},
                "step-4": {"summary": "方案类型完成", "solution_type": "现有资产改造", "flow_tier": "moderate"},
                "step-6": {"summary": "repowiki 检测完成", "repowiki_checked": True, "repowiki_exists": False},
                "step-9": {"summary": "因流程级别跳过 step-9", "skipped": True, "reason": "moderate 跳过 step-9"},
                "step-10": {"summary": "收敛完成", "completed_at": "2100-01-01T00:00:00+00:00"},
            },
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11("moderate", errors)
        assert any(error["code"] == "step_order_violation" for error in errors)

    def test_step_12_requires_non_empty_summary(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text("## WD-CTX\n\n## WD-TASK\n\n## WD-SYN\n", encoding="utf-8")
        workspace["final_document_path"].write_text(
            "# 技术方案文档\n\n## 一、背景\n\n### 1.1 需求概述\n\n内容\n\n### 1.2 核心目标\n\n内容\n\n## 二、设计\n\n### 2.1 方案设计\n\n内容\n\n### 2.2 风险与验证\n\n内容\n",
            encoding="utf-8",
        )
        state = make_state(
            workspace,
            current_step=12,
            completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            can_enter_step_12=True,
            produced_artifacts=["WD-CTX", "WD-TASK", "WD-SYN"],
            checkpoints={
                "step-2": {"summary": "前置文件检查完成", "prerequisites_checked": True},
                "step-3": {"summary": "模板快照已提取", "template_loaded": True},
                "step-4": {"summary": "方案类型完成", "solution_type": "现有资产改造"},
                "step-6": {"summary": "repowiki 检测完成", "repowiki_checked": True, "repowiki_exists": False},
                "step-12": {"summary": "", "working_draft_deleted": False, "state_file_deleted": False},
            },
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_12("moderate", errors)
        assert any(error["code"] == "missing_step_summary" for error in errors)

    def test_step_10_moderate_requires_explicit_skip_record_for_step_9(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text("## WD-CTX\n\n内容\n\n## WD-TASK\n\n### 1.1 需求概述\n\n任务\n", encoding="utf-8")
        state = make_state(
            workspace,
            current_step=10,
            completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 9],
            flow_tier="moderate",
            produced_artifacts=["WD-CTX", "WD-TASK"],
            skipped_steps=[],
            can_enter_step_10=True,
            checkpoints={
                "step-2": {"summary": "前置文件检查完成", "prerequisites_checked": True},
                "step-3": {"summary": "模板快照已提取", "template_loaded": True},
                "step-4": {"summary": "方案类型完成", "solution_type": "现有资产改造", "flow_tier": "moderate"},
                "step-6": {"summary": "repowiki 检测完成", "repowiki_checked": True, "repowiki_exists": False},
            },
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10("moderate", errors)
        assert any(error["code"] == "step_skipped_without_checkpoint" for error in errors)

    def test_step_12_flags_require_validator_passed(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text("## WD-CTX\n\n## WD-TASK\n\n## WD-SYN\n", encoding="utf-8")
        workspace["final_document_path"].write_text(
            "# 技术方案文档\n\n## 一、背景\n\n### 1.1 需求概述\n\n内容\n\n### 1.2 核心目标\n\n内容\n\n## 二、设计\n\n### 2.1 方案设计\n\n内容\n\n### 2.2 风险与验证\n\n内容\n",
            encoding="utf-8",
        )
        state = make_state(
            workspace,
            current_step=12,
            completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 10, 11],
            can_enter_step_12=True,
            produced_artifacts=["WD-CTX", "WD-TASK", "WD-SYN"],
            skipped_steps=[9],
            absorption_check_passed=True,
            cleanup_allowed=True,
            checkpoints={
                "step-2": {"summary": "前置文件检查完成", "prerequisites_checked": True},
                "step-3": {"summary": "模板快照已提取", "template_loaded": True},
                "step-4": {"summary": "方案类型完成", "solution_type": "现有资产改造", "flow_tier": "moderate"},
                "step-6": {"summary": "repowiki 检测完成", "repowiki_checked": True, "repowiki_exists": False},
                "step-9": {"summary": "因流程级别跳过", "skipped": True, "reason": "moderate 跳过 step-9"},
                "step-12": {"summary": "准备清理", "validator_passed": False, "working_draft_deleted": False, "state_file_deleted": False},
            },
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_12("moderate", errors)
        assert any(error["code"] == "cleanup_attempt_before_validation" for error in errors)


class TestCleanupScript:
    def test_finalize_cleanup_success(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text("## WD-CTX\n\n## WD-TASK\n\n## WD-SYN\n", encoding="utf-8")
        workspace["final_document_path"].write_text(
            "# 技术方案文档\n\n## 一、背景\n\n### 1.1 需求概述\n\n内容\n\n### 1.2 核心目标\n\n内容\n\n## 二、设计\n\n### 2.1 方案设计\n\n内容\n\n### 2.2 风险与验证\n\n内容\n",
            encoding="utf-8",
        )
        state = make_state(
            workspace,
            current_step=12,
            completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 10, 11],
            can_enter_step_12=True,
            produced_artifacts=["WD-CTX", "WD-TASK", "WD-SYN"],
            skipped_steps=[9],
            checkpoints={
                "step-2": {"summary": "前置文件检查完成", "prerequisites_checked": True},
                "step-3": {"summary": "模板快照已提取", "template_loaded": True},
                "step-4": {"summary": "方案类型完成", "solution_type": "现有资产改造", "flow_tier": "moderate"},
                "step-6": {"summary": "repowiki 检测完成", "repowiki_checked": True, "repowiki_exists": False},
                "step-9": {"summary": "因流程级别跳过", "skipped": True, "reason": "moderate 跳过 step-9"},
            },
        )
        workspace["state_path"].write_text(vs.yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
        exit_code, payload = fc.run_cleanup(workspace["state_path"], "moderate", "吸收检查通过，执行清理")
        assert exit_code == 0
        assert payload["passed"] is True
        assert not workspace["working_draft_path"].exists()
        assert not workspace["state_path"].exists()


class TestRepairPlan:
    def test_repair_plan_contains_final_document_and_block_hints(self) -> None:
        issues = [
            vs.make_issue(
                code="missing_working_draft_block",
                message="步骤 10: working draft 缺少 WD-TASK 区块",
                step=10,
                flow_tier="moderate",
                field="produced_artifacts",
                missing_artifacts=["WD-TASK"],
                recommended_rollback_step=8,
                recommended_repair_step=8,
            ),
            vs.make_issue(
                code="final_document_missing",
                message="步骤 12: 最终文档不存在",
                step=12,
                flow_tier="moderate",
                field="final_document_path",
                recommended_rollback_step=11,
                recommended_repair_step=11,
            ),
        ]
        plan = vs.build_repair_plan(issues)
        assert [item["step"] for item in plan] == [8, 11]
        assert any(hint["artifact"] == "WD-TASK" for hint in plan[0]["artifact_write_hint"])
        assert any(hint["artifact"] == "final_document" for hint in plan[1]["artifact_write_hint"])
