# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""显式记录被跳过的步骤，并保证不会混入 completed_steps。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"状态文件不存在: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"状态文件必须是 YAML 对象: {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def mark_step_skipped(*, state_path: Path, step: int, summary: str, reason: str, next_step: int | None) -> dict[str, Any]:
    state = load_yaml(state_path)
    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints
    checkpoint = checkpoints.setdefault(f"step-{step}", {})
    if not isinstance(checkpoint, dict):
        checkpoint = {}
        checkpoints[f"step-{step}"] = checkpoint
    checkpoint.update({"summary": summary, "skipped": True, "reason": reason, "completed_at": iso_now()})

    skipped_steps = state.setdefault("skipped_steps", [])
    if not isinstance(skipped_steps, list):
        skipped_steps = []
        state["skipped_steps"] = skipped_steps
    if step not in skipped_steps:
        skipped_steps.append(step)
        skipped_steps.sort()

    completed_steps = state.setdefault("completed_steps", [])
    if not isinstance(completed_steps, list):
        completed_steps = []
        state["completed_steps"] = completed_steps
    state["completed_steps"] = [item for item in completed_steps if item != step]

    if next_step is not None:
        state["current_step"] = next_step
    state["updated_at"] = iso_now()
    dump_yaml(state_path, state)
    return {
        "skipped_step": step,
        "skipped_steps": state["skipped_steps"],
        "completed_steps": state["completed_steps"],
        "current_step": state.get("current_step"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="显式记录被跳过的步骤")
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--step", type=int, required=True, help="被跳过的步骤号")
    parser.add_argument("--summary", required=True, help="写入 checkpoints.step-N.summary 的摘要")
    parser.add_argument("--reason", required=True, help="跳过原因")
    parser.add_argument("--next-step", type=int, help="设置 current_step")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    args = parser.parse_args()

    payload = mark_step_skipped(
        state_path=Path(args.state).resolve(),
        step=args.step,
        summary=args.summary,
        reason=args.reason,
        next_step=args.next_step,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"已显式跳过 step-{payload['skipped_step']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
