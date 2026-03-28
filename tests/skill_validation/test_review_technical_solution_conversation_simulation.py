import unittest
from typing import Any, cast

from tests.skill_validation.case_catalog import CASE_INDEX, REVIEW_TECHNICAL_SOLUTION_CASES


def _review_multi_turn_cases() -> tuple[Any, ...]:
    return tuple(case for case in REVIEW_TECHNICAL_SOLUTION_CASES if cast(Any, case).turns)


def _contains_any(items: tuple[str, ...], *keywords: str) -> bool:
    return any(any(keyword in item for keyword in keywords) for item in items)


REVIEW_GATE_EXPECTATIONS = {
    "RTS-10": (("方案类型", "主类型"), ("第 3 步", "不得进入"), ("主张提取", "第 3 步")),
    "RTS-11": (("核心主张", "主张清单"), ("第 4 步", "不得进入"), ("代码取证", "第 4 步")),
    "RTS-12": (("证据核验", "待核验"), ("第 5 步", "不得进入"), ("归因与分级", "第 5 步")),
    "RTS-13": (("归因", "分级"), ("第 6 步", "不得进入"), ("改进方案", "第 6 步")),
    "RTS-14": (("改进方案", "验证动作"), ("第 7 步", "不得进入"), ("输出前自检", "第 7 步")),
    "RTS-15": (("输出前自检", "自检"), ("第 8 步", "不得进入"), ("正式输出", "第 8 步")),
}


class ReviewTechnicalSolutionConversationSimulationTests(unittest.TestCase):
    def test_multi_turn_review_cases_exist(self) -> None:
        multi_turn_case_ids = {case.case_id for case in _review_multi_turn_cases()}
        self.assertTrue(
            {"RTS-10", "RTS-11", "RTS-12", "RTS-13", "RTS-14", "RTS-15"}.issubset(multi_turn_case_ids)
        )

    def test_review_gate_cases_stop_before_next_step(self) -> None:
        for case_id, (semantic_keywords, safety_keywords, forbidden_keywords) in REVIEW_GATE_EXPECTATIONS.items():
            case = cast(Any, CASE_INDEX[case_id])
            first_turn, second_turn = case.turns
            with self.subTest(case_id=case_id):
                self.assertEqual(
                    tuple(turn.expected_result for turn in case.turns),
                    ("STOP_AND_ASK", "STOP_AND_ASK"),
                )
                self.assertTrue(_contains_any(first_turn.assert_semantics, *semantic_keywords))
                self.assertTrue(_contains_any(first_turn.assert_safety, *safety_keywords))
                self.assertTrue(_contains_any(first_turn.forbidden_behavior, *forbidden_keywords))
                self.assertTrue(_contains_any(second_turn.assert_semantics, *semantic_keywords))
                self.assertTrue(_contains_any(second_turn.assert_safety, *safety_keywords))
                self.assertTrue(_contains_any(second_turn.forbidden_behavior, *forbidden_keywords))


if __name__ == "__main__":
    unittest.main()
