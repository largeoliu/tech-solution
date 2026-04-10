# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""以原子方式推进 create-technical-solution 的状态文件。"""

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

from protocol_runtime import dump_yaml, iso_now, load_yaml, refresh_receipt, require_receipt


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


def advance_state_step(
    *,
    state_path: Path,
    step: int,
    summary: str,
    field: list[str] | None = None,
    field_json: list[str] | None = None,
    state_fields: list[str] | None = None,
    state_fields_json: list[str] | None = None,
    append_completed: bool,
    next_step: int | None,
    require_receipt_step: int | None,
) -> dict[str, Any]:
    if step >= 10:
        raise SystemExit(
            f"advance-state-step.py 不允许用于 step-{step}。"
            " 对外请改用 run-step.py --state <状态文件> --complete 完成 step-10/11/12；"
            " 本脚本只保留给早期步骤和内部兼容流程使用。"
        )

    state = load_yaml(
        state_path,
        missing_message=f"状态文件不存在: {state_path}。若步骤 12 已完成清理，不应再次调用 advance-state-step.py。",
    )
    if require_receipt_step is not None:
        require_receipt(state, expected_step=require_receipt_step)

    field = list(field or [])
    field_json = list(field_json or [])
    state_fields = list(state_fields or [])
    state_fields_json = list(state_fields_json or [])

    if step == 2:
        found_checked = any(kv.startswith("prerequisites_checked=") for kv in field)
        if not found_checked:
            field.append("prerequisites_checked=true")

    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints
    checkpoint = {"summary": summary}
    checkpoint.update(parse_key_value(field))
    checkpoint.update(parse_json_key_value(field_json))
    checkpoint["completed_at"] = iso_now()
    checkpoints[f"step-{step}"] = checkpoint

    if append_completed:
        completed = state.setdefault("completed_steps", [])
        if not isinstance(completed, list):
            completed = []
            state["completed_steps"] = completed
        if step not in completed:
            completed.append(step)
            completed.sort()

    if next_step is not None:
        state["current_step"] = next_step
    for key, value in parse_key_value(state_fields).items():
        set_path(state, key, value)
    for key, value in parse_json_key_value(state_fields_json).items():
        set_path(state, key, value)
    refresh_receipt(state)
    dump_yaml(state_path, state)
    return {
        "passed": True,
        "step": step,
        "next_step": state.get("current_step"),
        "checkpoint": checkpoint,
    }


def main() -> int:
    if not os.environ.get("__CTS_INTERNAL_CALL"):
        print("❌ 本脚本不可直接调用。请使用 run-step.py --prepare / --complete --ticket。", file=sys.stderr)
        sys.exit(1)
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
    parser.add_argument("--require-receipt-step", type=int, help="要求 gate_receipt.step 与该值一致")
    args = parser.parse_args()

    advance_state_step(
        state_path=Path(args.state).resolve(),
        step=args.step,
        summary=args.summary,
        field=args.field,
        field_json=args.field_json,
        state_fields=args.state_fields,
        state_fields_json=args.state_fields_json,
        append_completed=args.append_completed,
        next_step=args.next_step,
        require_receipt_step=args.require_receipt_step,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
