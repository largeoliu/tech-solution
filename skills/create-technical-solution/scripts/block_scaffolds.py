# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import workflow_default_block
from runtime_snapshot import RuntimeSnapshot
from wd_syn_contract import render_slot_lines


def load_extract_template_snapshot_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "create_technical_solution_extract_template_snapshot",
        SCRIPTS_DIR / "extract-template-snapshot.py",
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def template_slot_titles(snapshot: RuntimeSnapshot) -> list[str]:
    if not snapshot.template_path.exists():
        raise SystemExit(f"模板文件不存在: {snapshot.template_path}")
    module = load_extract_template_snapshot_module()
    headings = module.extract_slot_headings(snapshot.template_path.read_text(encoding="utf-8"))
    titles = [str(item.get("title") or "").strip() for item in headings]
    titles = [title for title in titles if title]
    if not titles:
        raise SystemExit(f"模板未提取到任何槽位: {snapshot.template_path}")
    return titles


def selected_members(state: dict[str, Any]) -> list[str]:
    checkpoints = state.get("checkpoints", {})
    step5 = checkpoints.get("step-5", {}) if isinstance(checkpoints, dict) else {}
    raw = step5.get("selected_members", []) if isinstance(step5, dict) else []
    return [str(item).strip() for item in raw if str(item).strip()] if isinstance(raw, list) else []


def resolve_members(state: dict[str, Any], members: list[str] | None = None) -> list[str]:
    configured = selected_members(state)
    if not configured:
        raise SystemExit("步骤 9 缺少 checkpoints.step-5.selected_members，无法生成 WD-EXP-* scaffold。")
    if not members:
        return configured
    allowed = {member.upper(): member for member in configured}
    resolved: list[str] = []
    for member in members:
        key = str(member).strip().upper()
        if key not in allowed:
            raise SystemExit(f"步骤 9 的 scaffold 仅支持已选择成员: {member}")
        resolved.append(allowed[key])
    return resolved


def build_wd_ctx_scaffold(snapshot: RuntimeSnapshot) -> str:
    slots = template_slot_titles(snapshot)
    slot_line = "、".join(slots)
    return "\n".join(
        [
            "## WD-CTX",
            "",
            "### CTX-01",
            "来源: <文件路径 / 目录 / 用户输入>",
            "结论或约束: <共享事实、已有实现、限制条件>",
            f"适用槽位: {slot_line}",
            "可信度或缺口: 待补证",
        ]
    )


def build_wd_task_scaffold(snapshot: RuntimeSnapshot) -> str:
    members = ", ".join(selected_members(snapshot.state) or ["<MEMBER_ID>"])
    lines = ["## WD-TASK", ""]
    for title in template_slot_titles(snapshot):
        lines.extend(
            [
                f"### {title}",
                "- 槽位标识: <SLOT-ID>",
                "- 必须消费的共享上下文: CTX-01",
                f"- 参与专家: {members}",
                "- 每位专家必答问题:",
                "  - <围绕当前槽位补齐复用 / 改造 / 新建比较>",
                f"- 建议落位槽位: {title}",
                "- 落位表达要求: <只写当前模板槽位需要的最小闭环>",
                "- 缺口或阻塞项: <若无则写无>",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def build_wd_exp_scaffold(snapshot: RuntimeSnapshot, members: list[str] | None = None) -> str:
    slots = template_slot_titles(snapshot)
    payloads: list[str] = []
    for member in resolve_members(snapshot.state, members):
        payloads.append(
            "\n".join(
                [
                    f"## WD-EXP-{member.upper()}",
                    "",
                    "### 参与槽位",
                    f"- {slots[0]}",
                    "",
                    "### 决策类型",
                    "- <复用 / 改造 / 新建>",
                    "",
                    "### 核心理由",
                    "- <绑定 CTX 编号，说明为什么选这条路径>",
                    "",
                    "### 关键证据引用",
                    "- CTX-01",
                    "",
                    "### 未决点",
                    "- <若无则写无>",
                ]
            )
        )
    return "\n\n".join(payloads)


def build_wd_syn_scaffold(snapshot: RuntimeSnapshot) -> str:
    block_name = workflow_default_block(10, snapshot.flow_tier) or "WD-SYN"
    lines = [f"## {block_name}", ""]
    for title in template_slot_titles(snapshot):
        if block_name == "WD-SYN-LIGHT":
            lines.extend(
                [
                    f"### 槽位：{title}",
                    "- 目标能力: <要达成什么>",
                    "- 候选路径对比: 复用 / 改造 / 新建",
                    "- 选定路径: <最终选择>",
                    "- 关键证据: CTX-01",
                    f"- 建议落位槽位: {title}",
                    "- 未决问题或阻塞: <若无则写无>",
                    "",
                ]
            )
            continue
        lines.extend(
            render_slot_lines(title) + [""]
        )
    return "\n".join(lines).rstrip()


def effective_scaffold_step(snapshot: RuntimeSnapshot) -> int:
    step = snapshot.current_step
    flow_tier = snapshot.flow_tier
    if flow_tier == "light" and step in {8, 9, 10}:
        return 10
    if flow_tier == "moderate" and step in {9, 10}:
        return 10
    return step


def emit_scaffold(snapshot: RuntimeSnapshot, members: list[str] | None = None) -> str:
    step = effective_scaffold_step(snapshot)
    if step == 7:
        return build_wd_ctx_scaffold(snapshot)
    if step == 8:
        return build_wd_task_scaffold(snapshot)
    if step == 9:
        return build_wd_exp_scaffold(snapshot, members=members)
    if step == 10:
        return build_wd_syn_scaffold(snapshot)
    raise SystemExit(f"步骤 {step} 不支持 emit scaffold；仅支持步骤 7/8/9/10。")
