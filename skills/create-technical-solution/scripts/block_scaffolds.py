# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
from __future__ import annotations

import importlib.util
import json
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


def template_slots(snapshot: RuntimeSnapshot) -> list[dict[str, str]]:
    state_slots = snapshot.state.get("slots") or []
    if state_slots:
        return state_slots
    if not snapshot.template_path.exists():
        raise SystemExit(f"模板文件不存在: {snapshot.template_path}")
    module = load_extract_template_snapshot_module()
    headings = module.extract_slot_headings(snapshot.template_path.read_text(encoding="utf-8"))
    return [{"slot": item["slot"], "title": item["title"]} for item in headings]


def selected_members(state: dict[str, Any]) -> list[str]:
    checkpoints = state.get("checkpoints", {})
    step5 = checkpoints.get("step-5", {}) if isinstance(checkpoints, dict) else {}
    raw = step5.get("selected_members", []) if isinstance(step5, dict) else []
    return [str(item).strip() for item in raw if str(item).strip()] if isinstance(raw, list) else []


def resolve_members(state: dict[str, Any], members: list[str] | None = None) -> list[str]:
    configured = selected_members(state)
    if not configured:
        raise SystemExit("步骤 9 缺少 checkpoints.step-5.selected_members，无法生成 WD-EXP-SLOT-* scaffold。")
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
    slots = template_slots(snapshot)
    slot_line = "、".join(s["title"] for s in slots)
    return "\n".join(
        [
            "### CTX-01",
            "来源: <文件路径 / 目录 / 用户输入>",
            "结论或约束: <共享事实、已有实现、限制条件>",
            f"适用槽位: {slot_line}",
            "可信度或缺口: 待补证",
        ]
    )


def build_wd_task_scaffold(snapshot: RuntimeSnapshot) -> str:
    members = ", ".join(selected_members(snapshot.state) or ["<MEMBER_ID>"])
    lines: list[str] = []
    for slot_info in template_slots(snapshot):
        title = slot_info["title"]
        slot_id = slot_info.get("slot", "")
        lines.extend(
            [
                f"### {title}",
                f"- 槽位标识: {slot_id}",
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
    slots = template_slots(snapshot)
    resolved_members = resolve_members(snapshot.state, members)
    payloads: list[str] = []
    for slot_info in slots:
        slot_id = slot_info.get("slot", "")
        lines = [f"---BLOCK:WD-EXP-{slot_id}", ""]
        for member in resolved_members:
            lines.extend(
                [
                    f"### 专家：{member}",
                    "- 决策类型: <复用 / 改造 / 新建>",
                    "- 核心理由: <绑定 CTX 编号，说明为什么选这条路径>",
                    "- 关键证据引用: CTX-01",
                    "- 未决点: <若无则写无>",
                    "",
                ]
            )
        payloads.append("\n".join(lines).rstrip())
    return "\n\n".join(payloads)


def build_wd_syn_scaffold(snapshot: RuntimeSnapshot) -> str:
    slots = template_slots(snapshot)
    payloads: list[str] = []
    for slot_info in slots:
        slot_id = slot_info.get("slot", "")
        title = slot_info["title"]
        lines = [f"---BLOCK:WD-SYN-{slot_id}", ""]
        lines.extend(render_slot_lines(title))
        payloads.append("\n".join(lines).rstrip())
    return "\n\n".join(payloads)


def build_ctx_json_scaffold(snapshot: RuntimeSnapshot) -> list[dict[str, Any]]:
    return [
        {
            "id": f"CTX-{index:02d}",
            "source": "",
            "conclusion": "",
            "applicable_slots": [slot_info["title"]],
            "confidence": "",
        }
        for index, slot_info in enumerate(template_slots(snapshot), start=1)
    ]


def build_task_json_scaffold(snapshot: RuntimeSnapshot) -> list[dict[str, Any]]:
    return [
        {
            "slot": slot_info["title"],
            "required_ctx": [],
        }
        for slot_info in template_slots(snapshot)
    ]


def build_exp_json_scaffold(
    snapshot: RuntimeSnapshot, members: list[str] | None = None
) -> list[dict[str, Any]]:
    _resolved_members = resolve_members(snapshot.state, members)
    return [
        {
            "slot": slot_info["title"],
            "decision_type": "",
            "rationale": "",
            "evidence_refs": [],
            "open_questions": [],
        }
        for slot_info in template_slots(snapshot)
    ]


def build_syn_json_scaffold(snapshot: RuntimeSnapshot) -> list[dict[str, Any]]:
    return [
        {
            "slot": slot_info["title"],
            "target_capability": "",
            "comparisons": [
                {"path": "复用", "feasibility": "", "evidence": "", "reason": ""},
                {"path": "改造", "feasibility": "", "evidence": "", "reason": ""},
                {"path": "新建", "feasibility": "", "evidence": "", "reason": ""},
            ],
            "selected_path": "",
            "selected_writeup": "",
            "evidence_refs": [],
            "template_gap": "",
            "open_question": "",
        }
        for slot_info in template_slots(snapshot)
    ]


def emit_json_scaffold(snapshot: RuntimeSnapshot, members: list[str] | None = None) -> str:
    step = snapshot.current_step
    if step == 7:
        payload: Any = build_ctx_json_scaffold(snapshot)
    elif step == 8:
        payload = build_task_json_scaffold(snapshot)
    elif step == 9:
        payload = build_exp_json_scaffold(snapshot, members=members)
    elif step == 10:
        payload = build_syn_json_scaffold(snapshot)
    else:
        raise SystemExit(f"步骤 {step} 不支持 emit json scaffold；仅支持步骤 7/8/9/10。")
    return json.dumps(payload, ensure_ascii=False, indent=2)


def emit_scaffold(snapshot: RuntimeSnapshot, members: list[str] | None = None) -> str:
    step = snapshot.current_step
    if step == 7:
        return build_wd_ctx_scaffold(snapshot)
    if step == 8:
        return build_wd_task_scaffold(snapshot)
    if step == 9:
        return build_wd_exp_scaffold(snapshot, members=members)
    if step == 10:
        return build_wd_syn_scaffold(snapshot)
    raise SystemExit(f"步骤 {step} 不支持 emit scaffold；仅支持步骤 7/8/9/10。")
