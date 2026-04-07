# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""以原子方式推进 create-technical-solution 的状态文件。"""

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
        raise SystemExit(f"状态文件不存在: {path}。若步骤 12 已完成清理，不应再次调用 advance-state-step.py。")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"状态文件必须是 YAML 对象: {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def set_path(target: dict[str, Any], dotted_path: str, value: Any) -> None:
    parts = [part for part in dotted_path.split(".") if part]
    if not parts:
        raise SystemExit("字段路径不能为空")
    current = target
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value
    current[parts[-1]] = value


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


def parse_json_key_value(raw: list[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for item in raw:
        if "=" not in item:
            raise SystemExit(f"无效 JSON 键值对: {item}")
        key, value = item.split("=", 1)
        try:
            values[key] = json.loads(value)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"无法解析 JSON 值 ({key}): {exc}") from exc
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="推进状态文件中的步骤和 checkpoint")
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--step", type=int, required=True, help="当前完成的步骤号")
    parser.add_argument("--next-step", type=int, help="推进后的 current_step")
    parser.add_argument("--summary", required=True, help="写入 checkpoints.step-N.summary")
    parser.add_argument("--field", action="append", default=[], help="写入 checkpoints.step-N 的键值，格式 key=value")
    parser.add_argument("--field-json", action="append", default=[], help="写入 checkpoints.step-N 的 JSON 键值，格式 key=<json>")
    parser.add_argument("--set", dest="state_fields", action="append", default=[], help="写入顶层状态字段，格式 key=value")
    parser.add_argument("--set-json", dest="state_fields_json", action="append", default=[], help="写入顶层状态字段 JSON 值，格式 key=<json>")
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
    checkpoint.update(parse_json_key_value(args.field_json))
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
    for key, value in parse_key_value(args.state_fields).items():
        set_path(state, key, value)
    for key, value in parse_json_key_value(args.state_fields_json).items():
        set_path(state, key, value)
    dump_yaml(path, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
