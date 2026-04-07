# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""执行步骤 12 的原子清理：验证通过后置标志、删除中间产物并结束流程。"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"状态文件必须是 YAML 对象: {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def load_validator_module(scripts_dir: Path):
    spec = importlib.util.spec_from_file_location("validate_state", scripts_dir / "validate-state.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_cleanup(state_path: Path, flow_tier: str, summary: str) -> tuple[int, dict[str, Any]]:
    if not state_path.exists():
        return 2, {
            "passed": False,
            "error": "state_deleted_before_cleanup_finalization",
            "message": "状态文件不存在。若已删除 state，不应再尝试执行 cleanup finalize。",
            "state_path": str(state_path),
        }

    state = load_yaml(state_path)
    repo_root = state_path.parent.parent.parent.parent
    working_draft = repo_root / str(state.get("working_draft_path") or "")
    final_document = repo_root / str(state.get("final_document_path") or "")

    if not working_draft.exists():
        return 2, {
            "passed": False,
            "error": "state_deleted_before_cleanup_finalization",
            "message": "working draft 在 cleanup finalize 开始前已不存在。必须先保留中间产物，再执行步骤 12。",
            "working_draft_path": str(working_draft),
        }

    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints
    step12 = checkpoints.setdefault("step-12", {})
    if not isinstance(step12, dict):
        step12 = {}
        checkpoints["step-12"] = step12
    step12["summary"] = summary
    step12["validator_passed"] = False
    step12["working_draft_deleted"] = False
    step12["state_file_deleted"] = False
    state["updated_at"] = iso_now()
    dump_yaml(state_path, state)

    validator = load_validator_module(Path(__file__).resolve().parent)
    refreshed_state = load_yaml(state_path)
    gate = validator.GateValidator(refreshed_state, state_path)
    errors: list[dict[str, Any]] = []
    gate.step_12(flow_tier, errors)
    if errors:
        return 2, {
            "passed": False,
            "step": 12,
            "flow_tier": flow_tier,
            "summary": validator.build_summary(errors),
            "repair_plan": validator.build_repair_plan(errors),
            "issues": errors,
        }

    refreshed_state["absorption_check_passed"] = True
    refreshed_state["cleanup_allowed"] = True
    refreshed_state["updated_at"] = iso_now()
    step12 = refreshed_state.setdefault("checkpoints", {}).setdefault("step-12", {})
    step12["summary"] = summary
    step12["validator_passed"] = True
    step12["working_draft_deleted"] = False
    step12["state_file_deleted"] = False
    dump_yaml(state_path, refreshed_state)

    working_draft.unlink(missing_ok=False)
    state_path.unlink(missing_ok=False)

    return 0, {
        "passed": True,
        "step": 12,
        "flow_tier": flow_tier,
        "final_document_path": str(final_document),
        "deleted": {
            "working_draft": not working_draft.exists(),
            "state_file": not state_path.exists(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="步骤 12 原子清理：先验证，再置标志并删除中间产物")
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--flow-tier", choices=["light", "moderate", "full"], required=True, help="流程级别")
    parser.add_argument("--summary", required=True, help="写入 checkpoints.step-12.summary 的摘要")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    args = parser.parse_args()

    exit_code, payload = run_cleanup(Path(args.state).resolve(), args.flow_tier, args.summary)
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
