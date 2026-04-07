# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""提取当前模板快照，并按快照生成 working draft 骨架。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def normalize_text(value: str) -> str:
    return " ".join(str(value).replace("\xa0", " ").split())


def extract_slot_headings(markdown: str, slot_level: int | None = None) -> list[dict[str, Any]]:
    import re

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
        slots.append(
            {
                "slot": f"SLOT-{slot_index:02d}",
                "level": level,
                "title": title,
                "normalized_title": normalize_text(title),
            }
        )
        slot_index += 1
    return slots


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_working_draft(snapshot: dict[str, Any], slug: str) -> str:
    lines = [
        f"# Working Draft: {slug}",
        "",
        "## Template Snapshot",
        "",
        f"- template_path: {snapshot['path']}",
        f"- slot_level: H{snapshot['slot_level']}" if snapshot.get("slot_level") else "- slot_level: unknown",
        f"- captured_at: {snapshot['captured_at']}",
        "",
        "## Template Slots",
        "",
    ]
    for item in snapshot["headings"]:
        lines.append(f"- {item['slot']}: {item['title']}")
    lines.extend(
        [
            "",
            "## WD-CTX",
            "",
            "_待填充_",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"状态文件必须是 YAML 对象: {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="提取技术方案模板快照并生成 working draft 骨架")
    parser.add_argument("--template", required=True, help="模板路径")
    parser.add_argument("--slug", required=True, help="方案 slug")
    parser.add_argument("--working-draft", required=True, help="working draft 路径")
    parser.add_argument("--state", help="状态文件路径；若提供则同步写入 template_snapshot/template_slots")
    parser.add_argument("--write", action="store_true", help="实际写入 working draft / state；默认仅输出 JSON")
    args = parser.parse_args()

    template_path = Path(args.template).resolve()
    if not template_path.exists():
        print(f"模板文件不存在: {template_path}", file=sys.stderr)
        return 1

    headings = extract_slot_headings(template_path.read_text(encoding="utf-8"))
    if not headings:
        print(f"模板未提取到任何槽位: {template_path}", file=sys.stderr)
        return 1

    snapshot = {
        "path": str(template_path),
        "slot_level": headings[0]["level"],
        "headings": headings,
        "captured_at": iso_now(),
    }
    working_draft = Path(args.working_draft).resolve()
    draft_text = build_working_draft(snapshot, args.slug)

    output = {
        "template_snapshot": snapshot,
        "template_slots": [item["title"] for item in headings],
        "working_draft_path": str(working_draft),
    }

    if args.write:
        working_draft.parent.mkdir(parents=True, exist_ok=True)
        working_draft.write_text(draft_text, encoding="utf-8")
        if args.state:
            state_path = Path(args.state).resolve()
            state = load_yaml(state_path)
            state["solution_root"] = str(working_draft.parent.parent.relative_to(state_path.parent.parent.parent.parent))
            state["working_draft_path"] = str(working_draft.relative_to(state_path.parent.parent.parent.parent))
            state["template_snapshot"] = snapshot
            state["template_slots"] = output["template_slots"]
            checkpoints = state.setdefault("checkpoints", {})
            if not isinstance(checkpoints, dict):
                checkpoints = {}
                state["checkpoints"] = checkpoints
            checkpoints["step-3"] = {
                "summary": f"模板快照已提取。槽位数: {len(headings)}；层级: H{headings[0]['level']}",
                "template_loaded": True,
                "slot_count": len(headings),
                "slot_level": f"H{headings[0]['level']}",
            }
            dump_yaml(state_path, state)

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
