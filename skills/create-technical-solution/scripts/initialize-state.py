# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""初始化步骤 1 的最小状态字段。"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"状态文件不存在: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"状态文件必须是 YAML 对象: {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def load_or_create_state(path: Path) -> dict[str, Any]:
    if path.exists():
        return load_yaml(path)
    template_path = Path(__file__).resolve().parents[1] / "templates" / "_template.yaml"
    if not template_path.exists():
        raise SystemExit(f"状态模板不存在: {template_path}")
    state = load_yaml(template_path)
    dump_yaml(path, state)
    return state


def refresh_receipt(state: dict[str, Any], *, step: int, flow_tier: str) -> None:
    state["gate_receipt"] = {
        "step": step,
        "flow_tier": flow_tier,
        "state_fingerprint": "",
        "validated_at": "",
    }
    state["gate_receipt"]["state_fingerprint"] = compute_state_fingerprint(state)
    state["gate_receipt"]["validated_at"] = iso_now()


def initialize_state(
    *,
    state_path: Path,
    slug: str,
    summary: str,
    next_step: int | None,
    solution_root: str,
) -> dict[str, Any]:
    state = load_or_create_state(state_path)

    solution_root_path = Path(solution_root.strip("/"))
    final_document_path = solution_root_path / f"{slug}.md"
    current_flow_tier = str(state.get("flow_tier") or "").strip() or "pending"

    checkpoints = state.setdefault("checkpoints", {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
        state["checkpoints"] = checkpoints
    checkpoints["step-1"] = {
        "summary": summary,
        "slug": slug,
        "scope_ready": True,
        "completed_at": iso_now(),
    }
    state["solution_root"] = str(solution_root_path)
    state["final_document_path"] = str(final_document_path)
    state["flow_tier"] = current_flow_tier
    if next_step is not None:
        state["current_step"] = next_step

    completed = state.setdefault("completed_steps", [])
    if not isinstance(completed, list):
        completed = []
        state["completed_steps"] = completed
    if 1 not in completed:
        completed.append(1)
        completed.sort()

    refresh_receipt(
        state,
        step=int(state.get("current_step") or next_step or 1),
        flow_tier=current_flow_tier,
    )
    dump_yaml(state_path, state)
    return {
        "slug": slug,
        "solution_root": state["solution_root"],
        "final_document_path": state["final_document_path"],
        "current_step": state.get("current_step"),
        "gate_receipt_step": state["gate_receipt"]["step"],
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
