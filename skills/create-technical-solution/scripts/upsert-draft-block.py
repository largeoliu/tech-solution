# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""按 block 安全更新 working draft 目录；状态同步仅用于内部兼容场景。"""

from __future__ import annotations

import os
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import decision_truth_path, default_step_summary, dump_yaml, expert_truth_complete, expert_truth_digest, iso_now, load_yaml, refresh_receipt, repo_root_from_state_path, require_receipt

BLOCK_MARKER_RE = re.compile(r"^---BLOCK:(.+)$", re.MULTILINE)


def parse_stdin_blocks(raw: str, step: int) -> list[tuple[str, str]]:
    raw = raw.strip()
    if not raw:
        return []
    markers = list(BLOCK_MARKER_RE.finditer(raw))
    if not markers:
        default_block = _default_block_for_step(step)
        if default_block:
            return [(default_block, raw)]
        raise SystemExit(f"步骤 {step} 无法确定默认 block 名称，请使用 ---BLOCK: 标记。")
    blocks: list[tuple[str, str]] = []
    for i, match in enumerate(markers):
        block_name = match.group(1).strip()
        start = match.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(raw)
        body = raw[start:end].strip("\n")
        blocks.append((block_name, body))
    return blocks


def _default_block_for_step(step: int) -> str | None:
    return {7: "WD-CTX", 8: "WD-TASK"}.get(step)


CTX_EXTENSION_FIELDS = [
    ("资产类型", "asset_type"),
    ("资产标识", "asset_id"),
    ("位置", "location"),
    ("当前职责", "current_duty"),
    ("当前能力", "current_capability"),
    ("可扩展点", "extensibility"),
    ("已知限制", "known_limits"),
    ("调用方/依赖方", "callers_deps"),
    ("相关证据路径", "evidence_path"),
    ("搜索范围", "search_scope"),
    ("搜索关键词", "search_keywords"),
    ("已排除目录或对象", "excluded"),
    ("未发现结论", "not_found_conclusion"),
]


def _coerce_string_list(value: Any, *, field_name: str) -> list[str]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} 必须是数组。")
    return [str(item).strip() for item in value if str(item).strip()]


def _ctx_source_refs(entry: dict[str, Any]) -> list[str]:
    refs = _coerce_string_list(entry.get("source_refs"), field_name="WD-CTX source_refs")
    if refs:
        return refs
    source = str(entry.get("source") or "").strip()
    if not source:
        return []
    return [part.strip() for part in source.split(",") if part.strip()]


def _ctx_entry_traceable(entry: dict[str, Any]) -> bool:
    refs = _ctx_source_refs(entry)
    if not refs:
        return False
    return any("/" in ref or "." in ref or ref.startswith("repowiki:") for ref in refs)


def _ctx_repowiki_refs(entries: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for entry in entries:
        for ref in _ctx_source_refs(entry):
            if ref.startswith("repowiki:") and ref not in refs:
                refs.append(ref)
    return refs


def _ctx_gate_ready(entries: list[dict[str, Any]], state: dict[str, Any]) -> bool:
    if not entries:
        return False
    if any(not _ctx_entry_traceable(entry) for entry in entries):
        return False
    checkpoint6 = state.get("checkpoints", {}).get("step-6", {}) if isinstance(state.get("checkpoints"), dict) else {}
    if checkpoint6.get("repowiki_exists") is True and not _ctx_repowiki_refs(entries):
        return False
    return True


def _slot_id_for_title(slots: list[dict[str, Any]], title: str) -> str:
    normalized = title.strip()
    for slot in slots:
        if str(slot.get("title") or "").strip() == normalized:
            return str(slot.get("slot") or "").strip()
    raise ValueError(f"未找到槽位标题对应的 state.slots 记录: {title}")


def _json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _parse_json_array_content(content: str, label: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} 不是合法 JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise ValueError(f"{label} 必须是 JSON 数组。")
    normalized: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError(f"{label} 数组元素必须是 JSON 对象。")
        normalized.append(item)
    return normalized


def render_exp_payload(entries: list[dict[str, Any]], slots: list[dict[str, Any]]) -> list[tuple[str, str]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        slot_title = str(entry.get("slot") or "").strip()
        if not slot_title:
            raise ValueError("WD-EXP payload 缺少 slot。")
        slot_id = _slot_id_for_title(slots, slot_title)
        evidence_refs = entry.get("evidence_refs") or []
        open_questions = entry.get("open_questions") or []
        member = str(entry.get("member") or "").strip()
        if not isinstance(evidence_refs, list) or not isinstance(open_questions, list):
            raise ValueError("WD-EXP evidence_refs/open_questions 必须是数组。")
        if not member:
            raise ValueError("WD-EXP payload 缺少 member。")
        grouped.setdefault(slot_id, []).append(
            {
                "slot": slot_title,
                "member": member,
                "decision_type": str(entry.get("decision_type") or "").strip(),
                "rationale": str(entry.get("rationale") or "").strip(),
                "evidence_refs": evidence_refs,
                "open_questions": open_questions,
            }
        )
    return [(f"WD-EXP-{slot_id}", _json_text(grouped_entries)) for slot_id, grouped_entries in grouped.items()]


def render_syn_payload(entries: list[dict[str, Any]], slots: list[dict[str, Any]]) -> list[tuple[str, str]]:
    rendered: list[tuple[str, str]] = []
    for entry in entries:
        slot_title = str(entry.get("slot") or "").strip()
        if not slot_title:
            raise ValueError("WD-SYN payload 缺少 slot。")
        slot_id = _slot_id_for_title(slots, slot_title)
        comparisons = entry.get("comparisons") or []
        evidence_refs = entry.get("evidence_refs") or []
        if not isinstance(comparisons, list) or not isinstance(evidence_refs, list):
            raise ValueError("WD-SYN comparisons/evidence_refs 必须是数组。")
        for item in comparisons:
            if not isinstance(item, dict):
                raise ValueError("WD-SYN comparisons 数组元素必须是对象。")
        rendered.append((f"WD-SYN-{slot_id}", _json_text([entry])))
    return rendered


def validate_body(block_name: str, content: str) -> None:
    body = content.strip()
    if not body:
        raise SystemExit(f"{block_name} body 不能为空。")
    if re.search(r"^\s*##\s+WD-", body, re.MULTILINE):
        raise SystemExit(f"{block_name} body 不得包含 ## WD-* 标题。")


def resolve_file_for_block(working_dir: Path, block_name: str, slots: list[dict[str, Any]]) -> Path:
    if block_name == "WD-CTX":
        return working_dir / "ctx.json"
    if block_name == "WD-TASK":
        return working_dir / "task.json"
    exp_match = re.match(r"^WD-EXP-(SLOT-\d+)$", block_name)
    if exp_match:
        slot_id = exp_match.group(1)
        valid_ids = {s.get("slot", "") for s in slots}
        if valid_ids and slot_id not in valid_ids:
            raise SystemExit(f"block {block_name} 的 slot 不在 state.slots 中。")
        return working_dir / "slots" / slot_id / "experts"
    syn_match = re.match(r"^WD-SYN-(SLOT-\d+)$", block_name)
    if syn_match:
        slot_id = syn_match.group(1)
        valid_ids = {s.get("slot", "") for s in slots}
        if valid_ids and slot_id not in valid_ids:
            raise SystemExit(f"block {block_name} 的 slot 不在 state.slots 中。")
        return decision_truth_path(working_dir, slot_id)
    raise SystemExit(f"不支持的 block: {block_name}")


def resolve_registry_target_for_block(working_dir: Path, block_name: str, slots: list[dict[str, Any]]) -> Path | None:
    if block_name in {"WD-CTX", "WD-TASK"}:
        return resolve_file_for_block(working_dir, block_name, slots)
    exp_match = re.match(r"^WD-EXP-(SLOT-\d+)$", block_name)
    if exp_match:
        experts_dir = working_dir / "slots" / exp_match.group(1) / "experts"
        return experts_dir if experts_dir.is_dir() else None
    return resolve_file_for_block(working_dir, block_name, slots)


def write_working_draft_file(
    working_dir: Path,
    block_name: str,
    content: str,
    slots: list[dict[str, Any]],
) -> Path:
    target = resolve_file_for_block(working_dir, block_name, slots)
    if block_name == "WD-CTX":
        entries = _parse_json_array_content(content, "WD-CTX payload")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_json_text(entries), encoding="utf-8")
        return target
    if block_name == "WD-TASK":
        entries = _parse_json_array_content(content, "WD-TASK payload")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_json_text(entries), encoding="utf-8")
        return target
    exp_match = re.match(r"^WD-EXP-(SLOT-\d+)$", block_name)
    if exp_match:
        entries = _parse_json_array_content(content, "WD-EXP payload")
        slot_dir = working_dir / "slots" / exp_match.group(1)
        experts_dir = slot_dir / "experts"
        experts_dir.mkdir(parents=True, exist_ok=True)
        for json_file in experts_dir.glob("*.json"):
            json_file.unlink()
        for entry in entries:
            member = str(entry.get("member") or "").strip()
            if not member:
                raise ValueError("WD-EXP payload 缺少 member。")
            (experts_dir / f"{member}.json").write_text(
                _json_text(entry), encoding="utf-8"
            )
        return experts_dir
    syn_match = re.match(r"^WD-SYN-(SLOT-\d+)$", block_name)
    if syn_match:
        entries = _parse_json_array_content(content, "WD-SYN payload")
        if len(entries) != 1:
            raise ValueError("WD-SYN payload 每次只能写入单个槽位。")
        entry = entries[0]
        slot_dir = working_dir / "slots" / syn_match.group(1)
        slot_dir.mkdir(parents=True, exist_ok=True)
        decision_path = decision_truth_path(working_dir, syn_match.group(1))
        decision_path.write_text(_json_text(entry), encoding="utf-8")
        return decision_path
    validate_body(block_name, content)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    return target


def count_items(block: str, prefix: str) -> int:
    return len(re.findall(rf"^\s*###\s+{re.escape(prefix)}", block, re.MULTILINE))


def count_slot_sections(block: str) -> int:
    return len(re.findall(r"^\s*###\s+", block, re.MULTILINE))


def _extract_slot_id(block_name: str) -> str | None:
    m = re.match(r"^WD-(?:EXP|SYN)-(SLOT-\d+)$", block_name)
    return m.group(1) if m else None


def _all_slot_ids(state: dict[str, Any]) -> list[str]:
    return [s.get("slot", "") for s in state.get("slots") or [] if s.get("slot")]


def _ensure_artifact_progress(state: dict[str, Any]) -> None:
    progress = state.setdefault("artifact_progress", {})
    if not isinstance(progress, dict):
        progress = {}
        state["artifact_progress"] = progress
    for key in ("WD-EXP-SLOT-*", "WD-SYN-SLOT-*"):
        entry = progress.setdefault(key, {})
        if not isinstance(entry, dict):
            progress[key] = {}
            entry = progress[key]
        entry.setdefault("completed_slots", [])


def _record_slot_completion(state: dict[str, Any], block_name: str) -> None:
    slot_id = _extract_slot_id(block_name)
    if not slot_id:
        return
    _ensure_artifact_progress(state)
    progress = state["artifact_progress"]
    if block_name.startswith("WD-EXP-"):
        artifact_key = "WD-EXP-SLOT-*"
    elif block_name.startswith("WD-SYN-"):
        artifact_key = "WD-SYN-SLOT-*"
    else:
        return
    completed = progress.get(artifact_key, {}).get("completed_slots", [])
    if not isinstance(completed, list):
        completed = []
    if slot_id not in completed:
        completed.append(slot_id)
        completed.sort()
    progress.setdefault(artifact_key, {})["completed_slots"] = completed


def _check_step_completion(state: dict[str, Any], artifact_key: str) -> bool:
    _ensure_artifact_progress(state)
    completed = state.get("artifact_progress", {}).get(artifact_key, {}).get("completed_slots", [])
    all_ids = _all_slot_ids(state)
    if not all_ids:
        return False
    return set(completed) >= set(all_ids)


def _recompute_slot_progress(state: dict[str, Any], working_dir: Path) -> None:
    _ensure_artifact_progress(state)
    exp_completed: list[str] = []
    syn_completed: list[str] = []
    for slot_id in _all_slot_ids(state):
        if expert_truth_complete(state=state, working_dir=working_dir, slot_id=slot_id):
            exp_completed.append(slot_id)
        syn_path = decision_truth_path(working_dir, slot_id)
        if syn_path.exists():
            syn_completed.append(slot_id)
    state["artifact_progress"]["WD-EXP-SLOT-*"] = {"completed_slots": sorted(exp_completed)}
    state["artifact_progress"]["WD-SYN-SLOT-*"] = {"completed_slots": sorted(syn_completed)}


def _recompute_step_progress_checkpoints(state: dict[str, Any], block_updates: list[tuple[str, str]]) -> None:
    checkpoints = state.setdefault("checkpoints", {})
    completed = state.setdefault("completed_steps", [])
    if not isinstance(checkpoints, dict) or not isinstance(completed, list):
        return
    exp_completed = state.get("artifact_progress", {}).get("WD-EXP-SLOT-*", {}).get("completed_slots", [])
    syn_completed = state.get("artifact_progress", {}).get("WD-SYN-SLOT-*", {}).get("completed_slots", [])
    if not isinstance(exp_completed, list):
        exp_completed = []
    if not isinstance(syn_completed, list):
        syn_completed = []
    all_ids = _all_slot_ids(state)
    touched_exp = any(block_name.startswith("WD-EXP-") for block_name, _content in block_updates)
    touched_syn = any(block_name.startswith("WD-SYN-") for block_name, _content in block_updates)
    if touched_exp and "step-9" in checkpoints:
        checkpoints["step-9"]["wd_exp_count"] = len(exp_completed)
        all_done = bool(all_ids) and set(exp_completed) >= set(all_ids)
        state["can_enter_step_10"] = all_done
        state["current_step"] = 10 if all_done else 9
        if 9 not in completed:
            completed.append(9)
    if touched_syn and "step-10" in checkpoints:
        checkpoints["step-10"]["syn_slot_count"] = len(syn_completed)
        all_done = bool(all_ids) and set(syn_completed) >= set(all_ids)
        state["can_enter_step_11"] = all_done
        state["current_step"] = 11 if all_done else 10
        if 10 not in completed:
            completed.append(10)
    completed.sort()


def sync_state_for_block(state: dict[str, Any], block_name: str, summary: str | None, *, content: str | None = None) -> None:
    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints

    produced = state.setdefault("produced_artifacts", [])
    if not isinstance(produced, list):
        produced = []
        state["produced_artifacts"] = produced
    if block_name not in produced:
        produced.append(block_name)
        produced.sort()

    completed = state.setdefault("completed_steps", [])
    if not isinstance(completed, list):
        completed = []
        state["completed_steps"] = completed

    if block_name == "WD-CTX":
        entries = _parse_json_array_content(content or "[]", "WD-CTX payload")
        repowiki_consumed_paths = _ctx_repowiki_refs(entries)
        gate_ready = _ctx_gate_ready(entries, state)
        checkpoints["step-7"] = {
            "summary": str(summary or "").strip(),
            "wd_ctx_written": True,
            "ctx_count": 0,
            "repowiki_consumed_paths": repowiki_consumed_paths,
            "completed_at": iso_now(),
        }
        state["can_enter_step_8"] = gate_ready
        state["can_enter_step_10"] = False
        state["current_step"] = 8 if gate_ready else 7
        if 7 not in completed:
            completed.append(7)
    elif block_name == "WD-TASK":
        checkpoints["step-8"] = {
            "summary": str(summary or "").strip(),
            "wd_task_written": True,
            "task_slot_count": 0,
            "completed_at": iso_now(),
        }
        state["can_enter_step_9"] = True
        state["can_enter_step_10"] = False
        state["current_step"] = 9
        if 8 not in completed:
            completed.append(8)
    elif block_name.startswith("WD-EXP-"):
        _record_slot_completion(state, block_name)
        all_done = _check_step_completion(state, "WD-EXP-SLOT-*")
        completed_slots = state.get("artifact_progress", {}).get("WD-EXP-SLOT-*", {}).get("completed_slots", [])
        checkpoints["step-9"] = {
            "summary": str(summary or "").strip(),
            "skipped": False,
            "reason": "",
            "wd_exp_count": len(completed_slots),
            "completed_at": iso_now(),
        }
        if all_done:
            state["can_enter_step_10"] = True
            state["current_step"] = 10
            if 9 not in completed:
                completed.append(9)
        else:
            state["can_enter_step_10"] = False
            state["current_step"] = 9
            if 9 not in completed:
                completed.append(9)
    elif block_name.startswith("WD-SYN-"):
        _record_slot_completion(state, block_name)
        all_done = _check_step_completion(state, "WD-SYN-SLOT-*")
        completed_slots = state.get("artifact_progress", {}).get("WD-SYN-SLOT-*", {}).get("completed_slots", [])
        checkpoints["step-10"] = {
            "summary": str(summary or "").strip(),
            "wd_syn_written": True,
            "syn_slot_count": len(completed_slots),
            "completed_at": iso_now(),
        }
        if all_done:
            state["can_enter_step_11"] = True
            state["current_step"] = 11
            if 10 not in completed:
                completed.append(10)
        else:
            state["can_enter_step_11"] = False
            state["current_step"] = 10
            if 10 not in completed:
                completed.append(10)
    completed.sort()


def update_counts(state: dict[str, Any], block_name: str, content: str) -> None:
    checkpoints = state.setdefault("checkpoints", {})
    if block_name == "WD-CTX":
        checkpoints["step-7"]["ctx_count"] = len(
            _parse_json_array_content(content, "WD-CTX payload")
        )
    elif block_name == "WD-TASK":
        checkpoints["step-8"]["task_slot_count"] = len(
            _parse_json_array_content(content, "WD-TASK payload")
        )
    elif block_name.startswith("WD-EXP-"):
        completed_slots = state.get("artifact_progress", {}).get("WD-EXP-SLOT-*", {}).get("completed_slots", [])
        checkpoints["step-9"]["wd_exp_count"] = len(completed_slots)
    elif block_name.startswith("WD-SYN-"):
        completed_slots = state.get("artifact_progress", {}).get("WD-SYN-SLOT-*", {}).get("completed_slots", [])
        checkpoints["step-10"]["syn_slot_count"] = len(completed_slots)


def sync_artifact_registry(
    state: dict[str, Any],
    state_path: Path,
    working_dir: Path,
    slots: list[dict[str, Any]],
    block_updates: list[tuple[str, str]],
) -> None:
    registry = state.setdefault("artifact_registry", {})
    if not isinstance(registry, dict):
        registry = {}
        state["artifact_registry"] = registry
    repo_root = state_path_to_repo_root(state_path)
    for block_name, _content in block_updates:
        target = resolve_registry_target_for_block(working_dir, block_name, slots)
        if target is None or not target.exists():
            continue
        if block_name.startswith("WD-EXP-") and target.is_dir():
            slot_id = block_name.removeprefix("WD-EXP-")
            registry[block_name] = {
                "path": target.relative_to(repo_root).as_posix(),
                "content_hash": expert_truth_digest(working_dir, slot_id),
                "written_at": iso_now(),
                "writer": "run-step",
            }
        else:
            registry[block_name] = {
                "path": target.relative_to(repo_root).as_posix(),
                "content_hash": hashlib.sha256(target.read_bytes()).hexdigest(),
                "written_at": iso_now(),
                "writer": "run-step",
            }


def state_path_to_repo_root(state_path: Path) -> Path:
    return repo_root_from_state_path(state_path)


def _apply_generated_summary(state: dict[str, Any], block_name: str, summary: str | None) -> None:
    explicit = str(summary or "").strip()
    checkpoints = state.setdefault("checkpoints", {})
    if block_name == "WD-CTX":
        checkpoints["step-7"]["summary"] = explicit or default_step_summary(
            7, ctx_count=checkpoints["step-7"].get("ctx_count")
        )
    elif block_name == "WD-TASK":
        checkpoints["step-8"]["summary"] = explicit or default_step_summary(
            8, slot_count=checkpoints["step-8"].get("task_slot_count")
        )
    elif block_name.startswith("WD-EXP-"):
        completed_slots = state.get("artifact_progress", {}).get("WD-EXP-SLOT-*", {}).get("completed_slots", [])
        checkpoints["step-9"]["summary"] = explicit or default_step_summary(
            9,
            completed_slots=len(completed_slots),
            total_slots=len(_all_slot_ids(state)),
        )
    elif block_name.startswith("WD-SYN-"):
        completed_slots = state.get("artifact_progress", {}).get("WD-SYN-SLOT-*", {}).get("completed_slots", [])
        checkpoints["step-10"]["summary"] = explicit or default_step_summary(
            10,
            completed_slots=len(completed_slots),
            total_slots=len(_all_slot_ids(state)),
        )


def sync_state_for_blocks(state: dict[str, Any], block_updates: list[tuple[str, str]], summary: str | None, *, working_dir: Path | None = None) -> None:
    for block_name, content in block_updates:
        sync_state_for_block(state, block_name, summary, content=content)
    for block_name, content in block_updates:
        update_counts(state, block_name, content)
    if working_dir is not None:
        _recompute_slot_progress(state, working_dir)
        _recompute_step_progress_checkpoints(state, block_updates)
    for block_name, _content in block_updates:
        _apply_generated_summary(state, block_name, summary)


def upsert_with_sync(
    *,
    working_dir: Path,
    state_path: Path,
    block_updates: list[tuple[str, str]],
    summary: str | None,
    require_receipt_step: int,
) -> dict[str, Any]:
    state = load_yaml(state_path)
    require_receipt(state, expected_step=require_receipt_step)
    slots = state.get("slots") or []
    written: list[str] = []
    for block_name, content in block_updates:
        write_working_draft_file(working_dir, block_name, content, slots)
        written.append(block_name)
        sync_state_for_blocks(state, block_updates, summary, working_dir=working_dir)
    sync_artifact_registry(state, state_path, working_dir, slots, block_updates)
    refresh_receipt(state)
    dump_yaml(state_path, state)
    return {
        "working_dir": str(working_dir),
        "blocks": written,
        "current_step": state.get("current_step"),
        "gate_receipt_step": state["gate_receipt"]["step"],
    }


def main() -> int:
    if not os.environ.get("__CTS_INTERNAL_CALL"):
        print("❌ 本脚本不可直接调用。请使用 run-step.py --advance / --complete --ticket。", file=sys.stderr)
        sys.exit(1)
    parser = argparse.ArgumentParser(description="按 block 安全更新 working draft 目录")
    parser.add_argument("--working-dir", required=True, help="working draft 目录路径")
    parser.add_argument("--state", help="状态文件路径")
    parser.add_argument("--block", required=True, help="待更新的 WD block")
    parser.add_argument("--content", help="block 内容字符串（或通过 stdin 传入）")
    parser.add_argument("--summary", help="对应步骤摘要")
    parser.add_argument("--require-receipt-step", type=int, help="要求 gate_receipt.step 与该值一致")
    parser.add_argument("--sync-state", action="store_true", help="同时同步状态")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    content = args.content
    if content is None and not sys.stdin.isatty():
        content = sys.stdin.read()
    if not content:
        print("缺少内容：请通过 --content 或 stdin 传入 block 正文。", file=sys.stderr)
        return 1

    working_dir = Path(args.working_dir).resolve()
    state_path = Path(args.state).resolve() if args.state else None

    if args.sync_state:
        if not state_path or not args.summary or args.require_receipt_step is None:
            print("sync_state=true 时必须提供 --state、--summary、--require-receipt-step。", file=sys.stderr)
            return 1
        payload = upsert_with_sync(
            working_dir=working_dir,
            state_path=state_path,
            block_updates=[(args.block, content)],
            summary=args.summary,
            require_receipt_step=args.require_receipt_step,
        )
    else:
        state = load_yaml(state_path) if state_path else {}
        slots = state.get("slots") or []
        target = write_working_draft_file(working_dir, args.block, content, slots)
        payload = {"working_dir": str(working_dir), "block": args.block, "target": str(target)}

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload.get("working_dir", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
