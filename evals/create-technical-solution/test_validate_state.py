# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "pytest>=8.0"]
# ///
"""validate-state.py 的 pytest 单元测试"""

import pytest
import sys
from pathlib import Path
import importlib.util

# Load validate_state module
scripts_path = Path(__file__).parent.parent.parent / "skills" / "create-technical-solution" / "scripts"
spec = importlib.util.spec_from_file_location("validate_state", scripts_path / "validate-state.py")
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)


class TestLightFlow:
    def test_step_10_light_pass(self):
        state = {
            "slug": "test",
            "version": 1,
            "flow_tier": "light",
            "current_step": 10,
            "completed_steps": [1,2,3,4,5,6,7],
            "required_artifacts": ["WD-CTX", "WD-SYN-LIGHT"],
            "produced_artifacts": ["WD-CTX", "WD-SYN-LIGHT"],
            "selected_members": ["architect"],
            "blocked": False,
            "block_reason": "",
            "can_enter_step_8": True,
            "can_enter_step_9": False,
            "can_enter_step_10": True,
            "can_enter_step_11": True,
            "can_enter_step_12": True,
            "absorption_check_passed": True,
        }
        validator = vs.GateValidator(state)
        errors = []
        validator.step_10("light", errors)
        assert len(errors) == 0

    def test_step_8_light_skip(self):
        state = {
            "slug": "test",
            "version": 1,
            "flow_tier": "light",
            "current_step": 8,
            "completed_steps": [1,2,3,4,5,6,7],
            "required_artifacts": ["WD-CTX", "WD-SYN-LIGHT"],
            "produced_artifacts": ["WD-CTX"],
            "selected_members": ["architect"],
            "blocked": False,
            "block_reason": "",
            "can_enter_step_8": True,
            "can_enter_step_9": False,
            "can_enter_step_10": True,
            "can_enter_step_11": True,
            "can_enter_step_12": True,
            "absorption_check_passed": False,
        }
        validator = vs.GateValidator(state)
        errors = []
        validator.step_8("light", errors)
        assert len(errors) == 1
        assert errors[0]["code"] == "invalid_step_for_tier"


class TestModerateFlow:
    def test_step_9_moderate_skip(self):
        state = {
            "slug": "test",
            "version": 1,
            "flow_tier": "moderate",
            "current_step": 9,
            "completed_steps": [1,2,3,4,5,6,7,8],
            "required_artifacts": ["WD-CTX", "WD-TASK", "WD-SYN"],
            "produced_artifacts": ["WD-CTX", "WD-TASK"],
            "selected_members": ["architect"],
            "blocked": False,
            "block_reason": "",
            "can_enter_step_8": True,
            "can_enter_step_9": False,
            "can_enter_step_10": True,
            "can_enter_step_11": True,
            "can_enter_step_12": True,
            "absorption_check_passed": False,
        }
        validator = vs.GateValidator(state)
        errors = []
        validator.step_9("moderate", errors)
        assert len(errors) == 1
        assert errors[0]["code"] == "invalid_step_for_tier"

    def test_step_10_moderate_missing_wd_task(self):
        state = {
            "slug": "test",
            "version": 1,
            "flow_tier": "moderate",
            "current_step": 10,
            "completed_steps": [1,2,3,4,5,6,7,8],
            "required_artifacts": ["WD-CTX", "WD-TASK", "WD-SYN"],
            "produced_artifacts": ["WD-CTX"],
            "selected_members": ["architect"],
            "blocked": False,
            "block_reason": "",
            "can_enter_step_8": True,
            "can_enter_step_9": False,
            "can_enter_step_10": True,
            "can_enter_step_11": True,
            "can_enter_step_12": True,
            "absorption_check_passed": False,
        }
        validator = vs.GateValidator(state)
        errors = []
        validator.step_10("moderate", errors)
        assert len(errors) >= 1
        codes = [e["code"] for e in errors]
        assert "missing_artifact" in codes


class TestFullFlow:
    def test_step_9_missing_wd_task(self):
        state = {
            "slug": "test",
            "version": 1,
            "flow_tier": "full",
            "current_step": 9,
            "completed_steps": [1,2,3,4,5,6,7,8],
            "required_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP", "WD-SYN"],
            "produced_artifacts": ["WD-CTX"],
            "selected_members": ["architect"],
            "blocked": False,
            "block_reason": "",
            "can_enter_step_8": True,
            "can_enter_step_9": True,
            "can_enter_step_10": True,
            "can_enter_step_11": True,
            "can_enter_step_12": True,
            "absorption_check_passed": False,
        }
        validator = vs.GateValidator(state)
        errors = []
        validator.step_9("full", errors)
        assert len(errors) >= 1

    def test_step_10_missing_exp(self):
        state = {
            "slug": "test",
            "version": 1,
            "flow_tier": "full",
            "current_step": 10,
            "completed_steps": [1,2,3,4,5,6,7,8,9],
            "required_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP", "WD-SYN"],
            "produced_artifacts": ["WD-CTX", "WD-TASK"],
            "selected_members": ["architect", "backend-dev"],
            "blocked": False,
            "block_reason": "",
            "can_enter_step_8": True,
            "can_enter_step_9": True,
            "can_enter_step_10": True,
            "can_enter_step_11": True,
            "can_enter_step_12": True,
            "absorption_check_passed": False,
        }
        validator = vs.GateValidator(state)
        errors = []
        validator.step_10("full", errors)
        assert len(errors) >= 1

    def test_step_11_pass(self):
        state = {
            "slug": "test",
            "version": 1,
            "flow_tier": "full",
            "current_step": 11,
            "completed_steps": [1,2,3,4,5,6,7,8,9,10],
            "required_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP", "WD-SYN"],
            "produced_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP-architect", "WD-SYN"],
            "selected_members": ["architect"],
            "blocked": False,
            "block_reason": "",
            "can_enter_step_8": True,
            "can_enter_step_9": True,
            "can_enter_step_10": True,
            "can_enter_step_11": True,
            "can_enter_step_12": True,
            "absorption_check_passed": False,
        }
        validator = vs.GateValidator(state)
        errors = []
        validator.step_11("full", errors)
        assert len(errors) == 0

    def test_step_12_pass(self):
        state = {
            "slug": "test",
            "version": 1,
            "flow_tier": "full",
            "current_step": 12,
            "completed_steps": [1,2,3,4,5,6,7,8,9,10,11],
            "required_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP", "WD-SYN"],
            "produced_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP-architect", "WD-SYN"],
            "selected_members": ["architect"],
            "blocked": False,
            "block_reason": "",
            "can_enter_step_8": True,
            "can_enter_step_9": True,
            "can_enter_step_10": True,
            "can_enter_step_11": True,
            "can_enter_step_12": True,
            "absorption_check_passed": True,
        }
        validator = vs.GateValidator(state)
        errors = []
        validator.step_12("full", errors)
        assert len(errors) == 0

    def test_step_12_absorption_not_passed(self):
        state = {
            "slug": "test",
            "version": 1,
            "flow_tier": "full",
            "current_step": 12,
            "completed_steps": [1,2,3,4,5,6,7,8,9,10,11],
            "required_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP", "WD-SYN"],
            "produced_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP-architect", "WD-SYN"],
            "selected_members": ["architect"],
            "blocked": False,
            "block_reason": "",
            "can_enter_step_8": True,
            "can_enter_step_9": True,
            "can_enter_step_10": True,
            "can_enter_step_11": True,
            "can_enter_step_12": True,
            "absorption_check_passed": False,
        }
        validator = vs.GateValidator(state)
        errors = []
        validator.step_12("full", errors)
        assert len(errors) >= 1
        codes = [e["code"] for e in errors]
        assert "absorption_incomplete" in codes


class TestBlockedState:
    def test_blocked_state_blocked(self):
        state = {
            "slug": "test",
            "version": 1,
            "flow_tier": "full",
            "current_step": 7,
            "completed_steps": [1,2,3,4,5,6],
            "required_artifacts": ["WD-CTX"],
            "produced_artifacts": [],
            "selected_members": ["architect"],
            "blocked": True,
            "block_reason": "主题模糊",
            "can_enter_step_8": False,
            "can_enter_step_9": False,
            "can_enter_step_10": False,
            "can_enter_step_11": False,
            "can_enter_step_12": False,
            "absorption_check_passed": False,
        }
        validator = vs.GateValidator(state)
        errors = []
        validator.step_7("full", errors)
        assert len(errors) >= 1
        codes = [e["code"] for e in errors]
        assert "blocked_state" in codes


class TestRepairPlan:
    def test_repair_plan_structure(self):
        issues = [
            {
                "code": "missing_artifact",
                "message": "步骤 10: 缺少 WD-CTX",
                "step": 10,
                "flow_tier": "full",
                "field": "produced_artifacts",
                "missing_artifacts": ["WD-CTX"],
                "recommended_rollback_step": 7,
                "recommended_repair_step": 7,
                "skip_instead_of_retry": False,
            }
        ]
        plan = vs.build_repair_plan(issues)
        assert len(plan) >= 1
        assert plan[0]["step"] == 7

    def test_repair_plan_skip_instead_of_retry(self):
        issues = [
            {
                "code": "invalid_step_for_tier",
                "message": "步骤 8: light 流程不应进入此步骤",
                "step": 8,
                "flow_tier": "light",
                "skip_instead_of_retry": True,
            }
        ]
        plan = vs.build_repair_plan(issues)
        assert len(plan) == 0


class TestJSONOutput:
    def test_json_output_fields_pass(self):
        state = {
            "slug": "test",
            "version": 1,
            "flow_tier": "light",
            "current_step": 10,
            "completed_steps": [1,2,3,4,5,6,7],
            "required_artifacts": ["WD-CTX", "WD-SYN-LIGHT"],
            "produced_artifacts": ["WD-CTX", "WD-SYN-LIGHT"],
            "selected_members": ["architect"],
            "blocked": False,
            "block_reason": "",
            "can_enter_step_8": True,
            "can_enter_step_9": False,
            "can_enter_step_10": True,
            "can_enter_step_11": True,
            "can_enter_step_12": True,
            "absorption_check_passed": True,
        }
        issues = []
        validator = vs.GateValidator(state)
        validator.step_10("light", issues)
        result = {
            "step": 10,
            "flow_tier": "light",
            "passed": len(issues) == 0,
            "summary": vs.build_summary(issues),
            "issues": issues,
        }
        assert result["passed"] is True
        assert "summary" in result
        assert "issues" in result

    def test_json_output_fields_fail(self):
        state = {
            "slug": "test",
            "version": 1,
            "flow_tier": "full",
            "current_step": 10,
            "completed_steps": [1,2,3,4,5,6,7,8,9],
            "required_artifacts": ["WD-CTX", "WD-TASK", "WD-EXP", "WD-SYN"],
            "produced_artifacts": ["WD-CTX", "WD-TASK"],
            "selected_members": ["architect"],
            "blocked": False,
            "block_reason": "",
            "can_enter_step_8": True,
            "can_enter_step_9": True,
            "can_enter_step_10": True,
            "can_enter_step_11": True,
            "can_enter_step_12": True,
            "absorption_check_passed": True,
        }
        issues = []
        validator = vs.GateValidator(state)
        validator.step_10("full", issues)
        result = {
            "step": 10,
            "flow_tier": "full",
            "passed": len(issues) == 0,
            "summary": vs.build_summary(issues),
            "issues": issues,
        }
        assert result["passed"] is False
        assert len(result["issues"]) >= 1


class TestExpectedArtifacts:
    def test_artifacts_for_light_step_11(self):
        artifacts = vs.expected_artifacts_for_step(11, "light")
        assert "WD-CTX" in artifacts
        assert "WD-SYN-LIGHT" in artifacts

    def test_artifacts_for_moderate_step_11(self):
        artifacts = vs.expected_artifacts_for_step(11, "moderate")
        assert "WD-CTX" in artifacts
        assert "WD-TASK" in artifacts
        assert "WD-SYN" in artifacts

    def test_artifacts_for_full_step_11(self):
        artifacts = vs.expected_artifacts_for_step(11, "full")
        assert "WD-CTX" in artifacts
        assert "WD-TASK" in artifacts
        assert "WD-SYN" in artifacts
