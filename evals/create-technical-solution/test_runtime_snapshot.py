from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml


skill_root = Path(__file__).parent.parent.parent / "skills" / "create-technical-solution"
scripts_root = skill_root / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), scripts_root / f"{name}.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_load_runtime_snapshot_resolves_core_state_and_paths(tmp_path: Path) -> None:
    runtime_snapshot = load_script("runtime_snapshot")

    repo = tmp_path / "sample-project"
    state_dir = repo / ".architecture" / ".state" / "create-technical-solution"
    template_dir = repo / ".architecture" / "templates"
    solution_dir = repo / ".architecture" / "technical-solutions"
    state_dir.mkdir(parents=True)
    template_dir.mkdir(parents=True)
    solution_dir.mkdir(parents=True)

    state_path = state_dir / "sample-solution.yaml"
    state = {
        "current_step": 9,
        "template_path": ".architecture/templates/technical-solution-template.md",
        "working_draft_path": ".architecture/.state/create-technical-solution/sample-solution.working.md",
        "final_document_path": ".architecture/technical-solutions/sample-solution.md",
    }
    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    snapshot = runtime_snapshot.load_runtime_snapshot(state_path)

    assert snapshot.state_path == state_path.resolve()
    assert snapshot.repo_root == repo.resolve()
    assert snapshot.slug == "sample-solution"
    assert snapshot.state == state
    assert snapshot.current_step == 9
    assert snapshot.template_path == (repo / ".architecture/templates/technical-solution-template.md").resolve()
    assert snapshot.working_draft_path == (repo / ".architecture/.state/create-technical-solution/sample-solution.working.md").resolve()
    assert snapshot.final_document_path == (repo / ".architecture/technical-solutions/sample-solution.md").resolve()


def test_load_runtime_snapshot_falls_back_to_slug_based_paths(tmp_path: Path) -> None:
    runtime_snapshot = load_script("runtime_snapshot")

    repo = tmp_path / "sample-project"
    state_dir = repo / ".architecture" / ".state" / "create-technical-solution"
    state_dir.mkdir(parents=True)

    state_path = state_dir / "sample-solution.yaml"
    state = {
        "current_step": 3,
    }
    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    snapshot = runtime_snapshot.load_runtime_snapshot(state_path)

    assert snapshot.slug == "sample-solution"
    assert snapshot.current_step == 3
    assert snapshot.template_path == (repo / ".architecture/templates/technical-solution-template.md").resolve()
    assert snapshot.working_draft_path == (repo / ".architecture/.state/create-technical-solution/sample-solution.working.md").resolve()
    assert snapshot.final_document_path == (repo / ".architecture/technical-solutions/sample-solution.md").resolve()
