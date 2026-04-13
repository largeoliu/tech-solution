# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "pytest>=8.0"]
# ///
"""create-technical-solution runner/protocol regression tests."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml


skill_root = (
    Path(__file__).parent.parent.parent / "skills" / "create-technical-solution"
)
protocol_root = skill_root / "protocol"
scripts_root = skill_root / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), scripts_root / f"{name}.py"
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


vs = load_script("validate-state")
run_step = load_script("run-step")
protocol_runtime = load_script("protocol_runtime")


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
        "working_draft_path": state_dir / "sample-solution" / "draft",
        "template_path": template_path,
        "members_path": members_path,
        "principles_path": principles_path,
    }


def make_step9_state(workspace: dict[str, Path]) -> dict:
    template_text = workspace["template_path"].read_text(encoding="utf-8")
    headings = vs.extract_slot_headings(template_text)
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
        "working_draft_path": ".architecture/.state/create-technical-solution/sample-solution/draft",
        "final_document_path": ".architecture/technical-solutions/sample-solution.md",
        "slots": [{"slot": item["slot"], "title": item["title"]} for item in headings],
        "checkpoints": {
            "step-1": {
                "summary": "完成；slug=sample-solution",
                "slug": "sample-solution",
                "scope_ready": True,
            },
            "step-2": {"summary": "完成；检查前置文件", "prerequisites_checked": True},
            "step-3": {
                "summary": "完成；模板已加载",
                "template_loaded": True,
                "template_fingerprint": "",
                "slot_count": 4,
            },
            "step-4": {"summary": "完成；类型已判定", "solution_type": "新功能方案"},
            "step-5": {
                "summary": "完成；成员已选择",
                "members_checked": True,
                "selected_members": ["systems_architect"],
                "selected_member_count": 1,
            },
            "step-6": {
                "summary": "完成；repowiki 不存在",
                "repowiki_checked": True,
                "repowiki_exists": False,
                "repowiki_source_count": 0,
            },
            "step-7": {
                "summary": "完成；写入 WD-CTX",
                "wd_ctx_written": True,
                "ctx_count": 1,
            },
            "step-8": {
                "summary": "完成；写入 WD-TASK",
                "wd_task_written": True,
                "task_slot_count": 4,
            },
            "step-9": {
                "summary": "进行中",
                "skipped": False,
                "reason": "",
                "wd_exp_count": 0,
            },
            "step-10": {"summary": "", "wd_syn_written": False, "syn_slot_count": 0},
            "step-11": {
                "summary": "等待成稿",
                "final_document_written": False,
                "absorbed_slot_count": 0,
                "rendered_via_script": False,
            },
            "step-12": {
                "summary": "",
                "validator_passed": False,
                "working_draft_deleted": False,
                "state_file_deleted": False,
            },
        },
        "can_enter_step_8": True,
        "can_enter_step_9": True,
        "can_enter_step_10": False,
        "can_enter_step_11": False,
        "can_enter_step_12": False,
        "absorption_check_passed": False,
        "cleanup_allowed": False,
    }
    state["checkpoints"]["step-3"]["template_fingerprint"] = (
        vs.compute_template_fingerprint(
            template_text,
            headings,
        )
    )
    state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
    return state


def make_step11_state(workspace: dict[str, Path]) -> dict:
    template_text = workspace["template_path"].read_text(encoding="utf-8")
    headings = vs.extract_slot_headings(template_text)
    slot_artifacts = [f"WD-SYN-{item['slot']}" for item in headings]
    state = {
        "current_step": 11,
        "completed_steps": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "skipped_steps": [],
        "pending_questions": [],
        "required_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP-*"] + slot_artifacts,
        "produced_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP-*"] + slot_artifacts,
        "gate_receipt": {
            "step": 11,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        },
        "solution_root": ".architecture/technical-solutions",
        "template_path": ".architecture/templates/technical-solution-template.md",
        "members_path": ".architecture/members.yml",
        "principles_path": ".architecture/principles.md",
        "repowiki_path": ".qoder/repowiki",
        "working_draft_path": ".architecture/.state/create-technical-solution/sample-solution/draft",
        "final_document_path": ".architecture/technical-solutions/sample-solution.md",
        "slots": [{"slot": item["slot"], "title": item["title"]} for item in headings],
        "checkpoints": {
            "step-1": {
                "summary": "完成；slug=sample-solution",
                "slug": "sample-solution",
                "scope_ready": True,
            },
            "step-2": {"summary": "完成；检查前置文件", "prerequisites_checked": True},
            "step-3": {
                "summary": "完成；模板已加载",
                "template_loaded": True,
                "template_fingerprint": "",
                "slot_count": 4,
            },
            "step-4": {"summary": "完成；类型已判定", "solution_type": "新功能方案"},
            "step-5": {
                "summary": "完成；成员已选择",
                "members_checked": True,
                "selected_members": ["systems_architect"],
                "selected_member_count": 1,
            },
            "step-6": {
                "summary": "完成；repowiki 不存在",
                "repowiki_checked": True,
                "repowiki_exists": False,
                "repowiki_source_count": 0,
            },
            "step-7": {
                "summary": "完成；写入 WD-CTX",
                "wd_ctx_written": True,
                "ctx_count": 1,
            },
            "step-8": {
                "summary": "完成；写入 WD-TASK",
                "wd_task_written": True,
                "task_slot_count": 4,
            },
            "step-9": {
                "summary": "完成；写入 WD-EXP-*",
                "wd_exp_written": True,
                "wd_exp_count": 1,
            },
            "step-10": {
                "summary": "完成；写入 WD-SYN",
                "wd_syn_written": True,
                "syn_slot_count": 4,
            },
            "step-11": {
                "summary": "等待成稿",
                "final_document_written": False,
                "absorbed_slot_count": 0,
                "rendered_via_script": False,
            },
            "step-12": {
                "summary": "",
                "validator_passed": False,
                "working_draft_deleted": False,
                "state_file_deleted": False,
            },
        },
        "can_enter_step_8": True,
        "can_enter_step_9": True,
        "can_enter_step_10": True,
        "can_enter_step_11": True,
        "can_enter_step_12": False,
        "absorption_check_passed": False,
        "cleanup_allowed": False,
    }
    state["checkpoints"]["step-3"]["template_fingerprint"] = (
        vs.compute_template_fingerprint(template_text, headings)
    )
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
    state["checkpoints"]["step-9"] = {
        "summary": "待跳过",
        "skipped": False,
        "reason": "",
        "wd_exp_count": 0,
    }
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
        "working_draft_path": ".architecture/.state/create-technical-solution/sample-solution/draft",
        "final_document_path": ".architecture/technical-solutions/sample-solution.md",
        "slots": [
            {"slot": item["slot"], "title": item["title"]} for item in slot_headings
        ],
        "checkpoints": {
            "step-1": {
                "summary": "主题已确定",
                "slug": "sample-solution",
                "scope_ready": True,
            },
            "step-2": {"summary": "前置文件通过", "prerequisites_checked": True},
            "step-3": {
                "summary": "模板已读取",
                "template_loaded": True,
                "template_fingerprint": vs.compute_template_fingerprint(
                    template_text, slot_headings
                ),
                "slot_count": len(slot_headings),
            },
            "step-4": {"summary": "", "solution_type": ""},
            "step-5": {
                "summary": "",
                "members_checked": False,
                "selected_members": [],
                "selected_member_count": 0,
            },
            "step-6": {
                "summary": "",
                "repowiki_checked": False,
                "repowiki_exists": False,
                "repowiki_source_count": 0,
            },
            "step-7": {
                "summary": "",
                "wd_ctx_written": False,
                "ctx_entry_count": 0,
                "repowiki_consumed": False,
            },
            "step-8": {"summary": "", "wd_task_written": False, "task_slot_count": 0},
            "step-9": {
                "summary": "",
                "skipped": False,
                "reason": "",
                "wd_exp_count": 0,
            },
            "step-10": {"summary": "", "wd_syn_written": False, "syn_slot_count": 0},
            "step-11": {
                "summary": "",
                "final_document_written": False,
                "absorbed_slot_count": 0,
                "rendered_via_script": False,
            },
            "step-12": {
                "summary": "",
                "validator_passed": False,
                "working_draft_deleted": False,
                "state_file_deleted": False,
            },
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
    workspace["state_path"].write_text(
        vs.yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def write_directory_draft(
    workspace: dict[str, Path],
    *,
    with_experts: bool = False,
    with_synthesis: bool = False,
) -> None:
    working_dir = workspace["working_draft_path"]
    working_dir.mkdir(parents=True, exist_ok=True)
    (working_dir / "ctx.json").write_text(WD_CTX_PAYLOAD + "\n", encoding="utf-8")
    (working_dir / "task.json").write_text(WD_TASK_PAYLOAD + "\n", encoding="utf-8")
    slots_dir = working_dir / "slots"
    slots_dir.mkdir(parents=True, exist_ok=True)
    for index, title in enumerate(
        ("1.1 需求概述", "1.2 核心目标", "2.1 方案设计", "2.2 风险与验证"), start=1
    ):
        slot_id = f"SLOT-{index:02d}"
        slot_dir = slots_dir / slot_id
        slot_dir.mkdir(parents=True, exist_ok=True)
        experts_json_dir = slot_dir / "experts"
        if with_experts:
            experts_json_dir.mkdir(parents=True, exist_ok=True)
            (experts_json_dir / "systems_architect.json").write_text(
                json.dumps(
                    {
                        "slot": title,
                        "member": "systems_architect",
                        "decision_type": "改造",
                        "rationale": f"复用现有骨架并补齐 {title}。",
                        "evidence_refs": ["CTX-01"],
                        "open_questions": ["无"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        if with_synthesis:
            (slot_dir / "decision.json").write_text(
                json.dumps(
                    {
                        "slot": title,
                        "target_capability": f"收敛 {title} 的最终写法。",
                        "comparisons": [
                            {"path": "复用", "feasibility": "❌", "evidence": "CTX-01", "reason": "不足"},
                            {"path": "改造", "feasibility": "✅", "evidence": "CTX-01", "reason": "推荐"},
                            {"path": "新建", "feasibility": "❌", "evidence": "CTX-01", "reason": "成本高"},
                        ],
                        "selected_path": "改造",
                        "selected_writeup": f"在 {title} 位置补齐内容。",
                        "evidence_refs": ["CTX-01"],
                        "template_gap": "无",
                        "open_question": "无",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )


def write_step9_draft(workspace: dict[str, Path]) -> None:
    write_directory_draft(workspace)


def write_step11_draft(workspace: dict[str, Path]) -> None:
    write_directory_draft(workspace, with_experts=True, with_synthesis=True)


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


WD_CTX_PAYLOAD = """[
  {
    "id": "CTX-01",
    "source": "services/a.py, models/a.py",
    "source_refs": ["services/a.py", "models/a.py"],
    "conclusion": "需求概述沿用现有入口。",
    "applicable_slots": ["1.1 需求概述", "1.2 核心目标", "2.1 方案设计", "2.2 风险与验证"],
    "confidence": "已验证"
  }
]"""


WD_TASK_PAYLOAD = """[
  {
    "slot": "1.1 需求概述",
    "required_ctx": ["CTX-01"],
    "participating_experts": ["systems_architect"],
    "expert_questions": [],
    "suggested_slot": "1.1 需求概述",
    "expression_requirements": "",
    "blockers": "无"
  },
  {
    "slot": "1.2 核心目标",
    "required_ctx": ["CTX-01"],
    "participating_experts": ["systems_architect"],
    "expert_questions": [],
    "suggested_slot": "1.2 核心目标",
    "expression_requirements": "",
    "blockers": "无"
  },
  {
    "slot": "2.1 方案设计",
    "required_ctx": ["CTX-01"],
    "participating_experts": ["systems_architect"],
    "expert_questions": [],
    "suggested_slot": "2.1 方案设计",
    "expression_requirements": "",
    "blockers": "无"
  },
  {
    "slot": "2.2 风险与验证",
    "required_ctx": ["CTX-01"],
    "participating_experts": ["systems_architect"],
    "expert_questions": [],
    "suggested_slot": "2.2 风险与验证",
    "expression_requirements": "",
    "blockers": "无"
  }
]"""


def make_wd_exp_payload() -> str:
    return json.dumps(
        [
            {
                "slot": title,
                "member": "systems_architect",
                "decision_type": "改造",
                "rationale": "复用现有骨架并补齐专家分析。",
                "evidence_refs": ["CTX-01"],
                "open_questions": ["无"],
            }
            for title in ("1.1 需求概述", "1.2 核心目标", "2.1 方案设计", "2.2 风险与验证")
        ],
        ensure_ascii=False,
        indent=2,
    )


def make_wd_exp_payload_for_members(members: list[str]) -> str:
    headings = [
        {"title": "1.1 需求概述"},
        {"title": "1.2 核心目标"},
        {"title": "2.1 方案设计"},
        {"title": "2.2 风险与验证"},
    ]
    payload: list[dict[str, object]] = []
    for item in headings:
        title = item["title"]
        for member in members:
            payload.append(
                {
                    "slot": title,
                    "member": member,
                    "decision_type": "改造",
                    "rationale": "复用现有骨架并补齐专家分析。",
                    "evidence_refs": ["CTX-01"],
                    "open_questions": ["无"],
                }
            )
    return json.dumps(payload, ensure_ascii=False, indent=2)


def make_wd_syn_payload() -> str:
    return json.dumps(
        [
            {
                "slot": title,
                "target_capability": f"收敛 {title} 的最终写法。",
                "comparisons": [
                    {"path": "复用", "feasibility": "❌", "evidence": "CTX-01", "reason": "不足"},
                    {"path": "改造", "feasibility": "✅", "evidence": "CTX-01", "reason": "推荐"},
                    {"path": "新建", "feasibility": "❌", "evidence": "CTX-01", "reason": "成本高"},
                ],
                "selected_path": "改造",
                "selected_writeup": f"在 {title} 位置补齐内容。",
                "evidence_refs": ["CTX-01"],
                "template_gap": "无",
                "open_question": "无",
            }
            for title in ("1.1 需求概述", "1.2 核心目标", "2.1 方案设计", "2.2 风险与验证")
        ],
        ensure_ascii=False,
        indent=2,
    )


def make_args(
    state_path: Path,
    summary: str | None,
    *,
    slug: str | None = None,
    # flow_tier removed - all flows are full
    solution_type: str | None = None,
    member: list[str] | None = None,
    stdin_content: str | None = None,
    ticket: str | None = None,
    slot: str | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        state=str(state_path),
        complete=True,
        summary=summary,
        slug=slug,
        solution_type=solution_type,
        member=member or [],
        ticket=ticket,
        slot=slot,
        _stdin_content=stdin_content,
    )
def mark_card_and_prepare(workspace: dict[str, Path]) -> None:
    assert run_step.mark_step_card_read(workspace["state_path"]) == 0
    assert run_step.prepare_step(workspace["state_path"]) == 0


def prepare_and_get_ticket(workspace: dict[str, Path]) -> str:
    mark_card_and_prepare(workspace)
    return str(vs.load_state(workspace["state_path"])["pending_ticket"]["value"])


class TestProtocolContracts:
    def test_protocol_runtime_exposes_canonical_step_defs(self) -> None:
        assert protocol_runtime.canonical_step_defs() == run_step.STEP_DEFS

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
        assert step9["produces_pattern"] == "WD-EXP-SLOT-*"

    def test_workflow_contract_exposes_runner_metadata(self) -> None:
        workflow = load_protocol("workflow.yaml")
        steps = {step["id"]: step for step in workflow["steps"]}

        assert steps[7]["name"] == "构建共享上下文 (WD-CTX)"
        assert steps[7]["content_block"] == "WD-CTX"
        assert steps[8]["name"] == "生成模板任务单 (WD-TASK)"
        assert steps[8]["content_block"] == "WD-TASK"
        assert steps[10]["name"] == "协作收敛 (WD-SYN-SLOT-*)"
        assert steps[10]["produces_pattern"] == "WD-SYN-SLOT-*"
        assert "content_block" not in steps[10]

    def test_block_contract_defines_wd_exp_minimum_shape(self) -> None:
        contracts = load_protocol("block-contracts.yaml")
        blocks = contracts.get("blocks")
        assert isinstance(blocks, dict)

        wd_exp = blocks["WD-EXP-SLOT"]
        assert wd_exp["heading_pattern"] == r"WD-EXP-SLOT-\d+"
        assert wd_exp["required_sections"] == [
            "参与槽位",
            "决策类型",
            "核心理由",
            "关键证据引用",
            "未决点",
        ]


class TestRunStepBehavior:
    def test_advance_missing_state_bootstraps_step1_business_entry(
        self, workspace: dict[str, Path]
    ) -> None:
        result = run_step.advance_step(workspace["state_path"])

        assert result["status"] == "needs_input"
        assert result["step"] == 1
        assert result["artifact"] is None
        assert result["next_action"] == "submit_business_content"
        assert any("slug" in item for item in result["required_output_shape"]["items"])
        assert any("title" in item for item in result["required_output_shape"]["items"])
        assert workspace["state_path"].exists()
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 1

    def test_advance_missing_state_bootstraps_canonical_paths(
        self, workspace: dict[str, Path]
    ) -> None:
        result = run_step.advance_step(workspace["state_path"])

        assert result["status"] == "needs_input"
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["solution_root"] == ".architecture/technical-solutions"
        assert (
            new_state["working_draft_path"]
            == ".architecture/.state/create-technical-solution/sample-solution/draft"
        )
        assert (
            new_state["final_document_path"]
            == ".architecture/technical-solutions/sample-solution.md"
        )

    def test_prepare_missing_state_bootstraps_canonical_paths_for_legacy_callers(
        self, workspace: dict[str, Path]
    ) -> None:
        exit_code = run_step.prepare_step(workspace["state_path"], slug="sample-solution")

        assert exit_code == 0
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["solution_root"] == ".architecture/technical-solutions"
        assert (
            new_state["working_draft_path"]
            == ".architecture/.state/create-technical-solution/sample-solution/draft"
        )
        assert (
            new_state["final_document_path"]
            == ".architecture/technical-solutions/sample-solution.md"
        )

    def test_protocol_runtime_builds_same_canonical_bootstrap_payload(
        self, workspace: dict[str, Path]
    ) -> None:
        payload = protocol_runtime.build_canonical_state_payload(
            state_path=workspace["state_path"],
            slug="sample-solution",
        )

        assert payload == run_step.build_initial_state_payload(
            workspace["state_path"],
            slug="sample-solution",
        )

    def test_advance_automatic_step_runs_full_sequence(
        self, workspace: dict[str, Path]
    ) -> None:
        assert (
            run_step.complete_step(
                make_args(workspace["state_path"], "定题完成", slug="sample-solution")
            )
            == 0
        )

        result = run_step.advance_step(workspace["state_path"])

        assert result["status"] == "completed"
        assert result["step"] == 2
        assert result["next_step"] == 3
        new_state = vs.load_state(workspace["state_path"])
        assert 2 in new_state["completed_steps"]
        assert new_state["current_step"] == 3

    def test_advance_creative_step_returns_business_task(
        self, workspace: dict[str, Path]
    ) -> None:
        assert (
            run_step.complete_step(
                make_args(workspace["state_path"], "定题完成", slug="sample-solution")
            )
            == 0
        )
        assert run_step.complete_step(make_args(workspace["state_path"], "前置文件检查通过")) == 0
        assert run_step.complete_step(make_args(workspace["state_path"], "模板读取完成")) == 0
        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "类型判定完成",
                    solution_type="新功能方案",
                )
            )
            == 0
        )
        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "成员选定完成",
                    member=["SYSTEMS_ARCHITECT"],
                )
            )
            == 0
        )
        assert run_step.complete_step(make_args(workspace["state_path"], "repowiki 检查完成")) == 0

        result = run_step.advance_step(workspace["state_path"])

        assert result["status"] == "needs_input"
        assert result["step"] == 7
        assert result["artifact"] == "WD-CTX"
        assert result["business_task"]
        assert result["required_output_shape"]["type"] == "array"
        assert result["required_output_shape"]["item_schema"] == "ctx_entry"
        assert result["next_action"] == "submit_structured_payload"
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 7
        assert new_state["pending_ticket"]["step"] == 7
        assert result["ticket"] == new_state["pending_ticket"]["value"]
        assert result["allowed_block_pattern"] == "WD-CTX"
        assert "--complete --ticket" in result["submit_command"]
        assert result["json_scaffold_command"].endswith("--emit-json-scaffold")
        assert isinstance(result["json_scaffold_preview"], list)
        assert result["json_scaffold_preview"][0]["id"] == "CTX-01"

    def test_advance_step_9_returns_ticket_and_submit_contract(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)

        result = run_step.advance_step(workspace["state_path"])

        refreshed = vs.load_state(workspace["state_path"])
        ticket = refreshed["pending_ticket"]
        assert result["status"] == "needs_input"
        assert result["step"] == 9
        assert result["ticket"] == ticket["value"]
        assert result["allowed_block_pattern"] == "WD-EXP-SLOT-*"
        assert result["submit_command"].endswith("--complete --ticket <ticket> --summary \"<完成摘要>\"") is False
        assert "--complete --ticket" in result["submit_command"]
        assert result["json_scaffold_command"].endswith("--emit-json-scaffold --slot SLOT-01")
        assert isinstance(result["json_scaffold_preview"], list)
        assert result["json_scaffold_preview"][0]["slot"] == "1.1 需求概述"
        assert result["json_scaffold_preview"][0]["evidence_refs"] == []

    def test_advance_step_9_exposes_slot_progress_for_public_agent_path(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        state["artifact_progress"] = {
            "WD-EXP-SLOT-*": {"completed_slots": ["SLOT-02", "SLOT-04"]}
        }
        write_state(workspace, state)
        write_step9_draft(workspace)

        result = run_step.advance_step(workspace["state_path"])

        assert result["status"] == "needs_input"
        assert result["step"] == 9
        assert result["slot_progress"] == {
            "completed_slots": ["SLOT-02", "SLOT-04"],
            "remaining_slots": ["SLOT-01", "SLOT-03"],
            "recommended_slot": "SLOT-01",
        }

    def test_complete_step_7_accepts_structured_payload_and_renders_ctx_markdown(
        self, workspace: dict[str, Path]
    ) -> None:
        assert (
            run_step.complete_step(
                make_args(workspace["state_path"], "定题完成", slug="sample-solution")
            )
            == 0
        )
        assert run_step.complete_step(make_args(workspace["state_path"], "前置文件检查通过")) == 0
        assert run_step.complete_step(make_args(workspace["state_path"], "模板读取完成")) == 0
        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "类型判定完成",
                    solution_type="新功能方案",
                )
            )
            == 0
        )
        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "成员选定完成",
                    member=["SYSTEMS_ARCHITECT"],
                )
            )
            == 0
        )
        assert run_step.complete_step(make_args(workspace["state_path"], "repowiki 检查完成")) == 0

        result = run_step.advance_step(workspace["state_path"])
        step7_ticket = result["ticket"]

        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "WD-CTX 完成",
                    stdin_content=WD_CTX_PAYLOAD,
                    ticket=step7_ticket,
                )
            )
            == 0
        )

        assert json.loads(
            (workspace["working_draft_path"] / "ctx.json").read_text(encoding="utf-8")
        ) == json.loads(WD_CTX_PAYLOAD)
        assert not (workspace["working_draft_path"] / "ctx.md").exists()

    def test_complete_step_8_accepts_structured_payload_and_renders_task_markdown(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        state["current_step"] = 8
        state["completed_steps"] = [1, 2, 3, 4, 5, 6, 7]
        state["produced_artifacts"] = ["WD-CTX"]
        state["gate_receipt"] = {
            "step": 8,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step9_draft(workspace)
        step8_ticket = prepare_and_get_ticket(workspace)

        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "WD-TASK 完成",
                    stdin_content=WD_TASK_PAYLOAD,
                    ticket=step8_ticket,
                )
            )
            == 0
        )

        assert json.loads(
            (workspace["working_draft_path"] / "task.json").read_text(encoding="utf-8")
        ) == json.loads(WD_TASK_PAYLOAD)
        assert not (workspace["working_draft_path"] / "task.md").exists()

    def test_complete_step_9_accepts_structured_payload_and_writes_expert_truth(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        ticket = prepare_and_get_ticket(workspace)

        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "专家分析完成",
                    stdin_content=make_wd_exp_payload(),
                    ticket=ticket,
                )
            )
            == 0
        )

        member_truth = workspace["working_draft_path"] / "slots" / "SLOT-01" / "experts" / "systems_architect.json"
        assert json.loads(member_truth.read_text(encoding="utf-8")) == {
            "slot": "1.1 需求概述",
            "member": "systems_architect",
            "decision_type": "改造",
            "rationale": "复用现有骨架并补齐专家分析。",
            "evidence_refs": ["CTX-01"],
            "open_questions": ["无"],
        }
        assert not (workspace["working_draft_path"] / "slots" / "SLOT-01" / "experts.md").exists()

    def test_complete_step_10_accepts_structured_payload_and_writes_decision_truth(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step11_state(workspace)
        state["current_step"] = 10
        state["completed_steps"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        state["gate_receipt"] = {
            "step": 10,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step11_draft(workspace)
        ticket = prepare_and_get_ticket(workspace)

        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "WD-SYN 完成",
                    stdin_content=make_wd_syn_payload(),
                    ticket=ticket,
                )
            )
            == 0
        )

        decision_truth = json.loads(
            (workspace["working_draft_path"] / "slots" / "SLOT-01" / "decision.json").read_text(
                encoding="utf-8"
            )
        )
        assert decision_truth["slot"] == "1.1 需求概述"
        assert decision_truth["selected_writeup"] == "在 1.1 需求概述 位置补齐内容。"
        assert not (workspace["working_draft_path"] / "slots" / "SLOT-01" / "synthesis.md").exists()

    def test_complete_step_11_renders_from_canonical_decision_truth_and_records_traceability(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step11_state(workspace)
        write_state(workspace, state)
        write_step11_draft(workspace)
        slot1_dir = workspace["working_draft_path"] / "slots" / "SLOT-01"
        (slot1_dir / "decision.json").write_text(
            json.dumps(
                {
                    "slot": "1.1 需求概述",
                    "target_capability": "收敛 1.1 需求概述 的最终写法。",
                    "comparisons": [
                        {"path": "复用", "feasibility": "❌", "evidence": "CTX-01", "reason": "不足"},
                        {"path": "改造", "feasibility": "✅", "evidence": "CTX-01", "reason": "推荐"},
                        {"path": "新建", "feasibility": "❌", "evidence": "CTX-01", "reason": "成本高"},
                    ],
                    "selected_path": "改造",
                    "selected_writeup": "来自 canonical truth 的最终写法。",
                    "evidence_refs": ["CTX-01"],
                    "template_gap": "无",
                    "open_question": "无",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (slot1_dir / "synthesis.md").write_text(
            "### 槽位：1.1 需求概述\n#### 目标能力\n- 这是一份被篡改的 derived view。\n#### 选定路径\n- 选定写法:\n不要信任我。\n",
            encoding="utf-8",
        )

        code, message = run_step.complete_step_11(workspace["state_path"], "成稿完成")

        assert code == 0, message
        new_state = vs.load_state(workspace["state_path"])
        final_document_path = workspace["repo"] / new_state["final_document_path"]
        final_content = final_document_path.read_text(encoding="utf-8")
        assert "来自 canonical truth 的最终写法。" in final_content
        assert "不要信任我。" not in final_content
        render_receipt = new_state["checkpoints"]["step-11"]["render_receipt"]
        assert render_receipt["mode"] == "decision_truth"
        assert render_receipt["slots"][0]["slot"] == "SLOT-01"
        assert render_receipt["slots"][0]["decision_artifact"] == "WD-SYN-SLOT-01"

    def test_advance_step_4_returns_business_decision_contract(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step4_state(workspace)
        write_state(workspace, state)

        result = run_step.advance_step(workspace["state_path"])

        new_state = vs.load_state(workspace["state_path"])

        assert result["status"] == "needs_input"
        assert result["step"] == 4
        assert result["artifact"] is None
        assert result["next_action"] == "submit_business_content"
        assert result["ticket"] == new_state["pending_ticket"]["value"]
        assert "--complete --ticket" in result["submit_command"]
        assert "--summary" not in result["submit_command"]
        assert any("solution_type" in item for item in result["required_output_shape"]["items"])
        assert "方案类型" in result["business_task"]
        assert new_state["current_step"] == 4
        assert new_state["pending_ticket"]["step"] == 4

    def test_advance_step_4_contract_text_mentions_no_deep_exploration(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step4_state(workspace)
        write_state(workspace, state)

        result = run_step.advance_step(workspace["state_path"])

        assert "方案类型" in result["business_task"]
        contracts = result.get("required_output_shape", {}).get("items", [])
        all_text = result["business_task"] + " ".join(str(c) for c in contracts)
        assert (
            "不需要搜索或阅读业务实现代码" in all_text
            or "属于步骤 7" in all_text
        ), "step 4 contract should explicitly prohibit deep code exploration"

    def test_advance_step_5_returns_member_selection_contract(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step5_state(workspace)
        write_state(workspace, state)

        result = run_step.advance_step(workspace["state_path"])

        new_state = vs.load_state(workspace["state_path"])

        assert result["status"] == "needs_input"
        assert result["step"] == 5
        assert result["artifact"] is None
        assert result["next_action"] == "submit_business_content"
        assert result["ticket"] == new_state["pending_ticket"]["value"]
        assert "--complete --ticket" in result["submit_command"]
        assert "--summary" not in result["submit_command"]
        assert any("selected_members" in item for item in result["required_output_shape"]["items"])
        assert "参与成员" in result["business_task"]
        assert new_state["current_step"] == 5
        assert new_state["pending_ticket"]["step"] == 5

    def test_advance_step_8_refreshes_stale_ticket_after_task_drift(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        state["current_step"] = 8
        state["completed_steps"] = [1, 2, 3, 4, 5, 6, 7]
        state["gate_receipt"] = {
            "step": 8,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step9_draft(workspace)
        old_ticket = prepare_and_get_ticket(workspace)
        task_path = workspace["working_draft_path"] / "task.json"
        task_path.write_text(task_path.read_text(encoding="utf-8") + "\n- 新增一行\n", encoding="utf-8")

        result = run_step.advance_step(workspace["state_path"])

        assert result["status"] == "needs_input"
        assert result["step"] == 8
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["pending_ticket"]["step"] == 8
        assert new_state["pending_ticket"]["value"] != old_ticket

    def test_advance_step_dispatches_receipt_refresh_repair(self, workspace: dict[str, Path]) -> None:
        state = make_step9_state(workspace)
        state["gate_receipt"] = {
            "step": 5,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step9_draft(workspace)

        result = run_step.advance_step(workspace["state_path"])

        refreshed = vs.load_state(workspace["state_path"])
        assert result["status"] == "needs_input"
        assert result["step"] == 9
        assert refreshed["gate_receipt"]["step"] == 9
        assert refreshed["pending_ticket"]["step"] == 9

    def test_advance_step_dispatches_rebuild_repair_to_public_entry_surface(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step11_state(workspace)
        state["working_draft_path"] = ".architecture/.state/create-technical-solution/missing-solution"
        state["gate_receipt"] = {
            "step": 11,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)

        result = run_step.advance_step(workspace["state_path"])

        refreshed = vs.load_state(workspace["state_path"])
        assert result["status"] == "completed"
        assert result["step"] == 3
        assert result["next_step"] == 4
        assert refreshed["current_step"] == 4
        assert refreshed.get("pending_ticket", {}) == {}

    def test_advance_step_dispatches_repair_before_creative_entry_when_gate_is_false(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        state["current_step"] = 8
        state["completed_steps"] = [1, 2, 3, 4, 5, 6, 7]
        state["can_enter_step_8"] = False
        state["gate_receipt"] = {
            "step": 8,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step9_draft(workspace)

        result = run_step.advance_step(workspace["state_path"])

        refreshed = vs.load_state(workspace["state_path"])
        assert result["status"] == "needs_input"
        assert result["step"] == 7
        assert refreshed["current_step"] == 7
        assert refreshed["pending_ticket"]["step"] == 7

    def test_rebuild_from_step_prunes_future_runtime_state(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step11_state(workspace)
        state["checkpoints"]["step-10"] = {
            "summary": "完成；写入协作收敛；slots=4；gate: step-11 ready",
            "wd_syn_written": True,
            "syn_slot_count": 4,
        }
        state["checkpoints"]["step-11"] = {
            "summary": "完成；最终文档已渲染；absorbed_slots=4；gate: step-12 ready",
            "final_document_written": True,
            "absorbed_slot_count": 4,
            "rendered_via_script": True,
        }
        state["produced_artifacts"] = ["WD-CTX", "WD-TASK", "WD-EXP-SLOT-01", "WD-SYN-SLOT-01"]
        state["artifact_registry"] = {
            "WD-CTX": {"path": "ctx.json"},
            "WD-TASK": {"path": "task.json"},
            "WD-EXP-SLOT-01": {"path": "slots/SLOT-01/experts"},
            "WD-SYN-SLOT-01": {"path": "slots/SLOT-01/decision.json"},
        }
        state["artifact_progress"] = {
            "WD-EXP-SLOT-*": {"completed_slots": ["SLOT-01"]},
            "WD-SYN-SLOT-*": {"completed_slots": ["SLOT-01"]},
        }
        state["can_enter_step_11"] = True
        state["can_enter_step_12"] = True
        state["absorption_check_passed"] = True
        state["cleanup_allowed"] = True

        run_step._trim_runtime_state_for_repair(state, target_step=7)

        assert state["current_step"] == 7
        assert "step-10" not in state["checkpoints"]
        assert "step-11" not in state["checkpoints"]
        assert state["produced_artifacts"] == []
        assert state["artifact_registry"] == {}
        assert state["artifact_progress"] == {}
        assert "can_enter_step_11" not in state
        assert "can_enter_step_12" not in state
        assert "absorption_check_passed" not in state
        assert "cleanup_allowed" not in state

    def test_advance_step_dispatches_final_document_rerender(self, workspace: dict[str, Path]) -> None:
        state = make_step11_state(workspace)
        state["checkpoints"]["step-11"]["rendered_via_script"] = False
        state["gate_receipt"] = {
            "step": 11,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step11_draft(workspace)
        final_document_path = workspace["repo"] / state["final_document_path"]
        final_document_path.write_text(FINAL_DOC, encoding="utf-8")

        result = run_step.advance_step(workspace["state_path"])

        refreshed = vs.load_state(workspace["state_path"])
        assert result["status"] == "completed"
        assert result["step"] == 11
        assert result["next_step"] == 12
        assert refreshed["current_step"] == 12
        assert refreshed["checkpoints"]["step-11"]["rendered_via_script"] is True

    def test_complete_step_8_artifact_drift_message_discourages_delete_recovery(
        self, workspace: dict[str, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        state = make_step9_state(workspace)
        state["current_step"] = 8
        state["completed_steps"] = [1, 2, 3, 4, 5, 6, 7]
        state["gate_receipt"] = {
            "step": 8,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step9_draft(workspace)
        ticket = prepare_and_get_ticket(workspace)
        task_path = workspace["working_draft_path"] / "task.json"
        task_path.write_text(task_path.read_text(encoding="utf-8") + "\n- 新增一行\n", encoding="utf-8")

        exit_code = run_step.complete_step(
            make_args(
                workspace["state_path"],
                "WD-TASK 完成",
                stdin_content=WD_TASK_PAYLOAD,
                ticket=ticket,
            )
        )

        assert exit_code == 1
        output = capsys.readouterr().out
        assert "重新执行 --advance" in output
        assert "不要删除现有 draft 文件" in output

    def test_prepare_step_requires_step_card_read_ack(self, workspace: dict[str, Path]) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)

        exit_code = run_step.prepare_step(workspace["state_path"])

        assert exit_code != 0
        refreshed = vs.load_state(workspace["state_path"])
        assert refreshed.get("pending_ticket", {}) == {}

    def test_mark_step_card_read_allows_prepare(self, workspace: dict[str, Path]) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)

        mark_code = run_step.mark_step_card_read(workspace["state_path"])
        prepare_code = run_step.prepare_step(workspace["state_path"])

        assert mark_code == 0
        assert prepare_code == 0
        refreshed = vs.load_state(workspace["state_path"])
        step_cards_read = refreshed.get("step_cards_read", {})
        assert "9" in step_cards_read
        assert step_cards_read["9"]["card_path"].endswith("09-组织专家按模板逐槽位分析.md")
        assert step_cards_read["9"]["card_hash"]

    def test_main_prepare_mode_keeps_summary_optional(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, Path] = {}

        def fake_prepare_step(state_path: Path, *, slug: str | None = None) -> int:
            captured["state_path"] = state_path
            return 0

        monkeypatch.setattr(run_step, "prepare_step", fake_prepare_step)
        monkeypatch.setattr(
            "sys.argv",
            ["run-step.py", "--state", str(workspace["state_path"]), "--prepare"],
        )

        assert run_step.main() == 0
        assert captured["state_path"] == workspace["state_path"].resolve()

    def test_main_advance_mode_keeps_summary_optional(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        def fake_advance_step(state_path: Path) -> dict[str, object]:
            assert state_path == workspace["state_path"].resolve()
            return {
                "status": "needs_input",
                "step": 7,
                "artifact": "WD-CTX",
                "business_task": "产出共享上下文",
                "required_output_shape": {"type": "array", "item_schema": "ctx_entry"},
                "next_action": "submit_structured_payload",
            }

        monkeypatch.setattr(run_step, "advance_step", fake_advance_step)
        monkeypatch.setattr(
            "sys.argv",
            ["run-step.py", "--state", str(workspace["state_path"]), "--advance"],
        )

        assert run_step.main() == 0
        output = capsys.readouterr().out
        assert '"status": "needs_input"' in output
        assert '"artifact": "WD-CTX"' in output

    def test_main_rejects_advance_with_complete(
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
                "--advance",
                "--complete",
                "--summary",
                "noop",
            ],
        )

        with pytest.raises(SystemExit) as exc_info:
            run_step.main()

        assert exc_info.value.code == 2

    def test_main_emit_json_scaffold_mode_keeps_summary_optional(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, object] = {}

        def fake_emit_json_scaffold(
            state_path: Path, members: list[str] | None = None, slot: str | None = None
        ) -> int:
            captured["state_path"] = state_path
            captured["members"] = members
            captured["slot"] = slot
            return 0

        monkeypatch.setattr(run_step, "emit_json_scaffold", fake_emit_json_scaffold)
        monkeypatch.setattr(
            "sys.argv",
            ["run-step.py", "--state", str(workspace["state_path"]), "--emit-json-scaffold"],
        )

        assert run_step.main() == 0
        assert captured == {
            "state_path": workspace["state_path"].resolve(),
            "members": [],
            "slot": None,
        }

    def test_main_rejects_emit_json_scaffold_with_complete(
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
                "--emit-json-scaffold",
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
            captured["ticket"] = args.ticket
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
                "--ticket",
                "ticket-123",
                "--member",
                "SYSTEMS_ARCHITECT",
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
            "ticket": "ticket-123",
        }

    def test_main_complete_mode_keeps_summary_optional(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, object] = {}

        def fake_complete_step(args: argparse.Namespace) -> int:
            captured["state"] = args.state
            captured["complete"] = args.complete
            captured["summary"] = args.summary
            captured["ticket"] = args.ticket
            return 0

        monkeypatch.setattr(run_step, "complete_step", fake_complete_step)
        monkeypatch.setattr(
            "sys.argv",
            [
                "run-step.py",
                "--state",
                str(workspace["state_path"]),
                "--complete",
                "--ticket",
                "ticket-123",
            ],
        )

        assert run_step.main() == 0
        assert captured == {
            "state": str(workspace["state_path"]),
            "complete": True,
            "summary": None,
            "ticket": "ticket-123",
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

    def test_main_help_hides_internal_low_level_flags(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            ["run-step.py", "--state", str(workspace["state_path"]), "--help"],
        )

        with pytest.raises(SystemExit) as exc_info:
            run_step.main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out
        assert "--advance" in output
        assert "--complete" in output
        assert "--emit-json-scaffold" in output
        assert "--emit-scaffold" not in output
        assert "--prepare" not in output
        assert "--mark-step-card-read" not in output
        assert "--solution-type" not in output
        assert "--member" not in output
        assert "--slug" not in output

    def test_emit_json_scaffold_step7_matches_required_shape(
        self, workspace: dict[str, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        state = make_step9_state(workspace)
        state["current_step"] = 7
        state["completed_steps"] = [1, 2, 3, 4, 5, 6]
        state["gate_receipt"] = {
            "step": 7,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step9_draft(workspace)

        exit_code = run_step.emit_json_scaffold(workspace["state_path"])

        assert exit_code == 0
        payload = json.loads(capsys.readouterr().out)
        assert isinstance(payload, list)
        assert payload[0] == {
            "id": "CTX-01",
            "source": "",
            "source_refs": [],
            "conclusion": "",
            "applicable_slots": ["1.1 需求概述"],
            "confidence": "",
        }

    def test_emit_json_scaffold_step9_respects_member_filter(
        self, workspace: dict[str, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        state = make_step9_state(workspace)
        state["checkpoints"]["step-5"]["selected_members"] = [
            "systems_architect",
            "domain_expert",
        ]
        state["checkpoints"]["step-5"]["selected_member_count"] = 2
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step9_draft(workspace)

        exit_code = run_step.emit_json_scaffold(
            workspace["state_path"], members=["domain_expert"]
        )

        assert exit_code == 0
        payload = json.loads(capsys.readouterr().out)
        assert len(payload) == 4
        assert payload[0]["slot"] == "1.1 需求概述"
        assert payload[0]["member"] == "domain_expert"
        assert payload[0]["decision_type"] == ""
        assert payload[0]["rationale"] == ""
        assert payload[0]["evidence_refs"] == []
        assert payload[0]["open_questions"] == []

    def test_emit_json_scaffold_step9_expands_entries_for_all_selected_members(
        self, workspace: dict[str, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        state = make_step9_state(workspace)
        state["checkpoints"]["step-5"]["selected_members"] = [
            "systems_architect",
            "domain_expert",
        ]
        state["checkpoints"]["step-5"]["selected_member_count"] = 2
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step9_draft(workspace)

        exit_code = run_step.emit_json_scaffold(workspace["state_path"])

        assert exit_code == 0
        payload = json.loads(capsys.readouterr().out)
        assert len(payload) == 8
        assert payload[0]["slot"] == "1.1 需求概述"
        assert payload[0]["member"] == "systems_architect"
        assert payload[1]["slot"] == "1.1 需求概述"
        assert payload[1]["member"] == "domain_expert"

    def test_emit_json_scaffold_step9_respects_slot_filter(
        self, workspace: dict[str, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)

        exit_code = run_step.emit_json_scaffold(workspace["state_path"], slot="SLOT-02")

        assert exit_code == 0
        payload = json.loads(capsys.readouterr().out)
        assert len(payload) == 1
        assert payload[0]["slot"] == "1.2 核心目标"

    def test_emit_json_scaffold_step10_matches_required_shape(
        self, workspace: dict[str, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        state = make_step11_state(workspace)
        state["current_step"] = 10
        state["completed_steps"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        state["gate_receipt"] = {
            "step": 10,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step11_draft(workspace)

        exit_code = run_step.emit_json_scaffold(workspace["state_path"])

        assert exit_code == 0
        payload = json.loads(capsys.readouterr().out)
        assert isinstance(payload, list)
        assert payload[0]["slot"] == "1.1 需求概述"
        assert payload[0]["target_capability"] == ""
        assert payload[0]["comparisons"] == [
            {"path": "复用", "feasibility": "", "evidence": "", "reason": ""},
            {"path": "改造", "feasibility": "", "evidence": "", "reason": ""},
            {"path": "新建", "feasibility": "", "evidence": "", "reason": ""},
        ]
        assert payload[0]["selected_path"] == ""
        assert payload[0]["selected_writeup"] == ""
        assert payload[0]["evidence_refs"] == []

    def test_emit_json_scaffold_uses_stdout_instead_of_complete_path(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        state = make_step11_state(workspace)
        state["current_step"] = 10
        state["completed_steps"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        state["gate_receipt"] = {
            "step": 10,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step11_draft(workspace)

        def forbid_complete(*_args, **_kwargs):
            raise AssertionError("emit_json_scaffold should not call complete path")

        monkeypatch.setattr(run_step, "complete_creative_step", forbid_complete)

        exit_code = run_step.emit_json_scaffold(workspace["state_path"])

        assert exit_code == 0
        assert '"comparisons"' in capsys.readouterr().out

    def test_run_step_reads_names_and_default_blocks_from_workflow(self) -> None:
        assert run_step.get_step_name(7) == "构建共享上下文 (WD-CTX)"
        assert run_step.get_step_name(10) == "协作收敛 (WD-SYN-SLOT-*)"
        assert run_step.default_block_for_step(7) == "WD-CTX"
        assert run_step.default_block_for_step(8) == "WD-TASK"
        assert run_step.default_block_for_step(10) is None
        assert run_step.get_step_card_path(9).name == "09-组织专家按模板逐槽位分析.md"

    def test_render_run_step_command_prefers_advance_for_automatic_steps(
        self, workspace: dict[str, Path]
    ) -> None:
        commands = protocol_runtime.render_run_step_command(
            state_path=workspace["state_path"],
            step=2,
            state={"current_step": 2},
        )

        assert commands == [
            f"{protocol_runtime.run_step_base_command(workspace['state_path'])} --advance"
        ]

    def test_render_run_step_command_prefers_advance_for_step_1_entry(
        self, workspace: dict[str, Path]
    ) -> None:
        commands = protocol_runtime.render_run_step_command(
            state_path=workspace["state_path"],
            step=1,
            state={"current_step": 1},
        )

        assert commands == [
            f"{protocol_runtime.run_step_base_command(workspace['state_path'])} --advance"
        ]

    def test_run_step_base_command_prefers_scripts_entry(
        self, workspace: dict[str, Path]
    ) -> None:
        command = protocol_runtime.run_step_base_command(workspace["state_path"])
        assert "/skills/create-technical-solution/scripts/run-step.py" in command
        assert "/skills/create-technical-solution/run-step.py" not in command

    def test_render_run_step_command_uses_complete_only_after_creative_ticket_exists(
        self, workspace: dict[str, Path]
    ) -> None:
        no_ticket = protocol_runtime.render_run_step_command(
            state_path=workspace["state_path"],
            step=7,
            state={"current_step": 7, "pending_ticket": {}},
        )
        with_ticket = protocol_runtime.render_run_step_command(
            state_path=workspace["state_path"],
            step=7,
            state={"current_step": 7, "pending_ticket": {"step": 7, "value": "abc"}},
        )

        assert no_ticket == [
            f"{protocol_runtime.run_step_base_command(workspace['state_path'])} --advance"
        ]
        assert with_ticket[0].endswith("--complete --ticket <ticket> <<'HEREDOC'")

    def test_render_run_step_command_uses_business_payload_for_step_4_and_5(
        self, workspace: dict[str, Path]
    ) -> None:
        step4_no_ticket = protocol_runtime.render_run_step_command(
            state_path=workspace["state_path"],
            step=4,
            state={"current_step": 4, "pending_ticket": {}},
        )
        step4_with_ticket = protocol_runtime.render_run_step_command(
            state_path=workspace["state_path"],
            step=4,
            state={"current_step": 4, "pending_ticket": {"step": 4, "value": "abc"}},
        )
        step5_no_ticket = protocol_runtime.render_run_step_command(
            state_path=workspace["state_path"],
            step=5,
            state={"current_step": 5, "pending_ticket": {}},
        )
        step5_with_ticket = protocol_runtime.render_run_step_command(
            state_path=workspace["state_path"],
            step=5,
            state={"current_step": 5, "pending_ticket": {"step": 5, "value": "abc"}},
        )

        assert step4_no_ticket == [
            f"{protocol_runtime.run_step_base_command(workspace['state_path'])} --advance"
        ]
        assert step5_no_ticket == [
            f"{protocol_runtime.run_step_base_command(workspace['state_path'])} --advance"
        ]
        assert step4_with_ticket[0].endswith("--complete --ticket <ticket> <<'HEREDOC'")
        assert '"solution_type": "<方案类型>"' in "\n".join(step4_with_ticket)
        assert step5_with_ticket[0].endswith("--complete --ticket <ticket> <<'HEREDOC'")
        assert '"selected_members": ["<MEMBER_ID>"]' in "\n".join(step5_with_ticket)
        assert '"id": "CTX-01"' in "\n".join(protocol_runtime.render_run_step_command(state_path=workspace["state_path"], step=7, state={"pending_ticket": {"step": 7}}))
        assert '"slot": "1.1 需求概述"' in "\n".join(protocol_runtime.render_run_step_command(state_path=workspace["state_path"], step=8, state={"pending_ticket": {"step": 8}}))

    def test_complete_creative_step_uses_in_process_validator_and_writer(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        stdin_content = make_wd_exp_payload_for_members([
            "systems_architect",
            "domain_expert",
        ])

        def forbid_subprocess(*_args, **_kwargs):
            raise AssertionError("complete_creative_step should not use subprocess")

        monkeypatch.setattr(run_step, "run_script", forbid_subprocess)

        code, message = run_step.complete_creative_step(
            workspace["state_path"],
            "专家分析完成",
            9,
            stdin_content,
        )

        assert code == 0, message
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 10
        assert new_state["checkpoints"]["step-9"]["wd_exp_count"] == 4
        assert new_state["can_enter_step_10"] is True

    def test_prepare_step_persists_ticket_for_current_step(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)

        mark_card_and_prepare(workspace)
        exit_code = 0

        assert exit_code == 0
        new_state = vs.load_state(workspace["state_path"])
        ticket = new_state.get("pending_ticket")
        assert isinstance(ticket, dict)
        assert ticket["step"] == 9
        assert isinstance(ticket["value"], str) and ticket["value"]
        assert isinstance(ticket["state_fingerprint"], str) and ticket["state_fingerprint"]
        assert isinstance(ticket["artifact_fingerprint"], str)
        assert ticket["allowed_block_pattern"] == "WD-EXP-SLOT-*"

    def test_complete_step_9_rejects_payload_outside_requested_slot(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        ticket = prepare_and_get_ticket(workspace)

        exit_code = run_step.complete_step(
            make_args(
                workspace["state_path"],
                "专家分析完成",
                stdin_content=json.dumps(
                    [
                        {
                            "slot": "1.2 核心目标",
                            "member": "systems_architect",
                            "decision_type": "改造",
                            "rationale": "复用现有骨架并补齐专家分析。",
                            "evidence_refs": ["CTX-01"],
                            "open_questions": ["无"],
                        }
                    ],
                    ensure_ascii=False,
                    indent=2,
                ),
                ticket=ticket,
                slot="SLOT-01",
            )
        )

        assert exit_code != 0
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 9
        assert new_state["pending_ticket"]["value"] == ticket

    def test_complete_step_10_rejects_payload_outside_requested_slot(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step11_state(workspace)
        state["current_step"] = 10
        state["completed_steps"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        state["gate_receipt"] = {
            "step": 10,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step11_draft(workspace)
        ticket = prepare_and_get_ticket(workspace)

        exit_code = run_step.complete_step(
            make_args(
                workspace["state_path"],
                "WD-SYN 完成",
                stdin_content=json.dumps(
                    [
                        {
                            "slot": "1.2 核心目标",
                            "target_capability": "收敛 1.2 核心目标 的最终写法。",
                            "comparisons": [
                                {"path": "复用", "feasibility": "❌", "evidence": "CTX-01", "reason": "不足"},
                                {"path": "改造", "feasibility": "✅", "evidence": "CTX-01", "reason": "推荐"},
                                {"path": "新建", "feasibility": "❌", "evidence": "CTX-01", "reason": "成本高"},
                            ],
                            "selected_path": "改造",
                            "selected_writeup": "在 1.2 核心目标 位置补齐内容。",
                            "evidence_refs": ["CTX-01"],
                            "template_gap": "无",
                            "open_question": "无",
                        }
                    ],
                    ensure_ascii=False,
                    indent=2,
                ),
                ticket=ticket,
                slot="SLOT-01",
            )
        )

        assert exit_code != 0

    def test_complete_step_requires_ticket_after_prepare(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        mark_card_and_prepare(workspace)

        exp_blocks = make_wd_exp_payload()

        exit_code = run_step.complete_step(
            make_args(workspace["state_path"], "专家分析完成", stdin_content=exp_blocks)
        )

        assert exit_code != 0
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 9

    def test_complete_step_requires_prepare_ticket_for_creative_steps(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)

        exp_blocks = make_wd_exp_payload()

        exit_code = run_step.complete_step(
            make_args(workspace["state_path"], "专家分析完成", stdin_content=exp_blocks)
        )

        assert exit_code != 0
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 9
        assert new_state.get("pending_ticket", {}) == {}

    def test_complete_step_accepts_matching_ticket_after_prepare(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        mark_card_and_prepare(workspace)
        ticket = vs.load_state(workspace["state_path"])["pending_ticket"]["value"]

        exp_blocks = make_wd_exp_payload()

        exit_code = run_step.complete_step(
            make_args(
                workspace["state_path"],
                "专家分析完成",
                stdin_content=exp_blocks,
                ticket=ticket,
            )
        )

        assert exit_code == 0
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 10

    def test_complete_step_rejects_state_drift_after_prepare(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        mark_card_and_prepare(workspace)

        prepared_state = vs.load_state(workspace["state_path"])
        prepared_state["checkpoints"]["step-8"]["summary"] = "被篡改"
        write_state(workspace, prepared_state)
        ticket = vs.load_state(workspace["state_path"])["pending_ticket"]["value"]

        exp_blocks = make_wd_exp_payload()

        exit_code = run_step.complete_step(
            make_args(
                workspace["state_path"],
                "专家分析完成",
                stdin_content=exp_blocks,
                ticket=ticket,
            )
        )

        assert exit_code != 0
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 9

    def test_complete_step_rejects_artifact_drift_after_prepare(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        mark_card_and_prepare(workspace)
        ticket = vs.load_state(workspace["state_path"])["pending_ticket"]["value"]

        ctx_path = workspace["working_draft_path"] / "ctx.json"
        ctx_path.write_text(ctx_path.read_text(encoding="utf-8") + "\n外部篡改\n", encoding="utf-8")

        exp_blocks = make_wd_exp_payload()

        exit_code = run_step.complete_step(
            make_args(
                workspace["state_path"],
                "专家分析完成",
                stdin_content=exp_blocks,
                ticket=ticket,
            )
        )

        assert exit_code != 0
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 9

    def test_complete_step_clears_pending_ticket_after_success(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        mark_card_and_prepare(workspace)
        ticket = vs.load_state(workspace["state_path"])["pending_ticket"]["value"]

        exp_blocks = make_wd_exp_payload()

        exit_code = run_step.complete_step(
            make_args(
                workspace["state_path"],
                "专家分析完成",
                stdin_content=exp_blocks,
                ticket=ticket,
            )
        )

        assert exit_code == 0
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["pending_ticket"] == {}

    def test_complete_creative_step_batch_step9_is_atomic_on_success(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        state["checkpoints"]["step-5"]["selected_members"] = [
            "systems_architect",
            "domain_expert",
        ]
        state["checkpoints"]["step-5"]["selected_member_count"] = 2
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step9_draft(workspace)

        stdin_content = make_wd_exp_payload_for_members([
            "systems_architect",
            "domain_expert",
        ])

        code, message = run_step.complete_creative_step(
            workspace["state_path"],
            "专家分析完成",
            9,
            stdin_content,
        )

        assert code == 0, message
        new_state = vs.load_state(workspace["state_path"])
        slot1 = json.loads(
            (workspace["working_draft_path"] / "slots" / "SLOT-01" / "experts" / "systems_architect.json").read_text(encoding="utf-8")
        )
        slot2 = json.loads(
            (workspace["working_draft_path"] / "slots" / "SLOT-02" / "experts" / "systems_architect.json").read_text(encoding="utf-8")
        )
        assert new_state["current_step"] == 10
        assert new_state["gate_receipt"]["step"] == 10
        assert new_state["checkpoints"]["step-9"]["wd_exp_count"] == 4
        assert slot1["decision_type"] == "改造"
        assert slot2["decision_type"] == "改造"

    def test_complete_step_9_generates_summary_when_missing(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        ticket = prepare_and_get_ticket(workspace)

        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    None,
                    stdin_content=make_wd_exp_payload(),
                    ticket=ticket,
                )
            )
            == 0
        )

        refreshed = vs.load_state(workspace["state_path"])
        assert (
            refreshed["checkpoints"]["step-9"]["summary"]
            == "完成；写入专家分析；slots=4；gate: step-10 ready"
        )

    def test_complete_creative_step_batch_step9_writes_via_staging_dir(
        self,
        workspace: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        module = run_step.load_upsert_draft_block_module()
        original_write = module.write_working_draft_file
        seen_working_dirs: list[Path] = []

        def wrapped_write(
            working_dir: Path,
            block_name: str,
            content: str,
            slots: list[dict[str, str]],
        ) -> None:
            seen_working_dirs.append(Path(working_dir))
            original_write(working_dir, block_name, content, slots)

        monkeypatch.setattr(module, "write_working_draft_file", wrapped_write)
        monkeypatch.setattr(run_step, "load_upsert_draft_block_module", lambda: module)

        stdin_content = make_wd_exp_payload()

        code, message = run_step.complete_creative_step(
            workspace["state_path"],
            "专家分析完成",
            9,
            stdin_content,
        )

        assert code == 0, message
        assert seen_working_dirs
        assert all(path != workspace["working_draft_path"] for path in seen_working_dirs)
        promoted = json.loads(
            (workspace["working_draft_path"] / "slots" / "SLOT-01" / "experts" / "systems_architect.json").read_text(encoding="utf-8")
        )
        assert promoted["decision_type"] == "改造"

    def test_complete_creative_step_batch_step9_rolls_back_on_partial_failure(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        before_state = copy.deepcopy(state)
        write_state(workspace, state)
        write_directory_draft(workspace, with_experts=True)
        before_draft = (
            workspace["working_draft_path"] / "slots" / "SLOT-01" / "experts" / "systems_architect.json"
        ).read_text(encoding="utf-8")

        stdin_content = json.dumps(
            [
                {
                    "slot": "1.1 需求概述",
                    "member": "systems_architect",
                    "decision_type": "改造",
                    "rationale": "复用现有骨架并补齐专家分析。",
                    "evidence_refs": ["CTX-01"],
                    "open_questions": ["无"],
                },
                {
                    "slot": "2.2 风险与验证",
                    "member": "systems_architect",
                    "decision_type": "新建",
                    "rationale": "",
                    "evidence_refs": "CTX-01",
                    "open_questions": ["无"],
                },
            ],
            ensure_ascii=False,
            indent=2,
        )

        code, message = run_step.complete_creative_step(
                workspace["state_path"],
                "专家分析完成",
                9,
                stdin_content,
            )

        assert code != 0
        assert "WD-EXP evidence_refs/open_questions 必须是数组" in message
        assert (
            workspace["working_draft_path"] / "slots" / "SLOT-01" / "experts" / "systems_architect.json"
        ).read_text(encoding="utf-8") == before_draft
        assert vs.load_state(workspace["state_path"]) == before_state

    def test_step9_rejects_invalid_structured_payload_shape(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        stdin_content = json.dumps(
            {
                "slot": "2.1 方案设计",
                "decision_type": "改造",
            },
            ensure_ascii=False,
        )

        code, message = run_step.complete_creative_step(
            workspace["state_path"],
            "专家分析完成",
            9,
            stdin_content,
        )

        assert code != 0
        assert "步骤 9 结构化内容 必须是 JSON 数组" in message

    def test_step9_renderer_validation_returns_structured_error_not_system_exit(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step9_state(workspace)
        write_state(workspace, state)
        write_step9_draft(workspace)
        stdin_content = json.dumps(
            [
                {
                    "slot": "2.1 方案设计",
                    "decision_type": "改造",
                    "rationale": "x",
                    "evidence_refs": "NOT_AN_ARRAY",
                    "open_questions": ["无"],
                }
            ],
            ensure_ascii=False,
        )

        code, message = run_step.complete_creative_step(
            workspace["state_path"],
            "专家分析完成",
            9,
            stdin_content,
        )

        assert code != 0
        assert "WD-EXP evidence_refs/open_questions 必须是数组" in message

    def test_step7_renderer_validation_returns_structured_error_not_system_exit(
        self, workspace: dict[str, Path]
    ) -> None:
        assert (
            run_step.complete_step(
                make_args(workspace["state_path"], "定题完成", slug="sample-solution")
            )
            == 0
        )
        assert run_step.complete_step(make_args(workspace["state_path"], "前置文件检查通过")) == 0
        assert run_step.complete_step(make_args(workspace["state_path"], "模板读取完成")) == 0
        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "类型判定完成",
                    solution_type="新功能方案",
                )
            )
            == 0
        )
        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "成员选定完成",
                    member=["SYSTEMS_ARCHITECT"],
                )
            )
            == 0
        )
        assert run_step.complete_step(make_args(workspace["state_path"], "repowiki 检查完成")) == 0

        run_step.advance_step(workspace["state_path"])
        step7_ticket = prepare_and_get_ticket(workspace)

        bad_payload = json.dumps(
            [{"id": "CTX-01", "source": "a.py", "conclusion": "test", "applicable_slots": "NOT_AN_ARRAY", "confidence": "已验证"}],
            ensure_ascii=False,
        )

        code, message = run_step.complete_creative_step(
            workspace["state_path"],
            "WD-CTX 完成",
            7,
            bad_payload,
        )

        assert code != 0
        assert "步骤 7 验证失败" in message
        assert "wd_ctx_structure_invalid" in message

    def test_step10_renderer_validation_returns_structured_error_not_system_exit(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step11_state(workspace)
        state["current_step"] = 10
        state["completed_steps"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        state["gate_receipt"] = {
            "step": 10,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step11_draft(workspace)
        ticket = prepare_and_get_ticket(workspace)

        bad_payload = json.dumps(
            [
                {
                    "slot": "2.1 方案设计",
                    "target_capability": "收敛",
                    "comparisons": [{"path": "改造", "feasibility": "✅", "evidence": "CTX-01", "reason": "推荐"}],
                    "selected_path": "改造",
                    "selected_writeup": "补齐",
                    "evidence_refs": "NOT_AN_ARRAY",
                }
            ],
            ensure_ascii=False,
        )

        code = run_step.complete_step(
            make_args(
                workspace["state_path"],
                "WD-SYN 完成",
                stdin_content=bad_payload,
                ticket=ticket,
            )
        )

        assert code != 0

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

    def test_complete_step_11_failure_preserves_draft_and_guides_repair(
        self,
        workspace: dict[str, Path],
    ) -> None:
        state = make_step11_state(workspace)
        write_state(workspace, state)
        write_step11_draft(workspace)
        bad_truth = workspace["working_draft_path"] / "slots" / "SLOT-01" / "decision.json"
        bad_truth.write_text(
            json.dumps(
                {
                    "slot": "1.1 需求概述",
                    "selected_writeup": "",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        code, message = run_step.complete_step_11(workspace["state_path"], "成稿完成")

        assert code != 0
        assert "步骤 11 验证失败" in message
        assert "working draft 已保留" in message
        assert "不要手动编写最终文档" in message
        assert bad_truth.exists()
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 11
        assert new_state["checkpoints"]["step-11"]["rendered_via_script"] is False

    def test_complete_step_11_rejects_collapsed_state_slots_and_preserves_draft(
        self,
        workspace: dict[str, Path],
    ) -> None:
        state = make_step11_state(workspace)
        state["slots"] = [
            {"slot": "SLOT-01", "title": "一、需求背景与综合评估"},
            {"slot": "SLOT-02", "title": "二、总体设计"},
        ]
        state["checkpoints"]["step-3"]["slot_count"] = 2
        state["checkpoints"]["step-8"]["task_slot_count"] = 2
        state["checkpoints"]["step-9"]["wd_exp_count"] = 2
        state["checkpoints"]["step-10"]["syn_slot_count"] = 2
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        write_step11_draft(workspace)

        code, message = run_step.complete_step_11(workspace["state_path"], "成稿完成")

        assert code != 0
        assert "步骤 11 验证失败" in message
        assert "working draft 已保留" in message
        assert "不要手动编写最终文档" in message
        assert workspace["working_draft_path"].exists()
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 11
        assert new_state["checkpoints"]["step-11"]["rendered_via_script"] is False

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
            "render_receipt": {
                "mode": "decision_truth",
                "slots": [
                    {
                        "slot": "SLOT-01",
                        "decision_artifact": "WD-SYN-SLOT-01",
                    }
                ],
            },
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

    def test_complete_step_12_generates_summary_when_missing(
        self,
        workspace: dict[str, Path],
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
            "render_receipt": {
                "mode": "decision_truth",
                "slots": [
                    {
                        "slot": "SLOT-01",
                        "decision_artifact": "WD-SYN-SLOT-01",
                    }
                ],
            },
        }
        state["checkpoints"]["step-12"] = {
            "summary": "",
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

        code, message = run_step.complete_step_12(workspace["state_path"], None)

        assert code == 0, message
        assert not workspace["state_path"].exists()
        assert not workspace["working_draft_path"].exists()

    def test_complete_step_12_preserves_archive_receipt_before_cleanup(
        self,
        workspace: dict[str, Path],
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
            "render_receipt": {
                "mode": "decision_truth",
                "slots": [
                    {
                        "slot": "SLOT-01",
                        "decision_artifact": "WD-SYN-SLOT-01",
                    }
                ],
            },
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

        code, message = run_step.complete_step_12(workspace["state_path"], "清理完成")

        archive_receipt = workspace["working_draft_path"].parent / "archive" / "cleanup-receipt.json"
        assert code == 0, message
        assert not workspace["state_path"].exists()
        assert not workspace["working_draft_path"].exists()
        assert archive_receipt.exists()
        archived = json.loads(archive_receipt.read_text(encoding="utf-8"))
        assert archived["step_12_summary"] == "清理完成"
        assert archived["deleted"] == {"working_draft": True, "state_file": True}
        assert archived["render_receipt"]["mode"] == "decision_truth"

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
        assert new_state["checkpoints"]["step-5"]["selected_members"] == [
            "SYSTEMS_ARCHITECT",
            "DOMAIN_EXPERT",
        ]

    def test_complete_step_4_accepts_business_payload_from_stdin(
        self,
        workspace: dict[str, Path],
    ) -> None:
        state = make_step4_state(workspace)
        write_state(workspace, state)
        ticket = prepare_and_get_ticket(workspace)

        exit_code = run_step.complete_step(
            make_args(
                workspace["state_path"],
                "类型判定完成",
                stdin_content='{"solution_type": "新功能方案"}',
                ticket=ticket,
            )
        )

        assert exit_code == 0
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 5
        assert new_state["checkpoints"]["step-4"]["solution_type"] == "新功能方案"

    def test_complete_step_5_accepts_business_payload_from_stdin(
        self,
        workspace: dict[str, Path],
    ) -> None:
        state = make_step5_state(workspace)
        write_state(workspace, state)
        ticket = prepare_and_get_ticket(workspace)

        exit_code = run_step.complete_step(
            make_args(
                workspace["state_path"],
                "成员选定完成",
                stdin_content='{"selected_members": ["SYSTEMS_ARCHITECT", "DOMAIN_EXPERT"]}',
                ticket=ticket,
            )
        )

        assert exit_code == 0
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 6
        assert new_state["checkpoints"]["step-5"]["selected_members"] == [
            "SYSTEMS_ARCHITECT",
            "DOMAIN_EXPERT",
        ]

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

    def test_complete_step_3_uses_in_process_template_snapshot(
        self, workspace: dict[str, Path], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        state = make_step3_state(workspace)
        write_state(workspace, state)

        def forbid_subprocess(*_args, **_kwargs):
            raise AssertionError("complete_step_3 should not use subprocess")

        monkeypatch.setattr(run_step, "run_script", forbid_subprocess)

        code, message = run_step.complete_step_3(
            workspace["state_path"], "模板读取完成"
        )

        assert code == 0, message
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 4
        assert new_state["checkpoints"]["step-3"]["template_loaded"] is True
        assert (workspace["working_draft_path"].parent).is_dir()
        assert (workspace["working_draft_path"] / "slots").is_dir()
        assert not (workspace["working_draft_path"] / "ctx.md").exists()
        assert not (workspace["working_draft_path"] / "slots" / "SLOT-01" / "experts.md").exists()
        assert (
            new_state["working_draft_path"]
            == ".architecture/.state/create-technical-solution/sample-solution/draft"
        )

    def test_complete_step_3_ignores_tampered_external_working_draft_path(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_step3_state(workspace)
        external_draft_path = workspace["repo"].parent / "tampered" / "sample-solution"
        state["working_draft_path"] = str(external_draft_path.resolve())
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)

        code, message = run_step.complete_step_3(
            workspace["state_path"], "模板读取完成"
        )

        assert code == 0, message
        new_state = vs.load_state(workspace["state_path"])
        assert new_state["current_step"] == 4
        assert (
            new_state["working_draft_path"]
            == ".architecture/.state/create-technical-solution/sample-solution/draft"
        )
        assert (workspace["working_draft_path"].parent).is_dir()
        assert not external_draft_path.exists()

    def test_print_status_shows_public_repair_hint_and_next_command(
        self, workspace: dict[str, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        state = make_step9_state(workspace)
        state["working_draft_path"] = (
            ".architecture/technical-solutions/working-drafts/sample-solution"
        )
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)

        exit_code = run_step.print_status(workspace["state_path"])

        assert exit_code == 0
        output = capsys.readouterr().out
        assert (
            "working_draft_path 必须固定为 .architecture/.state/create-technical-solution/sample-solution/draft"
            in output
        )
        assert (
            "回到步骤 3，重新生成 .architecture/.state/create-technical-solution/[slug]/draft/ 目录"
            in output
        )
        assert '"slot": "2.1 方案设计"' in output
        assert '"decision_type": "改造"' in output

    def test_format_step_failure_surfaces_typed_recovery_action(self) -> None:
        raw_output = json.dumps(
            {
                "repair_plan": [
                    {
                        "step": 7,
                        "action_type": "rebuild_from_step_7",
                        "script_command": "python run-step.py --state x --advance",
                    }
                ]
            },
            ensure_ascii=False,
        )

        message = run_step.format_step_failure(
            step=7,
            prefix="验证失败",
            raw_output=raw_output,
        )

        assert "恢复动作：" in message
        assert "- rebuild_from_step_7" in message

    def test_print_status_missing_state_uses_advance_instead_of_prepare(
        self, workspace: dict[str, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = run_step.print_status(workspace["state_path"])

        assert exit_code == 0
        output = capsys.readouterr().out
        assert "状态文件不存在或为空。" in output
        assert f"{protocol_runtime.run_step_base_command(workspace['state_path'])} --advance" in output
        assert "--prepare --slug" not in output

    def test_light_sample_flow_end_to_end(self, workspace: dict[str, Path]) -> None:
        exp_blocks = make_wd_exp_payload()
        syn_blocks = make_wd_syn_payload()

        assert (
            run_step.complete_step(
                make_args(workspace["state_path"], "定题完成", slug="sample-solution")
            )
            == 0
        )
        assert (
            run_step.complete_step(
                make_args(workspace["state_path"], "前置文件检查通过")
            )
            == 0
        )
        assert (
            run_step.complete_step(make_args(workspace["state_path"], "模板读取完成"))
            == 0
        )
        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "类型判定完成",
                    solution_type="新功能方案",
                )
            )
            == 0
        )
        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "成员选定完成",
                    member=["SYSTEMS_ARCHITECT"],
                )
            )
            == 0
        )
        assert (
            run_step.complete_step(
                make_args(workspace["state_path"], "repowiki 检查完成")
            )
            == 0
        )
        step7_ticket = prepare_and_get_ticket(workspace)
        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "WD-CTX 完成",
                    stdin_content=WD_CTX_PAYLOAD,
                    ticket=step7_ticket,
                )
            )
            == 0
        )
        step8_ticket = prepare_and_get_ticket(workspace)
        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "WD-TASK 完成",
                    stdin_content=WD_TASK_PAYLOAD,
                    ticket=step8_ticket,
                )
            )
            == 0
        )

        state_after_task = vs.load_state(workspace["state_path"])
        assert state_after_task["current_step"] == 9

        step9_ticket = prepare_and_get_ticket(workspace)
        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "专家分析完成",
                    stdin_content=exp_blocks,
                    ticket=step9_ticket,
                )
            )
            == 0
        )
        step10_ticket = prepare_and_get_ticket(workspace)
        assert (
            run_step.complete_step(
                make_args(
                    workspace["state_path"],
                    "WD-SYN 完成",
                    stdin_content=syn_blocks,
                    ticket=step10_ticket,
                )
            )
            == 0
        )

        state_after_syn = vs.load_state(workspace["state_path"])
        assert state_after_syn["current_step"] == 11

        step11_ticket = prepare_and_get_ticket(workspace)
        assert (
            run_step.complete_step(
                make_args(workspace["state_path"], "成稿完成", ticket=step11_ticket)
            )
            == 0
        )
        step12_ticket = prepare_and_get_ticket(workspace)
        assert (
            run_step.complete_step(
                make_args(workspace["state_path"], "清理完成", ticket=step12_ticket)
            )
            == 0
        )

        assert not workspace["state_path"].exists()
        assert not workspace["working_draft_path"].exists()
        final_document = (
            workspace["arch"] / "technical-solutions" / "sample-solution.md"
        )
        assert final_document.exists()
        assert "### 2.1 方案设计" in final_document.read_text(encoding="utf-8")
