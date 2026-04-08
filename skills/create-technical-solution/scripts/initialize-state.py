# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""初始化步骤 1 的最小状态字段。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"状态文件不存在: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"状态文件必须是 YAML 对象: {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


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


def require_receipt(state: dict[str, Any], expected_step: int, expected_flow_tier: str) -> None:
    receipt = state.get("gate_receipt")
    if not isinstance(receipt, dict):
        raise SystemExit("缺少 gate_receipt，必须先运行 validate-state.py --write-pass-receipt。")
    if int(receipt.get("step") or 0) != expected_step:
        raise SystemExit(f"gate_receipt.step={receipt.get('step')}，期望 {expected_step}。")
    if str(receipt.get("flow_tier") or "") != expected_flow_tier:
        raise SystemExit(f"gate_receipt.flow_tier={receipt.get('flow_tier')}，期望 {expected_flow_tier}。")
    if str(receipt.get("state_fingerprint") or "") != compute_state_fingerprint(state):
        raise SystemExit("gate_receipt.state_fingerprint 与当前状态不一致，请重新运行 validator。")


def initialize_state(
    *,
    state_path: Path,
    slug: str,
    summary: str,
    next_step: int | None,
    solution_root: str,
) -> dict[str, Any]:
    state = load_yaml(state_path)
    require_receipt(state, expected_step=1, expected_flow_tier="light")

    solution_root_path = Path(solution_root.strip("/"))
    final_document_path = solution_root_path / f"{slug}.md"

    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints
    checkpoints["step-1"] = {
        "summary": summary,
        "slug": slug,
        "scope_ready": True,
    }
    state["solution_root"] = str(solution_root_path)
    state["final_document_path"] = str(final_document_path)
    if next_step is not None:
        state["current_step"] = next_step

    completed = state.setdefault("completed_steps", [])
    if not isinstance(completed, list):
        completed = []
        state["completed_steps"] = completed
    if 1 not in completed:
        completed.append(1)
        completed.sort()

    dump_yaml(state_path, state)
    return {
        "slug": slug,
        "solution_root": state["solution_root"],
        "final_document_path": state["final_document_path"],
        "current_step": state.get("current_step"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化步骤 1 的最小状态字段")
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--slug", required=True, help="方案 slug")
    parser.add_argument("--summary", required=True, help="写入 checkpoints.step-1.summary 的摘要")
    parser.add_argument("--solution-root", default=".architecture/technical-solutions", help="最终文档根目录")
    parser.add_argument("--next-step", type=int, default=2, help="设置 current_step")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    args = parser.parse_args()

    payload = initialize_state(
        state_path=Path(args.state).resolve(),
        slug=args.slug.strip(),
        summary=args.summary,
        next_step=args.next_step,
        solution_root=args.solution_root,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"步骤 1 已初始化: {payload['final_document_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

