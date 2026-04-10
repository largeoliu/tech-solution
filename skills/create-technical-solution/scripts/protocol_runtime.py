from __future__ import annotations

import hashlib
import shlex
import sys
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


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


def compute_state_fingerprint(state: dict[str, Any]) -> str:
    receipt = state.get("gate_receipt")
    scrubbed = dict(state)
    if isinstance(receipt, dict):
        scrubbed["gate_receipt"] = {
            "step": receipt.get("step", 0),
            "state_fingerprint": "",
            "validated_at": "",
        }
    scrubbed["pending_ticket"] = {
        "step": 0,
        "value": "",
        "state_fingerprint": "",
        "artifact_fingerprint": "",
        "allowed_block_pattern": "",
        "issued_at": "",
    }
    payload = yaml.safe_dump(scrubbed, allow_unicode=True, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_artifact_fingerprint(*, repo_root: Path, state: dict[str, Any]) -> str:
    entries: list[tuple[str, str]] = []

    draft_path = resolve_repo_path(repo_root, state.get("working_draft_path"))
    if draft_path and draft_path.is_dir():
        for path in sorted(p for p in draft_path.rglob("*") if p.is_file()):
            relative = path.relative_to(repo_root).as_posix()
            content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append((relative, content_hash))

    final_document_path = resolve_repo_path(repo_root, state.get("final_document_path"))
    if final_document_path and final_document_path.is_file():
        relative = final_document_path.relative_to(repo_root).as_posix()
        content_hash = hashlib.sha256(final_document_path.read_bytes()).hexdigest()
        entries.append((relative, content_hash))

    payload = "\n".join(f"{path}:{digest}" for path, digest in entries)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def require_receipt(
    state: dict[str, Any],
    *,
    expected_step: int,
) -> None:
    receipt = state.get("gate_receipt")
    if not isinstance(receipt, dict):
        raise SystemExit("缺少 gate_receipt，必须先运行 validate-state.py --write-pass-receipt。")
    if int(receipt.get("step") or 0) != expected_step:
        raise SystemExit(f"gate_receipt.step={receipt.get('step')}，期望 {expected_step}。")
    if str(receipt.get("state_fingerprint") or "") != compute_state_fingerprint(state):
        raise SystemExit("gate_receipt.state_fingerprint 与当前状态不一致，请重新运行 validator。")


def refresh_receipt(
    state: dict[str, Any],
    *,
    step: int | None = None,
    default_step: int = 1,
) -> None:
    resolved_step = int(step or state.get("current_step") or 0) or default_step
    state["gate_receipt"] = {
        "step": resolved_step,
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


def workflow_default_block(step_id: int) -> str | None:
    step = workflow_step(step_id)
    block = step.get("content_block")
    if block:
        return str(block)

    produces = step.get("produces")
    if isinstance(produces, list) and len(produces) == 1:
        return str(produces[0])

    return None


def slug_from_state_path(state_path: Path) -> str:
    resolved = state_path.resolve()
    if resolved.name == "meta.yaml":
        return resolved.parent.name
    return resolved.name.rsplit(".", 1)[0]


def repo_root_from_state_path(state_path: Path) -> Path:
    resolved = state_path.resolve()
    if resolved.name == "meta.yaml":
        return resolved.parents[4]
    return resolved.parents[3]


def state_root_from_repo_root(repo_root: Path) -> Path:
    return (repo_root / STATE_ROOT).resolve()


def working_draft_relative_path(slug: str) -> Path:
    return STATE_ROOT / slug


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
    state: dict[str, Any] | None = None,
    summary_placeholder: str = "<完成摘要>",
) -> list[str]:
    base = run_step_base_command(state_path)
    prepare_line = f"{base} --prepare"

    if step == 1:
        return [
            f"{base} --prepare --slug <slug>",
            f'{base} --complete --ticket <ticket> --summary "<主题摘要>" --slug <slug>',
        ]
    if step in {2, 3, 6}:
        return [
            prepare_line,
            f'{base} --complete --ticket <ticket> --summary "{summary_placeholder}"',
        ]
    if step == 4:
        return [
            prepare_line,
            f'{base} --complete --ticket <ticket> --summary "<类型判定>" '
            '--solution-type "<方案类型>"',
        ]
    if step == 5:
        return [
            prepare_line,
            f'{base} --complete --ticket <ticket> --summary "<成员选定>" --member <MEMBER_ID> [--member ...]',
        ]
    if step == 7:
        return [
            prepare_line,
            f'{base} --complete --ticket <ticket> --summary "<WD-CTX 完成>" <<\'HEREDOC\'',
            "<WD-CTX 内容>",
            "HEREDOC",
        ]
    if step == 8:
        return [
            prepare_line,
            f'{base} --complete --ticket <ticket> --summary "<WD-TASK 完成>" <<\'HEREDOC\'',
            "<WD-TASK 内容>",
            "HEREDOC",
        ]
    if step == 9:
        slot_ids: list[str] = []
        if isinstance(state, dict):
            for s in state.get("slots") or []:
                sid = s.get("slot", "")
                if sid:
                    slot_ids.append(sid)
        if not slot_ids:
            slot_ids = ["SLOT-01"]
        block_lines = []
        for sid in slot_ids:
            block_lines.append(f"---BLOCK:WD-EXP-{sid}")
            block_lines.append("")
            block_lines.append("<专家分析内容>")
            block_lines.append("")
        return [
            prepare_line,
            f'{base} --complete --ticket <ticket> --summary "<专家分析完成>" <<\'HEREDOC\'',
            *block_lines,
            "HEREDOC",
        ]
    if step == 10:
        slot_ids_syn: list[str] = []
        if isinstance(state, dict):
            for s in state.get("slots") or []:
                sid = s.get("slot", "")
                if sid:
                    slot_ids_syn.append(sid)
        if not slot_ids_syn:
            slot_ids_syn = ["SLOT-01"]
        syn_lines = []
        for sid in slot_ids_syn:
            syn_lines.append(f"---BLOCK:WD-SYN-{sid}")
            syn_lines.append("")
            syn_lines.append("<收敛内容>")
            syn_lines.append("")
        return [
            prepare_line,
            f'{base} --complete --ticket <ticket> --summary "<收敛完成>" <<\'HEREDOC\'',
            *syn_lines,
            "HEREDOC",
        ]
    if step in {11, 12}:
        return [
            prepare_line,
            f'{base} --complete --ticket <ticket> --summary "{summary_placeholder}"',
        ]
    return [f'{base} --complete --ticket <ticket> --summary "{summary_placeholder}"']


def render_repair_command(
    *,
    state_path: Path,
    repair_step: int,
    state: dict[str, Any] | None = None,
) -> str:
    commands = render_run_step_command(
        state_path=state_path,
        step=repair_step,
        state=state,
        summary_placeholder="<修复摘要>",
    )
    for line in commands:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("---BLOCK:"):
            return stripped
    return commands[-1]
