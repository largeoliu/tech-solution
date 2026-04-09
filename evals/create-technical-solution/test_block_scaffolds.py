from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml


skill_root = Path(__file__).parent.parent.parent / "skills" / "create-technical-solution"
scripts_root = skill_root / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), scripts_root / f"{name}.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_workspace(tmp_path: Path) -> dict[str, Path]:
    repo = tmp_path / "sample-project"
    state_dir = repo / ".architecture" / ".state" / "create-technical-solution"
    template_dir = repo / ".architecture" / "templates"
    state_dir.mkdir(parents=True)
    template_dir.mkdir(parents=True)
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
    return {
        "repo": repo,
        "state_path": state_dir / "sample-solution.yaml",
        "template_path": template_path,
        "working_draft_path": state_dir / "sample-solution.working.md",
    }


def write_state(path: Path, state: dict) -> None:
    path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def make_state(workspace: dict[str, Path], *, step: int, selected_members: list[str] | None = None) -> dict:
    members = ["systems_architect"] if selected_members is None else selected_members
    return {
        "current_step": step,
        "template_path": ".architecture/templates/technical-solution-template.md",
        "working_draft_path": ".architecture/.state/create-technical-solution/sample-solution.working.md",
        "final_document_path": ".architecture/technical-solutions/sample-solution.md",
        "checkpoints": {
            "step-5": {
                "selected_members": members,
                "selected_member_count": len(members),
            }
        },
    }


def test_step7_scaffold_emits_ctx_block(tmp_path: Path) -> None:
    scaffolds = load_script("block_scaffolds")
    runtime_snapshot = load_script("runtime_snapshot")
    workspace = make_workspace(tmp_path)
    write_state(workspace["state_path"], make_state(workspace, step=7))

    snapshot = runtime_snapshot.load_runtime_snapshot(workspace["state_path"])
    payload = scaffolds.emit_scaffold(snapshot)

    assert payload.startswith("## WD-CTX\n")
    assert "### CTX-01" in payload
    assert "适用槽位" in payload


def test_step8_scaffold_uses_template_slots(tmp_path: Path) -> None:
    scaffolds = load_script("block_scaffolds")
    runtime_snapshot = load_script("runtime_snapshot")
    workspace = make_workspace(tmp_path)
    write_state(workspace["state_path"], make_state(workspace, step=8))

    snapshot = runtime_snapshot.load_runtime_snapshot(workspace["state_path"])
    payload = scaffolds.emit_scaffold(snapshot)

    assert payload.startswith("## WD-TASK\n")
    assert "### 1.1 需求概述" in payload
    assert "### 2.2 风险与验证" in payload
    assert "必须消费的共享上下文" in payload
    assert payload.count("### ") == 4


def test_step9_scaffold_emits_all_selected_members_by_default(tmp_path: Path) -> None:
    scaffolds = load_script("block_scaffolds")
    runtime_snapshot = load_script("runtime_snapshot")
    workspace = make_workspace(tmp_path)
    write_state(
        workspace["state_path"],
        make_state(workspace, step=9, selected_members=["systems_architect", "domain_expert"]),
    )

    snapshot = runtime_snapshot.load_runtime_snapshot(workspace["state_path"])
    payload = scaffolds.emit_scaffold(snapshot)

    assert "## WD-EXP-SYSTEMS_ARCHITECT" in payload
    assert "## WD-EXP-DOMAIN_EXPERT" in payload
    assert "### 决策类型" in payload


def test_step9_scaffold_requires_selected_members(tmp_path: Path) -> None:
    scaffolds = load_script("block_scaffolds")
    runtime_snapshot = load_script("runtime_snapshot")
    workspace = make_workspace(tmp_path)
    write_state(workspace["state_path"], make_state(workspace, step=9, selected_members=[]))

    snapshot = runtime_snapshot.load_runtime_snapshot(workspace["state_path"])

    with pytest.raises(SystemExit, match="selected_members"):
        scaffolds.emit_scaffold(snapshot)


def test_step10_wd_syn_scaffold_matches_full_shared_slot_contract(tmp_path: Path) -> None:
    scaffolds = load_script("block_scaffolds")
    runtime_snapshot = load_script("runtime_snapshot")
    wd_syn_contract = load_script("wd_syn_contract")
    workspace = make_workspace(tmp_path)
    write_state(workspace["state_path"], make_state(workspace, step=10))

    snapshot = runtime_snapshot.load_runtime_snapshot(workspace["state_path"])
    payload = scaffolds.emit_scaffold(snapshot)

    for fragment in wd_syn_contract.required_slot_fragments("1.1 需求概述"):
        assert fragment in payload


def test_step10_wd_syn_scaffold_contains_explicit_target_capability_placeholder(tmp_path: Path) -> None:
    scaffolds = load_script("block_scaffolds")
    runtime_snapshot = load_script("runtime_snapshot")
    workspace = make_workspace(tmp_path)
    write_state(workspace["state_path"], make_state(workspace, step=10))

    snapshot = runtime_snapshot.load_runtime_snapshot(workspace["state_path"])
    payload = scaffolds.emit_scaffold(snapshot)

    assert "#### 目标能力" in payload
    assert "- <本槽位要承载的能力或结论>" in payload
