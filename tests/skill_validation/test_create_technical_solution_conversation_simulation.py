import unittest
from typing import Any, cast

from tests.skill_validation.case_catalog import CASE_INDEX, CREATE_TECHNICAL_SOLUTION_CASES


def _create_multi_turn_cases() -> tuple[Any, ...]:
    return tuple(case for case in CREATE_TECHNICAL_SOLUTION_CASES if cast(Any, case).turns)


def _contains_any(items: tuple[str, ...], *keywords: str) -> bool:
    return any(any(keyword in item for keyword in keywords) for item in items)


CREATE_GATE_EXPECTATIONS = {
    "CTS-13": (("正式成稿", "共享上下文"), ("第 11 步", "不得进入"), ("absorb-check", "第 11 步")),
    "CTS-14": (("定题", "范围"), ("第 2 步", "不得进入"), ("模板读取", "第 3 步")),
    "CTS-15": (("模板读取", "模板结构摘要"), ("第 4 步", "不得进入"), ("方案类型判定", "第 4 步")),
    "CTS-16": (("方案类型判定", "主类型"), ("第 5 步", "不得进入"), ("成员选择", "第 5 步")),
    "CTS-17": (("成员选择", "参与成员"), ("第 6 步", "不得进入"), ("共享上下文", "第 6 步")),
    "CTS-18": (("共享上下文", "上下文编号"), ("第 7 步", "不得进入"), ("模板任务单", "第 7 步")),
    "CTS-19": (("模板任务单", "槽位"), ("第 8 步", "不得进入"), ("专家逐槽位分析", "第 8 步")),
    "CTS-20": (("专家逐槽位分析", "专家产物"), ("第 9 步", "不得进入"), ("协作收敛", "第 9 步")),
    "CTS-21": (("协作收敛", "选定写法"), ("第 10 步", "不得进入"), ("严格模板成稿", "第 10 步")),
    "CTS-22": (("absorb-check", "working draft"), ("第 12 步", "不得进入"), ("删除 working draft", "第 12 步")),
}


class CreateTechnicalSolutionConversationSimulationTests(unittest.TestCase):
    def test_multi_turn_create_cases_exist(self) -> None:
        multi_turn_case_ids = {case.case_id for case in _create_multi_turn_cases()}
        self.assertTrue(
            {"CTS-13", "CTS-14", "CTS-15", "CTS-16", "CTS-17", "CTS-18", "CTS-19", "CTS-20", "CTS-21", "CTS-22"}.issubset(multi_turn_case_ids)
        )

    def test_create_gate_cases_stop_before_next_step(self) -> None:
        for case_id, (semantic_keywords, safety_keywords, forbidden_keywords) in CREATE_GATE_EXPECTATIONS.items():
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
