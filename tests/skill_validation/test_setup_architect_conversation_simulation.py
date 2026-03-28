import unittest
from typing import Any, cast

from tests.skill_validation.case_catalog import CASE_INDEX, SETUP_ARCHITECT_CASES


def _setup_architect_multi_turn_cases() -> tuple[Any, ...]:
    return tuple(case for case in SETUP_ARCHITECT_CASES if cast(Any, case).turns)


def _contains_any(items: tuple[str, ...], *keywords: str) -> bool:
    return any(any(keyword in item for keyword in keywords) for item in items)


def _contains_all(items: tuple[str, ...], *keywords: str) -> bool:
    return any(all(keyword in item for keyword in keywords) for item in items)


class SetupArchitectConversationSimulationTests(unittest.TestCase):
    def test_multi_turn_setup_architect_cases_exist(self) -> None:
        multi_turn_case_ids = {case.case_id for case in _setup_architect_multi_turn_cases()}

        self.assertIn("SA-13", multi_turn_case_ids)
        self.assertIn("SA-14", multi_turn_case_ids)
        self.assertIn("SA-15", multi_turn_case_ids)
        self.assertIn("SA-16", multi_turn_case_ids)
        self.assertIn("SA-17", multi_turn_case_ids)

    def test_sa_13_simulates_confirm_then_keep_current_template(self) -> None:
        case = cast(Any, CASE_INDEX["SA-13"])

        self.assertEqual(tuple(turn.expected_result for turn in case.turns), ("STOP_AND_ASK", "SUCCESS_INIT"))
        self.assertTrue(_contains_any(case.assert_semantics, "模板"))
        self.assertTrue(_contains_any(case.assert_safety, "总结", "确认前"))
        self.assertTrue(_contains_any(case.forbidden_behavior, "总结", "模板策略"))

        first_turn, second_turn = case.turns
        self.assertEqual(first_turn.expected_result, "STOP_AND_ASK")
        self.assertTrue(_contains_any(first_turn.assert_semantics, "模板"))
        self.assertTrue(_contains_any(first_turn.assert_semantics, "自定义", "定制"))
        self.assertTrue(_contains_any(first_turn.assert_safety, "等待", "暂停"))
        self.assertTrue(_contains_any(first_turn.forbidden_behavior, "总结"))
        self.assertTrue(_contains_any(second_turn.assert_semantics, "保留", "当前模板"))
        self.assertTrue(_contains_any(second_turn.assert_safety, "不发生模板替换", "保留"))

    def test_sa_14_simulates_confirm_then_replace_template(self) -> None:
        case = cast(Any, CASE_INDEX["SA-14"])

        self.assertEqual(
            tuple(turn.expected_result for turn in case.turns),
            ("STOP_AND_ASK", "SUCCESS_REPLACE_TEMPLATE"),
        )

        first_turn, second_turn = case.turns
        self.assertEqual(first_turn.expected_result, "STOP_AND_ASK")
        self.assertTrue(_contains_any(first_turn.assert_semantics, "模板"))
        self.assertTrue(_contains_any(first_turn.assert_semantics, "自定义", "定制"))
        self.assertTrue(_contains_any(first_turn.assert_safety, "等待", "暂停"))
        self.assertIn(".architecture/templates/technical-solution-template.md", second_turn.assert_paths)
        self.assertTrue(_contains_any(second_turn.assert_structure, "整体替换", "单个目标文件"))
        self.assertTrue(_contains_all(second_turn.assert_safety, "局部", "merge"))
        self.assertTrue(_contains_any(second_turn.forbidden_behavior, "局部编辑", "内容合并"))

    def test_multi_turn_cases_keep_safety_gate_before_final_summary(self) -> None:
        for case_id in ("SA-13", "SA-14"):
            case = cast(Any, CASE_INDEX[case_id])
            first_turn = case.turns[0]
            with self.subTest(case_id=case_id):
                self.assertEqual(first_turn.expected_result, "STOP_AND_ASK")
                self.assertTrue(
                    _contains_any(first_turn.assert_semantics, "模板")
                    and _contains_any(first_turn.assert_semantics, "自定义", "定制"),
                    first_turn.assert_semantics,
                )
                self.assertTrue(
                    _contains_any(first_turn.assert_safety, "等待", "暂停"),
                    first_turn.assert_safety,
                )
                self.assertTrue(
                    _contains_any(
                        case.assert_safety + case.forbidden_behavior + first_turn.forbidden_behavior,
                        "总结",
                        "确认前",
                    ),
                    case_id,
                )

    def test_sa_15_stops_before_entering_step_4(self) -> None:
        case = cast(Any, CASE_INDEX["SA-15"])

        self.assertEqual(tuple(turn.expected_result for turn in case.turns), ("STOP_AND_ASK", "STOP_AND_ASK"))
        first_turn, second_turn = case.turns
        self.assertTrue(_contains_any(first_turn.assert_semantics, "成员定制", "成员"))
        self.assertTrue(_contains_any(first_turn.assert_safety, "第 4 步", "不得进入"))
        self.assertTrue(_contains_any(first_turn.forbidden_behavior, "第 4 步", "原则定制"))
        self.assertTrue(_contains_any(second_turn.assert_semantics, "成员定制", "项目上下文"))
        self.assertTrue(_contains_any(second_turn.assert_safety, "第 4 步", "不得进入"))

    def test_sa_16_stops_before_entering_step_5(self) -> None:
        case = cast(Any, CASE_INDEX["SA-16"])

        self.assertEqual(tuple(turn.expected_result for turn in case.turns), ("STOP_AND_ASK", "STOP_AND_ASK"))
        first_turn, second_turn = case.turns
        self.assertTrue(_contains_any(first_turn.assert_semantics, "原则定制", "原则"))
        self.assertTrue(_contains_any(first_turn.assert_safety, "第 5 步", "不得进入"))
        self.assertTrue(_contains_any(first_turn.forbidden_behavior, "第 5 步", "结构复核"))
        self.assertTrue(_contains_any(second_turn.assert_semantics, "原则定制", "项目上下文"))
        self.assertTrue(_contains_any(second_turn.assert_safety, "第 5 步", "不得进入"))

    def test_sa_17_stops_before_entering_step_6(self) -> None:
        case = cast(Any, CASE_INDEX["SA-17"])

        self.assertEqual(tuple(turn.expected_result for turn in case.turns), ("STOP_AND_ASK", "STOP_AND_ASK"))
        first_turn, second_turn = case.turns
        self.assertTrue(_contains_any(first_turn.assert_semantics, "结构复核", "结构验证"))
        self.assertTrue(_contains_any(first_turn.assert_safety, "第 6 步", "不得进入"))
        self.assertTrue(_contains_any(first_turn.forbidden_behavior, "第 6 步", "模板"))
        self.assertTrue(_contains_any(second_turn.assert_semantics, "结构复核", "结构验证"))
        self.assertTrue(_contains_any(second_turn.assert_safety, "第 6 步", "不得进入"))


if __name__ == "__main__":
    unittest.main()
