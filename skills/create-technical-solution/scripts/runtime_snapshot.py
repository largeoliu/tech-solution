# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import (
    DEFAULT_TEMPLATE_PATH,
    final_document_relative_path,
    load_yaml,
    repo_root_from_state_path,
    resolve_repo_path,
    slug_from_state_path,
    working_draft_relative_path,
)


@dataclass(frozen=True)
class RuntimeSnapshot:
    state_path: Path
    repo_root: Path
    slug: str
    state: dict[str, Any]
    current_step: int
    working_draft_path: Path
    template_path: Path
    final_document_path: Path


def load_runtime_snapshot(state_path: Path) -> RuntimeSnapshot:
    resolved_state_path = state_path.resolve()
    state = load_yaml(resolved_state_path, missing_ok=True)
    repo_root = repo_root_from_state_path(resolved_state_path)
    slug = slug_from_state_path(resolved_state_path)
    working_draft_path = resolve_repo_path(
        repo_root,
        state.get("working_draft_path"),
        default_relative=working_draft_relative_path(slug),
    )
    template_path = resolve_repo_path(
        repo_root,
        state.get("template_path"),
        default_relative=DEFAULT_TEMPLATE_PATH,
    )
    final_document_path = resolve_repo_path(
        repo_root,
        state.get("final_document_path"),
        default_relative=final_document_relative_path(slug),
    )
    if working_draft_path is None:
        raise SystemExit(f"无法解析 working_draft_path：state 中无此字段且无默认值 (slug={slug})")
    if template_path is None:
        raise SystemExit(f"无法解析 template_path：state 中无此字段且无默认值 (slug={slug})")
    if final_document_path is None:
        raise SystemExit(f"无法解析 final_document_path：state 中无此字段且无默认值 (slug={slug})")
    return RuntimeSnapshot(
        state_path=resolved_state_path,
        repo_root=repo_root,
        slug=slug,
        state=state,
        current_step=int(state.get("current_step") or 1),
        working_draft_path=working_draft_path,
        template_path=template_path,
        final_document_path=final_document_path,
    )
