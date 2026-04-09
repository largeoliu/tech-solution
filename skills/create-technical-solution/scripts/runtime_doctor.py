# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import dump_yaml, final_document_path_for_slug, load_yaml, refresh_receipt
from protocol_runtime import resolve_repo_path, working_draft_path_for_slug, working_draft_relative_path
from runtime_snapshot import load_runtime_snapshot


@lru_cache(maxsize=1)
def load_validate_state_module():
    spec = importlib.util.spec_from_file_location("validate_state", SCRIPTS_DIR / "validate-state.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def validate_runtime_state(
    state: dict[str, Any],
    *,
    state_path: Path,
    step: int,
) -> dict[str, Any]:
    validator = load_validate_state_module().GateValidator(state, state_path)
    issues: list[dict[str, Any]] = []
    getattr(validator, f"step_{step}")(issues)
    passed = not issues
    payload = {
        "step": step,
        "passed": passed,
        "summary": {"error_count": 0} if passed else load_validate_state_module().build_summary(issues),
        "issues": issues,
        "repair_plan": []
        if passed
        else load_validate_state_module().build_repair_plan(
            issues,
            state_path=state_path,
            state=state,
        ),
    }
    return payload


def receipt_needs_repair(state: dict[str, Any], validation: dict[str, Any]) -> bool:
    issues = validation["issues"]
    receipt = state.get("gate_receipt")
    if validation["passed"]:
        return not isinstance(receipt, dict)
    return bool(issues) and all(issue["code"] == "invalid_gate_receipt" for issue in issues)


def planned_directory_fixes(*, state_path: Path, canonical_draft_path: Path, canonical_final_path: Path) -> list[dict[str, Any]]:
    fixes: list[dict[str, Any]] = []
    for directory in [state_path.parent, canonical_draft_path.parent, canonical_final_path.parent]:
        if directory.exists():
            continue
        fixes.append(
            {
                "code": "create_missing_directory",
                "description": f"create missing canonical directory: {directory}",
                "path": str(directory),
                "applied": False,
                "eligible": True,
            }
        )
    return fixes


def legacy_working_draft_fix(
    *,
    repo_root: Path,
    slug: str,
    state: dict[str, Any],
    canonical_draft_path: Path,
) -> dict[str, Any] | None:
    raw_path = str(state.get("working_draft_path") or "").strip()
    canonical_relative = str(working_draft_relative_path(slug))
    if not raw_path or raw_path == canonical_relative:
        return None
    current_path = resolve_repo_path(repo_root, raw_path)
    if current_path is None or current_path == canonical_draft_path:
        return None
    should_move = current_path.exists() and not canonical_draft_path.exists()
    return {
        "code": "legacy_working_draft_migration",
        "description": f"migrate working draft to canonical state dir: {canonical_relative}",
        "from_path": str(current_path),
        "path": str(canonical_draft_path),
        "applied": False,
        "eligible": True,
        "move_file": should_move,
    }


def receipt_fix_entry(*, step: int) -> dict[str, Any]:
    return {
        "code": "refresh_gate_receipt",
        "description": f"write a valid gate receipt for step {step}",
        "applied": False,
        "eligible": True,
    }


def run_doctor(
    state_path: Path,
    *,
    step: int | None = None,
    apply_safe_fixes: bool = False,
    output_format: str = "text",
) -> tuple[int, dict[str, Any]]:
    snapshot = load_runtime_snapshot(Path(state_path))
    resolved_state_path = snapshot.state_path
    state = load_yaml(resolved_state_path, missing_ok=True)
    resolved_step = int(step or snapshot.current_step or state.get("current_step") or 1)
    canonical_draft_path = working_draft_path_for_slug(repo_root=snapshot.repo_root, slug=snapshot.slug)
    canonical_final_path = final_document_path_for_slug(repo_root=snapshot.repo_root, slug=snapshot.slug)

    safe_fixes = planned_directory_fixes(
        state_path=resolved_state_path,
        canonical_draft_path=canonical_draft_path,
        canonical_final_path=canonical_final_path,
    )
    draft_fix = legacy_working_draft_fix(
        repo_root=snapshot.repo_root,
        slug=snapshot.slug,
        state=state,
        canonical_draft_path=canonical_draft_path,
    )
    if draft_fix is not None:
        safe_fixes.append(draft_fix)

    mutated = False
    if apply_safe_fixes:
        for fix in safe_fixes:
            if not fix["eligible"]:
                continue
            if fix["code"] == "create_missing_directory":
                Path(fix["path"]).mkdir(parents=True, exist_ok=True)
                fix["applied"] = True
                mutated = True
            elif fix["code"] == "legacy_working_draft_migration":
                if fix.get("move_file"):
                    source = Path(fix["from_path"])
                    target = Path(fix["path"])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source), str(target))
                state["working_draft_path"] = str(working_draft_relative_path(snapshot.slug))
                dump_yaml(resolved_state_path, state)
                fix["applied"] = True
                mutated = True

    validation = validate_runtime_state(
        state,
        state_path=resolved_state_path,
        step=resolved_step,
    )

    if receipt_needs_repair(state, validation):
        receipt_fix = receipt_fix_entry(step=resolved_step)
        safe_fixes.append(receipt_fix)
        if apply_safe_fixes:
            refresh_receipt(state, step=resolved_step)
            dump_yaml(resolved_state_path, state)
            receipt_fix["applied"] = True
            mutated = True
            validation = validate_runtime_state(
                state,
                state_path=resolved_state_path,
                step=resolved_step,
            )

    payload = {
        "step": resolved_step,
        "apply_safe_fixes": apply_safe_fixes,
        "passed": validation["passed"],
        "summary": validation["summary"],
        "issues": validation["issues"],
        "repair_plan": validation["repair_plan"],
        "safe_fixes": safe_fixes,
        "state_path": str(resolved_state_path),
        "mutated": mutated,
    }
    exit_code = 0 if validation["passed"] else 2
    if output_format == "json":
        return exit_code, payload
    return exit_code, payload


def format_text(payload: dict[str, Any]) -> str:
    lines = [
        f"runtime doctor: step={payload['step']}",
        "status: PASS" if payload["passed"] else "status: FAIL",
    ]
    for fix in payload["safe_fixes"]:
        prefix = "applied" if fix["applied"] else "proposed"
        lines.append(f"- {prefix}: {fix['code']} - {fix['description']}")
    if payload["issues"]:
        lines.append("issues:")
        for issue in payload["issues"]:
            lines.append(f"- {issue['code']}: {issue['message']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose create-technical-solution runtime state safely")
    parser.add_argument("--state", required=True, help="state file path")
    parser.add_argument("--step", type=int, help="override current step")
    parser.add_argument("--apply-safe-fixes", action="store_true", help="apply structural safe fixes")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="output format")
    args = parser.parse_args()

    exit_code, payload = run_doctor(
        Path(args.state),
        step=args.step,
        apply_safe_fixes=args.apply_safe_fixes,
        output_format=args.format,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_text(payload))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
