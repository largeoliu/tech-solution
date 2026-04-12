# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""按 block 安全更新 working draft 目录；状态同步仅用于内部兼容场景。"""

from __future__ import annotations

import os
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import dump_yaml, iso_now, load_yaml, refresh_receipt, repo_root_from_state_path, require_receipt

BLOCK_MARKER_RE = re.compile(r"^---BLOCK:(.+)$", re.MULTILINE)


def parse_stdin_blocks(raw: str, step: int) -> list[tuple[str, str]]:
    raw = raw.strip()
    if not raw:
        return []
    markers = list(BLOCK_MARKER_RE.finditer(raw))
    if not markers:
        default_block = _default_block_for_step(step)
        if default_block:
            return [(default_block, raw)]
        raise SystemExit(f"步骤 {step} 无法确定默认 block 名称，请使用 ---BLOCK: 标记。")
    blocks: list[tuple[str, str]] = []
    for i, match in enumerate(markers):
        block_name = match.group(1).strip()
        start = match.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(raw)
        body = raw[start:end].strip("\n")
        blocks.append((block_name, body))
    return blocks


def _default_block_for_step(step: int) -> str | None:
    return {7: "WD-CTX", 8: "WD-TASK"}.get(step)


def render_ctx_payload(entries: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for index, entry in enumerate(entries, start=1):
        ctx_id = str(entry.get("id") or f"CTX-{index:02d}").strip() or f"CTX-{index:02d}"
        source = str(entry.get("source") or "").strip()
        conclusion = str(entry.get("conclusion") or "").strip()
        confidence = str(entry.get("confidence") or "").strip()
        applicable_slots = entry.get("applicable_slots") or []
        if not isinstance(applicable_slots, list):
            raise ValueError("WD-CTX applicable_slots 必须是数组。")
        slots_text = ", ".join(str(item).strip() for item in applicable_slots if str(item).strip())
        lines.extend(
            [
                f"### {ctx_id}",
                f"来源: {source}",
                f"结论或约束: {conclusion}",
                f"适用槽位: {slots_text}",
                f"可信度或缺口: {confidence}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def render_task_payload(entries: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for entry in entries:
        slot = str(entry.get("slot") or "").strip()
        required_ctx = entry.get("required_ctx") or []
        if not slot:
            raise ValueError("WD-TASK slot 不能为空。")
        if not isinstance(required_ctx, list):
            raise ValueError("WD-TASK required_ctx 必须是数组。")
        ctx_text = ", ".join(str(item).strip() for item in required_ctx if str(item).strip())
        participating_experts = entry.get("participating_experts") or []
        if not isinstance(participating_experts, list):
            raise ValueError("WD-TASK participating_experts 必须是数组。")
        experts_items = [str(item).strip() for item in participating_experts if str(item).strip()]
        expert_questions = entry.get("expert_questions") or []
        if not isinstance(expert_questions, list):
            raise ValueError("WD-TASK expert_questions 必须是数组。")
        suggested_slot = str(entry.get("suggested_slot") or slot).strip()
        expression_requirements = str(entry.get("expression_requirements") or "").strip()
        blockers = str(entry.get("blockers") or "无").strip()
        question_lines = [f"  - {str(item).strip()}" for item in expert_questions if str(item).strip()] or ["  - 无"]
        lines.extend(
            [
                f"### {slot}",
                f"- 槽位标识: {slot}",
                f"- 必须消费的共享上下文: {ctx_text}",
                f"- 参与专家: {', '.join(experts_items)}" if experts_items else "- 参与专家:",
                "- 每位专家必答问题:",
                *question_lines,
                f"- 建议落位槽位: {suggested_slot}",
                f"- 落位表达要求: {expression_requirements}" if expression_requirements else "- 落位表达要求: <只写当前模板槽位需要的最小闭环>",
                f"- 缺口或阻塞项: {blockers}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def _slot_id_for_title(slots: list[dict[str, Any]], title: str) -> str:
    normalized = title.strip()
    for slot in slots:
        if str(slot.get("title") or "").strip() == normalized:
            return str(slot.get("slot") or "").strip()
    raise ValueError(f"未找到槽位标题对应的 state.slots 记录: {title}")


def render_exp_payload(entries: list[dict[str, Any]], slots: list[dict[str, Any]]) -> list[tuple[str, str]]:
    rendered: list[tuple[str, str]] = []
    for entry in entries:
        slot_title = str(entry.get("slot") or "").strip()
        if not slot_title:
            raise ValueError("WD-EXP payload 缺少 slot。")
        slot_id = _slot_id_for_title(slots, slot_title)
        evidence_refs = entry.get("evidence_refs") or []
        open_questions = entry.get("open_questions") or []
        if not isinstance(evidence_refs, list) or not isinstance(open_questions, list):
            raise ValueError("WD-EXP evidence_refs/open_questions 必须是数组。")
        body = "\n".join(
            [
                "### 参与槽位",
                f"- {slot_title}",
                "",
                "### 决策类型",
                f"- {str(entry.get('decision_type') or '').strip()}",
                "",
                "### 核心理由",
                f"- {str(entry.get('rationale') or '').strip()}",
                "",
                "### 关键证据引用",
                *[f"- {str(item).strip()}" for item in evidence_refs if str(item).strip()],
                "",
                "### 未决点",
                *([f"- {str(item).strip()}" for item in open_questions if str(item).strip()] or ["- 无"]),
            ]
        ).strip()
        rendered.append((f"WD-EXP-{slot_id}", body))
    return rendered


def render_syn_payload(entries: list[dict[str, Any]], slots: list[dict[str, Any]]) -> list[tuple[str, str]]:
    rendered: list[tuple[str, str]] = []
    for entry in entries:
        slot_title = str(entry.get("slot") or "").strip()
        if not slot_title:
            raise ValueError("WD-SYN payload 缺少 slot。")
        slot_id = _slot_id_for_title(slots, slot_title)
        comparisons = entry.get("comparisons") or []
        evidence_refs = entry.get("evidence_refs") or []
        if not isinstance(comparisons, list) or not isinstance(evidence_refs, list):
            raise ValueError("WD-SYN comparisons/evidence_refs 必须是数组。")
        table_lines = [
            "| 路径 | 可行性 | 关键证据 | 选择理由 |",
            "|------|--------|----------|----------|",
        ]
        for item in comparisons:
            if not isinstance(item, dict):
                raise ValueError("WD-SYN comparisons 数组元素必须是对象。")
            table_lines.append(
                "| {path} | {feasibility} | {evidence} | {reason} |".format(
                    path=str(item.get("path") or "").strip(),
                    feasibility=str(item.get("feasibility") or "").strip(),
                    evidence=str(item.get("evidence") or "").strip(),
                    reason=str(item.get("reason") or "").strip(),
                )
            )
        body = "\n".join(
            [
                f"### 槽位：{slot_title}",
                "#### 目标能力",
                f"- {str(entry.get('target_capability') or '').strip()}",
                "#### 候选方案对比",
                *table_lines,
                "#### 选定路径",
                f"- 路径: {str(entry.get('selected_path') or '').strip()}",
                f"- 选定写法: {str(entry.get('selected_writeup') or '').strip()}",
                f"- 关键证据引用: {', '.join(str(item).strip() for item in evidence_refs if str(item).strip())}",
                f"- 建议落位槽位: {slot_title}",
                f"- 模板承载缺口: {str(entry.get('template_gap') or '无').strip()}",
                f"- 未决问题: {str(entry.get('open_question') or '无').strip()}",
            ]
        ).strip()
        rendered.append((f"WD-SYN-{slot_id}", body))
    return rendered


def validate_body(block_name: str, content: str) -> None:
    body = content.strip()
    if not body:
        raise SystemExit(f"{block_name} body 不能为空。")
    if re.search(r"^\s*##\s+WD-", body, re.MULTILINE):
        raise SystemExit(f"{block_name} body 不得包含 ## WD-* 标题。")


def resolve_file_for_block(working_dir: Path, block_name: str, slots: list[dict[str, Any]]) -> Path:
    if block_name == "WD-CTX":
        return working_dir / "ctx.md"
    if block_name == "WD-TASK":
        return working_dir / "task.md"
    exp_match = re.match(r"^WD-EXP-(SLOT-\d+)$", block_name)
    if exp_match:
        slot_id = exp_match.group(1)
        valid_ids = {s.get("slot", "") for s in slots}
        if valid_ids and slot_id not in valid_ids:
            raise SystemExit(f"block {block_name} 的 slot 不在 state.slots 中。")
        return working_dir / "slots" / slot_id / "experts.md"
    syn_match = re.match(r"^WD-SYN-(SLOT-\d+)$", block_name)
    if syn_match:
        slot_id = syn_match.group(1)
        valid_ids = {s.get("slot", "") for s in slots}
        if valid_ids and slot_id not in valid_ids:
            raise SystemExit(f"block {block_name} 的 slot 不在 state.slots 中。")
        return working_dir / "slots" / slot_id / "synthesis.md"
    raise SystemExit(f"不支持的 block: {block_name}")


def write_working_draft_file(
    working_dir: Path,
    block_name: str,
    content: str,
    slots: list[dict[str, Any]],
) -> Path:
    validate_body(block_name, content)
    target = resolve_file_for_block(working_dir, block_name, slots)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    return target


def count_items(block: str, prefix: str) -> int:
    return len(re.findall(rf"^\s*###\s+{re.escape(prefix)}", block, re.MULTILINE))


def count_slot_sections(block: str) -> int:
    return len(re.findall(r"^\s*###\s+", block, re.MULTILINE))


def sync_state_for_block(state: dict[str, Any], block_name: str, summary: str) -> None:
    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints

    produced = state.setdefault("produced_artifacts", [])
    if not isinstance(produced, list):
        produced = []
        state["produced_artifacts"] = produced
    if block_name not in produced:
        produced.append(block_name)
        produced.sort()

    completed = state.setdefault("completed_steps", [])
    if not isinstance(completed, list):
        completed = []
        state["completed_steps"] = completed

    if block_name == "WD-CTX":
        checkpoints["step-7"] = {
            "summary": summary,
            "wd_ctx_written": True,
            "ctx_count": 0,
            "completed_at": iso_now(),
        }
        state["can_enter_step_8"] = True
        state["can_enter_step_10"] = False
        state["current_step"] = 8
        if 7 not in completed:
            completed.append(7)
    elif block_name == "WD-TASK":
        checkpoints["step-8"] = {
            "summary": summary,
            "wd_task_written": True,
            "task_slot_count": 0,
            "completed_at": iso_now(),
        }
        state["can_enter_step_9"] = True
        state["can_enter_step_10"] = False
        state["current_step"] = 9
        if 8 not in completed:
            completed.append(8)
    elif block_name.startswith("WD-EXP-"):
        checkpoints["step-9"] = {
            "summary": summary,
            "skipped": False,
            "reason": "",
            "wd_exp_count": 0,
            "completed_at": iso_now(),
        }
        state["can_enter_step_10"] = True
        state["current_step"] = 10
        if 9 not in completed:
            completed.append(9)
    elif block_name.startswith("WD-SYN-"):
        checkpoints["step-10"] = {
            "summary": summary,
            "wd_syn_written": True,
            "syn_slot_count": 0,
            "completed_at": iso_now(),
        }
        state["can_enter_step_11"] = True
        state["current_step"] = 11
        if 10 not in completed:
            completed.append(10)
    completed.sort()


def update_counts(state: dict[str, Any], block_name: str, content: str) -> None:
    checkpoints = state.setdefault("checkpoints", {})
    produced = state.get("produced_artifacts", [])
    if block_name == "WD-CTX":
        checkpoints["step-7"]["ctx_count"] = count_items(content, "CTX-")
    elif block_name == "WD-TASK":
        checkpoints["step-8"]["task_slot_count"] = count_slot_sections(content)
    elif block_name.startswith("WD-EXP-"):
        checkpoints["step-9"]["wd_exp_count"] = sum(
            1 for item in produced if isinstance(item, str) and item.startswith("WD-EXP-")
        )
    elif block_name.startswith("WD-SYN-"):
        checkpoints["step-10"]["syn_slot_count"] = sum(
            1 for item in produced if isinstance(item, str) and item.startswith("WD-SYN-")
        )


def sync_artifact_registry(
    state: dict[str, Any],
    state_path: Path,
    working_dir: Path,
    slots: list[dict[str, Any]],
    block_updates: list[tuple[str, str]],
) -> None:
    registry = state.setdefault("artifact_registry", {})
    if not isinstance(registry, dict):
        registry = {}
        state["artifact_registry"] = registry
    repo_root = state_path_to_repo_root(state_path)
    for block_name, _content in block_updates:
        target = resolve_file_for_block(working_dir, block_name, slots)
        if not target.exists():
            continue
        registry[block_name] = {
            "path": target.relative_to(repo_root).as_posix(),
            "content_hash": hashlib.sha256(target.read_bytes()).hexdigest(),
            "written_at": iso_now(),
            "writer": "run-step",
        }


def state_path_to_repo_root(state_path: Path) -> Path:
    return repo_root_from_state_path(state_path)


def sync_state_for_blocks(state: dict[str, Any], block_updates: list[tuple[str, str]], summary: str) -> None:
    for block_name, _content in block_updates:
        sync_state_for_block(state, block_name, summary)
    for block_name, content in block_updates:
        update_counts(state, block_name, content)


def upsert_with_sync(
    *,
    working_dir: Path,
    state_path: Path,
    block_updates: list[tuple[str, str]],
    summary: str,
    require_receipt_step: int,
) -> dict[str, Any]:
    state = load_yaml(state_path)
    require_receipt(state, expected_step=require_receipt_step)
    slots = state.get("slots") or []
    written: list[str] = []
    for block_name, content in block_updates:
        write_working_draft_file(working_dir, block_name, content, slots)
        written.append(block_name)
    sync_state_for_blocks(state, block_updates, summary)
    sync_artifact_registry(state, state_path, working_dir, slots, block_updates)
    refresh_receipt(state)
    dump_yaml(state_path, state)
    return {
        "working_dir": str(working_dir),
        "blocks": written,
        "current_step": state.get("current_step"),
        "gate_receipt_step": state["gate_receipt"]["step"],
    }


def main() -> int:
    if not os.environ.get("__CTS_INTERNAL_CALL"):
        print("❌ 本脚本不可直接调用。请使用 run-step.py --advance / --complete --ticket。", file=sys.stderr)
        sys.exit(1)
    parser = argparse.ArgumentParser(description="按 block 安全更新 working draft 目录")
    parser.add_argument("--working-dir", required=True, help="working draft 目录路径")
    parser.add_argument("--state", help="状态文件路径")
    parser.add_argument("--block", required=True, help="待更新的 WD block")
    parser.add_argument("--content", help="block 内容字符串（或通过 stdin 传入）")
    parser.add_argument("--summary", help="对应步骤摘要")
    parser.add_argument("--require-receipt-step", type=int, help="要求 gate_receipt.step 与该值一致")
    parser.add_argument("--sync-state", action="store_true", help="同时同步状态")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    content = args.content
    if content is None and not sys.stdin.isatty():
        content = sys.stdin.read()
    if not content:
        print("缺少内容：请通过 --content 或 stdin 传入 block 正文。", file=sys.stderr)
        return 1

    working_dir = Path(args.working_dir).resolve()
    state_path = Path(args.state).resolve() if args.state else None

    if args.sync_state:
        if not state_path or not args.summary or args.require_receipt_step is None:
            print("sync_state=true 时必须提供 --state、--summary、--require-receipt-step。", file=sys.stderr)
            return 1
        payload = upsert_with_sync(
            working_dir=working_dir,
            state_path=state_path,
            block_updates=[(args.block, content)],
            summary=args.summary,
            require_receipt_step=args.require_receipt_step,
        )
    else:
        state = load_yaml(state_path) if state_path else {}
        slots = state.get("slots") or []
        target = write_working_draft_file(working_dir, args.block, content, slots)
        payload = {"working_dir": str(working_dir), "block": args.block, "target": str(target)}

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload.get("working_dir", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
