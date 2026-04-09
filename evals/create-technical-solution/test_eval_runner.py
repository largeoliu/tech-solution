import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[2]
EVAL_RUNNER_PATH = ROOT / "evals" / "create-technical-solution" / "eval_runner.py"
TEMPLATE_PATH = ROOT / "skills" / "create-technical-solution" / "templates" / "_template.yaml"


def load_eval_runner():
    spec = importlib.util.spec_from_file_location("create_technical_solution_eval_runner", EVAL_RUNNER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_state_template_matches_live_skill_template():
    runner = load_eval_runner()
    live_template = yaml.safe_load(TEMPLATE_PATH.read_text(encoding="utf-8"))

    assert runner.load_state_template() == live_template


def test_cmd_fixture_uses_live_state_template(tmp_path, monkeypatch):
    runner = load_eval_runner()
    monkeypatch.setattr(runner, "FIXTURES_DIR", tmp_path)

    cases = [
        {
            "query": "新增订单支付模块",
            "expected_behavior": ["full"],
            "tags": ["T01"],
            "files": [],
            "notes": "",
        }
    ]

    runner.cmd_fixture(cases, "T01", all_cases=False)

    fixture_files = sorted(tmp_path.glob("*.json"))
    assert len(fixture_files) == 1

    fixture = json.loads(fixture_files[0].read_text(encoding="utf-8"))
    state_template = fixture["state_template"]

    assert state_template == runner.load_state_template()
    assert state_template["pending_questions"] == []
    assert "blocked" not in state_template
    assert "block_reason" not in state_template


def test_setup_project_uses_state_dir_layout(tmp_path):
    runner = load_eval_runner()
    target = tmp_path / "sample-project"

    runner.cmd_setup_project(str(target))

    assert (target / ".architecture" / ".state" / "create-technical-solution").exists()
    assert (target / ".architecture" / "technical-solutions").exists()
    assert not (target / ".architecture" / "technical-solutions" / "working-drafts").exists()


def test_eval_runner_installed_copy_smoke(tmp_path):
    install_root = tmp_path / "installed"
    installed_eval_dir = install_root / "evals" / "create-technical-solution"
    installed_skill_dir = install_root / "skills" / "create-technical-solution"
    shutil.copytree(EVAL_RUNNER_PATH.parent, installed_eval_dir)
    shutil.copytree(ROOT / "skills" / "create-technical-solution", installed_skill_dir)
    copied_runner = installed_eval_dir / "eval_runner.py"

    result = subprocess.run(
        ["python3", str(copied_runner), "fixture", "电商平台"],
        capture_output=True,
        text=True,
        check=False,
        cwd=install_root,
    )

    assert result.returncode == 0
    assert "Fixture 已生成" in result.stdout
    assert any((installed_eval_dir / "fixtures").glob("*.json"))


def _installed_copy_workspace(tmp_path):
    install_root = tmp_path / "installed"
    installed_eval_dir = install_root / "evals" / "create-technical-solution"
    installed_skill_dir = install_root / "skills" / "create-technical-solution"
    shutil.copytree(EVAL_RUNNER_PATH.parent, installed_eval_dir)
    shutil.copytree(ROOT / "skills" / "create-technical-solution", installed_skill_dir)
    copied_runner = installed_eval_dir / "eval_runner.py"
    copied_run_step = installed_skill_dir / "scripts" / "run-step.py"
    copied_doctor = installed_skill_dir / "scripts" / "runtime_doctor.py"

    workspace = tmp_path / "ws"
    r = subprocess.run(
        ["python3", str(copied_runner), "setup-project", str(workspace)],
        capture_output=True, text=True, check=False,
    )
    assert r.returncode == 0, f"setup-project failed: {r.stderr}"

    state_path = (
        workspace / ".architecture" / ".state"
        / "create-technical-solution" / "test-slug.yaml"
    )
    return install_root, copied_run_step, copied_doctor, state_path


def test_emit_scaffold_installed_copy_smoke(tmp_path):
    install_root, run_step, _, state_path = _installed_copy_workspace(tmp_path)

    for extra_args, label in [
        (["--complete", "--summary", "test", "--slug", "test-slug"], "step-1"),
        (["--complete", "--summary", "prerequisites checked"], "step-2"),
        (["--complete", "--summary", "template loaded"], "step-3"),
        (
            [
                "--complete", "--summary", "tier set",
                "--solution-type", "新功能方案",
            ],
            "step-4",
        ),
        (
            ["--complete", "--summary", "members selected", "--member", "SYSTEMS_ARCHITECT"],
            "step-5",
        ),
        (["--complete", "--summary", "repowiki checked"], "step-6"),
    ]:
        r = subprocess.run(
            ["python3", str(run_step), "--state", str(state_path)] + extra_args,
            capture_output=True, text=True, check=False, cwd=install_root,
        )
        assert r.returncode == 0, f"{label} failed: {r.stderr}\n{r.stdout}"

    result = subprocess.run(
        ["python3", str(run_step), "--state", str(state_path), "--emit-scaffold"],
        capture_output=True, text=True, check=False, cwd=install_root,
    )
    assert result.returncode == 0, f"emit-scaffold failed: {result.stderr}"
    assert "WD-CTX" in result.stdout


def test_runtime_doctor_installed_copy_smoke(tmp_path):
    install_root, run_step, doctor, state_path = _installed_copy_workspace(tmp_path)

    r = subprocess.run(
        ["python3", str(run_step), "--state", str(state_path),
         "--complete", "--summary", "test", "--slug", "test-slug"],
        capture_output=True, text=True, check=False, cwd=install_root,
    )
    assert r.returncode == 0, f"Step 1 failed: {r.stderr}"

    result = subprocess.run(
        ["python3", str(doctor), "--state", str(state_path),
         "--step", "1", "--format", "json"],
        capture_output=True, text=True, check=False, cwd=install_root,
    )
    assert result.returncode == 0, f"Doctor failed: {result.stdout}\n{result.stderr}"
    payload = json.loads(result.stdout)
    assert "passed" in payload
    assert "issues" in payload
