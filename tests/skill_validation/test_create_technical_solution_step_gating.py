import re
import unittest
from typing import Any, cast

from tests.skill_validation.case_catalog import CASE_INDEX
from tests.skill_validation.helpers import load_create_solution_contract_sources


def _required_create_step_from_progress(progress: Any) -> int:
    if not progress.scope_clarified:
        return 1
    if not progress.prerequisites_ready:
        return 2
    if not progress.template_read:
        return 3
    if not progress.solution_typed:
        return 4
    if not progress.participants_selected:
        return 5
    if not progress.context_built:
        return 6
    if not progress.task_sheet_ready:
        return 7
    if not progress.expert_analysis_complete:
        return 8
    if not progress.synthesis_complete:
        return 9
    if not progress.draft_written:
        return 10
    if not progress.absorb_check_passed:
        return 11
    return 12


def _documented_blocked_steps(contract_text: str, step: int) -> tuple[int, ...]:
    edges = {int(current): int(nxt) for current, nxt in re.findall(r"未完成第 (\d+) 步，不得进入第 (\d+) 步。", contract_text)}
    blocked_steps: list[int] = []
    current = step
    while current in edges:
        current = edges[current]
        blocked_steps.append(current)
    return tuple(blocked_steps)


def _simulate_create_result(progress: Any, action: str) -> str:
    required_step = _required_create_step_from_progress(progress)
    if required_step == 1:
        if action == "await_scope":
            return "STOP_AND_ASK"
        raise AssertionError(f"unsupported action {action!r} for step {required_step}")
    if required_step == 2:
        if action == "redirect_setup":
            return "STOP_AND_REDIRECT"
        raise AssertionError(f"unsupported action {action!r} for step {required_step}")
    if required_step in (3, 4, 5, 6, 7, 8, 9, 10, 11):
        if action == "await_context":
            return "STOP_AND_ASK"
        raise AssertionError(f"unsupported action {action!r} for step {required_step}")
    if action == "save_solution":
        return "SUCCESS_CREATE"
    raise AssertionError(f"unsupported action {action!r} for step {required_step}")


class CreateTechnicalSolutionStepGatingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_create_solution_contract_sources()
        cls.contract_text = "\n".join(cls.sources.values())

    def test_create_gate_cases_declare_progress_and_required_step(self) -> None:
        for case_id in ("CTS-13", "CTS-14", "CTS-15", "CTS-16", "CTS-17", "CTS-18", "CTS-19", "CTS-20", "CTS-21", "CTS-22"):
            case = cast(Any, CASE_INDEX[case_id])
            for index, turn in enumerate(case.turns, start=1):
                with self.subTest(case_id=case_id, turn=index):
                    self.assertIsNotNone(turn.create_progress)
                    self.assertEqual(turn.required_create_step, _required_create_step_from_progress(turn.create_progress))

    def test_create_gate_cases_follow_state_model(self) -> None:
        for case_id in ("CTS-13", "CTS-14", "CTS-15", "CTS-16", "CTS-17", "CTS-18", "CTS-19", "CTS-20", "CTS-21", "CTS-22"):
            case = cast(Any, CASE_INDEX[case_id])
            for index, turn in enumerate(case.turns, start=1):
                with self.subTest(case_id=case_id, turn=index):
                    self.assertEqual(
                        turn.expected_result,
                        _simulate_create_result(turn.create_progress, turn.create_turn_action),
                    )

    def test_create_gate_cases_block_all_later_steps(self) -> None:
        for case_id in ("CTS-13", "CTS-14", "CTS-15", "CTS-16", "CTS-17", "CTS-18", "CTS-19", "CTS-20", "CTS-21", "CTS-22"):
            case = cast(Any, CASE_INDEX[case_id])
            for index, turn in enumerate(case.turns, start=1):
                with self.subTest(case_id=case_id, turn=index):
                    self.assertEqual(
                        turn.blocked_steps,
                        _documented_blocked_steps(self.contract_text, turn.required_create_step),
                    )

    def test_absorb_check_case_blocks_working_draft_deletion(self) -> None:
        case = cast(Any, CASE_INDEX["CTS-22"])
        for index, turn in enumerate(case.turns, start=1):
            with self.subTest(turn=index):
                self.assertEqual(turn.required_create_step, 11)
                self.assertEqual(turn.blocked_steps, (12,))


if __name__ == "__main__":
    unittest.main()
