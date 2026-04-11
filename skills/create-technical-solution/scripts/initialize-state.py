# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""初始化步骤 1 的最小状态字段。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import (
    SOLUTION_ROOT,
    dump_yaml,
    final_document_relative_path,
    iso_now,
    load_yaml,
    refresh_receipt,
    working_draft_relative_path,
)


def load_or_create_state(path: Path) -> dict[str, Any]:
    if path.exists():
        return load_yaml(path)
    template_path = Path(__file__).resolve().parents[1] / "templates" / "_template.yaml"
    if not template_path.exists():
        raise SystemExit(f"状态模板不存在: {template_path}")
    state = load_yaml(template_path)
    dump_yaml(path, state, ensure_parent=True)
    return state


def initialize_state(
    *,
    state_path: Path,
    slug: str,
    summary: str,
    next_step: int | None,
) -> dict[str, Any]:
    state = load_or_create_state(state_path)

    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints
    checkpoints["step-1"] = {
        "summary": summary,
        "slug": slug,
        "scope_ready": True,
        "completed_at": iso_now(),
    }
    state["solution_root"] = str(SOLUTION_ROOT)
    state["working_draft_path"] = str(working_draft_relative_path(slug))
    state["final_document_path"] = str(final_document_relative_path(slug))
    state.setdefault("members_path", ".architecture/members.yml")
    state.setdefault("principles_path", ".architecture/principles.md")
    state.setdefault("template_path", ".architecture/templates/technical-solution-template.md")
    pending_questions = state.setdefault("pending_questions", [])
    if not isinstance(pending_questions, list):
        state["pending_questions"] = []
    if next_step is not None:
        state["current_step"] = next_step

    completed = state.setdefault("completed_steps", [])
    if not isinstance(completed, list):
        completed = []
        state["completed_steps"] = completed
    if 1 not in completed:
        completed.append(1)
        completed.sort()

    refresh_receipt(
        state,
        step=int(state.get("current_step") or next_step or 1),
    )
    dump_yaml(state_path, state, ensure_parent=True)
    return {
        "slug": slug,
        "solution_root": state["solution_root"],
        "working_draft_path": state["working_draft_path"],
        "final_document_path": state["final_document_path"],
        "current_step": state.get("current_step"),
        "gate_receipt_step": state["gate_receipt"]["step"],
    }


def main() -> int:
    if not os.environ.get("__CTS_INTERNAL_CALL"):
        print("❌ 本脚本不可直接调用。请使用 run-step.py --advance / --complete --ticket。", file=sys.stderr)
        sys.exit(1)
    parser = argparse.ArgumentParser(description="初始化步骤 1 的最小状态字段")
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--slug", required=True, help="方案 slug")
    parser.add_argument("--summary", required=True, help="写入 checkpoints.step-1.summary 的摘要")
    parser.add_argument("--next-step", type=int, default=2, help="设置 current_step")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    args = parser.parse_args()

    payload = initialize_state(
        state_path=Path(args.state).resolve(),
        slug=args.slug.strip(),
        summary=args.summary,
        next_step=args.next_step,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"步骤 1 已初始化: {payload['final_document_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
