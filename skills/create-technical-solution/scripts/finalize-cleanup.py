# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""执行步骤 12 的原子清理：验证通过后置标志、删除中间产物并结束流程。"""

from __future__ import annotations

import os
import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import compute_state_fingerprint, dump_yaml, iso_now, load_yaml, require_receipt


def load_validator_module(scripts_dir: Path):
    spec = importlib.util.spec_from_file_location("validate_state", scripts_dir / "validate-state.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_sync_module(scripts_dir: Path):
    spec = importlib.util.spec_from_file_location("sync_artifacts_from_draft", scripts_dir / "sync-artifacts-from-draft.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_cleanup(state_path: Path, summary: str) -> tuple[int, dict[str, Any]]:
    if not state_path.exists():
        return 2, {
            "passed": False,
            "error": "state_deleted_before_cleanup_finalization",
            "message": "状态文件不存在。若已删除 state，不应再尝试执行 cleanup finalize。",
            "state_path": str(state_path),
        }

    state = load_yaml(state_path, missing_ok=True)
    require_receipt(state, expected_step=12)
    resolved = state_path.resolve()
    if resolved.name == "meta.yaml":
        repo_root = resolved.parents[4]
    else:
        repo_root = resolved.parents[3]
    draft_value = str(state.get("working_draft_path") or "")
    working_draft = Path(draft_value) if Path(draft_value).is_absolute() else (repo_root / draft_value)
    final_document = repo_root / str(state.get("final_document_path") or "")

    if not working_draft.is_dir():
        return 2, {
            "passed": False,
            "error": "state_deleted_before_cleanup_finalization",
            "message": "working draft 目录在 cleanup finalize 开始前已不存在。必须先保留中间产物，再执行步骤 12。",
            "working_draft_path": str(working_draft),
        }

    scripts_dir = Path(__file__).resolve().parent
    sync_module = load_sync_module(scripts_dir)
    sync_module.sync_artifacts_in_state(state_path, require_receipt_step=12)
    refreshed_after_sync = load_yaml(state_path)
    checkpoints = refreshed_after_sync.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        refreshed_after_sync["checkpoints"] = checkpoints
    step12 = checkpoints.setdefault("step-12", {})
    if not isinstance(step12, dict):
        step12 = {}
        checkpoints["step-12"] = step12
    step12["summary"] = summary
    step12["validator_passed"] = False
    step12["working_draft_deleted"] = False
    step12["state_file_deleted"] = False
    refreshed_after_sync["gate_receipt"] = {
        "step": 12,
        "state_fingerprint": "",
        "validated_at": "",
    }
    refreshed_after_sync["gate_receipt"]["state_fingerprint"] = compute_state_fingerprint(refreshed_after_sync)
    refreshed_after_sync["gate_receipt"]["validated_at"] = iso_now()
    dump_yaml(state_path, refreshed_after_sync)

    validator = load_validator_module(scripts_dir)
    refreshed_state = load_yaml(state_path)
    gate = validator.GateValidator(refreshed_state, state_path)
    errors: list[dict[str, Any]] = []
    gate.step_12(errors)
    if errors:
        return 2, {
            "passed": False,
            "step": 12,
            "summary": validator.build_summary(errors),
            "repair_plan": validator.build_repair_plan(errors),
            "issues": errors,
        }

    refreshed_state["absorption_check_passed"] = True
    refreshed_state["cleanup_allowed"] = True
    step12 = refreshed_state.setdefault("checkpoints", {}).setdefault("step-12", {})
    step12["summary"] = summary
    step12["validator_passed"] = True
    step12["working_draft_deleted"] = False
    step12["state_file_deleted"] = False
    refreshed_state["gate_receipt"] = {
        "step": 12,
        "state_fingerprint": "",
        "validated_at": "",
    }
    refreshed_state["gate_receipt"]["state_fingerprint"] = compute_state_fingerprint(refreshed_state)
    refreshed_state["gate_receipt"]["validated_at"] = iso_now()
    dump_yaml(state_path, refreshed_state)

    import shutil
    shutil.rmtree(str(working_draft))
    if state_path.exists():
        state_parent = state_path.parent
        state_path.unlink(missing_ok=False)
        if state_parent.name != ".state" and not any(state_parent.iterdir()):
            state_parent.rmdir()

    return 0, {
        "passed": True,
        "step": 12,
        "final_document_path": str(final_document),
        "deleted": {
            "working_draft": not working_draft.exists(),
            "state_file": not state_path.exists(),
        },
    }


def main() -> int:
    if not os.environ.get("__CTS_INTERNAL_CALL"):
        print("❌ 本脚本不可直接调用。请使用 run-step.py --prepare / --complete --ticket。", file=sys.stderr)
        sys.exit(1)
    parser = argparse.ArgumentParser(description="步骤 12 原子清理：先验证，再置标志并删除中间产物")
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--summary", required=True, help="写入 checkpoints.step-12.summary 的摘要")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    args = parser.parse_args()

    exit_code, payload = run_cleanup(Path(args.state).resolve(), args.summary)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if payload.get("passed"):
            print("cleanup finalize 成功：working draft 与状态文件已删除。")
        else:
            print(payload.get("message") or payload.get("error") or "cleanup finalize 失败")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
