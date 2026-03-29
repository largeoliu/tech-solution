# Skill Sequential Gating Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce strict first-unmet-step gating across `review-technical-solution` and `create-technical-solution`, then prove that behavior with catalog, conversation-simulation, step-gating, lifecycle, and full-suite validation.

**Architecture:** Keep this as one phased plan because both skill hardenings share `tests/skill_validation/case_catalog.py`, the multi-turn metadata model, and the runbook/phase-order docs. Ship the work in two independently verifiable slices: harden `review-technical-solution` first, then harden `create-technical-solution`, and finally align the validation runbook/design docs with the new gating coverage.

**Tech Stack:** Markdown skill contracts, Python 3 standard library (`unittest`, `dataclasses`, `re`), existing `tests/skill_validation` harness

---

## File Structure

- Read: `docs/superpowers/specs/2026-03-28-skill-sequential-gating-hardening-design.md` - approved design baseline; every task in this plan must map back to it.
- Modify: `skills/review-technical-solution/SKILL.md` - add explicit `2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8` gate wording and step-completion stop semantics.
- Modify: `skills/review-technical-solution/references/review-process.md` - add completion criteria, self-check release gate, and first-unmet-step rollback wording.
- Modify: `skills/review-technical-solution/references/review-analysis-guide.md` - make multi-type union completion a formal prerequisite to later review steps.
- Modify: `skills/review-technical-solution/references/review-output-contract.md` - forbid final output from inventing fresh evidence, type, grading, or recommendation logic.
- Modify: `skills/create-technical-solution/SKILL.md` - add explicit `1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12` gate wording and tail-gate behavior.
- Modify: `skills/create-technical-solution/references/solution-process.md` - define completion evidence for template digest, member roster, shared context, task sheet, expert completion, synthesis, and draft rollback.
- Modify: `skills/create-technical-solution/references/progress-transparency.md` - convert display boundaries into enforced stage gates.
- Modify: `skills/create-technical-solution/references/working-draft-protocol.md` - turn `absorb-check -> delete` into a formal lifecycle contract.
- Modify: `tests/skill_validation/case_catalog.py` - extend `ConversationTurn` with review/create gating metadata, add `ReviewProgress` and `CreateProgress`, convert `CTS-13` into a multi-turn draft gate, and add new `RTS-*` / `CTS-*` gate cases.
- Create: `tests/skill_validation/test_review_technical_solution_conversation_simulation.py` - lock multi-turn review gate behavior at the conversation layer.
- Create: `tests/skill_validation/test_review_technical_solution_step_gating.py` - lock review step progression, blocked steps, and stop semantics against contract text.
- Create: `tests/skill_validation/test_create_technical_solution_conversation_simulation.py` - lock multi-turn create-solution gate behavior at the conversation layer.
- Create: `tests/skill_validation/test_create_technical_solution_step_gating.py` - lock create step progression, blocked steps, rollback rules, and absorb-check lifecycle.
- Modify: `tests/skill_validation/test_review_technical_solution_contracts.py` - strengthen review contract tests from wording-only checks to explicit gate-order checks.
- Modify: `tests/skill_validation/test_create_technical_solution_contracts.py` - strengthen create contract tests for explicit gates, rollback, and absorb-check lifecycle.
- Modify: `tests/skill_validation/test_case_catalog.py` - update total counts, phase ordering, and multi-turn metadata assertions.
- Modify: `tests/skill_validation/test_workflow_integration.py` - keep the runbook/examples aligned with the expanded case matrix.
- Modify: `docs/superpowers/testing/skill-validation.md` - update layer map, phase rollout, and representative cases for the new behavior suite.
- Modify: `docs/superpowers/specs/2026-03-26-skill-validation-design.md` - document the new gating-focused validation layers and new representative cases.
- Modify: `docs/superpowers/specs/2026-03-27-review-technical-solution-design.md` - align the original review skill design with the now-approved sequential gating model.

### Task 1: Add Review Gating Metadata and Failing Behavior Tests

**Files:**
- Create: `tests/skill_validation/test_review_technical_solution_conversation_simulation.py`
- Create: `tests/skill_validation/test_review_technical_solution_step_gating.py`
- Modify: `tests/skill_validation/case_catalog.py`
- Modify: `tests/skill_validation/test_case_catalog.py`

- [ ] **Step 1: Write the failing review conversation-simulation test**

Create `tests/skill_validation/test_review_technical_solution_conversation_simulation.py` with this full content:

```python
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
        self.assertEqual(
            multi_turn_case_ids,
            {"RTS-10", "RTS-11", "RTS-12", "RTS-13", "RTS-14", "RTS-15"},
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write the failing review step-gating state-model test**

Create `tests/skill_validation/test_review_technical_solution_step_gating.py` with this full content:

```python
import re
import unittest
from typing import Any, cast

from tests.skill_validation.case_catalog import CASE_INDEX
from tests.skill_validation.helpers import load_review_solution_contract_sources


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
    edges = {int(current): int(nxt) for current, nxt in re.findall(r"未完成第 (\d+) 步，不得进入第 (\d+) 步。", contract_text)}
    blocked_steps: list[int] = []
    current = step
    while current in edges:
        current = edges[current]
        blocked_steps.append(current)
    return tuple(blocked_steps)


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

    def test_review_gate_cases_are_backed_by_stop_and_ask_contract_text(self) -> None:
        stop_docs = {
            2: self.sources["main"] + "\n" + self.sources["analysis_guide"],
            3: self.sources["main"] + "\n" + self.sources["review_process"],
            4: self.sources["main"] + "\n" + self.sources["review_process"],
            5: self.sources["main"] + "\n" + self.sources["review_process"],
            6: self.sources["main"] + "\n" + self.sources["review_process"],
            7: self.sources["main"] + "\n" + self.sources["review_process"] + "\n" + self.sources["output_contract"],
        }
        for case_id in ("RTS-10", "RTS-11", "RTS-12", "RTS-13", "RTS-14", "RTS-15"):
            case = cast(Any, CASE_INDEX[case_id])
            for index, turn in enumerate(case.turns, start=1):
                with self.subTest(case_id=case_id, turn=index):
                    self.assertIn("STOP_AND_ASK", stop_docs[turn.required_review_step])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the new review behavior tests to verify they fail first**

Run: `python3 -m unittest tests.skill_validation.test_review_technical_solution_conversation_simulation tests.skill_validation.test_review_technical_solution_step_gating -v`
Expected: FAIL because `RTS-10` through `RTS-15`, `ReviewProgress`, and the new `ConversationTurn` review metadata do not exist yet.

- [ ] **Step 4: Extend `case_catalog.py` with review progress metadata and six review gate cases**

In `tests/skill_validation/case_catalog.py`, add the review progress dataclass directly after `SetupProgress` and extend `ConversationTurn` with review fields:

```python
@dataclass(frozen=True)
class ReviewProgress:
    inputs_ready: bool = False
    type_classified: bool = False
    claims_extracted: bool = False
    evidence_assigned: bool = False
    issues_classified: bool = False
    recommendations_defined: bool = False
    self_check_passed: bool = False


@dataclass(frozen=True)
class ConversationTurn:
    user_input: str
    expected_result: str
    assert_paths: Tuple[str, ...] = ()
    assert_structure: Tuple[str, ...] = ()
    assert_semantics: Tuple[str, ...] = ()
    assert_safety: Tuple[str, ...] = ()
    forbidden_behavior: Tuple[str, ...] = ()
    setup_progress: SetupProgress | None = None
    required_setup_step: int | None = None
    setup_turn_action: str | None = None
    blocked_steps: Tuple[int, ...] = ()
    review_progress: ReviewProgress | None = None
    required_review_step: int | None = None
    review_turn_action: str | None = None
```

Then append these six cases to `REVIEW_TECHNICAL_SOLUTION_CASES` immediately after `RTS-09`:

```python
    vcase(
        "RTS-10",
        "review-technical-solution",
        "流程场景层",
        "review-solution-complete-inputs",
        "正式输入齐全，但方案类型仍拿不准时，review-technical-solution 必须停在第 2 步。",
        "验证未完成第 2 步时不会进入第 3 到 8 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在方案类型判定",),
        assert_safety=("未完成第 2 步不得进入第 3 步",),
        forbidden_behavior=("进入第 3 步", "进入第 4 步", "进入第 8 步"),
        turns=(
            ConversationTurn(
                user_input="四类正式输入都给你了，但主类型和附加类型还没判定清楚。不要跳去提取主张。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("方案类型判定", "主类型", "附加类型"),
                assert_safety=("未完成第 2 步，不得进入第 3 步。",),
                forbidden_behavior=("进入第 3 步", "主张提取", "正式输出"),
                review_progress=ReviewProgress(inputs_ready=True),
                required_review_step=2,
                review_turn_action="await_context",
                blocked_steps=(3, 4, 5, 6, 7, 8),
            ),
            ConversationTurn(
                user_input="类型结论还是不稳定，先别继续做主张清单。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("方案类型判定", "主类型", "附加类型"),
                assert_safety=("未完成第 2 步，不得进入第 3 步。",),
                forbidden_behavior=("进入第 3 步", "进入第 8 步"),
                review_progress=ReviewProgress(inputs_ready=True),
                required_review_step=2,
                review_turn_action="await_context",
                blocked_steps=(3, 4, 5, 6, 7, 8),
            ),
        ),
    ),
    vcase(
        "RTS-11",
        "review-technical-solution",
        "流程场景层",
        "review-solution-complete-inputs",
        "方案类型已判定，但关键主张清单仍不完整时，review-technical-solution 必须停在第 3 步。",
        "验证未完成第 3 步时不会进入第 4 到 8 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在核心主张清单",),
        assert_safety=("未完成第 3 步不得进入第 4 步",),
        forbidden_behavior=("进入第 4 步", "进入第 8 步"),
        turns=(
            ConversationTurn(
                user_input="主类型和附加类型可以先按当前判断保留，但关键主张还没列全，不要继续查代码。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("核心主张", "主张清单"),
                assert_safety=("未完成第 3 步，不得进入第 4 步。",),
                forbidden_behavior=("进入第 4 步", "代码取证", "正式输出"),
                review_progress=ReviewProgress(inputs_ready=True, type_classified=True),
                required_review_step=3,
                review_turn_action="await_context",
                blocked_steps=(4, 5, 6, 7, 8),
            ),
            ConversationTurn(
                user_input="主张列表还是缺字段和核验方式，先别进入代码取证。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("核心主张", "主张清单"),
                assert_safety=("未完成第 3 步，不得进入第 4 步。",),
                forbidden_behavior=("进入第 4 步", "进入第 8 步"),
                review_progress=ReviewProgress(inputs_ready=True, type_classified=True),
                required_review_step=3,
                review_turn_action="await_context",
                blocked_steps=(4, 5, 6, 7, 8),
            ),
        ),
    ),
    vcase(
        "RTS-12",
        "review-technical-solution",
        "流程场景层",
        "review-solution-complete-inputs",
        "关键主张已提取，但证据状态矩阵仍不完整时，review-technical-solution 必须停在第 4 步。",
        "验证未完成第 4 步时不会进入第 5 到 8 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在证据核验矩阵",),
        assert_safety=("未完成第 4 步不得进入第 5 步",),
        forbidden_behavior=("进入第 5 步", "进入第 8 步"),
        turns=(
            ConversationTurn(
                user_input="主张清单可以保留，但有几条关键主张还没有证据状态，不要继续归因分级。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("证据核验", "待核验"),
                assert_safety=("未完成第 4 步，不得进入第 5 步。",),
                forbidden_behavior=("进入第 5 步", "归因与分级", "正式输出"),
                review_progress=ReviewProgress(inputs_ready=True, type_classified=True, claims_extracted=True),
                required_review_step=4,
                review_turn_action="await_context",
                blocked_steps=(5, 6, 7, 8),
            ),
            ConversationTurn(
                user_input="先别分级，还有主张没有落到 已证实 / 已证伪 / 待核验。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("证据核验", "待核验"),
                assert_safety=("未完成第 4 步，不得进入第 5 步。",),
                forbidden_behavior=("进入第 5 步", "进入第 8 步"),
                review_progress=ReviewProgress(inputs_ready=True, type_classified=True, claims_extracted=True),
                required_review_step=4,
                review_turn_action="await_context",
                blocked_steps=(5, 6, 7, 8),
            ),
        ),
    ),
    vcase(
        "RTS-13",
        "review-technical-solution",
        "流程场景层",
        "review-solution-complete-inputs",
        "证据状态已齐，但问题归因与分级仍不完整时，review-technical-solution 必须停在第 5 步。",
        "验证未完成第 5 步时不会进入第 6 到 8 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在归因与分级",),
        assert_safety=("未完成第 5 步不得进入第 6 步",),
        forbidden_behavior=("进入第 6 步", "进入第 8 步"),
        turns=(
            ConversationTurn(
                user_input="证据状态先保留，但问题维度和严重级别还没闭合，不要先给改进方案。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("归因", "分级"),
                assert_safety=("未完成第 5 步，不得进入第 6 步。",),
                forbidden_behavior=("进入第 6 步", "改进方案", "正式输出"),
                review_progress=ReviewProgress(
                    inputs_ready=True,
                    type_classified=True,
                    claims_extracted=True,
                    evidence_assigned=True,
                ),
                required_review_step=5,
                review_turn_action="await_context",
                blocked_steps=(6, 7, 8),
            ),
            ConversationTurn(
                user_input="还有问题没有完成归因与级别，先别写改进动作。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("归因", "分级"),
                assert_safety=("未完成第 5 步，不得进入第 6 步。",),
                forbidden_behavior=("进入第 6 步", "进入第 8 步"),
                review_progress=ReviewProgress(
                    inputs_ready=True,
                    type_classified=True,
                    claims_extracted=True,
                    evidence_assigned=True,
                ),
                required_review_step=5,
                review_turn_action="await_context",
                blocked_steps=(6, 7, 8),
            ),
        ),
    ),
    vcase(
        "RTS-14",
        "review-technical-solution",
        "流程场景层",
        "review-solution-complete-inputs",
        "归因与分级已完成，但 blocker / major 对应的改进方案还没闭合时，review-technical-solution 必须停在第 6 步。",
        "验证未完成第 6 步时不会进入第 7 到 8 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在改进方案",),
        assert_safety=("未完成第 6 步不得进入第 7 步",),
        forbidden_behavior=("进入第 7 步", "进入第 8 步"),
        turns=(
            ConversationTurn(
                user_input="问题分级先保留，但高优先级问题的修正动作和验证方式还没写全，不要进入输出前自检。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("改进方案", "验证动作"),
                assert_safety=("未完成第 6 步，不得进入第 7 步。",),
                forbidden_behavior=("进入第 7 步", "输出前自检", "正式输出"),
                review_progress=ReviewProgress(
                    inputs_ready=True,
                    type_classified=True,
                    claims_extracted=True,
                    evidence_assigned=True,
                    issues_classified=True,
                ),
                required_review_step=6,
                review_turn_action="await_context",
                blocked_steps=(7, 8),
            ),
            ConversationTurn(
                user_input="改进动作还是不完整，先别进入输出前自检。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("改进方案", "验证动作"),
                assert_safety=("未完成第 6 步，不得进入第 7 步。",),
                forbidden_behavior=("进入第 7 步", "进入第 8 步"),
                review_progress=ReviewProgress(
                    inputs_ready=True,
                    type_classified=True,
                    claims_extracted=True,
                    evidence_assigned=True,
                    issues_classified=True,
                ),
                required_review_step=6,
                review_turn_action="await_context",
                blocked_steps=(7, 8),
            ),
        ),
    ),
    vcase(
        "RTS-15",
        "review-technical-solution",
        "流程场景层",
        "review-solution-complete-inputs",
        "前六步都已完成，但输出前自检尚未通过时，review-technical-solution 必须停在第 7 步。",
        "验证未完成第 7 步时不会进入第 8 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在输出前自检",),
        assert_safety=("未完成第 7 步不得进入第 8 步",),
        forbidden_behavior=("进入第 8 步",),
        turns=(
            ConversationTurn(
                user_input="类型、主张、证据、分级和改进动作先按当前结果保留，但输出前自检还没通过，不要直接生成正式评审。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("输出前自检", "自检"),
                assert_safety=("未完成第 7 步，不得进入第 8 步。",),
                forbidden_behavior=("进入第 8 步", "正式输出"),
                review_progress=ReviewProgress(
                    inputs_ready=True,
                    type_classified=True,
                    claims_extracted=True,
                    evidence_assigned=True,
                    issues_classified=True,
                    recommendations_defined=True,
                ),
                required_review_step=7,
                review_turn_action="await_context",
                blocked_steps=(8,),
            ),
            ConversationTurn(
                user_input="先别出正式评审，自检还没闭合。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("输出前自检", "自检"),
                assert_safety=("未完成第 7 步，不得进入第 8 步。",),
                forbidden_behavior=("进入第 8 步",),
                review_progress=ReviewProgress(
                    inputs_ready=True,
                    type_classified=True,
                    claims_extracted=True,
                    evidence_assigned=True,
                    issues_classified=True,
                    recommendations_defined=True,
                ),
                required_review_step=7,
                review_turn_action="await_context",
                blocked_steps=(8,),
            ),
        ),
    ),
```

- [ ] **Step 5: Update `test_case_catalog.py` for the new review cases before any review docs are hardened**

Make these exact edits in `tests/skill_validation/test_case_catalog.py`:

```python
EXPECTED_PHASE_1 = {
    "SA-01",
    "SA-02",
    "SA-13",
    "SA-15",
    "SA-16",
    "SA-17",
    "SA-07",
    "SA-08",
    "CTS-01",
    "CTS-02",
    "CTS-04",
    "CTS-07",
    "CTS-08",
    "RTS-01",
    "RTS-02",
    "RTS-03",
    "RTS-10",
    "RTS-11",
    "RTS-12",
    "RTS-13",
    "RTS-14",
    "RTS-15",
}

EXPECTED_PHASE_1_ORDER = (
    "SA-01",
    "SA-02",
    "SA-13",
    "SA-15",
    "SA-16",
    "SA-17",
    "SA-07",
    "SA-08",
    "CTS-01",
    "CTS-02",
    "CTS-04",
    "CTS-07",
    "CTS-08",
    "RTS-01",
    "RTS-02",
    "RTS-03",
    "RTS-10",
    "RTS-11",
    "RTS-12",
    "RTS-13",
    "RTS-14",
    "RTS-15",
)

def test_catalog_contains_all_design_cases(self) -> None:
    self.assertEqual(len(ALL_CASES), 45)
    self.assertEqual({case.case_id for case in ALL_CASES}, EXPECTED_CASE_IDS)
    self.assertEqual(PHASE_1_CASE_IDS, EXPECTED_PHASE_1_ORDER)
    self.assertEqual(PHASE_2_CASE_IDS, EXPECTED_PHASE_2_ORDER)
    self.assertEqual(PHASE_3_CASE_IDS, EXPECTED_PHASE_3_ORDER)
    self.assertEqual(len(PHASE_1_CASE_IDS), len(set(PHASE_1_CASE_IDS)))
    self.assertEqual(len(PHASE_2_CASE_IDS), len(set(PHASE_2_CASE_IDS)))
    self.assertEqual(len(PHASE_3_CASE_IDS), len(set(PHASE_3_CASE_IDS)))

def test_rts_10_to_rts_15_stay_in_phase_1(self) -> None:
    for case_id in ("RTS-10", "RTS-11", "RTS-12", "RTS-13", "RTS-14", "RTS-15"):
        with self.subTest(case_id=case_id):
            self.assertIn(case_id, PHASE_1_CASE_IDS)
            self.assertEqual(CASE_INDEX[case_id].expected_result, "STOP_AND_ASK")
```

- [ ] **Step 6: Run the focused review catalog and behavior tests and make sure they pass**

Run: `python3 -m unittest tests.skill_validation.test_case_catalog tests.skill_validation.test_review_technical_solution_conversation_simulation tests.skill_validation.test_review_technical_solution_step_gating -v`
Expected: PASS.

- [ ] **Step 7: Commit the review gating metadata slice**

```bash
git add tests/skill_validation/case_catalog.py tests/skill_validation/test_case_catalog.py tests/skill_validation/test_review_technical_solution_conversation_simulation.py tests/skill_validation/test_review_technical_solution_step_gating.py
git commit -m "test(validation): add review step-gating cases"
```

### Task 2: Harden Review Contracts to Match the New Review Gating Tests

**Files:**
- Modify: `skills/review-technical-solution/SKILL.md`
- Modify: `skills/review-technical-solution/references/review-process.md`
- Modify: `skills/review-technical-solution/references/review-analysis-guide.md`
- Modify: `skills/review-technical-solution/references/review-output-contract.md`
- Modify: `tests/skill_validation/test_review_technical_solution_contracts.py`

- [ ] **Step 1: Extend the review contract test so the new gating rules fail first**

Append these test methods to `tests/skill_validation/test_review_technical_solution_contracts.py`:

```python
    def test_main_skill_locks_review_step_chain(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "### 2. 判断方案类型",
                "未完成第 2 步，不得进入第 3 步。",
                "### 3. 提取核心主张",
                "未完成第 3 步，不得进入第 4 步。",
                "### 4. 代码取证",
                "未完成第 4 步，不得进入第 5 步。",
                "### 5. 归因与分级",
                "未完成第 5 步，不得进入第 6 步。",
                "### 6. 生成改进方案",
                "未完成第 6 步，不得进入第 7 步。",
                "### 7. 输出前自检",
                "未完成第 7 步，不得进入第 8 步。",
                "### 8. 正式输出",
            ),
        )

    def test_review_process_promotes_self_check_to_release_gate(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["review_process"],
            (
                "## 10. 输出前自检",
                "未完成第 7 步，不得进入第 8 步。",
                "本轮结果为 `STOP_AND_ASK`。",
                "只允许回到第一个未完成步骤修正。",
            ),
        )

    def test_output_contract_forbids_new_reasoning_in_final_output(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["output_contract"],
            (
                "正式输出只能消费前七步已经闭合的结果。",
                "不得在正式输出阶段新增主类型 / 附加类型判断。",
                "不得在正式输出阶段补做主张提取、证据状态判定、问题分级或改进动作。",
            ),
        )
```

- [ ] **Step 2: Run the review contract test to verify it fails for the missing gate wording**

Run: `python3 -m unittest tests.skill_validation.test_review_technical_solution_contracts -v`
Expected: FAIL because the current review skill docs do not yet declare the explicit `2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8` gate chain or the self-check release gate.

- [ ] **Step 3: Update the review skill docs with exact hard-gate wording and completion rules**

Replace the `## 高层工作流` section in `skills/review-technical-solution/SKILL.md` with this exact block:

```markdown
## 高层工作流

### 1. 校验输入完整性

缺少必要上下文时立即停止，不输出 `通过`、`需修改` 或 `阻断`。

### 2. 判断方案类型

先判断方案属于哪一类主要变更，再识别是否同时涉及跨模块、数据、接口、部署或治理等附加影响范围。

完成条件：已经给出 `主类型`、`附加类型` 和本次评审必须执行的检查并集。

未完成第 2 步，不得进入第 3 步。
若类型依据仍不足，本轮结果为 `STOP_AND_ASK`，停在方案类型判定。

### 3. 提取核心主张

从需求与方案中提取目标、非目标、约束、复用能力、变更边界、接口、数据结构、测试与发布策略。

完成条件：关键主张清单完整，且每条主张都具备后续核验所需字段。

未完成第 3 步，不得进入第 4 步。
若关键主张仍不完整，本轮结果为 `STOP_AND_ASK`，停在核心主张提取。

### 4. 代码取证

在相关项目代码中核验核心主张是否成立、边界是否匹配、依赖是否存在。不能因为用户催促、方案写得完整，或“看起来合理”就跳过代码核验。

完成条件：每条关键主张都已落到 `已证实`、`已证伪` 或 `待核验` 之一，并附证据或缺证原因。

未完成第 4 步，不得进入第 5 步。
若证据状态矩阵仍不完整，本轮结果为 `STOP_AND_ASK`，停在代码取证。

### 5. 归因与分级

按需求对齐、架构对齐、代码现状对齐、完整性、可落地性归因问题，并基于证据与影响分级。

完成条件：所有问题或风险都已补齐归因维度与严重级别。

未完成第 5 步，不得进入第 6 步。
若归因与分级仍不完整，本轮结果为 `STOP_AND_ASK`，停在归因与分级。

### 6. 生成改进方案

每个重要问题都要给出可执行的改进方向与验证动作。

完成条件：所有 `blocker` / `major` 项都绑定了改进动作与验证方式。

未完成第 6 步，不得进入第 7 步。
若改进动作仍不完整，本轮结果为 `STOP_AND_ASK`，停在改进方案。

### 7. 输出前自检

正式输出前，必须确认前 1 到 6 步已经闭合，且不存在仍会影响结论的未完成项。

未完成第 7 步，不得进入第 8 步。
若自检未通过，本轮结果为 `STOP_AND_ASK`，并回到第一个未完成步骤修正。

### 8. 正式输出

正式输出只消费前 1 到 7 步已经闭合的结果，不得在这一阶段新增类型判断、证据判断、问题分级或改进动作。
```

In `skills/review-technical-solution/references/review-process.md`, make these exact additions:

```markdown
## 3. 方案分类与评审焦点确定

- 先根据方案目标判断主类型，再判断是否同时命中多个类型。
- 分类依据使用 `references/review-analysis-guide.md`。
- 如果同时命中多类：评审问题取并集，必查证据取并集，最终结论按最高严重级别判定。
- 分类只是帮助确定重点，不得因为某一类检查通过就跳过其余必要核验。
- 完成第 2 步的最低标准是：主类型、附加类型和检查并集都已明确。
- 未完成第 2 步，不得进入第 3 步。
- 若分类依据仍不足，本轮结果为 `STOP_AND_ASK`。

## 4. 主张提取

- `claim_id`
- `statement`
- `assumption`
- `expected_evidence`
- `risk_if_wrong`

- 所有关键主张都必须补齐最小字段集后，才算完成第 3 步。
- 未完成第 3 步，不得进入第 4 步。
- 若关键主张仍缺字段或缺核验方式，本轮结果为 `STOP_AND_ASK`。

## 5. 代码取证

- 对每条主张在 `相关项目代码` 中寻找直接证据。
- 每条主张只能落在 `已证实`、`已证伪`、`待核验` 三种状态之一。
- 找不到复用能力时，不能按“应该有”处理；必须标记为 `待核验` 或 `已证伪`。

- 所有关键主张都取得证据状态后，才算完成第 4 步。
- 未完成第 4 步，不得进入第 5 步。
- 若仍存在没有证据状态的关键主张，本轮结果为 `STOP_AND_ASK`。

## 6. 评审维度判定

- 所有问题都要归因到 `需求对齐`、`架构对齐`、`代码现状对齐`、`完整性`、`可落地性` 中的至少一个维度。
- 分级必须基于证据和影响，不得因为用户紧急程度或方案文字完整度而调整等级。

- 所有问题或风险都补齐归因维度与严重级别后，才算完成第 5 步。
- 未完成第 5 步，不得进入第 6 步。
- 若归因或分级仍不完整，本轮结果为 `STOP_AND_ASK`。

## 9. 改进建议规则

- 每个 `blocker` 和 `major` 都必须给出明确改进方案。
- 改进方案要写清：建议动作、涉及对象、预期修正结果、完成后应补的验证证据。
- 如果问题来自信息缺失，改进方案应明确要补哪类资料、代码入口或测试证据。
- 改进建议优先写可执行动作，不写空泛口号。
- 所有 `blocker` / `major` 项都补齐改进动作与验证方式后，才算完成第 6 步。
- 未完成第 6 步，不得进入第 7 步。
- 若改进动作仍不完整，本轮结果为 `STOP_AND_ASK`。

## 10. 输出前自检

正式输出前逐项确认：

- 四类必要输入是否齐全且本次确实已查看
- 每条关键结论是否都能回溯到需求、方案、原则或代码证据
- 是否把猜测和事实严格区分，未证实内容是否标为 `待核验`
- 复用声明是否都已在代码中找到证据或被明确指出缺失
- 问题分级、最终结论、改进建议是否彼此一致
- 输出顺序是否仍符合主 skill 的固定结构

未完成第 7 步，不得进入第 8 步。
若任一自检项不通过，本轮结果为 `STOP_AND_ASK`。
只允许回到第一个未完成步骤修正。
```

In `skills/review-technical-solution/references/review-analysis-guide.md`, add these lines under `## 2. 分类判定原则`:

```markdown
- 类型判定完成的最低标准是：主类型、附加类型和检查并集都已明确。
- 未完成第 2 步，不得进入第 3 步。
- 分类依据仍不足时，本轮结果为 `STOP_AND_ASK`。
```

In `skills/review-technical-solution/references/review-output-contract.md`, append this new section:

```markdown
## 8. 正式输出消费边界

- 正式输出只能消费前七步已经闭合的结果。
- 不得在正式输出阶段新增主类型 / 附加类型判断。
- 不得在正式输出阶段补做主张提取、证据状态判定、问题分级或改进动作。
- 输出前自检未通过时，不得生成正式评审输出。
```

- [ ] **Step 4: Run the full review-focused validation slice and verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_review_technical_solution_contracts tests.skill_validation.test_review_technical_solution_conversation_simulation tests.skill_validation.test_review_technical_solution_step_gating tests.skill_validation.test_case_catalog -v`
Expected: PASS.

- [ ] **Step 5: Commit the review contract hardening slice**

```bash
git add skills/review-technical-solution/SKILL.md skills/review-technical-solution/references/review-process.md skills/review-technical-solution/references/review-analysis-guide.md skills/review-technical-solution/references/review-output-contract.md tests/skill_validation/test_review_technical_solution_contracts.py
git commit -m "fix(skill): enforce strict review step gating"
```

### Task 3: Add Create Gating Metadata and Failing Behavior Tests

**Files:**
- Create: `tests/skill_validation/test_create_technical_solution_conversation_simulation.py`
- Create: `tests/skill_validation/test_create_technical_solution_step_gating.py`
- Modify: `tests/skill_validation/case_catalog.py`
- Modify: `tests/skill_validation/test_case_catalog.py`

- [ ] **Step 1: Write the failing create conversation-simulation test**

Create `tests/skill_validation/test_create_technical_solution_conversation_simulation.py` with this full content:

```python
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
        self.assertEqual(
            multi_turn_case_ids,
            {"CTS-13", "CTS-14", "CTS-15", "CTS-16", "CTS-17", "CTS-18", "CTS-19", "CTS-20", "CTS-21", "CTS-22"},
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write the failing create step-gating state-model test**

Create `tests/skill_validation/test_create_technical_solution_step_gating.py` with this full content:

```python
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
```

- [ ] **Step 3: Run the new create behavior tests to verify they fail first**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_conversation_simulation tests.skill_validation.test_create_technical_solution_step_gating -v`
Expected: FAIL because `CreateProgress`, the new create `ConversationTurn` metadata, and the new `CTS-13` / `CTS-14` through `CTS-22` multi-turn cases do not exist yet.

- [ ] **Step 4: Extend `case_catalog.py` with create progress metadata, convert `CTS-13`, and add eight new create gate cases**

In `tests/skill_validation/case_catalog.py`, add this dataclass after `ReviewProgress`, then extend `ConversationTurn` with create fields:

```python
@dataclass(frozen=True)
class CreateProgress:
    scope_clarified: bool = False
    prerequisites_ready: bool = False
    template_read: bool = False
    solution_typed: bool = False
    participants_selected: bool = False
    context_built: bool = False
    task_sheet_ready: bool = False
    expert_analysis_complete: bool = False
    synthesis_complete: bool = False
    draft_written: bool = False
    absorb_check_passed: bool = False


@dataclass(frozen=True)
class ConversationTurn:
    user_input: str
    expected_result: str
    assert_paths: Tuple[str, ...] = ()
    assert_structure: Tuple[str, ...] = ()
    assert_semantics: Tuple[str, ...] = ()
    assert_safety: Tuple[str, ...] = ()
    forbidden_behavior: Tuple[str, ...] = ()
    setup_progress: SetupProgress | None = None
    required_setup_step: int | None = None
    setup_turn_action: str | None = None
    blocked_steps: Tuple[int, ...] = ()
    review_progress: ReviewProgress | None = None
    required_review_step: int | None = None
    review_turn_action: str | None = None
    create_progress: CreateProgress | None = None
    required_create_step: int | None = None
    create_turn_action: str | None = None
```

Convert `CTS-13` to a multi-turn gate case by replacing it with this block:

```python
    vcase(
        "CTS-13",
        "create-technical-solution",
        "对抗边界层",
        "complete-architecture-default-template",
        "第六步已收集上下文，但专家分析和协作收敛没有显式引用任何共享上下文编号，仍试图继续成稿。",
        "缺少共享上下文消费链时必须停机并回退到受影响阶段",
        "STOP_AND_ASK",
        assert_semantics=("明确指出缺失的共享上下文消费链",),
        assert_safety=("不允许无证据继续成稿",),
        forbidden_behavior=("跳过上下文引用继续生成最终方案",),
        turns=(
            ConversationTurn(
                user_input="共享上下文已经列了，但协作收敛还没形成可回溯的消费链。不要直接成稿。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("正式成稿", "共享上下文"),
                assert_safety=("未完成第 10 步，不得进入第 11 步。",),
                forbidden_behavior=("进入第 11 步", "absorb-check"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                    participants_selected=True,
                    context_built=True,
                    task_sheet_ready=True,
                    expert_analysis_complete=True,
                    synthesis_complete=True,
                ),
                required_create_step=10,
                create_turn_action="await_context",
                blocked_steps=(11, 12),
            ),
            ConversationTurn(
                user_input="先别做 absorb-check，正式成稿这一步还没闭合。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("正式成稿", "共享上下文"),
                assert_safety=("未完成第 10 步，不得进入第 11 步。",),
                forbidden_behavior=("进入第 11 步", "进入第 12 步"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                    participants_selected=True,
                    context_built=True,
                    task_sheet_ready=True,
                    expert_analysis_complete=True,
                    synthesis_complete=True,
                ),
                required_create_step=10,
                create_turn_action="await_context",
                blocked_steps=(11, 12),
            ),
        ),
    ),
```

Then append these eight new cases after `CTS-13`:

```python
    vcase(
        "CTS-14",
        "create-technical-solution",
        "流程场景层",
        "complete-architecture-default-template",
        "主题和范围仍模糊时，create-technical-solution 必须停在第 1 步。",
        "验证未完成第 1 步时不会进入第 2 到 12 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在定题与范围判断",),
        assert_safety=("未完成第 1 步不得进入第 2 步",),
        forbidden_behavior=("进入第 2 步", "进入第 5 步", "进入第 10 步"),
        turns=(
            ConversationTurn(
                user_input="主题还很模糊，先别去检查模板和成员。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("定题", "范围"),
                assert_safety=("未完成第 1 步，不得进入第 2 步。",),
                forbidden_behavior=("模板读取", "第 3 步", "方案类型判定"),
                create_progress=CreateProgress(),
                required_create_step=1,
                create_turn_action="await_scope",
                blocked_steps=(2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
            ),
            ConversationTurn(
                user_input="范围还是没澄清，继续停在定题阶段。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("定题", "范围"),
                assert_safety=("未完成第 1 步，不得进入第 2 步。",),
                forbidden_behavior=("进入第 2 步", "进入第 10 步"),
                create_progress=CreateProgress(),
                required_create_step=1,
                create_turn_action="await_scope",
                blocked_steps=(2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
            ),
        ),
    ),
    vcase(
        "CTS-15",
        "create-technical-solution",
        "流程场景层",
        "complete-architecture-default-template",
        "语义前置齐全但当前模板还未读成稳定摘要时，create-technical-solution 必须停在第 3 步。",
        "验证未完成第 3 步时不会进入第 4 到 12 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在当前模板读取",),
        assert_safety=("未完成第 3 步不得进入第 4 步",),
        forbidden_behavior=("进入第 4 步", "进入第 10 步"),
        turns=(
            ConversationTurn(
                user_input="前置文件都在，但模板结构摘要还没稳定，不要继续判断方案类型。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("模板读取", "模板结构摘要"),
                assert_safety=("未完成第 3 步，不得进入第 4 步。",),
                forbidden_behavior=("方案类型判定", "第 4 步", "正式成稿"),
                create_progress=CreateProgress(scope_clarified=True, prerequisites_ready=True),
                required_create_step=3,
                create_turn_action="await_context",
                blocked_steps=(4, 5, 6, 7, 8, 9, 10, 11, 12),
            ),
            ConversationTurn(
                user_input="模板摘要还是不完整，先别去选成员。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("模板读取", "模板结构摘要"),
                assert_safety=("未完成第 3 步，不得进入第 4 步。",),
                forbidden_behavior=("进入第 4 步", "进入第 5 步"),
                create_progress=CreateProgress(scope_clarified=True, prerequisites_ready=True),
                required_create_step=3,
                create_turn_action="await_context",
                blocked_steps=(4, 5, 6, 7, 8, 9, 10, 11, 12),
            ),
        ),
    ),
    vcase(
        "CTS-16",
        "create-technical-solution",
        "流程场景层",
        "complete-architecture-default-template",
        "模板已读，但方案类型仍未闭合时，create-technical-solution 必须停在第 4 步。",
        "验证未完成第 4 步时不会进入第 5 到 12 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在方案类型判定",),
        assert_safety=("未完成第 4 步不得进入第 5 步",),
        forbidden_behavior=("进入第 5 步", "进入第 10 步"),
        turns=(
            ConversationTurn(
                user_input="模板先按当前结构保留，但方案类型还没定清，先别选参与成员。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("方案类型判定", "主类型"),
                assert_safety=("未完成第 4 步，不得进入第 5 步。",),
                forbidden_behavior=("成员选择", "第 5 步", "正式成稿"),
                create_progress=CreateProgress(scope_clarified=True, prerequisites_ready=True, template_read=True),
                required_create_step=4,
                create_turn_action="await_context",
                blocked_steps=(5, 6, 7, 8, 9, 10, 11, 12),
            ),
            ConversationTurn(
                user_input="类型还是拿不准，继续停在第 4 步。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("方案类型判定", "主类型"),
                assert_safety=("未完成第 4 步，不得进入第 5 步。",),
                forbidden_behavior=("进入第 5 步", "进入第 10 步"),
                create_progress=CreateProgress(scope_clarified=True, prerequisites_ready=True, template_read=True),
                required_create_step=4,
                create_turn_action="await_context",
                blocked_steps=(5, 6, 7, 8, 9, 10, 11, 12),
            ),
        ),
    ),
    vcase(
        "CTS-17",
        "create-technical-solution",
        "流程场景层",
        "complete-architecture-default-template",
        "方案类型已闭合，但参与成员与槽位覆盖仍不完整时，create-technical-solution 必须停在第 5 步。",
        "验证未完成第 5 步时不会进入第 6 到 12 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在成员选择",),
        assert_safety=("未完成第 5 步不得进入第 6 步",),
        forbidden_behavior=("进入第 6 步", "进入第 10 步"),
        turns=(
            ConversationTurn(
                user_input="类型先按当前结果保留，但成员和槽位覆盖还没定完，不要进入共享上下文。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("成员选择", "参与成员"),
                assert_safety=("未完成第 5 步，不得进入第 6 步。",),
                forbidden_behavior=("共享上下文", "第 6 步", "正式成稿"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                ),
                required_create_step=5,
                create_turn_action="await_context",
                blocked_steps=(6, 7, 8, 9, 10, 11, 12),
            ),
            ConversationTurn(
                user_input="成员名单还没闭合，先别写任务单。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("成员选择", "参与成员"),
                assert_safety=("未完成第 5 步，不得进入第 6 步。",),
                forbidden_behavior=("进入第 6 步", "进入第 7 步"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                ),
                required_create_step=5,
                create_turn_action="await_context",
                blocked_steps=(6, 7, 8, 9, 10, 11, 12),
            ),
        ),
    ),
    vcase(
        "CTS-18",
        "create-technical-solution",
        "流程场景层",
        "complete-architecture-default-template",
        "成员已选，但共享上下文清单仍不完整时，create-technical-solution 必须停在第 6 步。",
        "验证未完成第 6 步时不会进入第 7 到 12 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在共享上下文构建",),
        assert_safety=("未完成第 6 步不得进入第 7 步",),
        forbidden_behavior=("进入第 7 步", "进入第 10 步"),
        turns=(
            ConversationTurn(
                user_input="成员先按当前名单保留，但共享上下文编号、来源和槽位映射还没补齐，不要生成任务单。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("共享上下文", "上下文编号"),
                assert_safety=("未完成第 6 步，不得进入第 7 步。",),
                forbidden_behavior=("模板任务单", "第 7 步", "正式成稿"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                    participants_selected=True,
                ),
                required_create_step=6,
                create_turn_action="await_context",
                blocked_steps=(7, 8, 9, 10, 11, 12),
            ),
            ConversationTurn(
                user_input="共享上下文还是没闭合，先别进入任务单阶段。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("共享上下文", "上下文编号"),
                assert_safety=("未完成第 6 步，不得进入第 7 步。",),
                forbidden_behavior=("进入第 7 步", "进入第 10 步"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                    participants_selected=True,
                ),
                required_create_step=6,
                create_turn_action="await_context",
                blocked_steps=(7, 8, 9, 10, 11, 12),
            ),
        ),
    ),
    vcase(
        "CTS-19",
        "create-technical-solution",
        "流程场景层",
        "complete-architecture-default-template",
        "共享上下文已闭合，但模板任务单仍缺槽位状态或阻塞条件时，create-technical-solution 必须停在第 7 步。",
        "验证未完成第 7 步时不会进入第 8 到 12 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在模板任务单",),
        assert_safety=("未完成第 7 步不得进入第 8 步",),
        forbidden_behavior=("进入第 8 步", "进入第 10 步"),
        turns=(
            ConversationTurn(
                user_input="共享上下文先保留，但任务单还没补齐槽位状态和缺失即停止条件，不要进入专家分析。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("模板任务单", "槽位"),
                assert_safety=("未完成第 7 步，不得进入第 8 步。",),
                forbidden_behavior=("专家逐槽位分析", "第 8 步", "正式成稿"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                    participants_selected=True,
                    context_built=True,
                ),
                required_create_step=7,
                create_turn_action="await_context",
                blocked_steps=(8, 9, 10, 11, 12),
            ),
            ConversationTurn(
                user_input="任务单还没闭合，继续停在第 7 步。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("模板任务单", "槽位"),
                assert_safety=("未完成第 7 步，不得进入第 8 步。",),
                forbidden_behavior=("进入第 8 步", "进入第 10 步"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                    participants_selected=True,
                    context_built=True,
                ),
                required_create_step=7,
                create_turn_action="await_context",
                blocked_steps=(8, 9, 10, 11, 12),
            ),
        ),
    ),
    vcase(
        "CTS-20",
        "create-technical-solution",
        "流程场景层",
        "complete-architecture-default-template",
        "模板任务单已闭合，但并非所有专家都已完成逐槽位分析时，create-technical-solution 必须停在第 8 步。",
        "验证未完成第 8 步时不会进入第 9 到 12 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在专家逐槽位分析",),
        assert_safety=("未完成第 8 步不得进入第 9 步",),
        forbidden_behavior=("进入第 9 步", "进入第 10 步"),
        turns=(
            ConversationTurn(
                user_input="任务单可以先保留，但专家还没全部交齐产物，不要开始协作收敛。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("专家逐槽位分析", "专家产物"),
                assert_safety=("未完成第 8 步，不得进入第 9 步。",),
                forbidden_behavior=("协作收敛", "第 9 步", "正式成稿"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                    participants_selected=True,
                    context_built=True,
                    task_sheet_ready=True,
                ),
                required_create_step=8,
                create_turn_action="await_context",
                blocked_steps=(9, 10, 11, 12),
            ),
            ConversationTurn(
                user_input="专家产物还没齐，继续停在第 8 步。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("专家逐槽位分析", "专家产物"),
                assert_safety=("未完成第 8 步，不得进入第 9 步。",),
                forbidden_behavior=("进入第 9 步", "进入第 10 步"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                    participants_selected=True,
                    context_built=True,
                    task_sheet_ready=True,
                ),
                required_create_step=8,
                create_turn_action="await_context",
                blocked_steps=(9, 10, 11, 12),
            ),
        ),
    ),
    vcase(
        "CTS-21",
        "create-technical-solution",
        "流程场景层",
        "complete-architecture-default-template",
        "全部专家产物都已完成，但槽位收敛仍未闭合时，create-technical-solution 必须停在第 9 步。",
        "验证未完成第 9 步时不会进入第 10 到 12 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在协作收敛",),
        assert_safety=("未完成第 9 步不得进入第 10 步",),
        forbidden_behavior=("进入第 10 步", "进入第 12 步"),
        turns=(
            ConversationTurn(
                user_input="专家产物先按当前结果保留，但还有槽位没有形成选定写法，不要正式成稿。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("协作收敛", "选定写法"),
                assert_safety=("未完成第 9 步，不得进入第 10 步。",),
                forbidden_behavior=("严格模板成稿", "第 10 步", "删除 working draft"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                    participants_selected=True,
                    context_built=True,
                    task_sheet_ready=True,
                    expert_analysis_complete=True,
                ),
                required_create_step=9,
                create_turn_action="await_context",
                blocked_steps=(10, 11, 12),
            ),
            ConversationTurn(
                user_input="协作收敛还没闭合，继续停在第 9 步。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("协作收敛", "选定写法"),
                assert_safety=("未完成第 9 步，不得进入第 10 步。",),
                forbidden_behavior=("进入第 10 步", "进入第 12 步"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                    participants_selected=True,
                    context_built=True,
                    task_sheet_ready=True,
                    expert_analysis_complete=True,
                ),
                required_create_step=9,
                create_turn_action="await_context",
                blocked_steps=(10, 11, 12),
            ),
        ),
    ),
    vcase(
        "CTS-22",
        "create-technical-solution",
        "流程场景层",
        "complete-architecture-default-template",
        "正式文档已经写出，但 absorb-check 尚未通过时，create-technical-solution 必须停在第 11 步并保留 working draft。",
        "验证未完成第 11 步时不会进入第 12 步",
        "STOP_AND_ASK",
        assert_semantics=("当前停在 absorb-check",),
        assert_safety=("未完成第 11 步不得进入第 12 步",),
        forbidden_behavior=("进入第 12 步",),
        turns=(
            ConversationTurn(
                user_input="正式文档可以先保留，但 absorb-check 还没通过，不要删 working draft。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("absorb-check", "working draft"),
                assert_safety=("未完成第 11 步，不得进入第 12 步。",),
                forbidden_behavior=("删除 working draft", "第 12 步"),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                    participants_selected=True,
                    context_built=True,
                    task_sheet_ready=True,
                    expert_analysis_complete=True,
                    synthesis_complete=True,
                    draft_written=True,
                ),
                required_create_step=11,
                create_turn_action="await_context",
                blocked_steps=(12,),
            ),
            ConversationTurn(
                user_input="先别删 working draft，absorb-check 还是没通过。",
                expected_result="STOP_AND_ASK",
                assert_semantics=("absorb-check", "working draft"),
                assert_safety=("未完成第 11 步，不得进入第 12 步。",),
                forbidden_behavior=("进入第 12 步",),
                create_progress=CreateProgress(
                    scope_clarified=True,
                    prerequisites_ready=True,
                    template_read=True,
                    solution_typed=True,
                    participants_selected=True,
                    context_built=True,
                    task_sheet_ready=True,
                    expert_analysis_complete=True,
                    synthesis_complete=True,
                    draft_written=True,
                ),
                required_create_step=11,
                create_turn_action="await_context",
                blocked_steps=(12,),
            ),
        ),
    ),
```

- [ ] **Step 5: Update `test_case_catalog.py` for the expanded create matrix**

Make these exact edits in `tests/skill_validation/test_case_catalog.py`:

```python
EXPECTED_PHASE_1 = {
    "SA-01",
    "SA-02",
    "SA-13",
    "SA-15",
    "SA-16",
    "SA-17",
    "SA-07",
    "SA-08",
    "CTS-01",
    "CTS-02",
    "CTS-04",
    "CTS-07",
    "CTS-08",
    "CTS-13",
    "CTS-14",
    "CTS-15",
    "CTS-16",
    "CTS-17",
    "CTS-18",
    "CTS-19",
    "CTS-20",
    "CTS-21",
    "CTS-22",
    "RTS-01",
    "RTS-02",
    "RTS-03",
    "RTS-10",
    "RTS-11",
    "RTS-12",
    "RTS-13",
    "RTS-14",
    "RTS-15",
}

EXPECTED_PHASE_1_ORDER = (
    "SA-01",
    "SA-02",
    "SA-13",
    "SA-15",
    "SA-16",
    "SA-17",
    "SA-07",
    "SA-08",
    "CTS-01",
    "CTS-02",
    "CTS-04",
    "CTS-07",
    "CTS-08",
    "CTS-13",
    "CTS-14",
    "CTS-15",
    "CTS-16",
    "CTS-17",
    "CTS-18",
    "CTS-19",
    "CTS-20",
    "CTS-21",
    "CTS-22",
    "RTS-01",
    "RTS-02",
    "RTS-03",
    "RTS-10",
    "RTS-11",
    "RTS-12",
    "RTS-13",
    "RTS-14",
    "RTS-15",
)

def test_catalog_contains_all_design_cases(self) -> None:
    self.assertEqual(len(ALL_CASES), 54)
    self.assertEqual({case.case_id for case in ALL_CASES}, EXPECTED_CASE_IDS)
    self.assertEqual(PHASE_1_CASE_IDS, EXPECTED_PHASE_1_ORDER)
    self.assertEqual(PHASE_2_CASE_IDS, EXPECTED_PHASE_2_ORDER)
    self.assertEqual(PHASE_3_CASE_IDS, EXPECTED_PHASE_3_ORDER)
    self.assertEqual(len(PHASE_1_CASE_IDS), len(set(PHASE_1_CASE_IDS)))
    self.assertEqual(len(PHASE_2_CASE_IDS), len(set(PHASE_2_CASE_IDS)))
    self.assertEqual(len(PHASE_3_CASE_IDS), len(set(PHASE_3_CASE_IDS)))

def test_cts_13_to_cts_22_stay_in_phase_1(self) -> None:
    for case_id in ("CTS-13", "CTS-14", "CTS-15", "CTS-16", "CTS-17", "CTS-18", "CTS-19", "CTS-20", "CTS-21", "CTS-22"):
        with self.subTest(case_id=case_id):
            self.assertIn(case_id, PHASE_1_CASE_IDS)
            self.assertEqual(CASE_INDEX[case_id].expected_result, "STOP_AND_ASK")
```

- [ ] **Step 6: Run the focused create catalog and behavior tests and make sure they pass**

Run: `python3 -m unittest tests.skill_validation.test_case_catalog tests.skill_validation.test_create_technical_solution_conversation_simulation tests.skill_validation.test_create_technical_solution_step_gating -v`
Expected: PASS.

- [ ] **Step 7: Commit the create gating metadata slice**

```bash
git add tests/skill_validation/case_catalog.py tests/skill_validation/test_case_catalog.py tests/skill_validation/test_create_technical_solution_conversation_simulation.py tests/skill_validation/test_create_technical_solution_step_gating.py
git commit -m "test(validation): add create step-gating cases"
```

### Task 4: Harden Create Contracts to Match the New Create Gating Tests

**Files:**
- Modify: `skills/create-technical-solution/SKILL.md`
- Modify: `skills/create-technical-solution/references/solution-process.md`
- Modify: `skills/create-technical-solution/references/progress-transparency.md`
- Modify: `skills/create-technical-solution/references/working-draft-protocol.md`
- Modify: `tests/skill_validation/test_create_technical_solution_contracts.py`

- [ ] **Step 1: Extend the create contract test so the new gates fail first**

Append these test methods to `tests/skill_validation/test_create_technical_solution_contracts.py`:

```python
    def test_main_skill_enforces_first_unfinished_step_gate(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "### 1. 定题与范围判断",
                "未完成第 1 步，不得进入第 2 步。",
                "### 3. 读取当前生效模板",
                "未完成第 3 步，不得进入第 4 步。",
                "### 4. 判断方案类型",
                "未完成第 4 步，不得进入第 5 步。",
                "### 5. 加载成员名册并选择参与者",
                "未完成第 5 步，不得进入第 6 步。",
                "### 6. 构建共享上下文",
                "未完成第 6 步，不得进入第 7 步。",
                "### 7. 生成模板任务单",
                "未完成第 7 步，不得进入第 8 步。",
                "### 8. 组织专家按模板逐槽位分析",
                "未完成第 8 步，不得进入第 9 步。",
                "### 9. 按模板逐槽位协作收敛",
                "未完成第 9 步，不得进入第 10 步。",
                "### 10. 严格模板成稿并保存结果",
                "未完成第 10 步，不得进入第 11 步。",
                "### 11. absorb-check",
                "未完成第 11 步，不得进入第 12 步。",
                "### 12. 删除 working draft",
            ),
        )

    def test_solution_process_promotes_intermediate_artifacts_to_hard_gates(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["solution_process"],
            (
                "`共享上下文清单` 必须先于 `模板任务单` 完成",
                "未完成第 6 步，不得进入第 7 步。",
                "`模板任务单` 必须严格按当前模板顺序列出槽位",
                "未完成第 7 步，不得进入第 8 步。",
                "全部专家完成逐槽位分析后，必须按同一槽位顺序进行收敛。",
                "未完成第 8 步，不得进入第 9 步。",
                "如果 `仍缺哪条共享上下文` 不为无，或上下文冲突未处理完毕，该槽位不得进入最终成稿。",
                "未完成第 9 步，不得进入第 10 步。",
            ),
        )

    def test_working_draft_protocol_requires_absorb_check_before_delete(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["working_draft_protocol"],
            (
                "最终文档生成后，必须先执行 absorb-check。",
                "未完成第 11 步，不得进入第 12 步。",
                "absorb-check 未完成或未通过时，本轮结果为 `STOP_AND_ASK`。",
                "只有 absorb-check 通过后，删除 working draft。",
            ),
        )
```

- [ ] **Step 2: Run the create contract test to verify it fails for the missing gate wording**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts -v`
Expected: FAIL because the current create skill docs do not yet declare the explicit `1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12` gate chain or the absorb-check release gate.

- [ ] **Step 3: Update the create skill docs with exact hard-gate wording, rollback rules, and absorb-check lifecycle**

In `skills/create-technical-solution/SKILL.md`, make these exact additions inside the step sections:

```markdown
### 1. 定题与范围判断

输入可以是方案主题、需求描述、已有文档路径，或用户给出的上下文片段。

先明确：问题、目标与非目标、约束与依赖、影响范围、相关需求。主题模糊时先澄清，再生成安全的短横线风格文件名。

生成短横线文件名后，立即预留 working draft 路径：`.architecture/technical-solutions/working-drafts/[主题-短横线文件名].working.md`。

完成条件：主题、目标、非目标、约束、影响范围已经明确。

未完成第 1 步，不得进入第 2 步。
若主题或范围仍模糊，本轮结果为 `STOP_AND_ASK`，停在定题与范围判断。

### 3. 读取当前生效模板

读取当前 `.architecture/templates/technical-solution-template.md` 的标题、章节层级、说明文字和现有结构。它可能是默认模板，也可能是用户替换后的自定义模板；后续正文必须服从它的实际结构。

完成条件：已经形成稳定的 `模板结构摘要`，至少包含模板版本、必填槽位和关键约束。

未完成第 3 步，不得进入第 4 步。
若模板结构摘要仍不稳定，本轮结果为 `STOP_AND_ASK`，停在当前模板读取。

### 4. 判断方案类型

先按 [references/solution-analysis-guide.md](references/solution-analysis-guide.md) 判断主题命中哪一类方案，再据此确定必答问题、易漏风险、评审重点和推荐参与成员。

完成条件：已经明确主类型、附加类型和判定依据。

未完成第 4 步，不得进入第 5 步。
若方案类型仍未闭合，本轮结果为 `STOP_AND_ASK`，停在方案类型判定。

### 5. 加载成员名册并选择参与者

读取 `.architecture/members.yml`。

默认至少包含系统架构师；再根据上一步的方案类型与名册中的自定义专家决定最终参与成员集合。

完成条件：已经形成 `参与成员名单`，并说明每位成员覆盖的槽位与参与理由。

未完成第 5 步，不得进入第 6 步。
若参与成员与槽位覆盖仍不完整，本轮结果为 `STOP_AND_ASK`，停在成员选择。

### 6. 构建共享上下文

整合 `.architecture/principles.md`、代码与配置、现有实现、相关文档和外部约束。原则文档是判断标准，不是可选背景。

先形成一份 `共享上下文清单`，至少列出 `上下文编号`、`来源`、`结论或约束`、`适用槽位`、`可信度或缺口`。如果某条上下文无法映射到模板槽位，或关键槽位缺少可用上下文，先标记缺口，不得带着隐含假设进入下一阶段。

完成后，必须先按 [references/working-draft-protocol.md](references/working-draft-protocol.md) 将 `共享上下文清单` 写入 `WD-CTX`，再按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示摘要。

完成条件：`共享上下文清单` 已补齐 `上下文编号`、`来源`、`结论或约束`、`适用槽位`、`可信度或缺口`。

未完成第 6 步，不得进入第 7 步。
若共享上下文仍缺关键编号或槽位映射，本轮结果为 `STOP_AND_ASK`，停在共享上下文构建。

### 7. 生成模板任务单

先基于当前生效模板生成一份 `模板任务单`，明确每个模板槽位的语义、负责参与成员、专家必答问题、禁止越界输出的事项，以及会阻止安全落位的阻塞条件。每个槽位都必须补齐 `本槽位必须消费的共享上下文` 与 `缺失即停止的上下文`，把第 6 步共享上下文显式绑定到后续分析单元。

`模板任务单` 只描述如何围绕当前模板推进，不引入任何模板外组织层。

完成后，必须先按 [references/working-draft-protocol.md](references/working-draft-protocol.md) 将这份 `模板任务单` 写入 `WD-TASK`，再在对话中展示摘要。

完成条件：每个模板槽位都已补齐状态、参与成员、阻塞条件、共享上下文绑定与缺口说明。

未完成第 7 步，不得进入第 8 步。
若模板任务单仍缺必填字段，本轮结果为 `STOP_AND_ASK`，停在模板任务单生成。

### 8. 组织专家按模板逐槽位分析

要求每个参与成员基于共享上下文和 `模板任务单`，按模板槽位逐项独立分析，不要直接重复别人的结论，也不要输出模板外可见结构。先检测是否存在 `repowiki`（指仓库内用于沉淀项目知识的 repowiki/ 或同名目录，可用 `find . -type d -name "repowiki"` 确认）；若存在，专家分析必须同时参考其中与当前槽位相关的内容；若不存在，不作为阻塞条件。

每个槽位分析都必须显式写出 `已使用的共享上下文编号`、`未使用原因`、`结论是否超出上下文支持`。如果专家结论无法对应第 6 步的共享上下文编号，必须把该槽位标记为待补证，而不是继续补齐看似完整的结论。

每个成员完成独立输入后，先写入对应 `WD-EXP-[expert-slug]` 区块，再展示摘要。

完成条件：所有已选专家都完成各自槽位分析，且缺证项已显式标记。

未完成第 8 步，不得进入第 9 步。
若专家产物仍未齐全，本轮结果为 `STOP_AND_ASK`，停在专家逐槽位分析。

### 9. 按模板逐槽位协作收敛

把成员输入按模板槽位收敛成共同结论、争议点、候选方案对比、选定方向、原则冲突与取舍、未决问题，只保留能够稳定落回当前模板已有位置的内容。

每个槽位收敛时都必须显式记录 `本槽位已核销的共享上下文`、`上下文冲突如何处理`、`仍缺哪条共享上下文`。如果专家结论之间无法核销到同一批共享上下文，或关键上下文仍缺失，先停止该槽位收敛并回退，不得直接生成表面完整的最终写法。

完成收敛后、生成最终文档前，必须先将 `协作收敛纪要` 写入 `WD-SYN`，再在对话中展示摘要。如果用户在 `专家产物` 或 `协作收敛纪要` 展示后新增约束、修正目标或调整范围，先说明失效范围，再从最近受影响的阶段边界重进。

完成条件：每个模板槽位都已有共同结论、选定写法、上下文核销结果和未决项状态。

未完成第 9 步，不得进入第 10 步。
若任一槽位仍未收敛，本轮结果为 `STOP_AND_ASK`，停在协作收敛。

### 10. 严格模板成稿并保存结果

把已收敛内容写回当前生效模板，保持当前生效模板的现有结构，不新增任何模板外可见结构；若模板没有同名章节，则按现有结构语义落位。最终只把已收敛内容写回当前模板已有位置。缺少语义前置、无法展示稳定中间产物或无法安全落位时停止并确认。生成最终文档前，逐项检查主文档可见的最小质量门槛和 [references/solution-process.md](references/solution-process.md) 的完整质量门槛。

任一槽位若无法回溯到已核销的共享上下文编号，停止成稿并确认。

将最终文档写入 `.architecture/technical-solutions/[主题-短横线文件名].md`。

未完成第 10 步，不得进入第 11 步。
若任一槽位无法回溯到已核销的共享上下文编号，回退到第 9 步，而不是继续硬写。

### 11. absorb-check

生成最终文档后，先执行 absorb-check，确认 working draft 中需要保留的关键信息已被正式文档吸收，或明确记录为未吸收项。

未完成第 11 步，不得进入第 12 步。
若 absorb-check 未完成或未通过，本轮结果为 `STOP_AND_ASK`，并保留 working draft。

### 12. 删除 working draft

只有 absorb-check 通过后，才允许删除 working draft。
```

In `skills/create-technical-solution/references/solution-process.md`, add these exact lines in the relevant sections:

```markdown
- `共享上下文清单` 必须先于 `模板任务单` 完成，不能在专家分析过程中临时补造。
- 未完成第 6 步，不得进入第 7 步。
- 若关键槽位没有足够共享上下文支撑，必须先标记缺口，再停止进入 `模板任务单` 或后续阶段。

- 任何槽位如果没有足够语义支撑，必须标记为阻塞并停止后续自动成稿。
- 未完成第 7 步，不得进入第 8 步。

- 如果专家建议无法引用共享上下文编号，或 `结论是否超出上下文支持` 不是“没有超出”，必须把该槽位继续标记为待补证，而不是直接进入收敛定稿。
- 未完成第 8 步，不得进入第 9 步。

- 如果 `仍缺哪条共享上下文` 不为无，或上下文冲突未处理完毕，该槽位不得进入最终成稿。
- 未完成第 9 步，不得进入第 10 步。

- 若正式成稿时发现槽位仍未闭合，只允许回退到第 9 步补齐收敛结果，不得继续向后进入 absorb-check。
```

In `skills/create-technical-solution/references/progress-transparency.md`, add these exact lines:

```markdown
1. `共享上下文清单阶段`：共享上下文来源、适用槽位和关键缺口稳定后，先展示 `共享上下文清单`，再允许进入 `模板任务单阶段`。
   未完成第 6 步，不得进入第 7 步。

2. `模板任务单阶段`：模板槽位、参与专家、必答问题和阻塞条件稳定后，才允许进入后续分析。
   未完成第 7 步，不得进入第 8 步。

3. `专家按模板逐槽位分析阶段`：单个专家补齐当前模板槽位所需必填字段后，立即展示该专家的 `专家产物`。
   未完成第 8 步，不得进入第 9 步。

4. `按模板逐槽位协作收敛阶段`：全部专家输入完成后，统一展示一份 `协作收敛纪要`。
   未完成第 9 步，不得进入第 10 步。

5. `严格模板成稿阶段`：用户看过收敛结果后，再把选定方向、权衡、风险和未决问题按当前模板严格成稿。
   未完成第 10 步，不得进入第 11 步。
```

In `skills/create-technical-solution/references/working-draft-protocol.md`, replace the lifecycle section with:

```markdown
## 4. 生命周期

- 最终文档生成后，必须先执行 absorb-check。
- 未完成第 11 步，不得进入第 12 步。
- absorb-check 未完成或未通过时，本轮结果为 `STOP_AND_ASK`。
- absorb-check 未通过时，working draft 必须保留，作为可追溯依据。
- 只有 absorb-check 通过后，删除 working draft。
```

- [ ] **Step 4: Run the full create-focused validation slice and verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts tests.skill_validation.test_create_technical_solution_conversation_simulation tests.skill_validation.test_create_technical_solution_step_gating tests.skill_validation.test_case_catalog -v`
Expected: PASS.

- [ ] **Step 5: Commit the create contract hardening slice**

```bash
git add skills/create-technical-solution/SKILL.md skills/create-technical-solution/references/solution-process.md skills/create-technical-solution/references/progress-transparency.md skills/create-technical-solution/references/working-draft-protocol.md tests/skill_validation/test_create_technical_solution_contracts.py
git commit -m "fix(skill): enforce strict create step gating"
```

### Task 5: Align the Runbook, Design Docs, and Full Validation Suite

**Files:**
- Modify: `docs/superpowers/testing/skill-validation.md`
- Modify: `docs/superpowers/specs/2026-03-26-skill-validation-design.md`
- Modify: `docs/superpowers/specs/2026-03-27-review-technical-solution-design.md`
- Modify: `tests/skill_validation/test_workflow_integration.py`

- [ ] **Step 1: Extend workflow/runbook integration tests so the new validation layers fail first**

Append these assertions to `tests/skill_validation/test_workflow_integration.py`:

```python
    def test_runbook_mentions_behavior_gating_layers(self) -> None:
        runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("conversation simulation", runbook)
        self.assertIn("step-gating / 状态机测试", runbook)
        self.assertIn("尾流程生命周期测试", runbook)
        self.assertIn("RTS-10", runbook)
        self.assertIn("CTS-22", runbook)

    def test_runbook_case_layer_examples_match_catalog(self) -> None:
        runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

        expected_layer_examples = {
            "静态契约层": ("SA-11", "SA-12", "RTS-09"),
            "流程场景层": ("SA-01", "SA-15", "CTS-14", "CTS-18", "RTS-10", "RTS-15"),
            "行为回归层": ("SA-03", "CTS-04", "CTS-09", "RTS-04", "RTS-05", "RTS-06"),
            "对抗边界层": ("SA-07", "SA-08", "CTS-07", "CTS-08", "CTS-13", "RTS-03", "RTS-07", "RTS-08"),
        }

        for layer, case_ids in expected_layer_examples.items():
            layer_section = section_body(runbook, layer)
            for case_id in case_ids:
                self.assertEqual(CASE_INDEX[case_id].layer, layer)
                self.assertIn(case_id, layer_section)
```

- [ ] **Step 2: Run the workflow/runbook integration test and verify it fails for stale docs**

Run: `python3 -m unittest tests.skill_validation.test_workflow_integration -v`
Expected: FAIL because the runbook and design docs do not yet mention the new gating-focused layers and representative cases.

- [ ] **Step 3: Update the runbook and design docs to reflect the final gating matrix**

Make these exact edits in `docs/superpowers/testing/skill-validation.md`:

```markdown
## Layer map

### 静态契约层

- Focus: install targets, required files, forbidden legacy artifacts, minimum `.architecture/` layout, and fixed review output contracts.
- Representative cases: `SA-11`, `SA-12`, `RTS-09`.

### 流程场景层

- Focus: stop/redirect behavior, prerequisite enforcement, and first-unmet-step gating.
- Representative cases: `SA-01`, `SA-13`, `SA-15`, `SA-16`, `SA-17`, `CTS-14`, `CTS-18`, `RTS-10`, `RTS-15`.

### 行为回归层

- Focus: fixed prompts and fixtures that verify template adherence, required semantic blocks, non-overwrite behavior, and stable review-report semantics over time.
- Representative cases: `SA-03`, `CTS-04`, `CTS-09`, `RTS-04`, `RTS-05`, `RTS-06`.

### 对抗边界层

- Focus: ambiguous, partial, or risky inputs that could trigger unsafe inference, invalid formal output, skipped intermediate steps, or unsafe lifecycle actions.
- Representative cases: `SA-07`, `SA-08`, `CTS-07`, `CTS-08`, `CTS-13`, `RTS-03`, `RTS-07`, `RTS-08`.

## Validation architecture

- Layer 1: contract tests
- Layer 2: case-catalog tests
- Layer 3: conversation simulation
- Layer 4: step-gating / 状态机测试
- Layer 5: 尾流程生命周期测试
```

Update `docs/superpowers/specs/2026-03-26-skill-validation-design.md` with these exact additions:

```markdown
- `review-technical-solution` 的步骤门禁现在纳入长期验证范围：类型判定、主张提取、证据状态、归因分级、改进方案、输出前自检都必须具备 first-unmet-step 行为测试。
- `create-technical-solution` 的步骤门禁现在纳入长期验证范围：定题、模板读取、方案类型、成员选择、共享上下文、模板任务单、专家完成、协作收敛、正式成稿、absorb-check / 删除 working draft 都必须具备行为测试。
- catalog 允许 skill 专属 progress 对象；当前正式采用 `SetupProgress`、`ReviewProgress`、`CreateProgress`。
- 除静态 contract 外，新增 `conversation simulation`、`step-gating / 状态机测试`、`尾流程生命周期测试` 三层行为验证。
```

Update `docs/superpowers/specs/2026-03-27-review-technical-solution-design.md` with these exact additions:

```markdown
- 正式评审主链现已升级为 `1 输入完整性 -> 2 方案类型判定 -> 3 核心主张清单 -> 4 证据核验矩阵 -> 5 归因与分级 -> 6 改进方案 -> 7 输出前自检 -> 8 正式输出`。
- 输出前自检不再是 advisory checklist，而是 release gate；未通过时必须回到第一个未完成步骤。
- validation 除静态 contract 外，还必须覆盖 `RTS-10` 到 `RTS-15` 的多轮 gating case、conversation simulation、step-gating / 状态机测试。
```

- [ ] **Step 4: Re-run the workflow/runbook integration slice and verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_workflow_integration -v`
Expected: PASS.

- [ ] **Step 5: Run the complete validation suite as the final proof**

Run: `python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v`
Expected: PASS.

- [ ] **Step 6: Commit the runbook and design-alignment slice**

```bash
git add docs/superpowers/testing/skill-validation.md docs/superpowers/specs/2026-03-26-skill-validation-design.md docs/superpowers/specs/2026-03-27-review-technical-solution-design.md tests/skill_validation/test_workflow_integration.py
git commit -m "docs(validation): align sequential gating runbook"
```
