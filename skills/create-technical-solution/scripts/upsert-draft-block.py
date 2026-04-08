# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""按 block 安全更新 working draft，并同步对应步骤状态。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


BLOCK_ORDER = [
    "Template Metadata",
    "Template Slots",
    "WD-CTX",
    "WD-TASK",
    "WD-SYN",
    "WD-SYN-LIGHT",
]

STEP_FOR_BLOCK = {
    "WD-CTX": 7,
    "WD-TASK": 8,
    "WD-SYN": 10,
    "WD-SYN-LIGHT": 10,
}


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"状态文件必须是 YAML 对象: {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def compute_state_fingerprint(state: dict[str, Any]) -> str:
    receipt = state.get("gate_receipt")
    scrubbed = dict(state)
    if isinstance(receipt, dict):
        scrubbed["gate_receipt"] = {
            "step": receipt.get("step", 0),
            "flow_tier": receipt.get("flow_tier", ""),
            "state_fingerprint": "",
            "validated_at": "",
        }
    payload = yaml.safe_dump(scrubbed, allow_unicode=True, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def require_receipt(state: dict[str, Any], expected_step: int) -> None:
    receipt = state.get("gate_receipt")
    if not isinstance(receipt, dict):
        raise SystemExit("缺少 gate_receipt，必须先运行 validate-state.py --write-pass-receipt。")
    if int(receipt.get("step") or 0) != expected_step:
        raise SystemExit(f"gate_receipt.step={receipt.get('step')}，期望 {expected_step}。")
    if str(receipt.get("state_fingerprint") or "") != compute_state_fingerprint(state):
        raise SystemExit("gate_receipt.state_fingerprint 与当前状态不一致，请重新运行 validator。")


def refresh_receipt(state: dict[str, Any]) -> None:
    flow_tier = str(state.get("flow_tier") or "").strip() or "light"
    step = int(state.get("current_step") or 0) or 1
    state["gate_receipt"] = {
        "step": step,
        "flow_tier": flow_tier,
        "state_fingerprint": "",
        "validated_at": "",
    }
    state["gate_receipt"]["state_fingerprint"] = compute_state_fingerprint(state)
    state["gate_receipt"]["validated_at"] = iso_now()


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
        state["can_enter_step_10"] = True
        state["current_step"] = 10
        if 8 not in completed:
            completed.append(8)
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
    if block_name == "WD-CTX":
        checkpoints["step-7"]["ctx_count"] = count_items(content, "CTX-")
    elif block_name == "WD-TASK":
        checkpoints["step-8"]["task_slot_count"] = count_slot_sections(content)
    elif block_name in {"WD-SYN", "WD-SYN-LIGHT"}:
        checkpoints["step-10"]["syn_slot_count"] = count_slot_sections(content)


def upsert_block(
    *,
    working_draft_path: Path,
    state_path: Path,
    block_name: str,
    content_path: Path,
    summary: str,
    require_receipt_step: int,
) -> dict[str, Any]:
    state = load_yaml(state_path)
    require_receipt(state, require_receipt_step)
    if block_name not in STEP_FOR_BLOCK:
        raise SystemExit(f"不支持的 block: {block_name}")
    if not working_draft_path.exists():
        raise SystemExit(f"working draft 不存在: {working_draft_path}")

    title_lines, blocks = extract_blocks(working_draft_path.read_text(encoding="utf-8"))
    block_content = content_path.read_text(encoding="utf-8").strip()
    blocks[block_name] = block_content
    working_draft_path.write_text(compose_markdown(title_lines, blocks), encoding="utf-8")

    sync_state_for_block(state, block_name, summary)
    update_counts(state, block_name, block_content)
    refresh_receipt(state)
    dump_yaml(state_path, state)
    return {
        "working_draft_path": str(working_draft_path),
        "block": block_name,
        "current_step": state.get("current_step"),
        "gate_receipt_step": state["gate_receipt"]["step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="按 block 安全更新 working draft，并同步步骤状态")
    parser.add_argument("--working-draft", required=True, help="working draft 路径")
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--block", choices=sorted(STEP_FOR_BLOCK), required=True, help="待更新的 WD block")
    parser.add_argument("--content-file", required=True, help="block 内容文件")
    parser.add_argument("--summary", required=True, help="对应步骤摘要")
    parser.add_argument("--require-receipt-step", type=int, required=True, help="要求 gate_receipt.step 与该值一致")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    payload = upsert_block(
        working_draft_path=Path(args.working_draft).resolve(),
        state_path=Path(args.state).resolve(),
        block_name=args.block,
        content_path=Path(args.content_file).resolve(),
        summary=args.summary,
        require_receipt_step=args.require_receipt_step,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["working_draft_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
