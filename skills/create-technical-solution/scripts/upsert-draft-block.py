# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""按 block 安全更新 working draft；状态同步仅用于内部兼容场景。"""

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


BLOCK_ORDER = [
    "Template Metadata",
    "Template Slots",
    "WD-CTX",
    "WD-TASK",
]

STEP_FOR_BLOCK = {
    "WD-CTX": 7,
    "WD-TASK": 8,
    "WD-SYN": 10,
    "WD-SYN-LIGHT": 10,
}

FORBIDDEN_BODY_HEADINGS = {
    "Template Metadata",
    "Template Slots",
    "WD-CTX",
    "WD-TASK",
    "WD-SYN",
    "WD-SYN-LIGHT",
}


def extract_blocks(markdown: str) -> tuple[list[str], dict[str, str]]:
    title_match = re.match(r"^(# .+?)\n+", markdown, re.DOTALL)
    title = title_match.group(1) if title_match else "# Working Draft"
    blocks: dict[str, str] = {}
    headings = list(re.finditer(r"^##\s+(.+?)\s*$", markdown, re.MULTILINE))
    for index, match in enumerate(headings):
        name = match.group(1).strip()
        start = match.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
        body = markdown[start:end].strip("\n")
        blocks[name] = body
    return [title], blocks


def compose_markdown(title_lines: list[str], blocks: dict[str, str]) -> str:
    lines = [title_lines[0], ""]
    emitted = set()
    ordered_names = [name for name in BLOCK_ORDER if name in blocks]
    ordered_names.extend(sorted(name for name in blocks if name.startswith("WD-EXP-")))
    ordered_names.extend(name for name in ("WD-SYN", "WD-SYN-LIGHT") if name in blocks)
    ordered_names.extend(name for name in blocks if name not in emitted and name not in ordered_names)
    for name in ordered_names:
        emitted.add(name)
        lines.append(f"## {name}")
        lines.append("")
        body = blocks[name].strip("\n")
        if body:
            lines.append(body)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def count_items(block: str, prefix: str) -> int:
    return len(re.findall(rf"^\s*###\s+{re.escape(prefix)}", block, re.MULTILINE))


def count_slot_sections(block: str) -> int:
    return len(re.findall(r"^\s*###\s+", block, re.MULTILINE))


def validate_block_body(block_name: str, content: str) -> None:
    body = content.strip()
    if not body:
        raise SystemExit(f"{block_name} body 不能为空。content-file 只能包含区块体内容。")
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^#\s+Working Draft\b", stripped):
            raise SystemExit(f"{block_name} body 不得包含 Working Draft 标题。content-file 只能包含区块体内容。")
        match = re.match(r"^##\s+(.+?)\s*$", stripped)
        if match:
            nested_heading = match.group(1).strip()
            if nested_heading in FORBIDDEN_BODY_HEADINGS or nested_heading.startswith("WD-EXP-"):
                raise SystemExit(
                    f"{block_name} body 不得包含区块标题 {nested_heading}."
                    " content-file 只能包含区块体内容。"
                )


def block_step(block_name: str) -> int | None:
    if block_name.startswith("WD-EXP-"):
        return 9
    return STEP_FOR_BLOCK.get(block_name)


def read_block_body(content_path: Path) -> str:
    block_content = content_path.read_text(encoding="utf-8").strip()
    return block_content


def upsert_blocks_into_markdown(markdown: str, updates: list[tuple[str, str]]) -> str:
    title_lines, blocks = extract_blocks(markdown)
    for block_name, block_content in updates:
        if block_step(block_name) is None:
            raise SystemExit(f"不支持的 block: {block_name}")
        validate_block_body(block_name, block_content)
        blocks[block_name] = block_content
    return compose_markdown(title_lines, blocks)


def render_updated_markdown(
    *,
    working_draft_path: Path,
    block_updates: list[tuple[str, str]],
) -> str:
    if not working_draft_path.exists():
        raise SystemExit(f"working draft 不存在: {working_draft_path}")
    return upsert_blocks_into_markdown(
        working_draft_path.read_text(encoding="utf-8"),
        block_updates,
    )


def write_blocks(
    *,
    working_draft_path: Path,
    block_updates: list[tuple[str, str]],
) -> dict[str, Any]:
    updated_markdown = render_updated_markdown(
        working_draft_path=working_draft_path,
        block_updates=block_updates,
    )
    working_draft_path.write_text(updated_markdown, encoding="utf-8")
    return {
        "working_draft_path": str(working_draft_path),
        "blocks": [name for name, _content in block_updates],
    }


def write_block(
    *,
    working_draft_path: Path,
    block_name: str,
    content_path: Path,
) -> dict[str, Any]:
    return write_blocks(
        working_draft_path=working_draft_path,
        block_updates=[(block_name, read_block_body(content_path))],
    )


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
        state["can_enter_step_8"] = state.get("flow_tier") != "light"
        state["can_enter_step_10"] = state.get("flow_tier") == "light"
        state["current_step"] = 8 if state.get("flow_tier") != "light" else 10
        if 7 not in completed:
            completed.append(7)
    elif block_name == "WD-TASK":
        checkpoints["step-8"] = {
            "summary": summary,
            "wd_task_written": True,
            "task_slot_count": 0,
            "completed_at": iso_now(),
        }
        if state.get("flow_tier") == "full":
            state["can_enter_step_9"] = True
            state["can_enter_step_10"] = False
            state["current_step"] = 9
        else:
            state["can_enter_step_10"] = True
            state["current_step"] = 10
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
    elif block_name in {"WD-SYN", "WD-SYN-LIGHT"}:
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
    elif block_name in {"WD-SYN", "WD-SYN-LIGHT"}:
        checkpoints["step-10"]["syn_slot_count"] = count_slot_sections(content)


def sync_state_for_blocks(state: dict[str, Any], block_updates: list[tuple[str, str]], summary: str) -> None:
    for block_name, _content in block_updates:
        sync_state_for_block(state, block_name, summary)
    for block_name, content in block_updates:
        update_counts(state, block_name, content)


def apply_block_updates_to_state(state: dict[str, Any], block_updates: list[tuple[str, str]], summary: str) -> None:
    sync_state_for_blocks(state, block_updates, summary)


def upsert_blocks_with_sync(
    *,
    working_draft_path: Path,
    state_path: Path,
    block_updates: list[tuple[str, Path]],
    summary: str,
    require_receipt_step: int,
) -> dict[str, Any]:
    state = load_yaml(state_path)
    require_receipt(state, expected_step=require_receipt_step)
    normalized_updates: list[tuple[str, str]] = []
    for block_name, content_path in block_updates:
        if block_step(block_name) is None:
            raise SystemExit(f"不支持的 block: {block_name}")
        normalized_updates.append((block_name, read_block_body(content_path)))

    write_payload = write_blocks(
        working_draft_path=working_draft_path,
        block_updates=normalized_updates,
    )
    sync_state_for_blocks(state, normalized_updates, summary)
    refresh_receipt(state)
    dump_yaml(state_path, state)
    return {
        **write_payload,
        "block": normalized_updates[0][0] if len(normalized_updates) == 1 else None,
        "current_step": state.get("current_step"),
        "gate_receipt_step": state["gate_receipt"]["step"],
    }


def upsert_block(
    *,
    working_draft_path: Path,
    block_name: str,
    content_path: Path,
    state_path: Path | None = None,
    summary: str | None = None,
    require_receipt_step: int | None = None,
    sync_state: bool = False,
) -> dict[str, Any]:
    if not sync_state:
        return write_block(
            working_draft_path=working_draft_path,
            block_name=block_name,
            content_path=content_path,
        )
    if state_path is None or summary is None or require_receipt_step is None:
        raise SystemExit("sync_state=true 时必须提供 --state、--summary、--require-receipt-step。")
    return upsert_blocks_with_sync(
        working_draft_path=working_draft_path,
        state_path=state_path,
        block_updates=[(block_name, content_path)],
        summary=summary,
        require_receipt_step=require_receipt_step,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="按 block 安全更新 working draft")
    parser.add_argument("--working-draft", required=True, help="working draft 路径")
    parser.add_argument("--state", help="状态文件路径；仅 --sync-state 时需要")
    parser.add_argument("--block", required=True, help="待更新的 WD block")
    parser.add_argument("--content-file", required=True, help="block 内容文件")
    parser.add_argument("--summary", help="对应步骤摘要；仅 --sync-state 时需要")
    parser.add_argument("--require-receipt-step", type=int, help="要求 gate_receipt.step 与该值一致；仅 --sync-state 时需要")
    parser.add_argument("--sync-state", action="store_true", help="内部兼容模式：同时同步状态")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    payload = upsert_block(
        working_draft_path=Path(args.working_draft).resolve(),
        block_name=args.block,
        content_path=Path(args.content_file).resolve(),
        summary=args.summary,
        require_receipt_step=args.require_receipt_step,
        state_path=Path(args.state).resolve() if args.state else None,
        sync_state=args.sync_state,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["working_draft_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
