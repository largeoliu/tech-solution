# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""以原子方式推进 create-technical-solution 的状态文件。"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"状态文件必须是 YAML 对象: {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def parse_key_value(raw: list[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for item in raw:
        if "=" not in item:
            raise SystemExit(f"无效键值对: {item}")
        key, value = item.split("=", 1)
        lowered = value.lower()
        if lowered == "true":
            parsed: Any = True
        elif lowered == "false":
            parsed = False
        else:
            parsed = value
        values[key] = parsed
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="推进状态文件中的步骤和 checkpoint")
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--step", type=int, required=True, help="当前完成的步骤号")
    parser.add_argument("--next-step", type=int, help="推进后的 current_step")
    parser.add_argument("--summary", required=True, help="写入 checkpoints.step-N.summary")
    parser.add_argument("--field", action="append", default=[], help="写入 checkpoints.step-N 的键值，格式 key=value")
    parser.add_argument("--set", dest="state_fields", action="append", default=[], help="写入顶层状态字段，格式 key=value")
    parser.add_argument("--append-completed", action="store_true", help="将当前 step 追加到 completed_steps")
    args = parser.parse_args()

    path = Path(args.state).resolve()
    state = load_yaml(path)
    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints
    checkpoint = {"summary": args.summary}
    checkpoint.update(parse_key_value(args.field))
    checkpoints[f"step-{args.step}"] = checkpoint

    if args.append_completed:
        completed = state.setdefault("completed_steps", [])
        if not isinstance(completed, list):
            completed = []
            state["completed_steps"] = completed
        if args.step not in completed:
            completed.append(args.step)
            completed.sort()

    if args.next_step is not None:
        state["current_step"] = args.next_step
    state["updated_at"] = iso_now()
    state.update(parse_key_value(args.state_fields))
    dump_yaml(path, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
