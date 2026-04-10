# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""提取模板指纹并生成 working draft 骨架。"""

from __future__ import annotations

import os
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import (
    SOLUTION_ROOT,
    dump_yaml,
    iso_now,
    load_yaml,
    repo_root_from_state_path,
    require_receipt,
    working_draft_relative_path,
)


def normalize_text(value: str) -> str:
    return " ".join(str(value).replace("\xa0", " ").split())


def extract_slot_headings(markdown: str, slot_level: int | None = None) -> list[dict[str, Any]]:
    headings: list[tuple[int, str]] = []
    for line in markdown.splitlines():
        match = re.match(r"^(#{2,6})\s+(.+?)\s*$", line)
        if not match:
            continue
        level = len(match.group(1))
        title = normalize_text(match.group(2))
        if title:
            headings.append((level, title))

    if not headings:
        return []

    if slot_level is None:
        counts: dict[int, int] = {}
        for level, _title in headings:
            counts[level] = counts.get(level, 0) + 1
        slot_level = max(counts.items(), key=lambda item: (item[1], item[0]))[0]

    slots: list[dict[str, Any]] = []
    slot_index = 1
    for level, title in headings:
        if level != slot_level:
            continue
        slots.append({"slot": f"SLOT-{slot_index:02d}", "level": level, "title": title})
        slot_index += 1
    return slots


def compute_template_fingerprint(markdown: str, headings: list[dict[str, Any]]) -> str:
    normalized = "\n".join(item["title"] for item in headings)
    payload = f"{normalize_text(markdown)}\n--slot-headings--\n{normalized}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_working_directory(working_dir: Path, headings: list[dict[str, Any]]) -> None:
    working_dir.mkdir(parents=True, exist_ok=True)
    (working_dir / "ctx.md").write_text("", encoding="utf-8")
    (working_dir / "task.md").write_text("", encoding="utf-8")
    slots_dir = working_dir / "slots"
    slots_dir.mkdir(parents=True, exist_ok=True)
    for item in headings:
        slot_id = item["slot"]
        slot_dir = slots_dir / slot_id
        slot_dir.mkdir(parents=True, exist_ok=True)
        (slot_dir / "experts.md").write_text("", encoding="utf-8")
        (slot_dir / "synthesis.md").write_text("", encoding="utf-8")


def update_state(
    *,
    state_path: Path,
    template_path: Path,
    working_draft: Path,
    headings: list[dict[str, Any]],
    fingerprint: str,
) -> None:
    state = load_yaml(state_path)
    require_receipt(
        state,
        expected_step=3,
    )
    slug = str(state.get("checkpoints", {}).get("step-1", {}).get("slug") or "").strip()
    if not slug:
        raise SystemExit("状态缺少 checkpoints.step-1.slug，无法派生 working_draft_path。")
    repo_root = repo_root_from_state_path(state_path)
    expected_working_draft = working_draft_relative_path(slug)
    actual_working_draft = working_draft.relative_to(repo_root)
    if actual_working_draft != expected_working_draft:
        raise SystemExit(
            "working draft 路径不符合协议："
            f"期望 {expected_working_draft}，实际 {actual_working_draft}"
        )
    state["solution_root"] = str(SOLUTION_ROOT)
    state["template_path"] = str(template_path.relative_to(repo_root))
    state["working_draft_path"] = str(expected_working_draft)
    state["slots"] = [{"slot": item["slot"], "title": item["title"]} for item in headings]
    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints
    checkpoints["step-3"] = {
        "summary": f"完成；写入 draft 骨架；slots={len(headings)}；gate: step-4 ready",
        "template_loaded": True,
        "template_fingerprint": fingerprint,
        "slot_count": len(headings),
        "completed_at": iso_now(),
    }
    completed = state.setdefault("completed_steps", [])
    if not isinstance(completed, list):
        completed = []
        state["completed_steps"] = completed
    if 3 not in completed:
        completed.append(3)
        completed.sort()
    state["current_step"] = 4
    from protocol_runtime import refresh_receipt

    refresh_receipt(state, step=4)
    dump_yaml(state_path, state, ensure_parent=True)


def main() -> int:
    if not os.environ.get("__CTS_INTERNAL_CALL"):
        print("❌ 本脚本不可直接调用。请使用 run-step.py --prepare / --complete --ticket。", file=sys.stderr)
        sys.exit(1)
    parser = argparse.ArgumentParser(description="提取模板指纹并生成 working draft 骨架")
    parser.add_argument("--template", required=True, help="模板路径")
    parser.add_argument("--slug", required=True, help="方案 slug")
    parser.add_argument("--working-draft", required=True, help="working draft 目录路径")
    parser.add_argument("--state", help="状态文件路径；若提供则同步写入最小 checkpoint")
    parser.add_argument("--write", action="store_true", help="实际写入 working draft / state")
    args = parser.parse_args()

    template_path = Path(args.template).resolve()
    if not template_path.exists():
        print(f"模板文件不存在: {template_path}", file=sys.stderr)
        return 1

    template_markdown = template_path.read_text(encoding="utf-8")
    headings = extract_slot_headings(template_markdown)
    if not headings:
        print(f"模板未提取到任何槽位: {template_path}", file=sys.stderr)
        return 1

    fingerprint = compute_template_fingerprint(template_markdown, headings)
    working_dir = Path(args.working_draft).resolve()
    output = {
        "template_path": str(template_path),
        "template_fingerprint": fingerprint,
        "slot_count": len(headings),
        "slots": [{"slot": item["slot"], "title": item["title"]} for item in headings],
        "working_draft_path": str(working_dir),
    }

    if args.write:
        create_working_directory(working_dir, headings)
        if args.state:
            update_state(
                state_path=Path(args.state).resolve(),
                template_path=template_path,
                working_draft=working_dir,
                headings=headings,
                fingerprint=fingerprint,
            )

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
