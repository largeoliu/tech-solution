# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "pytest>=8.0"]
# ///
"""create-technical-solution validator regression tests."""

from __future__ import annotations

import importlib.util
import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

scripts_path = Path(__file__).parent.parent.parent / "skills" / "create-technical-solution" / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), scripts_path / f"{name}.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


vs = load_script("validate-state")
fc = load_script("finalize-cleanup")
iss = load_script("initialize-state")
rfd = load_script("render-final-document")
udb = load_script("upsert-draft-block")
rs = load_script("runtime_snapshot")
protocol_runtime = load_script("protocol_runtime")


TEMPLATE = """# 技术方案文档

## 一、背景

### 1.1 需求概述

### 1.2 核心目标

## 二、设计

### 2.1 方案设计

### 2.2 风险与验证
"""


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
        "arch": arch,
        "state_dir": state_dir,
        "template_path": template_path,
        "members_path": members_path,
        "principles_path": principles_path,
        "solution_root": solution_root,
        "working_draft_path": state_dir / "sample-solution",
        "final_document_path": solution_root / "sample-solution.md",
        "state_path": state_dir / "sample-solution.yaml",
        "content_file": repo / "final-content.md",
    }


def make_state(workspace: dict[str, Path], **overrides) -> dict:
    headings = vs.extract_slot_headings(workspace["template_path"].read_text(encoding="utf-8"))
    syn_artifacts = [f"WD-SYN-{item['slot']}" for item in headings]
    state = {
        "current_step": 10,
        "completed_steps": [1, 2, 3, 4, 5, 6, 7, 8],
        "skipped_steps": [],
        "pending_questions": [],
        "artifact_registry": {},
        "required_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP-*"] + syn_artifacts,
        "produced_artifacts": ["WD-CTX", "WD-TASK"] + syn_artifacts,
        "gate_receipt": {"step": 10, "state_fingerprint": "", "validated_at": "2026-04-08T09:31:00"},
        "solution_root": ".architecture/technical-solutions",
        "template_path": ".architecture/templates/technical-solution-template.md",
        "members_path": ".architecture/members.yml",
        "principles_path": ".architecture/principles.md",
        "repowiki_path": ".qoder/repowiki",
        "working_draft_path": ".architecture/.state/create-technical-solution/sample-solution",
        "final_document_path": ".architecture/technical-solutions/sample-solution.md",
        "slots": [{"slot": item["slot"], "title": item["title"]} for item in headings],
        "checkpoints": {
            "step-1": {"summary": "完成；slug=sample-solution；paths=1；gate: step-2 ready", "slug": "sample-solution", "scope_ready": True},
            "step-2": {"summary": "完成；检查前置文件；files=3；gate: step-3 ready", "prerequisites_checked": True},
            "step-3": {"summary": "完成；写入 draft 骨架；slots=4；gate: step-4 ready", "template_loaded": True, "template_fingerprint": "", "slot_count": 4},
            "step-4": {"summary": "完成；类型已判定", "solution_type": "现有资产改造"},
            "step-5": {"summary": "完成；成员已选择；count=1；gate: step-6 ready", "members_checked": True, "selected_members": ["systems_architect"], "selected_member_count": 1},
            "step-6": {"summary": "完成；repowiki 不存在；sources=0；gate: step-7 ready", "repowiki_checked": True, "repowiki_exists": False, "repowiki_source_count": 0},
            "step-7": {"summary": "完成；写入 WD-CTX；CTX=4；gate: step-8 ready", "wd_ctx_written": True, "ctx_count": 4},
            "step-8": {"summary": "完成；写入 WD-TASK；slots=4；gate: step-9 ready", "wd_task_written": True, "task_slot_count": 4},
            "step-9": {"summary": "进行中", "skipped": False, "reason": "", "wd_exp_count": 0},
            "step-10": {"summary": "完成；写入 WD-SYN-SLOT-*；slots=4；gate: step-11 ready", "wd_syn_written": True, "syn_slot_count": 4},
            "step-11": {"summary": "完成；final_document=1；absorbed_slots=4；gate: step-12 ready", "final_document_written": True, "absorbed_slot_count": 4, "rendered_via_script": True},
            "step-12": {"summary": "完成；validator_passed=true；deleted=0", "validator_passed": False, "working_draft_deleted": False, "state_file_deleted": False},
        },
        "can_enter_step_8": True,
        "can_enter_step_9": True,
        "can_enter_step_10": True,
        "can_enter_step_11": True,
        "can_enter_step_12": True,
        "absorption_check_passed": False,
        "cleanup_allowed": False,
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


def make_validator(state: dict, workspace: dict[str, Path]):
    write_state(workspace, state)
    return vs.GateValidator(state, workspace["state_path"])


def write_good_draft(workspace: dict[str, Path]) -> None:
    working_dir = workspace["working_draft_path"]
    working_dir.mkdir(parents=True, exist_ok=True)
    (working_dir / "ctx.md").write_text(
        """### CTX-01
来源: services/a.py, models/a.py
结论或约束: 需求概述已在现有流程中有入口。
适用槽位: 1.1 需求概述
可信度或缺口: 已验证

### CTX-02
来源: services/b.py, models/b.py
结论或约束: 核心目标依赖现有审核规则扩展。
适用槽位: 1.2 核心目标
可信度或缺口: 已验证

### CTX-03
来源: services/c.py, repositories/c.py
结论或约束: 方案设计需要复用既有配置结构。
适用槽位: 2.1 方案设计
可信度或缺口: 已验证

### CTX-04
来源: tests/d.py, docs/d.md
结论或约束: 风险与验证应覆盖回归与灰度检查。
适用槽位: 2.2 风险与验证
可信度或缺口: 已验证
""",
        encoding="utf-8",
    )
    (working_dir / "task.md").write_text(
        """### 1.1 需求概述
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
    for index, title in enumerate(("1.1 需求概述", "1.2 核心目标", "2.1 方案设计", "2.2 风险与验证"), start=1):
        slot_dir = working_dir / "slots" / f"SLOT-{index:02d}"
        slot_dir.mkdir(parents=True, exist_ok=True)
        (slot_dir / "experts.md").write_text(
            f"### 专家：systems_architect\n- 决策类型: 改造\n- 核心理由: 复用现有骨架并补齐 {title}。\n- 关键证据引用: CTX-01\n- 未决点: 无\n",
            encoding="utf-8",
        )
        (slot_dir / "synthesis.md").write_text(
            make_wd_syn_block(title),
            encoding="utf-8",
        )


def register_artifacts(state: dict, workspace: dict[str, Path]) -> None:
    registry = {}
    for artifact, relative in {
        "WD-CTX": ".architecture/.state/create-technical-solution/sample-solution/ctx.md",
        "WD-TASK": ".architecture/.state/create-technical-solution/sample-solution/task.md",
    }.items():
        path = workspace["repo"] / relative
        if path.exists():
            registry[artifact] = {
                "path": relative,
                "content_hash": vs.hashlib.sha256(path.read_bytes()).hexdigest(),
                "written_at": "2026-04-08T09:31:00",
                "writer": "run-step",
            }
    state["artifact_registry"] = registry


def make_wd_syn_block(title: str) -> str:
    return f"""### 槽位：{title}
#### 目标能力
- 收敛 {title} 的最终写法。
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- 路径: 改造
- 选定写法: 在 {title} 位置补齐内容。
- 关键证据引用: CTX-01
- 建议落位槽位: {title}
- 模板承载缺口: 无
- 未决问题: 无
"""


def slot_dir(workspace: dict[str, Path], index: int) -> Path:
    return workspace["working_draft_path"] / "slots" / f"SLOT-{index:02d}"


class TestStateBoundary:
    def test_validator_rejects_forbidden_state_fields(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, slug="sample-solution")
        state["evil_forbidden_field"] = "should not be here"
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10(errors)
        assert any(error["code"] == "forbidden_state_field" for error in errors)

    def test_validator_rejects_verbose_summary(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace)
        state["checkpoints"]["step-7"]["summary"] = "完成；写入 WD-CTX；CTX-01: 这是共享上下文正文"
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_7(errors)
        assert any(error["code"] == "summary_contains_forbidden_content" for error in errors)

    def test_validator_rejects_summary_that_is_too_long(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace)
        state["checkpoints"]["step-7"]["summary"] = (
            "完成；写入 WD-CTX；"
            + "这是一段被故意拉长的流程摘要，用来验证长度超限时应该返回专门的错误码而不是和正文混在一起。" * 3
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_7(errors)

        assert any(error["code"] == "summary_too_long" for error in errors)

    def test_step_7_rejects_unstructured_wd_ctx(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].mkdir(parents=True, exist_ok=True)
        (workspace["working_draft_path"] / "ctx.md").write_text(
            "这是自由文本总结，不是结构化 CTX 条目。\n已有实现很多，但没有按协议编号。\n",
            encoding="utf-8",
        )
        state = make_state(workspace, current_step=7, completed_steps=[1, 2, 3, 4, 5, 6], produced_artifacts=["WD-CTX"])
        state["can_enter_step_8"] = True
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_7(errors)

        assert any(error["code"] == "wd_ctx_structure_invalid" for error in errors)

    def test_step_7_rejects_ctx_count_mismatch(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        state = make_state(workspace, current_step=7, completed_steps=[1, 2, 3, 4, 5, 6], produced_artifacts=["WD-CTX"])
        state["checkpoints"]["step-7"]["ctx_count"] = 0
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_7(errors)

        assert any(error["code"] == "wd_ctx_count_mismatch" for error in errors)

    def test_step_2_requires_step_1_scope(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace)
        state["checkpoints"].pop("step-1")
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_2(errors)
        assert any(error["code"] == "missing_step1_scope" for error in errors)

    def test_step_11_missing_working_draft_repairs_from_step_7(
        self, workspace: dict[str, Path]
    ) -> None:
        state = make_state(workspace, current_step=11)
        state["completed_steps"] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        state["can_enter_step_11"] = True
        state["working_draft_path"] = ".architecture/.state/create-technical-solution/missing-solution"
        state["gate_receipt"] = {
            "step": 11,
            "state_fingerprint": "",
            "validated_at": "2026-04-08T09:31:00",
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_11(errors)

        missing_draft = next(
            error for error in errors if error["code"] == "missing_working_draft_path"
        )
        assert missing_draft["recommended_rollback_step"] == 7
        assert missing_draft["recommended_repair_step"] == 7

    def test_step_10_rejects_state_slots_collapsed_away_from_template(
        self, workspace: dict[str, Path]
    ) -> None:
        write_good_draft(workspace)
        state = make_state(workspace, current_step=10)
        state["slots"] = [
            {"slot": "SLOT-01", "title": "一、需求背景与综合评估"},
            {"slot": "SLOT-02", "title": "二、总体设计"},
        ]
        state["checkpoints"]["step-3"]["slot_count"] = 2
        state["checkpoints"]["step-8"]["task_slot_count"] = 2
        state["checkpoints"]["step-9"]["wd_exp_count"] = 2
        state["checkpoints"]["step-10"]["syn_slot_count"] = 2
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_10(errors)

        assert any(error["code"] == "state_slots_out_of_sync" for error in errors)

    def test_step_11_rejects_state_slots_collapsed_away_from_template(
        self, workspace: dict[str, Path]
    ) -> None:
        write_good_draft(workspace)
        state = make_state(workspace, current_step=11)
        state["completed_steps"] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        state["slots"] = [
            {"slot": "SLOT-01", "title": "一、需求背景与综合评估"},
            {"slot": "SLOT-02", "title": "二、总体设计"},
        ]
        state["checkpoints"]["step-3"]["slot_count"] = 2
        state["checkpoints"]["step-8"]["task_slot_count"] = 2
        state["checkpoints"]["step-9"]["wd_exp_count"] = 2
        state["checkpoints"]["step-10"]["syn_slot_count"] = 2
        state["gate_receipt"] = {"step": 11, "state_fingerprint": "", "validated_at": "2026-04-08T09:31:00"}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_11(errors)

        assert any(error["code"] == "state_slots_out_of_sync" for error in errors)


class TestScripts:



    def test_initialize_state_bootstraps_missing_state(self, workspace: dict[str, Path]) -> None:
        payload = iss.initialize_state(
            state_path=workspace["state_path"],
            slug="sample-solution",
            summary="完成；slug=sample-solution；paths=1；gate: step-2 ready",
            next_step=2,
        )
        state = vs.load_state(workspace["state_path"])
        assert payload["current_step"] == 2
        assert state["checkpoints"]["step-1"]["scope_ready"] is True
        assert state["gate_receipt"]["step"] == 2

    def test_initialize_state_uses_canonical_runtime_paths(self, workspace: dict[str, Path]) -> None:
        iss.initialize_state(
            state_path=workspace["state_path"],
            slug="sample-solution",
            summary="完成；slug=sample-solution；paths=1；gate: step-2 ready",
            next_step=2,
        )

        state = vs.load_state(workspace["state_path"])
        canonical = protocol_runtime.build_canonical_state_payload(
            state_path=workspace["state_path"],
            slug="sample-solution",
        )

        assert state["solution_root"] == canonical["solution_root"]
        assert state["template_path"] == canonical["template_path"]
        assert state["members_path"] == canonical["members_path"]
        assert state["principles_path"] == canonical["principles_path"]
        assert state["working_draft_path"] == canonical["working_draft_path"]
        assert state["final_document_path"] == canonical["final_document_path"]

    def test_initialize_state_returns_canonical_paths_in_result(self, workspace: dict[str, Path]) -> None:
        result = iss.initialize_state(
            state_path=workspace["state_path"],
            slug="sample-solution",
            summary="完成；slug=sample-solution；paths=1；gate: step-2 ready",
            next_step=2,
        )

        canonical = protocol_runtime.build_canonical_state_payload(
            state_path=workspace["state_path"],
            slug="sample-solution",
        )

        assert result["template_path"] == canonical["template_path"]
        assert result["members_path"] == canonical["members_path"]
        assert result["principles_path"] == canonical["principles_path"]
        assert result["solution_root"] == canonical["solution_root"]
        assert result["working_draft_path"] == canonical["working_draft_path"]
        assert result["final_document_path"] == canonical["final_document_path"]

    def test_runtime_snapshot_uses_canonical_defaults_for_missing_paths(self, workspace: dict[str, Path]) -> None:
        state = {
            "current_step": 3,
            "checkpoints": {},
        }
        vs.dump_state(workspace["state_path"], state)

        snapshot = rs.load_runtime_snapshot(workspace["state_path"])
        canonical = protocol_runtime.canonical_repo_paths_for_slug(
            repo_root=workspace["repo"],
            slug="sample-solution",
        )

        assert snapshot.working_draft_path == canonical["working_draft_path"]
        assert snapshot.template_path == canonical["template_path"]
        assert snapshot.final_document_path == canonical["final_document_path"]

    def test_initialize_state_starts_with_empty_question_queue(self, workspace: dict[str, Path]) -> None:
        iss.initialize_state(
            state_path=workspace["state_path"],
            slug="sample-solution",
            summary="完成；slug=sample-solution；paths=1；gate: step-2 ready",
            next_step=2,
        )
        state = vs.load_state(workspace["state_path"])
        assert state["pending_questions"] == []

    def test_render_final_document_rejects_docs_directory(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["content_file"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11)
        state["final_document_path"] = "docs/sample-solution.md"
        state["gate_receipt"] = {"step": 11, "state_fingerprint": "", "validated_at": ""}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        with pytest.raises(SystemExit):
            rfd.render_final_document(
            state_path=workspace["state_path"],
            content_path=workspace["content_file"],
                summary="完成；final_document=1；absorbed_slots=4；gate: step-12 ready",
            )

    def test_upsert_draft_block_preserves_existing_blocks(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        slots = make_state(workspace)["slots"]
        target = udb.write_working_draft_file(
            workspace["working_draft_path"],
            "WD-TASK",
            "### 1.1 需求概述\n任务\n",
            slots,
        )
        assert (workspace["working_draft_path"] / "ctx.md").exists()
        assert target == workspace["working_draft_path"] / "task.md"
        assert "### 1.1 需求概述" in target.read_text(encoding="utf-8")

    def test_upsert_draft_block_rejects_nested_block_heading(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        slots = make_state(workspace)["slots"]
        with pytest.raises(SystemExit):
            udb.write_working_draft_file(
                workspace["working_draft_path"],
                "WD-SYN-SLOT-01",
                "## WD-SYN\n\n### 槽位：1.1 需求概述\n\n内容\n",
                slots,
            )

    def test_upsert_draft_block_supports_wd_exp_member_block(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        slots = make_state(workspace)["slots"]
        target = udb.write_working_draft_file(
            workspace["working_draft_path"],
            "WD-EXP-SLOT-03",
            "### 专家：systems_architect\n- 决策类型: 改造\n- 核心理由: 复用不足，需要在现有资产上扩展。\n- 关键证据引用: CTX-01\n- 未决点: 无\n",
            slots,
        )
        updated = target.read_text(encoding="utf-8")
        assert target == workspace["working_draft_path"] / "slots" / "SLOT-03" / "experts.md"
        assert "### 专家：systems_architect" in updated

    def test_upsert_draft_block_sync_requires_explicit_flag(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        state = make_state(
            workspace,
            current_step=9,
            completed_steps=[1, 2, 3, 4, 5, 6, 7, 8],
            skipped_steps=[],
            produced_artifacts=["WD-CTX", "WD-TASK"],
            can_enter_step_9=True,
            can_enter_step_10=False,
        )
        state["gate_receipt"] = {"step": 9, "state_fingerprint": "", "validated_at": "2026-04-08T09:31:00"}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)

        payload = udb.upsert_with_sync(
            working_dir=workspace["working_draft_path"],
            state_path=workspace["state_path"],
            block_updates=[(
                "WD-EXP-SLOT-03",
                "### 专家：systems_architect\n- 决策类型: 改造\n- 核心理由: 复用不足，需要在现有资产上扩展。\n- 关键证据引用: CTX-01\n- 未决点: 无\n",
            )],
            summary="完成；写入 WD-EXP-SLOT-*；count=1；gate: step-10 ready",
            require_receipt_step=9,
        )

        refreshed = vs.load_state(workspace["state_path"])
        assert payload["gate_receipt_step"] == 10
        assert refreshed["checkpoints"]["step-9"]["wd_exp_count"] == 1
        assert refreshed["can_enter_step_10"] is True

    def test_advance_state_step_rejects_step_10_plus(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, current_step=10)
        write_state(workspace, state)
        result = subprocess.run(
            [
                "python3",
                str(scripts_path / "advance-state-step.py"),
                "--state",
                str(workspace["state_path"]),
                "--step",
                "10",
                "--summary",
                "完成；写入 WD-SYN；slots=4；gate: step-11 ready",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        output = result.stderr or result.stdout
        assert (
            "本脚本不可直接调用" in output
            or "advance-state-step.py 不允许用于 step-10" in output
        )

    def test_render_cli_rejects_content_file_flag(self, workspace: dict[str, Path]) -> None:
        workspace["content_file"].write_text(FINAL_DOC, encoding="utf-8")
        result = subprocess.run(
            [
                "python3",
                str(scripts_path / "render-final-document.py"),
                "--state",
                str(workspace["state_path"]),
                "--content-file",
                str(workspace["content_file"]),
                "--summary",
                "完成；final_document=1；absorbed_slots=4；gate: step-12 ready",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        output = result.stderr or result.stdout
        assert (
            "本脚本不可直接调用" in output
            or "unrecognized arguments: --content-file" in output
        )


class TestValidator:
    def test_build_repair_plan_uses_typed_action_for_ticket_refresh(self, workspace: dict[str, Path]) -> None:
        issues = [
            vs.make_issue(
                code="invalid_gate_receipt",
                message="receipt 已失效",
                step=9,
                field="gate_receipt.state_fingerprint",
                recommended_rollback_step=9,
                recommended_repair_step=9,
            )
        ]

        plan = vs.build_repair_plan(
            issues,
            state_path=workspace["state_path"],
            state=make_state(workspace, current_step=9),
        )

        assert plan[0]["action_type"] == "refresh_ticket"
        assert plan[0]["revalidate_step"] == 9

    def test_build_repair_plan_uses_typed_action_for_wd_rebuild(self, workspace: dict[str, Path]) -> None:
        issues = [
            vs.make_issue(
                code="missing_artifact",
                message="缺少 WD-CTX",
                step=7,
                field="produced_artifacts",
                missing_artifacts=["WD-CTX"],
                recommended_rollback_step=7,
                recommended_repair_step=7,
            )
        ]

        plan = vs.build_repair_plan(
            issues,
            state_path=workspace["state_path"],
            state=make_state(workspace, current_step=7, completed_steps=[1, 2, 3, 4, 5, 6]),
        )

        assert plan[0]["action_type"] == "rebuild_from_step_7"
        assert plan[0]["expected_artifacts_after_fix"] == ["WD-CTX"]

    def test_build_repair_plan_uses_typed_action_for_final_document_rerender(self, workspace: dict[str, Path]) -> None:
        issues = [
            vs.make_issue(
                code="final_document_not_rendered_via_script",
                message="最终文档不是脚本生成",
                step=11,
                field="checkpoints.step-11.rendered_via_script",
                recommended_rollback_step=11,
                recommended_repair_step=11,
            )
        ]

        plan = vs.build_repair_plan(
            issues,
            state_path=workspace["state_path"],
            state=make_state(workspace, current_step=11),
        )

        assert plan[0]["action_type"] == "rerender_final_document"

    def test_build_repair_plan_uses_step8_rebuild_for_task_slot_mismatch(self, workspace: dict[str, Path]) -> None:
        issues = [
            vs.make_issue(
                code="task_slots_incomplete",
                message="WD-TASK 与模板槽位不一致",
                step=8,
                field="working_draft_path",
                recommended_rollback_step=8,
                recommended_repair_step=8,
            )
        ]

        plan = vs.build_repair_plan(
            issues,
            state_path=workspace["state_path"],
            state=make_state(workspace, current_step=8),
        )

        assert plan[0]["action_type"] == "rebuild_from_step_8"

    def test_build_repair_plan_uses_step3_rebuild_for_template_truth_mismatch(self, workspace: dict[str, Path]) -> None:
        issues = [
            vs.make_issue(
                code="state_slots_out_of_sync",
                message="state.slots 与模板不一致",
                step=9,
                field="slots",
                recommended_rollback_step=3,
                recommended_repair_step=3,
            )
        ]

        plan = vs.build_repair_plan(
            issues,
            state_path=workspace["state_path"],
            state=make_state(workspace, current_step=9),
        )

        assert plan[0]["action_type"] == "rebuild_from_step_3"
    def test_validator_rejects_receipt_lagging_current_step(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, current_step=11)
        state["gate_receipt"] = {"step": 5, "state_fingerprint": "", "validated_at": "2026-04-08T09:31:00"}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11(errors)
        assert any(error["code"] == "invalid_gate_receipt" for error in errors)

    def test_step_10_rejects_incomplete_receipt(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        state = make_state(workspace)
        state["gate_receipt"] = {
            "step": 10,
            "state_fingerprint": vs.compute_state_fingerprint(state),
            "validated_at": "",
        }
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10(errors)
        assert any(error["code"] == "invalid_gate_receipt" for error in errors)

    def test_step_10_rejects_receipt_fingerprint_mismatch(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        state = make_state(workspace)
        state["gate_receipt"] = {
            "step": 10,
            "state_fingerprint": "stale-fingerprint",
            "validated_at": "2026-04-08T09:31:00",
        }
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10(errors)
        assert any(error["code"] == "invalid_gate_receipt" for error in errors)

    def test_step_3_allows_pre_extract_state(self, workspace: dict[str, Path]) -> None:
        state = make_state(
            workspace,
            current_step=3,
            completed_steps=[1, 2],
            working_draft_path="",
        )
        state["checkpoints"]["step-3"] = {"summary": "准备提取模板；前置已就绪；gate: extract pending"}
        state["gate_receipt"] = {"step": 3, "state_fingerprint": "", "validated_at": ""}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_3(errors)
        assert not any(error["code"] in {"template_not_loaded", "missing_template_snapshot", "invalid_working_draft_path"} for error in errors)

    def test_step_4_rejects_incomplete_receipt(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, current_step=4, completed_steps=[1, 2, 3])
        state["gate_receipt"] = {"step": 4, "state_fingerprint": "", "validated_at": ""}
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_4(errors)
        assert any(error["code"] == "invalid_gate_receipt" for error in errors)

    def test_step_4_requires_working_draft_path(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, current_step=4, completed_steps=[1, 2, 3], working_draft_path="")
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_4(errors)
        assert any(error["code"] == "invalid_working_draft_path" for error in errors)

    def test_step_4_accepts_state_dir_working_draft_path(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].mkdir(parents=True, exist_ok=True)
        state = make_state(workspace, current_step=4, completed_steps=[1, 2, 3])
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_4(errors)
        assert not any(error["code"] == "invalid_working_draft_path" for error in errors)

    def test_step_4_rejects_legacy_solution_root_working_draft_path(self, workspace: dict[str, Path]) -> None:
        state = make_state(
            workspace,
            current_step=4,
            completed_steps=[1, 2, 3],
            working_draft_path=".architecture/technical-solutions/working-drafts/sample-solution.working.md",
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_4(errors)
        assert any(error["code"] == "invalid_working_draft_path" for error in errors)

    def test_step_8_detects_missing_task_slots(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        (workspace["working_draft_path"] / "task.md").write_text("### 一、背景\n粗粒度任务\n", encoding="utf-8")
        state = make_state(workspace, current_step=8, completed_steps=[1, 2, 3, 4, 5, 6, 7], can_enter_step_8=True)
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_8(errors)
        assert any(error["code"] == "task_slots_incomplete" for error in errors)

    def test_step_8_rejects_ctx_mixed_into_task_block(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        (workspace["working_draft_path"] / "task.md").write_text(
            "### SLOT-01: 1.1 需求概述\n任务\n\n### CTX-02\n错误位置\n",
            encoding="utf-8",
        )
        state = make_state(workspace, current_step=8, completed_steps=[1, 2, 3, 4, 5, 6, 7], can_enter_step_8=True)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_8(errors)
        assert any(error["code"] == "task_block_structure_invalid" for error in errors)

    def test_step_10_requires_can_enter_gate(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        state = make_state(workspace, can_enter_step_10=False)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10(errors)
        assert any(error["code"] == "gate_flag_false" and error["field"] == "can_enter_step_10" for error in errors)

    def test_step_10_blocks_on_pending_questions(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        state = make_state(
            workspace,
            pending_questions=[
                {
                    "id": "q-step-10-01",
                    "step": 10,
                    "question": "是否接受模板承载缺口？",
                }
            ],
        )
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10(errors)
        assert any(error["code"] == "pending_questions_blocking_progress" for error in errors)

    def test_step_10_rejects_draft_state_desync(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        state = make_state(
            workspace,
            current_step=10,
            produced_artifacts=[],
            can_enter_step_10=True,
        )
        state["checkpoints"]["step-7"]["wd_ctx_written"] = False
        state["checkpoints"]["step-8"]["wd_task_written"] = False
        state["checkpoints"]["step-10"]["wd_syn_written"] = False
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10(errors)
        assert any(error["code"] == "artifact_state_desync" for error in errors)

    def test_step_7_requires_repowiki_consumption_when_exists(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].mkdir(parents=True, exist_ok=True)
        (workspace["working_draft_path"] / "ctx.md").write_text("", encoding="utf-8")
        state = make_state(workspace, current_step=7, completed_steps=[1, 2, 3, 4, 5, 6], produced_artifacts=["WD-CTX"])
        state["checkpoints"]["step-6"]["repowiki_exists"] = True
        state["checkpoints"]["step-6"]["repowiki_source_count"] = 0
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_7(errors)
        assert any(error["code"] == "repowiki_not_consumed" for error in errors)

    def test_step_10_requires_wd_syn_quality(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        (slot_dir(workspace, 1) / "synthesis.md").write_text("### 槽位：1.1 需求概述\n", encoding="utf-8")
        state = make_state(workspace)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10(errors)
        assert any(error["code"] == "missing_working_draft_block" for error in errors)

    def test_step_10_reports_missing_wd_syn_fragments_from_shared_contract(self, workspace: dict[str, Path]) -> None:
        wd_syn_contract = load_script("wd_syn_contract")
        slot_block = "### 槽位：1.1 需求概述\n#### 候选方案对比\n"
        write_good_draft(workspace)
        (slot_dir(workspace, 1) / "synthesis.md").write_text(slot_block, encoding="utf-8")
        state = make_state(workspace)
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_10(errors)

        issue = next(error for error in errors if error["code"] == "missing_working_draft_block")
        expected = [
            fragment
            for fragment in wd_syn_contract.required_slot_fragments("1.1 需求概述")
            if fragment not in slot_block and fragment != "- <本槽位要承载的能力或结论>"
        ]
        assert sorted(issue["missing_fragments"]) == sorted(expected)

    def test_step_10_rejects_missing_full_shared_slot_contract_lines(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        (slot_dir(workspace, 1) / "synthesis.md").write_text(
            "### 槽位：1.1 需求概述\n#### 目标能力\n- <本槽位要承载的能力或结论>\n#### 候选方案对比\n| 路径 | 可行性 | 关键证据 | 选择理由 |\n|------|--------|----------|----------|\n| 复用 | ☐ | CTX-01 | <待补充> |\n| 改造 | ☐ | CTX-01 | <待补充> |\n| 新建 | ☐ | CTX-01 | <待补充> |\n#### 选定路径\n- 路径: <复用 / 改造 / 新建>\n- 选定写法: <一句话写法>\n- 关键证据引用: CTX-01\n- 建议落位槽位: 1.1 需求概述\n- 未决问题: <若无则写无>\n",
            encoding="utf-8",
        )
        state = make_state(workspace)
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_10(errors)

        issue = next(error for error in errors if error["code"] == "missing_working_draft_block")
        assert issue["missing_fragments"] == ["- 模板承载缺口:"]

    def test_step_10_rejects_empty_target_capability_section(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        (slot_dir(workspace, 1) / "synthesis.md").write_text(
            "### 槽位：1.1 需求概述\n#### 目标能力\n\n#### 候选方案对比\n| 路径 | 可行性 | 关键证据 | 选择理由 |\n|------|--------|----------|----------|\n| 复用 | ☐ | CTX-01 | <待补充> |\n| 改造 | ☐ | CTX-01 | <待补充> |\n| 新建 | ☐ | CTX-01 | <待补充> |\n#### 选定路径\n- 路径: <复用 / 改造 / 新建>\n- 选定写法: <一句话写法>\n- 关键证据引用: CTX-01\n- 建议落位槽位: 1.1 需求概述\n- 模板承载缺口: <若无则写无>\n- 未决问题: <若无则写无>\n",
            encoding="utf-8",
        )
        state = make_state(workspace)
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_10(errors)

        issue = next(error for error in errors if error["code"] == "missing_working_draft_block")
        assert issue["missing_fragments"] == ["#### 目标能力"]

    def test_step_8_rejects_out_of_band_artifact_mutation(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        state = make_state(
            workspace,
            current_step=8,
            completed_steps=[1, 2, 3, 4, 5, 6, 7],
            can_enter_step_8=True,
        )
        register_artifacts(state, workspace)
        ctx_path = workspace["working_draft_path"] / "ctx.md"
        ctx_path.write_text(ctx_path.read_text(encoding="utf-8") + "\n外部改写\n", encoding="utf-8")
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_8(errors)

        assert any(error["code"] == "artifact_registry_mismatch" for error in errors)

    def test_step_10_rejects_placeholder_target_capability_text(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        (slot_dir(workspace, 1) / "synthesis.md").write_text(
            "### 槽位：1.1 需求概述\n#### 目标能力\n- 承载1.1 需求概述的技术结论\n#### 候选方案对比\n| 路径 | 可行性 | 关键证据 | 选择理由 |\n|------|--------|----------|----------|\n| 复用 | ❌ | CTX-01 | 不足 |\n| 改造 | ✅ | CTX-01 | 推荐 |\n| 新建 | ❌ | CTX-01 | 成本高 |\n#### 选定路径\n- 路径: 改造\n- 选定写法: 在 1.1 需求概述 位置补齐内容。\n- 关键证据引用: CTX-01\n- 建议落位槽位: 1.1 需求概述\n- 模板承载缺口: 无\n- 未决问题: 无\n",
            encoding="utf-8",
        )
        state = make_state(workspace)
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_10(errors)

        assert any(error["code"] == "placeholder_content_detected" for error in errors)

    def test_step_10_rejects_overly_similar_slot_synthesis(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        duplicated = "#### 目标能力\n- 收敛统一改造结论。\n#### 候选方案对比\n| 路径 | 可行性 | 关键证据 | 选择理由 |\n|------|--------|----------|----------|\n| 复用 | ❌ | CTX-01, CTX-02 | 现有能力不足 |\n| 改造 | ✅ | CTX-01, CTX-02, CTX-03 | 扩展现有SpotRule模型即可 |\n| 新建 | ❌ | CTX-03 | 成本高 |\n#### 选定路径\n- 路径: 改造\n- 选定写法: 扩展现有SpotRule模型，新增比例模式分支\n- 关键证据引用: CTX-01, CTX-02, CTX-03\n- 模板承载缺口: 无\n- 未决问题: 无\n"
        for index, title in enumerate(("1.1 需求概述", "1.2 核心目标", "2.1 方案设计", "2.2 风险与验证"), start=1):
            (slot_dir(workspace, index) / "synthesis.md").write_text(
                f"### 槽位：{title}\n{duplicated}- 建议落位槽位: {title}\n",
                encoding="utf-8",
            )
        state = make_state(workspace)
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_10(errors)

        assert any(error["code"] == "wd_syn_slots_too_similar" for error in errors)

    def test_step_10_requires_wd_syn_per_slot(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        for index in range(2, 5):
            (slot_dir(workspace, index) / "synthesis.md").write_text("", encoding="utf-8")
        state = make_state(workspace)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10(errors)
        assert any(error["code"] == "wd_syn_slots_incomplete" for error in errors)

    def test_step_8_rejects_task_ctx_reference_not_present_in_wd_ctx(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        (workspace["working_draft_path"] / "task.md").write_text(
            "### SLOT-01: 1.1 需求概述\n\n- 绑定上下文：CTX-01、CTX-13\n- 任务：补齐内容\n- 产出：结论\n\n"
            "### SLOT-02: 1.2 核心目标\n\n- 绑定上下文：CTX-02\n- 任务：补齐内容\n- 产出：结论\n\n"
            "### SLOT-03: 2.1 方案设计\n\n- 绑定上下文：CTX-03\n- 任务：补齐内容\n- 产出：结论\n\n"
            "### SLOT-04: 2.2 风险与验证\n\n- 绑定上下文：CTX-04\n- 任务：补齐内容\n- 产出：结论\n",
            encoding="utf-8",
        )
        state = make_state(workspace, current_step=8, completed_steps=[1, 2, 3, 4, 5, 6, 7])
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_8(errors)

        assert any(error["code"] == "task_ctx_reference_invalid" for error in errors)

    def test_step_9_rejects_out_of_band_wd_exp_mutation(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        state = make_state(workspace, current_step=9, completed_steps=[1, 2, 3, 4, 5, 6, 7, 8])
        exp_path = slot_dir(workspace, 1) / "experts.md"
        original = exp_path.read_text(encoding="utf-8")
        state["artifact_registry"]["WD-EXP-SLOT-01"] = {
            "path": exp_path.relative_to(workspace["repo"]).as_posix(),
            "content_hash": hashlib.sha256(original.encode("utf-8")).hexdigest(),
            "written_at": "2026-04-11T12:00:00+00:00",
            "writer": "run-step",
        }
        exp_path.write_text(original + "\n流程外改写\n", encoding="utf-8")
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_9(errors)

        assert any(error["code"] == "artifact_registry_mismatch" for error in errors)

    def test_step_10_rejects_out_of_band_wd_syn_mutation(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        state = make_state(workspace)
        syn_path = slot_dir(workspace, 1) / "synthesis.md"
        original = syn_path.read_text(encoding="utf-8")
        state["artifact_registry"]["WD-SYN-SLOT-01"] = {
            "path": syn_path.relative_to(workspace["repo"]).as_posix(),
            "content_hash": hashlib.sha256(original.encode("utf-8")).hexdigest(),
            "written_at": "2026-04-11T12:00:00+00:00",
            "writer": "run-step",
        }
        syn_path.write_text(original + "\n流程外改写\n", encoding="utf-8")
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_10(errors)

        assert any(error["code"] == "artifact_registry_mismatch" for error in errors)

    def test_step_11_rejects_docs_final_document_path(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        docs_path = workspace["repo"] / "docs" / "sample-solution.md"
        docs_path.parent.mkdir(parents=True)
        docs_path.write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11, final_document_path="docs/sample-solution.md")
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11(errors)
        assert any(error["code"] == "invalid_final_document_path" for error in errors)

    def test_step_11_accepts_canonical_absolute_final_document_path(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11, final_document_path=str(workspace["final_document_path"]))
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11(errors)
        assert not any(error["code"] == "invalid_final_document_path" for error in errors)

    def test_step_11_requires_render_script_marker(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11)
        state["checkpoints"]["step-11"]["rendered_via_script"] = False
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11(errors)
        assert any(error["code"] == "final_document_not_rendered_via_script" for error in errors)

    def test_step_11_requires_can_enter_gate(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11, can_enter_step_11=False)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11(errors)
        assert any(error["code"] == "gate_flag_false" and error["field"] == "can_enter_step_11" for error in errors)

    def test_step_11_rejects_absolute_working_draft_path(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11)
        state["working_draft_path"] = str(workspace["working_draft_path"])
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11(errors)
        assert any(error["code"] == "invalid_working_draft_path" for error in errors)

    def test_step_11_rejects_invalid_solution_root(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11, solution_root=".architecture")
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11(errors)
        assert any(error["code"] == "invalid_solution_root" for error in errors)

    def test_step_11_detects_overwritten_wd_ctx(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        (workspace["working_draft_path"] / "ctx.md").write_text("", encoding="utf-8")
        state = make_state(workspace, current_step=11)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11(errors)
        assert any(error["code"] == "draft_block_overwritten" for error in errors)

    def test_step_12_rejects_wrong_final_document_order(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(
            "# 技术方案文档\n\n## 一、背景\n\n### 1.2 核心目标\n\n内容\n\n### 1.1 需求概述\n\n内容\n\n## 二、设计\n\n### 2.1 方案设计\n\n内容\n\n### 2.2 风险与验证\n\n内容\n",
            encoding="utf-8",
        )
        state = make_state(workspace, current_step=12, completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 10, 11])
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_12(errors)
        assert any(error["code"] == "final_document_headings_mismatch" for error in errors)

    def test_step_11_detects_document_built_before_step_10(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11, completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 10])
        state["checkpoints"]["step-10"]["completed_at"] = "2100-01-01T00:00:00+00:00"
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11(errors)
        assert any(error["code"] == "step_order_violation" for error in errors)

    def test_step_12_rejects_final_document_with_template_placeholders(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(
            "# 技术方案文档\n\n## 一、背景\n\n### 1.1 需求概述\n\n*   **需求地址**\n\n### 1.2 核心目标\n\n*   **Redmine地址**\n\n## 二、设计\n\n### 2.1 方案设计\n\n> 对接三方接口文档，外部资料信息等\n\n### 2.2 风险与验证\n\n内容\n",
            encoding="utf-8",
        )
        state = make_state(workspace, current_step=12, completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        validator = make_validator(state, workspace)
        errors: list[dict] = []

        validator.step_12(errors)

        assert any(error["code"] == "placeholder_content_detected" for error in errors)


class TestCleanup:
    def test_render_final_document_refreshes_receipt(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        state = make_state(workspace, current_step=11)
        state["gate_receipt"] = {"step": 11, "state_fingerprint": "", "validated_at": "2026-04-08T09:31:00"}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        payload = rfd.render_final_document(
            state_path=workspace["state_path"],
            content_path=None,
            summary="完成；final_document=1；absorbed_slots=4；gate: step-12 ready",
        )
        refreshed = vs.load_state(workspace["state_path"])
        assert payload["current_step"] == 12
        assert refreshed["gate_receipt"]["step"] == 12
        assert refreshed["checkpoints"]["step-11"]["rendered_via_script"] is True

    def test_finalize_cleanup_failure_keeps_files(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=12, completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 10, 11], produced_artifacts=["WD-TASK"])
        state["checkpoints"]["step-7"]["wd_ctx_written"] = True
        state["gate_receipt"] = {"step": 12, "state_fingerprint": "", "validated_at": "2026-04-08T09:31:00"}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        exit_code, payload = fc.run_cleanup(workspace["state_path"], "完成；validator_passed=true；deleted=2")
        assert exit_code == 2
        assert payload["passed"] is False
        assert workspace["working_draft_path"].exists()
        assert workspace["state_path"].exists()

    def test_finalize_cleanup_success(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=12, completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        state["gate_receipt"] = {"step": 12, "state_fingerprint": "", "validated_at": "2026-04-08T09:31:00"}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        exit_code, payload = fc.run_cleanup(workspace["state_path"], "完成；validator_passed=true；deleted=2")
        assert exit_code == 0
        assert payload["passed"] is True
        assert not workspace["working_draft_path"].exists()
        assert not workspace["state_path"].exists()


class TestProjectRootResolution:
    def test_repo_root_from_external_skill_state_path_prefers_real_project_root(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "ugc-project"
        (project_root / ".architecture").mkdir(parents=True)
        external_state = (
            project_root
            / ".agents"
            / "skills"
            / "create-technical-solution"
            / "state"
            / "sample-solution"
            / "meta.yaml"
        )
        external_state.parent.mkdir(parents=True)
        external_state.write_text("{}\n", encoding="utf-8")

        repo_root = vs.repo_root_from_state_path(external_state)

        assert repo_root == project_root.resolve()

    def test_validator_resolves_architecture_paths_from_real_project_root(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "ugc-project"
        arch = project_root / ".architecture"
        template_dir = arch / "templates"
        template_dir.mkdir(parents=True)
        template_path = template_dir / "technical-solution-template.md"
        template_path.write_text(TEMPLATE, encoding="utf-8")
        (arch / "members.yml").write_text("members:\n  - id: systems_architect\n", encoding="utf-8")
        (arch / "principles.md").write_text("# principles\n", encoding="utf-8")

        external_state_path = (
            project_root
            / ".agents"
            / "skills"
            / "create-technical-solution"
            / "state"
            / "sample-solution"
            / "meta.yaml"
        )
        external_state_path.parent.mkdir(parents=True)

        state = {
            "current_step": 4,
            "completed_steps": [1, 2, 3],
            "skipped_steps": [],
            "pending_questions": [],
            "solution_root": ".architecture/technical-solutions",
            "template_path": ".architecture/templates/technical-solution-template.md",
            "members_path": ".architecture/members.yml",
            "principles_path": ".architecture/principles.md",
            "working_draft_path": ".architecture/.state/create-technical-solution/sample-solution",
            "final_document_path": ".architecture/technical-solutions/sample-solution.md",
            "slots": [{"slot": item["slot"], "title": item["title"]} for item in vs.extract_slot_headings(TEMPLATE)],
            "checkpoints": {
                "step-1": {"summary": "完成", "slug": "sample-solution", "scope_ready": True},
                "step-2": {"summary": "完成", "prerequisites_checked": True},
                "step-3": {
                    "summary": "完成",
                    "template_loaded": True,
                    "template_fingerprint": vs.compute_template_fingerprint(TEMPLATE, vs.extract_slot_headings(TEMPLATE)),
                    "slot_count": 4,
                },
                "step-4": {"summary": "完成", "solution_type": "新功能方案"},
            },
            "gate_receipt": {"step": 4, "state_fingerprint": "", "validated_at": "2026-04-11T10:00:00"},
        }
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        external_state_path.write_text(vs.yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

        validator = vs.GateValidator(state, external_state_path)

        assert validator.repo_root == project_root.resolve()
        assert validator.template_path() == template_path.resolve()
        assert validator.members_path() == (arch / "members.yml").resolve()
        assert validator.principles_path() == (arch / "principles.md").resolve()


def test_installed_copy_run_step_smoke(tmp_path: Path) -> None:
    source_root = scripts_path.parent
    installed_root = tmp_path / "create-technical-solution"
    shutil.copytree(source_root, installed_root)
    project_root = tmp_path / "sample-project"
    state_path = project_root / ".architecture" / ".state" / "create-technical-solution" / "sample-solution.yaml"

    result = subprocess.run(
        [
            "python3",
            str(installed_root / "scripts" / "run-step.py"),
            "--state",
            str(state_path),
            "--complete",
            "--summary",
            "定题完成",
            "--slug",
            "sample-solution",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert state_path.exists()

    status = subprocess.run(
        ["python3", str(installed_root / "scripts" / "run-step.py"), "--state", str(state_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert status.returncode == 0
    assert str(installed_root / "scripts" / "run-step.py") in status.stdout
