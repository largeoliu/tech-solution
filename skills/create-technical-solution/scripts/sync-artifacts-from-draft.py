# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""从 working draft 目录反推稳定产物，并可回写状态文件。"""

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

from protocol_runtime import decision_truth_path, dump_yaml, expert_truth_complete, expert_truth_files, load_yaml, refresh_receipt, repo_root_from_state_path, require_receipt


def sync_artifacts(working_dir: Path, slots: list[dict[str, Any]], state: dict[str, Any] | None = None) -> tuple[list[str], dict[str, Any]]:
    artifacts: list[str] = []
    progress: dict[str, Any] = {}
    ctx_path = working_dir / "ctx.json"
    if ctx_path.exists() and ctx_path.stat().st_size > 0:
        artifacts.append("WD-CTX")
    task_path = working_dir / "task.json"
    if task_path.exists() and task_path.stat().st_size > 0:
        artifacts.append("WD-TASK")
    exp_completed: list[str] = []
    syn_completed: list[str] = []
    for slot_info in slots:
        slot_id = slot_info.get("slot", "")
        if not slot_id:
            continue
        exp_files = expert_truth_files(working_dir, slot_id)
        if exp_files:
            artifacts.append(f"WD-EXP-{slot_id}")
            if state is not None and expert_truth_complete(state=state, working_dir=working_dir, slot_id=slot_id):
                exp_completed.append(slot_id)
        syn_path = decision_truth_path(working_dir, slot_id)
        if syn_path.exists() and syn_path.stat().st_size > 0:
            artifacts.append(f"WD-SYN-{slot_id}")
            syn_completed.append(slot_id)
    exp_completed.sort()
    syn_completed.sort()
    progress = {
        "WD-EXP-SLOT-*": {"completed_slots": exp_completed},
        "WD-SYN-SLOT-*": {"completed_slots": syn_completed},
    }
    return artifacts, progress


def resolve_path(value: Any, base: Path) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else (base / path).resolve()


def sync_artifacts_in_state(state_path: Path, require_receipt_step: int | None = None) -> tuple[list[str], dict[str, Any]]:
    state = load_yaml(state_path)
    repo_root = repo_root_from_state_path(state_path)
    draft_path = resolve_path(state.get("working_draft_path") or "", repo_root)
    if not draft_path.is_dir():
        raise SystemExit(f"working draft 目录不存在: {draft_path}")
    if require_receipt_step is not None:
        require_receipt(state, expected_step=require_receipt_step)
    slots = state.get("slots") or []
    artifacts, progress = sync_artifacts(draft_path, slots, state)
    state["produced_artifacts"] = artifacts
    state["artifact_progress"] = progress
    refresh_receipt(state)
    dump_yaml(state_path, state)
    return artifacts, progress


def main() -> int:
    if not os.environ.get("__CTS_INTERNAL_CALL"):
        print("❌ 本脚本不可直接调用。请使用 run-step.py --advance / --complete --ticket。", file=sys.stderr)
        sys.exit(1)
    parser = argparse.ArgumentParser(description="从 working draft 目录反推产物列表并可回写状态")
    parser.add_argument("--working-dir", required=True, help="working draft 目录路径")
    parser.add_argument("--state", help="状态文件路径；若提供则回写 produced_artifacts")
    parser.add_argument("--write", action="store_true", help="是否回写状态文件")
    parser.add_argument("--require-receipt-step", type=int, help="要求 gate_receipt.step 与该值一致")
    args = parser.parse_args()

    working_dir = Path(args.working_dir).resolve()
    if not working_dir.is_dir():
        print(f"working draft 目录不存在: {working_dir}", file=sys.stderr)
        return 1
    state: dict[str, Any] = {}
    slots: list[dict[str, Any]] = []
    if args.state:
        state = load_yaml(Path(args.state).resolve())
        slots = state.get("slots") or []
    artifacts, progress = sync_artifacts(working_dir, slots)
    output = {"produced_artifacts": artifacts, "artifact_progress": progress}

    if args.write and args.state:
        state_path = Path(args.state).resolve()
        sync_artifacts_in_state(state_path, args.require_receipt_step if args.write else None)

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
