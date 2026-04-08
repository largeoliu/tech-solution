import importlib.util
import json
from pathlib import Path

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
