# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""原子设置 flow_tier 及其伴随状态。"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


FULL_SIGNALS = {
    "introduces-core-capability",
    "cross-system",
    "boundary-redraw",
    "high-compat-risk",
    "split-or-migrate",
}
MODERATE_SIGNALS = {
    "cross-module",
    "existing-asset-refactor",
    "medium-compat-risk",
}
LIGHT_SIGNALS = {
    "single-module",
    "low-compat-risk",
}
VALID_SIGNALS = FULL_SIGNALS | MODERATE_SIGNALS | LIGHT_SIGNALS


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


def require_receipt(state: dict[str, Any], expected_step: int, expected_flow_tier: str) -> None:
    receipt = state.get("gate_receipt")
    if not isinstance(receipt, dict):
        raise SystemExit("缺少 gate_receipt，必须先运行 validate-state.py --write-pass-receipt。")
    if int(receipt.get("step") or 0) != expected_step:
        raise SystemExit(f"gate_receipt.step={receipt.get('step')}，期望 {expected_step}。")
    if str(receipt.get("flow_tier") or "") != expected_flow_tier:
        raise SystemExit(f"gate_receipt.flow_tier={receipt.get('flow_tier')}，期望 {expected_flow_tier}。")
    if str(receipt.get("state_fingerprint") or "") != compute_state_fingerprint(state):
        raise SystemExit("gate_receipt.state_fingerprint 与当前状态不一致，请重新运行 validator。")


def contract_for_tier(flow_tier: str) -> tuple[list[str], list[int]]:
    if flow_tier == "light":
        return ["WD-CTX", "WD-SYN-LIGHT"], [8, 9]
    if flow_tier == "moderate":
        return ["WD-CTX", "WD-TASK", "WD-SYN"], [9]
    return ["WD-CTX", "WD-TASK", "WD-EXP-*", "WD-SYN"], []


def validate_tier_against_signals(flow_tier: str, signals: list[str]) -> None:
    signal_set = set(signals)
    unknown = sorted(signal_set - VALID_SIGNALS)
    if unknown:
        raise SystemExit(f"存在未注册信号 {unknown}，只能使用受支持的 step-4 signals")
    if signal_set & FULL_SIGNALS and flow_tier != "full":
        raise SystemExit(f"命中 full 信号 {sorted(signal_set & FULL_SIGNALS)}，flow_tier 必须为 full")
    if flow_tier == "light" and signal_set & MODERATE_SIGNALS:
        raise SystemExit(f"命中 moderate 信号 {sorted(signal_set & MODERATE_SIGNALS)}，flow_tier 不得为 light")


def set_flow_tier(
    *,
    state_path: Path,
    flow_tier: str,
    solution_type: str,
    summary: str,
    next_step: int | None,
    append_completed: bool,
    signals: list[str],
    require_receipt_step: int | None,
) -> dict[str, Any]:
    validate_tier_against_signals(flow_tier, signals)
    state = load_yaml(state_path)
    if require_receipt_step is not None:
        require_receipt(state, require_receipt_step, flow_tier)
    required_artifacts, skipped_steps = contract_for_tier(flow_tier)

    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints
    step4 = checkpoints.setdefault("step-4", {})
    if not isinstance(step4, dict):
        step4 = {}
        checkpoints["step-4"] = step4
    step4.update(
        {
            "summary": summary,
            "solution_type": solution_type,
            "flow_tier": flow_tier,
            "signals": signals,
            "completed_at": iso_now(),
        }
    )

    state["flow_tier"] = flow_tier
    state["required_artifacts"] = required_artifacts
    state["skipped_steps"] = skipped_steps
    if next_step is not None:
        state["current_step"] = next_step

    if append_completed:
        completed = state.setdefault("completed_steps", [])
        if not isinstance(completed, list):
            completed = []
            state["completed_steps"] = completed
        if 4 not in completed:
            completed.append(4)
            completed.sort()

    dump_yaml(state_path, state)
    return {
        "flow_tier": flow_tier,
        "required_artifacts": required_artifacts,
        "skipped_steps": skipped_steps,
        "signals": signals,
        "current_step": state.get("current_step"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="原子设置 flow_tier、required_artifacts 与 skipped_steps")
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--flow-tier", choices=["light", "moderate", "full"], required=True, help="流程级别")
    parser.add_argument("--solution-type", required=True, help="步骤4判定出的方案类型")
    parser.add_argument("--summary", required=True, help="写入 checkpoints.step-4.summary 的摘要")
    parser.add_argument("--next-step", type=int, help="设置 current_step")
    parser.add_argument("--append-completed", action="store_true", help="将 step-4 追加到 completed_steps")
    parser.add_argument("--signal", action="append", default=[], help="步骤4命中的分类信号，可重复传入")
    parser.add_argument("--require-receipt-step", type=int, help="要求 gate_receipt.step 与该值一致")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    args = parser.parse_args()

    payload = set_flow_tier(
        state_path=Path(args.state).resolve(),
        flow_tier=args.flow_tier,
        solution_type=args.solution_type,
        summary=args.summary,
        next_step=args.next_step,
        append_completed=args.append_completed,
        signals=[item.strip() for item in args.signal if item.strip()],
        require_receipt_step=args.require_receipt_step,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"flow_tier 已设置为 {payload['flow_tier']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
