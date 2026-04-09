# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""步骤 11 的唯一合法成稿路径。"""

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


def count_absorbed_slots(markdown: str) -> int:
    return len(re.findall(r"^(#{2,6})\s+.+$", markdown, flags=re.MULTILINE))


def normalize_text(value: str) -> str:
    return " ".join(str(value).replace("\xa0", " ").split())


def extract_slot_headings(markdown: str) -> list[str]:
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
    counts: dict[int, int] = {}
    for level, _title in headings:
        counts[level] = counts.get(level, 0) + 1
    slot_level = max(counts.items(), key=lambda item: (item[1], item[0]))[0]
    return [title for level, title in headings if level == slot_level]


def extract_named_block(markdown: str, heading: str) -> str:
    pattern = re.compile(rf"^\s*##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^\s*##\s+.+$", markdown[start:], re.MULTILINE)
    end = start + next_match.start() if next_match else len(markdown)
    return markdown[start:end].strip()


def normalize_syn_heading(title: str) -> str:
    normalized = normalize_text(title)
    return re.sub(r"^槽位：\s*", "", normalized)


def extract_syn_sections(block: str) -> dict[str, str]:
    headings = list(re.finditer(r"^\s*###\s+(.+?)\s*$", block, re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(headings):
        title = normalize_syn_heading(match.group(1))
        start = match.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(block)
        body = block[start:end].strip()
        sections[title] = body
    return sections


def render_from_draft(state_path: Path) -> str:
    state = load_yaml(state_path)
    draft_value = str(state.get("working_draft_path") or "").strip()
    if not draft_value:
        raise SystemExit("working_draft_path 为空，无法从 draft 渲染最终文档。")
    repo_root = state_path.parent.parent.parent.parent
    draft_path = Path(draft_value)
    if not draft_path.is_absolute():
        draft_path = (repo_root / draft_value).resolve()
    if not draft_path.exists():
        raise SystemExit(f"working draft 不存在: {draft_path}")

    template_value = str(state.get("template_path") or "").strip()
    template_path = Path(template_value)
    if not template_path.is_absolute():
        template_path = (repo_root / template_value).resolve()
    if not template_path.exists():
        raise SystemExit(f"模板不存在: {template_path}")

    draft_content = draft_path.read_text(encoding="utf-8")
    syn_block_name = "WD-SYN"
    syn_block = extract_named_block(draft_content, syn_block_name)
    if not syn_block:
        raise SystemExit(f"{syn_block_name} 区块不存在，无法渲染最终文档。")

    sections = extract_syn_sections(syn_block)
    template_content = template_path.read_text(encoding="utf-8")
    expected_slots = extract_slot_headings(template_content)
    lines: list[str] = []
    for raw_line in template_content.splitlines():
        lines.append(raw_line)
        match = re.match(r"^(#{2,6})\s+(.+?)\s*$", raw_line)
        if not match:
            continue
        title = normalize_text(match.group(2))
        if title not in expected_slots:
            continue
        body = sections.get(title, "").strip()
        if body:
            lines.append("")
            lines.extend(body.splitlines())
    return "\n".join(lines).rstrip() + "\n"


def render_final_document(
    *,
    state_path: Path,
    content_path: Path | None,
    summary: str,
) -> dict[str, Any]:
    state = load_yaml(state_path)
    require_receipt(state, expected_step=11)
    final_document_value = str(state.get("final_document_path") or "").strip()
    if not final_document_value:
        raise SystemExit("final_document_path 为空，必须先在步骤 1 生成最终文档路径。")

    repo_root = state_path.parent.parent.parent.parent
    final_document_path = (repo_root / final_document_value).resolve()
    allowed_root = (repo_root / str(state.get("solution_root") or ".architecture/technical-solutions")).resolve()
    if allowed_root not in final_document_path.parents:
        raise SystemExit(f"final_document_path 必须位于 {allowed_root} 下，当前为 {final_document_path}")

    if content_path is not None:
        content = content_path.read_text(encoding="utf-8")
    else:
        content = render_from_draft(state_path)
    final_document_path.parent.mkdir(parents=True, exist_ok=True)
    final_document_path.write_text(content, encoding="utf-8")

    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints
    checkpoints["step-11"] = {
        "summary": summary,
        "final_document_written": True,
        "absorbed_slot_count": count_absorbed_slots(content),
        "rendered_via_script": True,
        "completed_at": iso_now(),
    }
    state["can_enter_step_12"] = True
    completed = state.setdefault("completed_steps", [])
    if not isinstance(completed, list):
        completed = []
        state["completed_steps"] = completed
    if 11 not in completed:
        completed.append(11)
        completed.sort()
    state["current_step"] = 12
    refresh_receipt(state, default_step=12)
    dump_yaml(state_path, state)
    return {
        "final_document_path": str(final_document_path),
        "absorbed_slot_count": checkpoints["step-11"]["absorbed_slot_count"],
        "current_step": state["current_step"],
        "gate_receipt_step": state["gate_receipt"]["step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="步骤 11 的唯一合法成稿路径")
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--summary", required=True, help="写入 checkpoints.step-11.summary 的摘要")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    args = parser.parse_args()

    payload = render_final_document(
        state_path=Path(args.state).resolve(),
        content_path=None,
        summary=args.summary,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["final_document_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
