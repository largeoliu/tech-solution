# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""从 working draft 反推稳定产物，并可回写状态文件。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import dump_yaml, load_yaml, refresh_receipt, require_receipt

ARTIFACT_PATTERNS = {
    "WD-CTX": re.compile(r"^\s*#{2,6}\s+WD-CTX\b", re.MULTILINE),
    "WD-TASK": re.compile(r"^\s*#{2,6}\s+WD-TASK\b", re.MULTILINE),
    "WD-SYN": re.compile(r"^\s*#{2,6}\s+WD-SYN\b", re.MULTILINE),
    "WD-SYN-LIGHT": re.compile(r"^\s*#{2,6}\s+WD-SYN-LIGHT\b", re.MULTILINE),
}


def resolve_path(value: Any, base: Path) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else (base / path).resolve()


def sync_artifacts(content: str, selected_members: list[str]) -> list[str]:
    artifacts: list[str] = []
    for artifact, pattern in ARTIFACT_PATTERNS.items():
        if pattern.search(content):
            artifacts.append(artifact)
    for member in selected_members:
        artifact = f"WD-EXP-{str(member).upper()}"
        if re.search(rf"^\s*#{{2,6}}\s+{re.escape(artifact)}\b", content, re.MULTILINE):
            artifacts.append(artifact)
    return artifacts


def sync_artifacts_in_state(state_path: Path, require_receipt_step: int | None = None) -> list[str]:
    state = load_yaml(state_path)
    repo_root = state_path.parent.parent.parent.parent
    draft_path = resolve_path(state.get("working_draft_path") or "", repo_root)
    if not draft_path.exists():
        raise SystemExit(f"working draft 不存在: {draft_path}")
    if require_receipt_step is not None:
        require_receipt(state, expected_step=require_receipt_step)
    checkpoints = state.get("checkpoints") or {}
    step5 = checkpoints.get("step-5") if isinstance(checkpoints, dict) else {}
    raw_members = step5.get("selected_members") if isinstance(step5, dict) else []
    selected_members = [str(item) for item in raw_members if str(item).strip()] if isinstance(raw_members, list) else []
    artifacts = sync_artifacts(draft_path.read_text(encoding="utf-8"), selected_members)
    state["produced_artifacts"] = artifacts
    refresh_receipt(state)
    dump_yaml(state_path, state)
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="从 working draft 反推产物列表并可回写状态")
    parser.add_argument("--working-draft", required=True, help="working draft 路径")
    parser.add_argument("--state", help="状态文件路径；若提供则回写 produced_artifacts")
    parser.add_argument("--write", action="store_true", help="是否回写状态文件")
    parser.add_argument("--require-receipt-step", type=int, help="要求 gate_receipt.step 与该值一致")
    args = parser.parse_args()

    draft_path = Path(args.working_draft).resolve()
    if not draft_path.exists():
        print(f"working draft 不存在: {draft_path}", file=sys.stderr)
        return 1
    content = draft_path.read_text(encoding="utf-8")
    state: dict[str, Any] = {}
    selected_members: list[str] = []
    if args.state:
        state = load_yaml(Path(args.state).resolve())
        if args.write and args.require_receipt_step is not None:
            require_receipt(state, expected_step=args.require_receipt_step)
        checkpoints = state.get("checkpoints") or {}
        step5 = checkpoints.get("step-5") if isinstance(checkpoints, dict) else {}
        raw_members = step5.get("selected_members") if isinstance(step5, dict) else []
        if isinstance(raw_members, list):
            selected_members = [str(item) for item in raw_members if str(item).strip()]
    artifacts = sync_artifacts(content, selected_members)
    output = {"produced_artifacts": artifacts}

    if args.write and args.state:
        state_path = Path(args.state).resolve()
        sync_artifacts_in_state(state_path, args.require_receipt_step if args.write else None)

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
