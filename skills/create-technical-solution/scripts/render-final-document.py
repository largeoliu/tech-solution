# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""步骤 11 的唯一合法成稿路径。"""

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

from protocol_runtime import (
    DEFAULT_TEMPLATE_PATH,
    SOLUTION_ROOT,
    default_step_summary,
    decision_truth_digest,
    decision_truth_path,
    dump_yaml,
    final_document_relative_path,
    iso_now,
    load_yaml,
    refresh_receipt,
    repo_root_from_state_path,
    require_receipt,
    resolve_repo_path,
    slug_from_state_path,
    working_draft_relative_path,
)
from quality_checks import intermediate_field_hits, placeholder_hits, repeated_slot_groups


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


WRITEUP_START_RE = re.compile(r"^-\s*选定写法:\s*$", re.MULTILINE)
WRITEUP_INLINE_RE = re.compile(r"^-\s*选定写法:\s*(.+?)\s*$", re.MULTILINE)


def extract_final_writeup(content: str, title: str) -> str:
    match = WRITEUP_START_RE.search(content)
    if match:
        remainder = content[match.end():]
        end_match = re.search(
            r"^-\s*(?:关键证据引用|建议落位槽位|模板承载缺口|未决问题)",
            remainder,
            re.MULTILINE,
        )
        body = remainder[: end_match.start()] if end_match else remainder
        return body.strip()
    match = WRITEUP_INLINE_RE.search(content)
    if match:
        return match.group(1).strip()
    raise SystemExit(
        f"槽位「{title}」的 WD-SYN 缺少可用于最终成稿的 `选定写法`。"
        "请在步骤 10 补齐该字段后重新提交。"
    )


def load_decision_truth(slot_path: Path, title: str) -> dict[str, Any]:
    if not slot_path.exists():
        raise SystemExit(
            f"槽位「{title}」缺少 canonical decision truth: {slot_path}。"
            "请在步骤 10 重新提交结构化决策。"
        )
    try:
        payload = json.loads(slot_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"槽位「{title}」的 canonical decision truth 不是合法 JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"槽位「{title}」的 canonical decision truth 必须是 JSON 对象。")
    if not str(payload.get("selected_writeup") or "").strip():
        raise SystemExit(
            f"槽位「{title}」的 canonical decision truth 缺少可用于最终成稿的 `选定写法`。"
            "请在步骤 10 补齐该字段后重新提交。"
        )
    return payload


def strip_slot_heading(content: str, title: str) -> str:
    lines = content.strip().splitlines()
    if not lines:
        return ""
    expected = f"### 槽位：{title}"
    if normalize_text(lines[0]) != normalize_text(expected):
        return content.strip()
    stripped = "\n".join(lines[1:]).strip()
    return stripped


def render_from_draft(state_path: Path) -> str:
    state = load_yaml(state_path)
    repo_root = repo_root_from_state_path(state_path)
    slug = str(state.get("slug") or "").strip() or slug_from_state_path(state_path)
    draft_path = resolve_repo_path(
        repo_root,
        state.get("working_draft_path"),
        default_relative=working_draft_relative_path(slug),
    )
    if draft_path is None:
        raise SystemExit("working_draft_path 为空，无法从 draft 渲染最终文档。")
    if not draft_path.is_dir():
        raise SystemExit(f"working draft 目录不存在: {draft_path}")

    template_path = resolve_repo_path(
        repo_root,
        state.get("template_path"),
        default_relative=DEFAULT_TEMPLATE_PATH,
    )
    if template_path is None:
        raise SystemExit("template_path 为空，无法渲染最终文档。")
    if not template_path.exists():
        raise SystemExit(f"模板不存在: {template_path}")

    slots = state.get("slots") or []
    sections: dict[str, str] = {}
    for slot_info in slots:
        slot_id = slot_info.get("slot", "")
        title = slot_info.get("title", "")
        truth = load_decision_truth(decision_truth_path(draft_path, slot_id), title)
        sections[title] = str(truth.get("selected_writeup") or "").strip()

    template_content = template_path.read_text(encoding="utf-8")
    expected_slots = extract_slot_headings(template_content)
    slot_levels: dict[str, int] = {}
    for line in template_content.splitlines():
        m = re.match(r"^(#{2,6})\s+(.+?)\s*$", line)
        if m:
            t = normalize_text(m.group(2))
            if t in expected_slots:
                slot_levels[t] = len(m.group(1))
    lines: list[str] = []
    skip_until_level: int | None = None
    for raw_line in template_content.splitlines():
        heading_match = re.match(r"^(#{2,6})\s+(.+?)\s*$", raw_line)
        if heading_match:
            level = len(heading_match.group(1))
            title = normalize_text(heading_match.group(2))
            if title in expected_slots:
                lines.append(raw_line)
                body = sections.get(title, "").strip()
                if body:
                    lines.append("")
                    lines.extend(body.splitlines())
                skip_until_level = slot_levels.get(title)
                continue
            if level <= (skip_until_level or 99):
                skip_until_level = None
        if skip_until_level is not None:
            continue
        lines.append(raw_line)
    return "\n".join(lines).rstrip() + "\n"


def build_render_receipt(*, state: dict[str, Any], draft_path: Path, repo_root: Path) -> dict[str, Any]:
    slots_receipt: list[dict[str, Any]] = []
    for slot_info in state.get("slots") or []:
        slot_id = str(slot_info.get("slot") or "").strip()
        title = str(slot_info.get("title") or "").strip()
        if not slot_id or not title:
            continue
        truth_path = decision_truth_path(draft_path, slot_id)
        slots_receipt.append(
            {
                "slot": slot_id,
                "title": title,
                "decision_artifact": f"WD-SYN-{slot_id}",
                "decision_path": truth_path.relative_to(repo_root).as_posix(),
                "decision_hash": decision_truth_digest(draft_path, slot_id),
            }
        )
    return {
        "mode": "decision_truth",
        "slots": slots_receipt,
    }


def render_final_document(
    *,
    state_path: Path,
    content_path: Path | None,
    summary: str | None,
) -> dict[str, Any]:
    state = load_yaml(state_path)
    require_receipt(state, expected_step=11)
    repo_root = repo_root_from_state_path(state_path)
    slug = str(state.get("slug") or "").strip() or slug_from_state_path(state_path)
    final_document_path = resolve_repo_path(
        repo_root,
        state.get("final_document_path"),
        default_relative=final_document_relative_path(slug),
    )
    if final_document_path is None:
        raise SystemExit("final_document_path 为空，必须先在步骤 1 生成最终文档路径。")
    allowed_root = resolve_repo_path(
        repo_root,
        state.get("solution_root"),
        default_relative=SOLUTION_ROOT,
    )
    if allowed_root is None:
        raise SystemExit("solution_root 为空，无法校验最终文档目录。")
    if allowed_root not in final_document_path.parents:
        raise SystemExit(f"final_document_path 必须位于 {allowed_root} 下，当前为 {final_document_path}")

    if content_path is not None:
        content = content_path.read_text(encoding="utf-8")
    else:
        content = render_from_draft(state_path)

    placeholder_findings = placeholder_hits(content)
    if placeholder_findings:
        raise SystemExit(f"最终文档仍含占位内容: {', '.join(placeholder_findings)}")

    intermediate_findings = intermediate_field_hits(content)
    if intermediate_findings:
        raise SystemExit(f"最终文档含有中间产物字段，应只保留正式写法: {', '.join(intermediate_findings)}")

    draft_path = resolve_repo_path(
        repo_root,
        state.get("working_draft_path"),
        default_relative=working_draft_relative_path(slug),
    )
    render_receipt: dict[str, Any] = {"mode": "decision_truth", "slots": []}
    if draft_path and draft_path.is_dir():
        render_receipt = build_render_receipt(
            state=state,
            draft_path=draft_path,
            repo_root=repo_root,
        )
        slot_blocks: dict[str, str] = {}
        for slot_info in state.get("slots") or []:
            slot_id = slot_info.get("slot", "")
            title = slot_info.get("title", "")
            syn_path = draft_path / "slots" / slot_id / "synthesis.md"
            if title and syn_path.exists():
                slot_blocks[title] = syn_path.read_text(encoding="utf-8")
        repeated_groups = repeated_slot_groups(slot_blocks)
        if repeated_groups:
            raise SystemExit("WD-SYN-SLOT-* 内容过于相似，拒绝生成最终文档。")

    final_document_path.parent.mkdir(parents=True, exist_ok=True)
    final_document_path.write_text(content, encoding="utf-8")

    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints
    checkpoints["step-11"] = {
        "summary": "",
        "final_document_written": True,
        "absorbed_slot_count": count_absorbed_slots(content),
        "rendered_via_script": True,
        "render_receipt": {
            **render_receipt,
            "final_document_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        },
        "completed_at": iso_now(),
    }
    checkpoints["step-11"]["summary"] = str(summary or "").strip() or default_step_summary(
        11,
        absorbed_slot_count=checkpoints["step-11"]["absorbed_slot_count"],
    )
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
    if not os.environ.get("__CTS_INTERNAL_CALL"):
        print("❌ 本脚本不可直接调用。请使用 run-step.py --advance / --complete --ticket。", file=sys.stderr)
        sys.exit(1)
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
