from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


skill_root = Path(__file__).parent.parent.parent / "skills" / "create-technical-solution"
scripts_root = skill_root / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), scripts_root / f"{name}.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


vs = load_script("validate-state")


TEMPLATE = """# 技术方案文档

## 一、背景

### 1.1 需求概述

### 1.2 核心目标

## 二、设计

### 2.1 方案设计

### 2.2 风险与验证
"""


def make_wd_syn_block(title: str) -> str:
    return "\n".join(
        [
            f"### 槽位：{title}",
            "#### 目标能力",
            f"- 收敛 {title} 的最终写法",
            "#### 候选方案对比",
            "| 路径 | 可行性 | 关键证据 | 选择理由 |",
            "|------|--------|----------|----------|",
            f"| 复用 | ☐ | CTX-01 | {title} 不能直接复用现有产物 |",
            f"| 改造 | ☑ | CTX-01 | {title} 适合在现有资产上扩展 |",
            f"| 新建 | ☐ | CTX-01 | {title} 新建成本高于收益 |",
            "#### 选定路径",
            "- 路径: 改造",
            f"- 选定写法: 在 {title} 槽位补齐针对性的技术结论",
            "- 关键证据引用: CTX-01",
            f"- 建议落位槽位: {title}",
            "- 模板承载缺口: 无",
            "- 未决问题: 无",
        ]
    )


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
    template_path.write_text(TEMPLATE, encoding="utf-8")
    members_path = arch / "members.yml"
    members_path.write_text("members:\n  - id: systems_architect\n", encoding="utf-8")
    principles_path = arch / "principles.md"
    principles_path.write_text("# principles\n", encoding="utf-8")

    return {
        "repo": repo,
        "state_dir": state_dir,
        "solution_root": solution_root,
        "template_path": template_path,
        "members_path": members_path,
        "principles_path": principles_path,
        "state_path": state_dir / "sample-solution.yaml",
        "working_draft_path": state_dir / "sample-solution",
        "final_document_path": solution_root / "sample-solution.md",
    }


def make_state(workspace: dict[str, Path], **overrides) -> dict:
    headings = vs.extract_slot_headings(workspace["template_path"].read_text(encoding="utf-8"))
    syn_artifacts = [f"WD-SYN-{item['slot']}" for item in headings]
    state = {
        "current_step": 10,
        "completed_steps": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "skipped_steps": [],
        "pending_questions": [],
        "required_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP-*"] + syn_artifacts,
        "produced_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP-*"] + syn_artifacts,
        "gate_receipt": {
            "step": 10,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        },
        "solution_root": ".architecture/technical-solutions",
        "template_path": ".architecture/templates/technical-solution-template.md",
        "members_path": ".architecture/members.yml",
        "principles_path": ".architecture/principles.md",
        "repowiki_path": ".qoder/repowiki",
        "working_draft_path": ".architecture/.state/create-technical-solution/sample-solution",
        "final_document_path": ".architecture/technical-solutions/sample-solution.md",
        "checkpoints": {
            "step-1": {"summary": "完成；slug=sample-solution；paths=1；gate: step-2 ready", "slug": "sample-solution", "scope_ready": True},
            "step-2": {"summary": "完成；检查前置文件；files=3；gate: step-3 ready", "prerequisites_checked": True},
            "step-3": {"summary": "完成；写入 draft 骨架；slots=4；gate: step-4 ready", "template_loaded": True, "template_fingerprint": "", "slot_count": 4},
            "step-4": {"summary": "完成；方案类型=现有资产改造；gate: step-5 ready", "solution_type": "现有资产改造"},
            "step-5": {"summary": "完成；成员已选择；count=1；gate: step-6 ready", "members_checked": True, "selected_members": ["systems_architect"], "selected_member_count": 1},
            "step-6": {"summary": "完成；repowiki 不存在；sources=0；gate: step-7 ready", "repowiki_checked": True, "repowiki_exists": False, "repowiki_source_count": 0},
            "step-7": {"summary": "完成；写入 WD-CTX；CTX=1；gate: step-8 ready", "wd_ctx_written": True, "ctx_count": 1},
            "step-8": {"summary": "完成；写入 WD-TASK；slots=4；gate: step-9 ready", "wd_task_written": True, "task_slot_count": 4},
            "step-9": {"summary": "完成；写入 WD-EXP-*；members=1；gate: step-10 ready", "wd_exp_written": True, "wd_exp_count": 4},
            "step-10": {"summary": "完成；写入 WD-SYN-SLOT-*；slots=4；gate: step-11 ready", "wd_syn_written": True, "syn_slot_count": 4},
            "step-11": {"summary": "等待成稿", "final_document_written": False, "absorbed_slot_count": 0, "rendered_via_script": False},
            "step-12": {"summary": "等待校验", "validator_passed": False, "working_draft_deleted": False, "state_file_deleted": False},
        },
        "can_enter_step_8": True,
        "can_enter_step_9": True,
        "can_enter_step_10": True,
        "can_enter_step_11": True,
        "can_enter_step_12": False,
        "absorption_check_passed": False,
        "cleanup_allowed": False,
        "slots": [{"slot": item["slot"], "title": item["title"]} for item in headings],
    }
    state["checkpoints"]["step-3"]["template_fingerprint"] = vs.compute_template_fingerprint(
        workspace["template_path"].read_text(encoding="utf-8"),
        headings,
    )
    state.update(overrides)
    state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
    return state


def write_state(workspace: dict[str, Path], state: dict) -> None:
    workspace["state_path"].write_text(vs.yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_good_draft(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "ctx.md").write_text(
        "\n".join([
            "### CTX-01",
            "来源: code",
            "结论或约束: existing implementation",
            "适用槽位: 1.1 需求概述、1.2 核心目标、2.1 方案设计、2.2 风险与验证",
            "可信度或缺口: 已核实",
        ]),
        encoding="utf-8",
    )
    (path / "task.md").write_text(
        "\n\n".join([
            "\n".join([
                "### 1.1 需求概述",
                "- 槽位标识: SLOT-01",
                "- 必须消费的共享上下文: CTX-01",
                "- 参与专家: systems_architect",
                "- 每位专家必答问题:",
                "  - <围绕当前槽位补齐复用 / 改造 / 新建比较>",
                "- 建议落位槽位: 1.1 需求概述",
                "- 落位表达要求: <只写当前模板槽位需要的最小闭环>",
                "- 缺口或阻塞项: 无",
            ]),
            "\n".join([
                "### 1.2 核心目标",
                "- 槽位标识: SLOT-02",
                "- 必须消费的共享上下文: CTX-01",
                "- 参与专家: systems_architect",
                "- 每位专家必答问题:",
                "  - <围绕当前槽位补齐复用 / 改造 / 新建比较>",
                "- 建议落位槽位: 1.2 核心目标",
                "- 落位表达要求: <只写当前模板槽位需要的最小闭环>",
                "- 缺口或阻塞项: 无",
            ]),
            "\n".join([
                "### 2.1 方案设计",
                "- 槽位标识: SLOT-03",
                "- 必须消费的共享上下文: CTX-01",
                "- 参与专家: systems_architect",
                "- 每位专家必答问题:",
                "  - <围绕当前槽位补齐复用 / 改造 / 新建比较>",
                "- 建议落位槽位: 2.1 方案设计",
                "- 落位表达要求: <只写当前模板槽位需要的最小闭环>",
                "- 缺口或阻塞项: 无",
            ]),
            "\n".join([
                "### 2.2 风险与验证",
                "- 槽位标识: SLOT-04",
                "- 必须消费的共享上下文: CTX-01",
                "- 参与专家: systems_architect",
                "- 每位专家必答问题:",
                "  - <围绕当前槽位补齐复用 / 改造 / 新建比较>",
                "- 建议落位槽位: 2.2 风险与验证",
                "- 落位表达要求: <只写当前模板槽位需要的最小闭环>",
                "- 缺口或阻塞项: 无",
            ]),
        ]),
        encoding="utf-8",
    )
    for index, title in enumerate(["1.1 需求概述", "1.2 核心目标", "2.1 方案设计", "2.2 风险与验证"], start=1):
        slot = path / "slots" / f"SLOT-{index:02d}"
        slot.mkdir(parents=True, exist_ok=True)
        (slot / "experts.md").write_text(
            "\n".join([
                "### 专家：systems_architect",
                "- 决策类型: 改造",
                "- 核心理由: 绑定 CTX-01，说明为什么选这条路径",
                "- 关键证据引用: CTX-01",
                "- 未决点: 无",
            ]),
            encoding="utf-8",
        )
        (slot / "synthesis.md").write_text(make_wd_syn_block(title), encoding="utf-8")


def assert_good_draft(path: Path) -> None:
    assert path.is_dir()
    assert (path / "ctx.md").exists()
    assert (path / "task.md").exists()
    assert (path / "slots" / "SLOT-01" / "experts.md").exists()
    assert (path / "slots" / "SLOT-04" / "synthesis.md").exists()


def write_incomplete_draft(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "ctx.md").write_text("### CTX-01\n来源: code\n", encoding="utf-8")


def load_doctor():
    return load_script("runtime_doctor")


def test_dry_run_reports_legacy_working_draft_migration_without_mutation(workspace: dict[str, Path]) -> None:
    doctor = load_doctor()
    legacy_path = workspace["repo"] / ".architecture" / "technical-solutions" / "working-drafts" / "sample-solution.working.md"
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    write_good_draft(legacy_path)
    state = make_state(workspace, working_draft_path=".architecture/technical-solutions/working-drafts/sample-solution.working.md")
    write_state(workspace, state)

    exit_code, payload = doctor.run_doctor(workspace["state_path"], output_format="json")

    assert exit_code == 2
    assert any(fix["code"] == "legacy_working_draft_migration" and fix["applied"] is False for fix in payload["safe_fixes"])
    refreshed = vs.load_state(workspace["state_path"])
    assert refreshed["working_draft_path"] == ".architecture/technical-solutions/working-drafts/sample-solution.working.md"
    assert legacy_path.exists()
    assert not workspace["working_draft_path"].exists()


def test_apply_mode_migrates_legacy_working_draft_to_canonical_state_dir(workspace: dict[str, Path]) -> None:
    doctor = load_doctor()
    legacy_path = workspace["repo"] / ".architecture" / "technical-solutions" / "working-drafts" / "sample-solution.working.md"
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    write_good_draft(legacy_path)
    state = make_state(workspace, working_draft_path=".architecture/technical-solutions/working-drafts/sample-solution.working.md")
    write_state(workspace, state)

    exit_code, payload = doctor.run_doctor(workspace["state_path"], apply_safe_fixes=True, output_format="json")

    assert exit_code == 0
    assert payload["passed"] is True
    refreshed = vs.load_state(workspace["state_path"])
    assert refreshed["working_draft_path"] == ".architecture/.state/create-technical-solution/sample-solution"
    assert_good_draft(workspace["working_draft_path"])
    assert not legacy_path.exists()


def test_apply_mode_rewrites_legacy_state_path_without_clobbering_existing_canonical_draft(workspace: dict[str, Path]) -> None:
    doctor = load_doctor()
    legacy_path = workspace["repo"] / ".architecture" / "technical-solutions" / "working-drafts" / "sample-solution.working.md"
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.write_text("legacy draft content\n", encoding="utf-8")
    write_good_draft(workspace["working_draft_path"])
    state = make_state(workspace, working_draft_path=".architecture/technical-solutions/working-drafts/sample-solution.working.md")
    write_state(workspace, state)

    exit_code, payload = doctor.run_doctor(workspace["state_path"], apply_safe_fixes=True, output_format="json")

    assert exit_code == 0
    assert payload["passed"] is True
    refreshed = vs.load_state(workspace["state_path"])
    assert refreshed["working_draft_path"] == ".architecture/.state/create-technical-solution/sample-solution"
    assert_good_draft(workspace["working_draft_path"])
    assert legacy_path.read_text(encoding="utf-8") == "legacy draft content\n"


def test_apply_mode_creates_missing_canonical_parent_directories_only(workspace: dict[str, Path]) -> None:
    doctor = load_doctor()
    write_good_draft(workspace["working_draft_path"])
    state = make_state(workspace)
    write_state(workspace, state)
    for path in [workspace["solution_root"]]:
        path.rmdir()

    exit_code, payload = doctor.run_doctor(workspace["state_path"], apply_safe_fixes=True, output_format="json")

    assert exit_code == 0
    assert payload["passed"] is True
    assert workspace["solution_root"].exists()
    assert not workspace["final_document_path"].exists()
    assert_good_draft(workspace["working_draft_path"])


def test_healthy_state_with_valid_receipt_stays_no_op(workspace: dict[str, Path]) -> None:
    doctor = load_doctor()
    write_good_draft(workspace["working_draft_path"])
    state = make_state(workspace)
    write_state(workspace, state)

    before = vs.load_state(workspace["state_path"])
    exit_code, payload = doctor.run_doctor(workspace["state_path"], apply_safe_fixes=True, output_format="json")
    after = vs.load_state(workspace["state_path"])

    assert exit_code == 0
    assert payload["passed"] is True
    assert payload["mutated"] is False
    assert not any(fix["code"] == "refresh_gate_receipt" for fix in payload["safe_fixes"])
    assert after == before


def test_directory_only_mutation_reports_mutated_true_even_when_semantic_issues_remain(workspace: dict[str, Path]) -> None:
    doctor = load_doctor()
    write_incomplete_draft(workspace["working_draft_path"])
    state = make_state(workspace)
    write_state(workspace, state)
    workspace["solution_root"].rmdir()

    exit_code, payload = doctor.run_doctor(workspace["state_path"], apply_safe_fixes=True, output_format="json")

    assert exit_code == 2
    assert payload["passed"] is False
    assert payload["mutated"] is True
    assert workspace["solution_root"].exists()
    assert any(issue["code"] == "draft_block_overwritten" for issue in payload["issues"])
    assert any("WD-TASK" in issue.get("missing_artifacts", []) for issue in payload["issues"])


def test_apply_mode_refreshes_gate_receipt_when_receipt_is_only_problem(workspace: dict[str, Path]) -> None:
    doctor = load_doctor()
    write_good_draft(workspace["working_draft_path"])
    state = make_state(workspace)
    state["gate_receipt"] = {
        "step": 10,
        "state_fingerprint": vs.compute_state_fingerprint(state),
        "validated_at": "",
    }
    write_state(workspace, state)

    exit_code, payload = doctor.run_doctor(workspace["state_path"], apply_safe_fixes=True, output_format="json")

    assert exit_code == 0
    assert payload["passed"] is True
    refreshed = vs.load_state(workspace["state_path"])
    assert refreshed["gate_receipt"]["step"] == 10
    assert refreshed["gate_receipt"]["validated_at"]
    assert refreshed["gate_receipt"]["state_fingerprint"] == vs.compute_state_fingerprint(refreshed)


def test_apply_mode_does_not_refresh_receipt_when_semantic_issues_remain(workspace: dict[str, Path]) -> None:
    doctor = load_doctor()
    write_incomplete_draft(workspace["working_draft_path"])
    state = make_state(workspace)
    original_receipt = {
        "step": 10,
        "state_fingerprint": "stale-fingerprint",
        "validated_at": "2026-04-08T09:31:00",
    }
    state["gate_receipt"] = dict(original_receipt)
    write_state(workspace, state)

    exit_code, payload = doctor.run_doctor(workspace["state_path"], apply_safe_fixes=True, output_format="json")

    assert exit_code == 2
    assert payload["passed"] is False
    refreshed = vs.load_state(workspace["state_path"])
    assert refreshed["gate_receipt"] == original_receipt
    assert any(issue["code"] == "draft_block_overwritten" for issue in payload["issues"])
    assert any("WD-TASK" in issue.get("missing_artifacts", []) for issue in payload["issues"])


def test_doctor_returns_validator_issues_and_repair_plan(workspace: dict[str, Path]) -> None:
    doctor = load_doctor()
    write_incomplete_draft(workspace["working_draft_path"])
    state = make_state(workspace)
    state["gate_receipt"] = {
        "step": 10,
        "state_fingerprint": "stale-fingerprint",
        "validated_at": "2026-04-08T09:31:00",
    }
    write_state(workspace, state)

    exit_code, payload = doctor.run_doctor(workspace["state_path"], output_format="json")

    assert exit_code == 2
    assert any(issue["code"] == "invalid_gate_receipt" for issue in payload["issues"])
    assert any(issue["code"] == "draft_block_overwritten" for issue in payload["issues"])
    assert any("WD-TASK" in issue.get("missing_artifacts", []) for issue in payload["issues"])
    assert any(item["step"] == 10 and "run-step.py" in item["script_command"] for item in payload["repair_plan"])
