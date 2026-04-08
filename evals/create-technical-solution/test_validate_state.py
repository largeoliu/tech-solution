# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "pytest>=8.0"]
# ///
"""create-technical-solution validator regression tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

scripts_path = Path(__file__).parent.parent.parent / "skills" / "create-technical-solution" / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), scripts_path / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


vs = load_script("validate-state")
fc = load_script("finalize-cleanup")
sft = load_script("set-flow-tier")
mss = load_script("mark-step-skipped")
iss = load_script("initialize-state")
rfd = load_script("render-final-document")


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
    working_drafts = solution_root / "working-drafts"

    state_dir.mkdir(parents=True)
    template_dir.mkdir(parents=True)
    working_drafts.mkdir(parents=True)

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
        "working_draft_path": working_drafts / "sample-solution.working.md",
        "final_document_path": solution_root / "sample-solution.md",
        "state_path": state_dir / "sample-solution.yaml",
        "content_file": repo / "final-content.md",
    }


def make_state(workspace: dict[str, Path], **overrides) -> dict:
    state = {
        "current_step": 10,
        "completed_steps": [1, 2, 3, 4, 5, 6, 7, 8],
        "skipped_steps": [9],
        "flow_tier": "moderate",
        "required_artifacts": ["WD-CTX", "WD-TASK", "WD-SYN"],
        "produced_artifacts": ["WD-CTX", "WD-TASK", "WD-SYN"],
        "gate_receipt": {"step": 10, "flow_tier": "moderate", "state_fingerprint": "", "validated_at": "2026-04-08T09:31:00"},
        "solution_root": ".architecture/technical-solutions",
        "template_path": ".architecture/templates/technical-solution-template.md",
        "members_path": ".architecture/members.yml",
        "principles_path": ".architecture/principles.md",
        "repowiki_path": ".qoder/repowiki",
        "working_draft_path": ".architecture/technical-solutions/working-drafts/sample-solution.working.md",
        "final_document_path": ".architecture/technical-solutions/sample-solution.md",
        "checkpoints": {
            "step-1": {"summary": "完成；slug=sample-solution；paths=1；gate: step-2 ready", "slug": "sample-solution", "scope_ready": True},
            "step-2": {"summary": "完成；检查前置文件；files=3；gate: step-3 ready", "prerequisites_checked": True},
            "step-3": {"summary": "完成；写入 draft 骨架；slots=4；gate: step-4 ready", "template_loaded": True, "template_fingerprint": "", "slot_count": 4},
            "step-4": {"summary": "完成；flow_tier=moderate；signals=1；gate: step-5 ready", "solution_type": "现有资产改造", "flow_tier": "moderate", "signals": ["existing-asset-refactor"]},
            "step-5": {"summary": "完成；成员已选择；count=1；gate: step-6 ready", "members_checked": True, "selected_members": ["systems_architect"], "selected_member_count": 1},
            "step-6": {"summary": "完成；repowiki 不存在；sources=0；gate: step-7 ready", "repowiki_checked": True, "repowiki_exists": False, "repowiki_source_count": 0},
            "step-7": {"summary": "完成；写入 WD-CTX；CTX=4；gate: step-8 ready", "wd_ctx_written": True, "ctx_count": 4},
            "step-8": {"summary": "完成；写入 WD-TASK；slots=4；gate: step-10 ready", "wd_task_written": True, "task_slot_count": 4},
            "step-9": {"summary": "跳过；WD-EXP=0；reason=moderate；gate: step-10 ready", "skipped": True, "reason": "moderate 无需 WD-EXP-*", "wd_exp_count": 0},
            "step-10": {"summary": "完成；写入 WD-SYN；slots=4；gate: step-11 ready", "wd_syn_written": True, "syn_slot_count": 4},
            "step-11": {"summary": "完成；final_document=1；absorbed_slots=4；gate: step-12 ready", "final_document_written": True, "absorbed_slot_count": 4, "rendered_via_script": True},
            "step-12": {"summary": "完成；validator_passed=true；deleted=0", "validator_passed": False, "working_draft_deleted": False, "state_file_deleted": False},
        },
        "can_enter_step_8": True,
        "can_enter_step_9": False,
        "can_enter_step_10": True,
        "can_enter_step_11": True,
        "can_enter_step_12": True,
        "absorption_check_passed": False,
        "cleanup_allowed": False,
    }
    headings = vs.extract_slot_headings(workspace["template_path"].read_text(encoding="utf-8"))
    state["checkpoints"]["step-3"]["template_fingerprint"] = vs.compute_template_fingerprint(
        workspace["template_path"].read_text(encoding="utf-8"),
        headings,
    )
    state.update(overrides)
    state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
    return state


def write_state(workspace: dict[str, Path], state: dict) -> None:
    workspace["state_path"].write_text(vs.yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def make_validator(state: dict, workspace: dict[str, Path]) -> vs.GateValidator:
    write_state(workspace, state)
    return vs.GateValidator(state, workspace["state_path"])


def write_good_draft(workspace: dict[str, Path]) -> None:
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
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- **关键证据引用**：CTX-01

### 槽位：1.2 核心目标
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- **关键证据引用**：CTX-01

### 槽位：2.1 方案设计
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- **关键证据引用**：CTX-01

### 槽位：2.2 风险与验证
#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | CTX-01 | 不足 |
| 改造 | ✅ | CTX-01 | 推荐 |
| 新建 | ❌ | CTX-01 | 成本高 |
#### 选定路径
- **关键证据引用**：CTX-01
""",
        encoding="utf-8",
    )


class TestStateBoundary:
    def test_validator_rejects_forbidden_state_fields(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, slug="sample-solution")
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10("moderate", errors)
        assert any(error["code"] == "forbidden_state_field" for error in errors)

    def test_validator_rejects_verbose_summary(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace)
        state["checkpoints"]["step-7"]["summary"] = "完成；写入 WD-CTX；CTX-01: 这是共享上下文正文"
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_7("moderate", errors)
        assert any(error["code"] == "verbose_summary" for error in errors)

    def test_step_2_requires_step_1_scope(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace)
        state["checkpoints"].pop("step-1")
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_2("light", errors)
        assert any(error["code"] == "missing_step1_scope" for error in errors)


class TestScripts:
    def test_set_flow_tier_enforces_signal_contract(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, current_step=4, completed_steps=[1, 2, 3], flow_tier="moderate")
        state["gate_receipt"] = {"step": 4, "flow_tier": "moderate", "state_fingerprint": "", "validated_at": ""}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        with pytest.raises(SystemExit):
            sft.set_flow_tier(
                state_path=workspace["state_path"],
                flow_tier="moderate",
                solution_type="新增能力",
                summary="完成；flow_tier=moderate；signals=1；gate: step-5 ready",
                next_step=5,
                append_completed=True,
                signals=["introduces-core-capability"],
                require_receipt_step=4,
            )

    def test_mark_step_skipped_requires_receipt(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, current_step=9, completed_steps=[1, 2, 3, 4, 5, 6, 7, 8], skipped_steps=[])
        state["gate_receipt"] = {"step": 8, "flow_tier": "moderate", "state_fingerprint": "bad", "validated_at": ""}
        write_state(workspace, state)
        with pytest.raises(SystemExit):
            mss.mark_step_skipped(
                state_path=workspace["state_path"],
                step=9,
                summary="跳过；WD-EXP=0；reason=moderate；gate: step-10 ready",
                reason="moderate 无需 WD-EXP-*",
                next_step=10,
                require_receipt_step=9,
            )

    def test_initialize_state_bootstraps_missing_state(self, workspace: dict[str, Path]) -> None:
        payload = iss.initialize_state(
            state_path=workspace["state_path"],
            slug="sample-solution",
            summary="完成；slug=sample-solution；paths=1；gate: step-2 ready",
            next_step=2,
            solution_root=".architecture/technical-solutions",
        )
        state = vs.load_state(workspace["state_path"])
        assert payload["current_step"] == 2
        assert state["checkpoints"]["step-1"]["scope_ready"] is True
        assert state["gate_receipt"]["step"] == 2
        assert state["gate_receipt"]["flow_tier"] == "light"

    def test_render_final_document_rejects_docs_directory(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["content_file"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11)
        state["final_document_path"] = "docs/sample-solution.md"
        state["gate_receipt"] = {"step": 11, "flow_tier": "moderate", "state_fingerprint": "", "validated_at": ""}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        with pytest.raises(SystemExit):
            rfd.render_final_document(
                state_path=workspace["state_path"],
                flow_tier="moderate",
                content_path=workspace["content_file"],
                summary="完成；final_document=1；absorbed_slots=4；gate: step-12 ready",
            )


class TestValidator:
    def test_validator_rejects_receipt_lagging_current_step(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, current_step=11)
        state["gate_receipt"] = {"step": 5, "flow_tier": "moderate", "state_fingerprint": "", "validated_at": "2026-04-08T09:31:00"}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11("moderate", errors)
        assert any(error["code"] == "invalid_gate_receipt" for error in errors)

    def test_step_3_allows_pre_extract_state(self, workspace: dict[str, Path]) -> None:
        state = make_state(
            workspace,
            current_step=3,
            completed_steps=[1, 2],
            working_draft_path="",
        )
        state["checkpoints"]["step-3"] = {"summary": "准备提取模板；前置已就绪；gate: extract pending"}
        state["gate_receipt"] = {"step": 3, "flow_tier": "light", "state_fingerprint": "", "validated_at": ""}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_3("light", errors)
        assert not any(error["code"] in {"template_not_loaded", "missing_template_snapshot", "invalid_working_draft_path"} for error in errors)

    def test_step_4_rejects_incomplete_receipt(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, current_step=4, completed_steps=[1, 2, 3])
        state["gate_receipt"] = {"step": 4, "flow_tier": "moderate", "state_fingerprint": "", "validated_at": ""}
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_4("moderate", errors)
        assert any(error["code"] == "invalid_gate_receipt" for error in errors)

    def test_step_4_requires_working_draft_path(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, current_step=4, completed_steps=[1, 2, 3], working_draft_path="")
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_4("moderate", errors)
        assert any(error["code"] == "invalid_working_draft_path" for error in errors)

    def test_step_4_rejects_unregistered_signals(self, workspace: dict[str, Path]) -> None:
        state = make_state(workspace, current_step=4, completed_steps=[1, 2, 3])
        state["checkpoints"]["step-4"]["signals"] = ["existing_system_enhancement", "frontend_form_change"]
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_4("moderate", errors)
        assert any(error["code"] == "invalid_step4_signals" for error in errors)

    def test_step_8_detects_missing_task_slots(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text("## WD-CTX\n\n## WD-TASK\n\n### 一、背景\n\n粗粒度任务\n", encoding="utf-8")
        state = make_state(workspace, current_step=8, completed_steps=[1, 2, 3, 4, 5, 6, 7], flow_tier="full", can_enter_step_8=True)
        state["checkpoints"]["step-4"]["flow_tier"] = "full"
        state["flow_tier"] = "full"
        state["required_artifacts"] = ["WD-CTX", "WD-TASK", "WD-EXP-*", "WD-SYN"]
        state["gate_receipt"]["flow_tier"] = "full"
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_8("full", errors)
        assert any(error["code"] == "task_slots_incomplete" for error in errors)

    def test_step_8_rejects_ctx_mixed_into_task_block(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text(
            "## WD-CTX\n\n### CTX-01\n\n来源\n\n## WD-TASK\n\n### SLOT-01: 1.1 需求概述\n\n任务\n\n### CTX-02\n\n错误位置\n",
            encoding="utf-8",
        )
        state = make_state(workspace, current_step=8, completed_steps=[1, 2, 3, 4, 5, 6, 7], flow_tier="moderate", can_enter_step_8=True)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_8("moderate", errors)
        assert any(error["code"] == "task_block_structure_invalid" for error in errors)

    def test_step_10_requires_explicit_skip_record(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        state = make_state(workspace, skipped_steps=[], completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 9])
        state["checkpoints"].pop("step-9")
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10("moderate", errors)
        assert any(error["code"] == "step_skipped_without_checkpoint" for error in errors)

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
        validator.step_10("moderate", errors)
        assert any(error["code"] == "artifact_state_desync" for error in errors)

    def test_step_7_requires_repowiki_consumption_when_exists(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text("## WD-CTX\n\n", encoding="utf-8")
        state = make_state(workspace, current_step=7, completed_steps=[1, 2, 3, 4, 5, 6], produced_artifacts=["WD-CTX"])
        state["checkpoints"]["step-6"]["repowiki_exists"] = True
        state["checkpoints"]["step-6"]["repowiki_source_count"] = 0
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_7("moderate", errors)
        assert any(error["code"] == "repowiki_not_consumed" for error in errors)

    def test_step_10_requires_wd_syn_quality(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text("## WD-CTX\n\n## WD-TASK\n\n## WD-SYN\n\n### 槽位：1.1 需求概述\n", encoding="utf-8")
        state = make_state(workspace)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10("moderate", errors)
        assert any(error["code"] == "missing_working_draft_block" for error in errors)

    def test_step_10_requires_wd_syn_per_slot(self, workspace: dict[str, Path]) -> None:
        workspace["working_draft_path"].write_text(
            "## WD-CTX\n\n### CTX-01\n\n来源\n\n## WD-TASK\n\n### 1.1 需求概述\n\n任务\n\n### 1.2 核心目标\n\n任务\n\n### 2.1 方案设计\n\n任务\n\n### 2.2 风险与验证\n\n任务\n\n## WD-SYN\n\n### 槽位：1.1 需求概述\n\n#### 候选方案对比\n\n| 路径 | 可行性 | 关键证据 | 选择理由 |\n|------|--------|----------|----------|\n| 复用 | ❌ | CTX-01 | 不足 |\n| 改造 | ✅ | CTX-01 | 推荐 |\n| 新建 | ❌ | CTX-01 | 成本高 |\n\n#### 选定路径\n\n- **关键证据引用**：CTX-01\n",
            encoding="utf-8",
        )
        state = make_state(workspace)
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_10("moderate", errors)
        assert any(error["code"] == "wd_syn_slots_incomplete" for error in errors)

    def test_step_11_rejects_docs_final_document_path(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        docs_path = workspace["repo"] / "docs" / "sample-solution.md"
        docs_path.parent.mkdir(parents=True)
        docs_path.write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11, final_document_path="docs/sample-solution.md")
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11("moderate", errors)
        assert any(error["code"] == "invalid_final_document_path" for error in errors)

    def test_step_11_requires_render_script_marker(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11)
        state["checkpoints"]["step-11"]["rendered_via_script"] = False
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11("moderate", errors)
        assert any(error["code"] == "final_document_not_rendered_via_script" for error in errors)

    def test_step_12_rejects_wrong_final_document_order(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(
            "# 技术方案文档\n\n## 一、背景\n\n### 1.2 核心目标\n\n内容\n\n### 1.1 需求概述\n\n内容\n\n## 二、设计\n\n### 2.1 方案设计\n\n内容\n\n### 2.2 风险与验证\n\n内容\n",
            encoding="utf-8",
        )
        state = make_state(workspace, current_step=12, completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 10, 11])
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_12("moderate", errors)
        assert any(error["code"] == "final_document_headings_mismatch" for error in errors)

    def test_step_11_detects_document_built_before_step_10(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11, completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 10])
        state["checkpoints"]["step-10"]["completed_at"] = "2100-01-01T00:00:00+00:00"
        validator = make_validator(state, workspace)
        errors: list[dict] = []
        validator.step_11("moderate", errors)
        assert any(error["code"] == "step_order_violation" for error in errors)


class TestCleanup:
    def test_render_final_document_refreshes_receipt(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["content_file"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=11)
        state["gate_receipt"] = {"step": 11, "flow_tier": "moderate", "state_fingerprint": "", "validated_at": "2026-04-08T09:31:00"}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        payload = rfd.render_final_document(
            state_path=workspace["state_path"],
            flow_tier="moderate",
            content_path=workspace["content_file"],
            summary="完成；final_document=1；absorbed_slots=4；gate: step-12 ready",
        )
        refreshed = vs.load_state(workspace["state_path"])
        assert payload["current_step"] == 12
        assert refreshed["gate_receipt"]["step"] == 12
        assert refreshed["checkpoints"]["step-11"]["rendered_via_script"] is True

    def test_finalize_cleanup_success(self, workspace: dict[str, Path]) -> None:
        write_good_draft(workspace)
        workspace["final_document_path"].write_text(FINAL_DOC, encoding="utf-8")
        state = make_state(workspace, current_step=12, completed_steps=[1, 2, 3, 4, 5, 6, 7, 8, 10, 11])
        state["gate_receipt"] = {"step": 12, "flow_tier": "moderate", "state_fingerprint": "", "validated_at": "2026-04-08T09:31:00"}
        state["gate_receipt"]["state_fingerprint"] = vs.compute_state_fingerprint(state)
        write_state(workspace, state)
        exit_code, payload = fc.run_cleanup(workspace["state_path"], "moderate", "完成；validator_passed=true；deleted=2")
        assert exit_code == 0
        assert payload["passed"] is True
        assert not workspace["working_draft_path"].exists()
        assert not workspace["state_path"].exists()
