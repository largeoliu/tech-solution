import unittest
from typing import Any, cast

from tests.skill_validation.case_catalog import CASE_INDEX
from tests.skill_validation.helpers import load_review_solution_contract_sources


STEP_MARKERS = {
    1: "### 1. 校验输入完整性",
    2: "### 2. 判断方案类型",
    3: "### 3. 提取核心主张",
    4: "### 4. 代码取证",
    5: "### 5. 归因与分级",
    6: "### 6. 生成改进方案",
    7: "## 10. 输出前自检",
    8: "## 2. 固定输出顺序",
}


def _required_review_step_from_progress(progress: Any) -> int:
    if not progress.inputs_ready:
        return 1
    if not progress.type_classified:
        return 2
    if not progress.claims_extracted:
        return 3
    if not progress.evidence_assigned:
        return 4
    if not progress.issues_classified:
        return 5
    if not progress.recommendations_defined:
        return 6
    if not progress.self_check_passed:
        return 7
    return 8


def _documented_blocked_steps(contract_text: str, step: int) -> tuple[int, ...]:
    marker_positions = {
        documented_step: contract_text.find(marker)
        for documented_step, marker in STEP_MARKERS.items()
    }
    current_position = marker_positions.get(step, -1)
    if current_position == -1:
        return ()

    return tuple(
        documented_step
        for documented_step, position in sorted(marker_positions.items(), key=lambda item: item[1])
        if position != -1 and position > current_position
    )


def _simulate_review_result(progress: Any, action: str) -> str:
    required_step = _required_review_step_from_progress(progress)
    if required_step == 1:
        if action == "await_inputs":
            return "STOP_FORMAL_REVIEW"
        raise AssertionError(f"unsupported action {action!r} for step {required_step}")
    if required_step in (2, 3, 4, 5, 6, 7):
        if action == "await_context":
            return "STOP_AND_ASK"
        raise AssertionError(f"unsupported action {action!r} for step {required_step}")
    if action == "emit_review":
        return "SUCCESS_REVIEW"
    raise AssertionError(f"unsupported action {action!r} for step {required_step}")


class ReviewTechnicalSolutionStepGatingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_review_solution_contract_sources()
        cls.contract_text = "\n".join(cls.sources.values())
        cls.step_contract_snippets = {
            2: (
                "### 2. 判断方案类型",
                "## 2. 分类判定原则",
                "如果分类拿不准，先按更高风险的类别补查，不得因为分类模糊而缩小评审范围。",
            ),
            3: (
                "### 3. 提取核心主张",
                "## 4. 主张提取",
                "- `claim_id`",
                "- `expected_evidence`",
            ),
            4: (
                "### 4. 代码取证",
                "## 5. 代码取证",
                "每条主张只能落在以下三种状态之一：",
                "- `待核验`：当前看不到足够证据",
            ),
            5: (
                "### 5. 归因与分级",
                "## 6. 评审维度判定",
                "## 7. 问题分级规则",
                "分级必须基于证据和影响，不得因为用户紧急程度、作者资深程度或方案文字完整度而调整等级。",
            ),
            6: (
                "### 6. 生成改进方案",
                "## 9. 改进建议规则",
                "- 每个 `blocker` 和 `major` 都必须给出明确改进方案。",
                "- 改进方案要写清：建议动作、涉及对象、预期修正结果、完成后应补的验证证据。",
            ),
            7: (
                "## 10. 输出前自检",
                "正式输出前逐项确认：",
                "## 2. 固定输出顺序",
                "正式评审输出必须严格按以下顺序展开：",
            ),
        }

    def test_review_gate_cases_declare_progress_and_required_step(self) -> None:
        for case_id in ("RTS-10", "RTS-11", "RTS-12", "RTS-13", "RTS-14", "RTS-15"):
            case = cast(Any, CASE_INDEX[case_id])
            for index, turn in enumerate(case.turns, start=1):
                with self.subTest(case_id=case_id, turn=index):
                    self.assertIsNotNone(turn.review_progress)
                    self.assertEqual(turn.required_review_step, _required_review_step_from_progress(turn.review_progress))
                    self.assertEqual(turn.review_turn_action, "await_context")

    def test_review_gate_cases_follow_state_model(self) -> None:
        for case_id in ("RTS-10", "RTS-11", "RTS-12", "RTS-13", "RTS-14", "RTS-15"):
            case = cast(Any, CASE_INDEX[case_id])
            for index, turn in enumerate(case.turns, start=1):
                with self.subTest(case_id=case_id, turn=index):
                    self.assertEqual(
                        turn.expected_result,
                        _simulate_review_result(turn.review_progress, turn.review_turn_action),
                    )

    def test_review_gate_cases_block_all_later_steps(self) -> None:
        for case_id in ("RTS-10", "RTS-11", "RTS-12", "RTS-13", "RTS-14", "RTS-15"):
            case = cast(Any, CASE_INDEX[case_id])
            for index, turn in enumerate(case.turns, start=1):
                with self.subTest(case_id=case_id, turn=index):
                    self.assertEqual(
                        turn.blocked_steps,
                        _documented_blocked_steps(self.contract_text, turn.required_review_step),
                    )

    def test_documented_blocked_steps_track_current_contract_markers(self) -> None:
        full_expected = {
            2: (3, 4, 5, 6, 7, 8),
            3: (4, 5, 6, 7, 8),
            4: (5, 6, 7, 8),
            5: (6, 7, 8),
            6: (7, 8),
            7: (8,),
        }
        for step, blocked_steps in full_expected.items():
            with self.subTest(step=step):
                self.assertEqual(_documented_blocked_steps(self.contract_text, step), blocked_steps)

        contract_without_self_check = self.contract_text.replace(STEP_MARKERS[7], "", 1)
        self.assertEqual(_documented_blocked_steps(contract_without_self_check, 6), (8,))

        contract_without_formal_output = self.contract_text.replace(STEP_MARKERS[8], "", 1)
        self.assertEqual(_documented_blocked_steps(contract_without_formal_output, 7), ())

    def test_review_gate_cases_are_backed_by_current_contract_text(self) -> None:
        stop_docs = {
            2: self.sources["main"] + "\n" + self.sources["analysis_guide"],
            3: self.sources["main"] + "\n" + self.sources["review_process"],
            4: self.sources["main"] + "\n" + self.sources["review_process"],
            5: self.sources["main"] + "\n" + self.sources["review_process"],
            6: self.sources["main"] + "\n" + self.sources["review_process"] + "\n" + self.sources["output_contract"],
            7: self.sources["review_process"] + "\n" + self.sources["output_contract"],
        }
        for case_id in ("RTS-10", "RTS-11", "RTS-12", "RTS-13", "RTS-14", "RTS-15"):
            case = cast(Any, CASE_INDEX[case_id])
            for index, turn in enumerate(case.turns, start=1):
                with self.subTest(case_id=case_id, turn=index):
                    for snippet in self.step_contract_snippets[turn.required_review_step]:
                        self.assertIn(snippet, stop_docs[turn.required_review_step])


if __name__ == "__main__":
    unittest.main()
