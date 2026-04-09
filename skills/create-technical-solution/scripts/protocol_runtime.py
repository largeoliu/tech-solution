from __future__ import annotations

import hashlib
import shlex
import sys
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


VALID_FLOW_TIERS = {"light", "moderate", "full"}
PROTOCOL_DIR = Path(__file__).resolve().parent.parent / "protocol"
RUN_STEP_SCRIPT = Path(__file__).resolve().parent / "run-step.py"
VALIDATE_STATE_SCRIPT = Path(__file__).resolve().parent / "validate-state.py"
SOLUTION_ROOT = Path(".architecture/technical-solutions")
STATE_ROOT = Path(".architecture/.state/create-technical-solution")


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


def slug_from_state_path(state_path: Path) -> str:
    return state_path.name.rsplit(".", 1)[0]


def repo_root_from_state_path(state_path: Path) -> Path:
    return state_path.resolve().parents[3]


def state_root_from_repo_root(repo_root: Path) -> Path:
    return (repo_root / STATE_ROOT).resolve()


def working_draft_relative_path(slug: str) -> Path:
    return STATE_ROOT / f"{slug}.working.md"


def final_document_relative_path(slug: str) -> Path:
    return SOLUTION_ROOT / f"{slug}.md"


def working_draft_path_for_slug(*, repo_root: Path, slug: str) -> Path:
    return (repo_root / working_draft_relative_path(slug)).resolve()


def final_document_path_for_slug(*, repo_root: Path, slug: str) -> Path:
    return (repo_root / final_document_relative_path(slug)).resolve()


def resolve_repo_path(
    repo_root: Path,
    path_value: Any,
    *,
    default_relative: Path | str | None = None,
) -> Path | None:
    raw = str(path_value or "").strip()
    if raw:
        candidate = Path(raw)
    elif default_relative is None:
        return None
    else:
        candidate = Path(default_relative)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def run_step_base_command(state_path: Path) -> str:
    python_bin = shlex.quote(sys.executable or "python3")
    script_path = shlex.quote(str(RUN_STEP_SCRIPT.resolve()))
    state_arg = shlex.quote(str(state_path.resolve()))
    return f"{python_bin} {script_path} --state {state_arg}"


def render_run_step_command(
    *,
    state_path: Path,
    step: int,
    flow_tier: str,
    state: dict[str, Any] | None = None,
    summary_placeholder: str = "<完成摘要>",
) -> list[str]:
    base = run_step_base_command(state_path)

    if step == 1:
        return [f'{base} --complete --summary "<主题摘要>" --slug <slug>']
    if step in {2, 3, 6, 11, 12}:
        return [f'{base} --complete --summary "{summary_placeholder}"']
    if step == 4:
        return [
            f'{base} --complete --summary "<类型判定>" --flow-tier <light|moderate|full> '
            '--solution-type "<方案类型>" --signal <信号>'
        ]
    if step == 5:
        return [f'{base} --complete --summary "<成员选定>" --member <MEMBER_ID> [--member ...]']
    if step == 7:
        return [
            "# 先将 WD-CTX 内容写入临时文件，然后：",
            f'{base} --complete --summary "<WD-CTX 完成>" --content-file /tmp/wd-ctx.md',
        ]
    if step == 8:
        return [
            "# 先将 WD-TASK 内容写入临时文件，然后：",
            f'{base} --complete --summary "<WD-TASK 完成>" --content-file /tmp/wd-task.md',
        ]
    if step == 9:
        members: list[str] = []
        if isinstance(state, dict):
            checkpoints = state.get("checkpoints", {})
            if isinstance(checkpoints, dict):
                step5 = checkpoints.get("step-5", {})
                if isinstance(step5, dict):
                    raw_members = step5.get("selected_members", [])
                    if isinstance(raw_members, list):
                        members = [str(item) for item in raw_members if str(item).strip()]
        if members:
            files = " ".join(f"--content-file /tmp/wd-exp-{member}.md" for member in members)
            return [
                "# 为每位专家生成内容文件，然后一次性提交：",
                f'{base} --complete --summary "<专家分析完成>" {files}',
            ]
        return [
            "# 为每位专家生成内容文件，然后一次性提交：",
            f'{base} --complete --summary "<专家分析完成>" --content-file /tmp/wd-exp-<MEMBER>.md',
        ]
    if step == 10:
        block = "WD-SYN-LIGHT" if flow_tier == "light" else "WD-SYN"
        return [
            f"# 先将 {block} 内容写入临时文件，然后：",
            f'{base} --complete --summary "<收敛完成>" --content-file /tmp/wd-syn.md',
        ]
    return [f'{base} --complete --summary "{summary_placeholder}"']


def render_repair_command(
    *,
    state_path: Path,
    repair_step: int,
    flow_tier: str,
    state: dict[str, Any] | None = None,
) -> str:
    commands = render_run_step_command(
        state_path=state_path,
        step=repair_step,
        flow_tier=flow_tier,
        state=state,
        summary_placeholder="<修复摘要>",
    )
    for line in commands:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return commands[-1]
