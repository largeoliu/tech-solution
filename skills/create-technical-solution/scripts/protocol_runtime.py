from __future__ import annotations

import hashlib
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


VALID_FLOW_TIERS = {"light", "moderate", "full"}
PROTOCOL_DIR = Path(__file__).resolve().parent.parent / "protocol"


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_yaml(path: Path, *, missing_ok: bool = False, missing_message: str | None = None) -> dict[str, Any]:
    if not path.exists():
        if missing_ok:
            return {}
        raise SystemExit(missing_message or f"状态文件不存在: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"状态文件必须是 YAML 对象: {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any], *, ensure_parent: bool = False) -> None:
    if ensure_parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def normalize_flow_tier(value: Any, *, fallback: str = "light") -> str:
    tier = str(value or "").strip().lower()
    return tier if tier in VALID_FLOW_TIERS else fallback


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


def require_receipt(
    state: dict[str, Any],
    *,
    expected_step: int,
    expected_flow_tier: str | None = None,
    allow_pending_flow_tier: bool = False,
) -> None:
    receipt = state.get("gate_receipt")
    if not isinstance(receipt, dict):
        raise SystemExit("缺少 gate_receipt，必须先运行 validate-state.py --write-pass-receipt。")
    if int(receipt.get("step") or 0) != expected_step:
        raise SystemExit(f"gate_receipt.step={receipt.get('step')}，期望 {expected_step}。")
    if expected_flow_tier is not None:
        receipt_flow_tier = str(receipt.get("flow_tier") or "")
        if not (allow_pending_flow_tier and expected_flow_tier == "pending"):
            if receipt_flow_tier != expected_flow_tier:
                raise SystemExit(
                    f"gate_receipt.flow_tier={receipt.get('flow_tier')}，期望 {expected_flow_tier}。"
                )
    if str(receipt.get("state_fingerprint") or "") != compute_state_fingerprint(state):
        raise SystemExit("gate_receipt.state_fingerprint 与当前状态不一致，请重新运行 validator。")


def refresh_receipt(
    state: dict[str, Any],
    *,
    step: int | None = None,
    flow_tier: str | None = None,
    default_step: int = 1,
    default_flow_tier: str = "light",
) -> None:
    resolved_step = int(step or state.get("current_step") or 0) or default_step
    resolved_flow_tier = normalize_flow_tier(
        state.get("flow_tier") if flow_tier is None else flow_tier,
        fallback=default_flow_tier,
    )
    state["gate_receipt"] = {
        "step": resolved_step,
        "flow_tier": resolved_flow_tier,
        "state_fingerprint": "",
        "validated_at": "",
    }
    state["gate_receipt"]["state_fingerprint"] = compute_state_fingerprint(state)
    state["gate_receipt"]["validated_at"] = iso_now()


@lru_cache(maxsize=1)
def load_workflow() -> dict[str, Any]:
    workflow_path = PROTOCOL_DIR / "workflow.yaml"
    data = load_yaml(workflow_path)
    steps = data.get("steps")
    if not isinstance(steps, list):
        raise SystemExit(f"workflow 协议缺少 steps 列表: {workflow_path}")
    return data


@lru_cache(maxsize=1)
def workflow_steps_by_id() -> dict[int, dict[str, Any]]:
    steps = load_workflow()["steps"]
    return {int(step["id"]): step for step in steps if isinstance(step, dict) and "id" in step}


def workflow_step(step_id: int) -> dict[str, Any]:
    step = workflow_steps_by_id().get(step_id)
    if not step:
        raise KeyError(f"workflow 中不存在步骤 {step_id}")
    return step


def workflow_step_name(step_id: int) -> str:
    step = workflow_step(step_id)
    return str(step.get("name") or f"步骤 {step_id}")


def workflow_step_card_path(step_id: int) -> Path:
    step = workflow_step(step_id)
    card = str(step.get("card") or "").strip()
    if not card:
        raise KeyError(f"workflow 步骤 {step_id} 缺少 card")
    return PROTOCOL_DIR.parent / card


def workflow_default_block(step_id: int, flow_tier: str) -> str | None:
    step = workflow_step(step_id)
    block_by_tier = step.get("content_block_by_tier")
    if isinstance(block_by_tier, dict):
        block = block_by_tier.get(flow_tier)
        return str(block) if block else None

    block = step.get("content_block")
    if block:
        return str(block)

    produces = step.get("produces")
    if isinstance(produces, list) and len(produces) == 1:
        return str(produces[0])

    return None
