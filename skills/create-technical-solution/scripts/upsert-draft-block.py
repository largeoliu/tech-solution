# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""按 block 安全更新 working draft 目录；状态同步仅用于内部兼容场景。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import dump_yaml, iso_now, load_yaml, refresh_receipt, require_receipt

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
    refresh_receipt(state)
    dump_yaml(state_path, state)
    return {
        "working_dir": str(working_dir),
        "blocks": written,
        "current_step": state.get("current_step"),
        "gate_receipt_step": state["gate_receipt"]["step"],
    }


def main() -> int:
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
