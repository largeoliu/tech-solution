import unittest
import re
from typing import Any, cast

from tests.skill_validation.case_catalog import CASE_INDEX
from tests.skill_validation.helpers import load_setup_contract_sources


def _required_step_from_progress(progress: Any) -> int:
    if not progress.members_customized:
        return 3
    if not progress.principles_customized:
        return 4
    if not progress.structure_verified:
        return 5
    return 6
def _documented_blocked_steps(main_skill: str, step: int) -> tuple[int, ...]:
    edges = {int(current): int(nxt) for current, nxt in re.findall(r"未完成第 (\d) 步，不得进入第 (\d) 步。", main_skill)}
    blocked_steps: list[int] = []
    current = step
    while current in edges:
        nxt = edges[current]
        blocked_steps.append(nxt)
        current = nxt
    return tuple(blocked_steps)


def _simulate_setup_result(progress: Any, action: str) -> str:
    required_step = _required_step_from_progress(progress)
    if required_step in (3, 4, 5):
        if action == "await_context":
            return "STOP_AND_ASK"
        raise AssertionError(f"unsupported action {action!r} for step {required_step}")

    if action == "await_template_decision":
        return "STOP_AND_ASK"
    if action == "keep_current_template":
        return "SUCCESS_INIT"
    if action == "replace_template":
        return "SUCCESS_REPLACE_TEMPLATE"
    raise AssertionError(f"unsupported action {action!r} for step {required_step}")


class SetupArchitectStepGatingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_setup_contract_sources()

    def test_gate_cases_declare_progress_and_required_step(self) -> None:
        for case_id in ("SA-13", "SA-14", "SA-15", "SA-16", "SA-17"):
            case = cast(Any, CASE_INDEX[case_id])
            for index, turn in enumerate(case.turns, start=1):
                with self.subTest(case_id=case_id, turn=index):
                    progress = turn.setup_progress
                    self.assertIsNotNone(progress)
                    self.assertEqual(turn.required_setup_step, _required_step_from_progress(progress))
                    self.assertTrue(turn.setup_turn_action)

    def test_gate_cases_follow_setup_state_machine(self) -> None:
        for case_id in ("SA-13", "SA-14", "SA-15", "SA-16", "SA-17"):
            case = cast(Any, CASE_INDEX[case_id])
            for index, turn in enumerate(case.turns, start=1):
                with self.subTest(case_id=case_id, turn=index):
                    self.assertEqual(
                        turn.expected_result,
                        _simulate_setup_result(turn.setup_progress, turn.setup_turn_action),
                    )

    def test_unresolved_gate_turns_block_all_later_steps(self) -> None:
        for case_id in ("SA-13", "SA-14", "SA-15", "SA-16", "SA-17"):
            case = cast(Any, CASE_INDEX[case_id])
            for index, turn in enumerate(case.turns, start=1):
                if turn.expected_result != "STOP_AND_ASK":
                    continue
                with self.subTest(case_id=case_id, turn=index):
                    self.assertEqual(
                        turn.blocked_steps,
                        _documented_blocked_steps(self.sources["main"], turn.required_setup_step),
                    )

    def test_unresolved_gate_turns_are_backed_by_stop_and_ask_contract_text(self) -> None:
        stop_docs = {
            3: self.sources["member_customization"],
            4: self.sources["principles_customization"],
            5: self.sources["installation"],
            6: self.sources["main"] + "\n" + self.sources["template_customization"],
        }
        for case_id in ("SA-13", "SA-14", "SA-15", "SA-16", "SA-17"):
            case = cast(Any, CASE_INDEX[case_id])
            for index, turn in enumerate(case.turns, start=1):
                if turn.expected_result != "STOP_AND_ASK":
                    continue
                with self.subTest(case_id=case_id, turn=index):
                    self.assertIn("STOP_AND_ASK", stop_docs[turn.required_setup_step])

    def test_step_3_must_block_steps_4_to_6(self) -> None:
        case = cast(Any, CASE_INDEX["SA-15"])
        for turn in case.turns:
            self.assertEqual(turn.required_setup_step, 3)
            self.assertEqual(turn.blocked_steps, (4, 5, 6))

    def test_step_4_must_block_steps_5_to_6(self) -> None:
        case = cast(Any, CASE_INDEX["SA-16"])
        for turn in case.turns:
            self.assertEqual(turn.required_setup_step, 4)
            self.assertEqual(turn.blocked_steps, (5, 6))

    def test_step_5_must_block_step_6(self) -> None:
        case = cast(Any, CASE_INDEX["SA-17"])
        for turn in case.turns:
            self.assertEqual(turn.required_setup_step, 5)
            self.assertEqual(turn.blocked_steps, (6,))

    def test_template_question_only_appears_after_steps_3_to_5(self) -> None:
        for case_id in ("SA-13", "SA-14"):
            case = cast(Any, CASE_INDEX[case_id])
            first_turn = case.turns[0]
            with self.subTest(case_id=case_id):
                self.assertEqual(first_turn.required_setup_step, 6)
                self.assertTrue(first_turn.setup_progress.members_customized)
                self.assertTrue(first_turn.setup_progress.principles_customized)
                self.assertTrue(first_turn.setup_progress.structure_verified)


if __name__ == "__main__":
    unittest.main()
