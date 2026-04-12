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
DEFAULT_TEMPLATE_PATH = Path(".architecture/templates/technical-solution-template.md")
DEFAULT_MEMBERS_PATH = Path(".architecture/members.yml")
DEFAULT_PRINCIPLES_PATH = Path(".architecture/principles.md")

CANONICAL_STEP_DEFS: dict[int, dict[str, Any]] = {
    1: {"mode": "business", "artifact": None},
    2: {"mode": "automatic", "artifact": None},
    3: {"mode": "automatic", "artifact": None},
    4: {"mode": "business", "artifact": None},
    5: {"mode": "business", "artifact": None},
    6: {"mode": "automatic", "artifact": None},
    7: {"mode": "creative", "artifact": "WD-CTX"},
    8: {"mode": "creative", "artifact": "WD-TASK"},
    9: {"mode": "creative", "artifact": "WD-EXP-SLOT-*"},
    10: {"mode": "creative", "artifact": "WD-SYN-SLOT-*"},
    11: {"mode": "automatic", "artifact": None},
    12: {"mode": "automatic", "artifact": None},
}


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


ARTIFACT_FINGERPRINT_EXCLUDED_NAMES = frozenset({
    "state.yaml",
    "meta.yaml",
    ".gitkeep",
    ".gitignore",
    ".DS_Store",
})


def compute_artifact_fingerprint(*, repo_root: Path, state: dict[str, Any]) -> str:
    entries: list[tuple[str, str]] = []

    draft_path = resolve_repo_path(repo_root, state.get("working_draft_path"))
    if draft_path and draft_path.is_dir():
        for path in sorted(p for p in draft_path.rglob("*") if p.is_file()):
            if path.name in ARTIFACT_FINGERPRINT_EXCLUDED_NAMES:
                continue
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
    if resolved.name in ("meta.yaml", "state.yaml"):
        return resolved.parent.name
    return resolved.name.rsplit(".", 1)[0]


def detect_project_root(start_path: Path) -> Path:
    resolved = start_path.resolve()
    current = resolved if resolved.is_dir() else resolved.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / ".architecture").exists():
            return candidate
    if resolved.name == "meta.yaml" and len(resolved.parents) >= 5:
        return resolved.parents[4]
    if len(resolved.parents) >= 4:
        return resolved.parents[3]
    return current


def repo_root_from_state_path(state_path: Path) -> Path:
    return detect_project_root(state_path)


def working_draft_relative_path(slug: str) -> Path:
    return STATE_ROOT / slug / "draft"


def final_document_relative_path(slug: str) -> Path:
    return SOLUTION_ROOT / f"{slug}.md"


def canonical_state_paths_for_slug(slug: str) -> dict[str, str]:
    return {
        "solution_root": str(SOLUTION_ROOT),
        "members_path": str(DEFAULT_MEMBERS_PATH),
        "principles_path": str(DEFAULT_PRINCIPLES_PATH),
        "template_path": str(DEFAULT_TEMPLATE_PATH),
        "working_draft_path": str(working_draft_relative_path(slug)),
        "final_document_path": str(final_document_relative_path(slug)),
    }


def build_canonical_state_payload(*, state_path: Path, slug: str | None = None) -> dict[str, Any]:
    resolved_slug = (slug or state_path.stem or "solution").strip() or "solution"
    payload = {
        "slug": resolved_slug,
        "current_step": 1,
    }
    payload.update(canonical_state_paths_for_slug(resolved_slug))
    return payload


def canonical_step_defs() -> dict[int, dict[str, Any]]:
    return {step: dict(defn) for step, defn in CANONICAL_STEP_DEFS.items()}


def default_step_summary(
    step: int,
    *,
    slug: str | None = None,
    ctx_count: int | None = None,
    slot_count: int | None = None,
    completed_slots: int | None = None,
    total_slots: int | None = None,
    absorbed_slot_count: int | None = None,
) -> str:
    if step == 1:
        slug_part = f"；slug={slug}" if slug else ""
        return f"完成；定题与范围判断已记录{slug_part}；gate: step-2 ready"
    if step == 2:
        return "完成；前置文件检查通过；gate: step-3 ready"
    if step == 3:
        return "完成；模板已读取；gate: step-4 ready"
    if step == 4:
        return "完成；方案类型已确定；gate: step-5 ready"
    if step == 5:
        return "完成；参与成员已记录；gate: step-6 ready"
    if step == 6:
        return "完成；repowiki 检查完成；gate: step-7 ready"
    if step == 7:
        return f"完成；写入 WD-CTX；CTX={int(ctx_count or 0)}；gate: step-8 ready"
    if step == 8:
        return f"完成；写入 WD-TASK；slots={int(slot_count or 0)}；gate: step-9 ready"
    if step == 9:
        completed = int(completed_slots or 0)
        total = int(total_slots or completed)
        if total and completed < total:
            return f"进行中；新增专家分析；累计完成={completed}/{total}；gate: step-9 continue"
        return f"完成；写入专家分析；slots={completed}；gate: step-10 ready"
    if step == 10:
        completed = int(completed_slots or 0)
        total = int(total_slots or completed)
        if total and completed < total:
            return f"进行中；新增收敛；累计完成={completed}/{total}；gate: step-10 continue"
        return f"完成；写入协作收敛；slots={completed}；gate: step-11 ready"
    if step == 11:
        return f"完成；最终文档已渲染；absorbed_slots={int(absorbed_slot_count or 0)}；gate: step-12 ready"
    if step == 12:
        return "完成；清理已执行；gate: done"
    return "完成；步骤已处理"


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


def selected_member_ids(state: dict[str, Any]) -> list[str]:
    checkpoints = state.get("checkpoints") or {}
    if not isinstance(checkpoints, dict):
        return []
    step5 = checkpoints.get("step-5") or {}
    if not isinstance(step5, dict):
        return []
    raw = step5.get("selected_members") or []
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def expert_truth_dir(working_dir: Path, slot_id: str) -> Path:
    return working_dir / "slots" / slot_id / "experts"


def expert_truth_files(working_dir: Path, slot_id: str) -> list[Path]:
    experts_dir = expert_truth_dir(working_dir, slot_id)
    if not experts_dir.is_dir():
        return []
    return sorted(experts_dir.glob("*.json"))


def expert_truth_member_ids(working_dir: Path, slot_id: str) -> list[str]:
    return [path.stem for path in expert_truth_files(working_dir, slot_id)]


def expert_truth_complete(*, state: dict[str, Any], working_dir: Path, slot_id: str) -> bool:
    expected = selected_member_ids(state)
    if not expected:
        return False
    expected_normalized = {item.strip().lower() for item in expected if item.strip()}
    actual = {item.strip().lower() for item in expert_truth_member_ids(working_dir, slot_id) if item.strip()}
    return expected_normalized.issubset(actual)


def expert_truth_digest(working_dir: Path, slot_id: str) -> str:
    payload_lines: list[str] = []
    for path in expert_truth_files(working_dir, slot_id):
        payload_lines.append(f"{path.name}:{hashlib.sha256(path.read_bytes()).hexdigest()}")
    payload = "\n".join(payload_lines)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def decision_truth_path(working_dir: Path, slot_id: str) -> Path:
    return working_dir / "slots" / slot_id / "decision.json"


def decision_truth_digest(working_dir: Path, slot_id: str) -> str:
    path = decision_truth_path(working_dir, slot_id)
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    advance_line = f"{base} --advance"
    prepare_line = f"{base} --prepare"
    pending_ticket = state.get("pending_ticket") if isinstance(state, dict) else None
    has_current_ticket = isinstance(pending_ticket, dict) and int(
        pending_ticket.get("step") or 0
    ) == step

    if step == 1:
        return [advance_line]
    if step in {2, 3, 6}:
        return [advance_line]
    if step == 4:
        if not has_current_ticket:
            return [advance_line]
        return [
            f"{base} --complete --ticket <ticket> <<'HEREDOC'",
            '{"solution_type": "<方案类型>"}',
            'HEREDOC',
        ]
    if step == 5:
        if not has_current_ticket:
            return [advance_line]
        return [
            f"{base} --complete --ticket <ticket> <<'HEREDOC'",
            '{"selected_members": ["<MEMBER_ID>"]}',
            'HEREDOC',
        ]
    if step == 7:
        if not has_current_ticket:
            return [advance_line]
        return [
            f"{base} --complete --ticket <ticket> <<'HEREDOC'",
            '[',
            '  {"id": "CTX-01", "source": "src/module.py", "conclusion": "复用现有入口", "applicable_slots": ["1.1 需求概述"], "confidence": "已验证"}',
            ']',
            "HEREDOC",
        ]
    if step == 8:
        if not has_current_ticket:
            return [advance_line]
        return [
            f"{base} --complete --ticket <ticket> <<'HEREDOC'",
            '[',
            '  {"slot": "1.1 需求概述", "required_ctx": ["CTX-01"]}',
            ']',
            "HEREDOC",
        ]
    if step == 9:
        if not has_current_ticket:
            return [advance_line]
        return [
            f"{base} --complete --ticket <ticket> <<'HEREDOC'",
            '[',
            '  {',
            '    "slot": "2.1 方案设计",',
            '    "decision_type": "改造",',
            '    "rationale": "复用现有骨架并补齐专家分析。",',
            '    "evidence_refs": ["CTX-01"],',
            '    "open_questions": ["无"]',
            '  }',
            ']',
            "HEREDOC",
        ]
    if step == 10:
        if not has_current_ticket:
            return [advance_line]
        return [
            f"{base} --complete --ticket <ticket> <<'HEREDOC'",
            '[',
            '  {',
            '    "slot": "2.1 方案设计",',
            '    "target_capability": "收敛 2.1 方案设计 的最终写法。",',
            '    "comparisons": [',
            '      {"path": "复用", "feasibility": "❌", "evidence": "CTX-01", "reason": "不足"},',
            '      {"path": "改造", "feasibility": "✅", "evidence": "CTX-01", "reason": "推荐"}',
            '    ],',
            '    "selected_path": "改造",',
            '    "selected_writeup": "在 2.1 方案设计 位置补齐内容。",',
            '    "evidence_refs": ["CTX-01"],',
            '    "template_gap": "无",',
            '    "open_question": "无"',
            '  }',
            ']',
            "HEREDOC",
        ]
    if step in {11, 12}:
        return [advance_line]
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
