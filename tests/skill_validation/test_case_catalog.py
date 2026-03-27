import unittest

from tests.skill_validation.case_catalog import (
    ALL_CASES,
    CASE_INDEX,
    PHASE_1_CASE_IDS,
    PHASE_2_CASE_IDS,
    PHASE_3_CASE_IDS,
)


EXPECTED_PHASE_1 = {
    "SA-01",
    "SA-02",
    "SA-13",
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
}

EXPECTED_PHASE_1_ORDER = (
    "SA-01",
    "SA-02",
    "SA-13",
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
)

EXPECTED_PHASE_2 = {
    "SA-03",
    "SA-04",
    "SA-05",
    "SA-06",
    "SA-14",
    "CTS-03",
    "CTS-05",
    "CTS-06",
    "CTS-09",
    "RTS-04",
    "RTS-05",
    "RTS-06",
}

EXPECTED_PHASE_2_ORDER = (
    "SA-03",
    "SA-04",
    "SA-05",
    "SA-06",
    "SA-14",
    "CTS-03",
    "CTS-05",
    "CTS-06",
    "CTS-09",
    "RTS-04",
    "RTS-05",
    "RTS-06",
)

EXPECTED_PHASE_3 = {
    "SA-09",
    "SA-10",
    "SA-11",
    "SA-12",
    "CTS-10",
    "CTS-11",
    "CTS-12",
    "CTS-13",
    "RTS-07",
    "RTS-08",
    "RTS-09",
}

EXPECTED_PHASE_3_ORDER = (
    "SA-09",
    "SA-10",
    "SA-11",
    "SA-12",
    "CTS-10",
    "CTS-11",
    "CTS-12",
    "CTS-13",
    "RTS-07",
    "RTS-08",
    "RTS-09",
)

EXPECTED_CASE_IDS = EXPECTED_PHASE_1 | EXPECTED_PHASE_2 | EXPECTED_PHASE_3


class CaseCatalogTests(unittest.TestCase):
    def test_case_ids_are_unique(self) -> None:
        case_ids = [case.case_id for case in ALL_CASES]
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_catalog_contains_all_design_cases(self) -> None:
        self.assertEqual(len(ALL_CASES), 36)
        self.assertEqual({case.case_id for case in ALL_CASES}, EXPECTED_CASE_IDS)
        self.assertEqual(PHASE_1_CASE_IDS, EXPECTED_PHASE_1_ORDER)
        self.assertEqual(PHASE_2_CASE_IDS, EXPECTED_PHASE_2_ORDER)
        self.assertEqual(PHASE_3_CASE_IDS, EXPECTED_PHASE_3_ORDER)
        self.assertEqual(len(PHASE_1_CASE_IDS), len(set(PHASE_1_CASE_IDS)))
        self.assertEqual(len(PHASE_2_CASE_IDS), len(set(PHASE_2_CASE_IDS)))
        self.assertEqual(len(PHASE_3_CASE_IDS), len(set(PHASE_3_CASE_IDS)))

    def test_every_case_has_actionable_metadata(self) -> None:
        for case in ALL_CASES:
            with self.subTest(case_id=case.case_id):
                self.assertTrue(case.skill)
                self.assertTrue(case.layer)
                self.assertTrue(case.fixture)
                self.assertTrue(case.prompt)
                self.assertTrue(case.purpose)
                self.assertTrue(case.expected_result)
                self.assertTrue(
                    case.assert_paths
                    or case.assert_structure
                    or case.assert_semantics
                    or case.assert_safety
                )

    def test_placeholder_like_assertions_are_not_allowed(self) -> None:
        disallowed_values = {
            "缺失文件被补齐",
            "缺失前置项被明确指出",
            "明确列出缺失前置",
            "原始目标文件保持不变",
        }
        for case in ALL_CASES:
            with self.subTest(case_id=case.case_id):
                self.assertTrue(disallowed_values.isdisjoint(case.assert_paths))

    def test_assert_paths_only_contains_concrete_repo_paths(self) -> None:
        for case in ALL_CASES:
            for path_assertion in case.assert_paths:
                with self.subTest(case_id=case.case_id, path_assertion=path_assertion):
                    self.assertTrue(path_assertion.startswith("."), path_assertion)

    def test_rts_04_uses_current_review_output_sections(self) -> None:
        self.assertEqual(
            CASE_INDEX["RTS-04"].assert_semantics,
            (
                "评审结论",
                "阻断项",
                "主要问题",
                "改进方案",
                "待补充信息",
                "建议验证",
            ),
        )

    def test_multi_turn_cases_have_required_metadata(self) -> None:
        for case in ALL_CASES:
            turns = getattr(case, "turns", ())
            if not turns:
                continue
            with self.subTest(case_id=case.case_id):
                self.assertGreaterEqual(len(turns), 2)
                self.assertEqual(turns[0].expected_result, "STOP_AND_ASK")
                self.assertEqual(turns[-1].expected_result, case.expected_result)
                for index, turn in enumerate(turns, start=1):
                    with self.subTest(case_id=case.case_id, turn=index):
                        self.assertTrue(turn.user_input)
                        self.assertTrue(turn.expected_result)
                        self.assertTrue(
                            turn.assert_paths
                            or turn.assert_structure
                            or turn.assert_semantics
                            or turn.assert_safety
                            or turn.forbidden_behavior
                        )

    def test_setup_architect_multi_turn_cases_have_actionable_case_metadata(self) -> None:
        for case_id in ("SA-13", "SA-14"):
            case = CASE_INDEX[case_id]
            with self.subTest(case_id=case_id):
                self.assertTrue(case.prompt)
                self.assertTrue(case.purpose)
                self.assertTrue(case.assert_semantics or case.assert_safety or case.forbidden_behavior)

    def test_sa_13_stays_in_phase_1(self) -> None:
        self.assertIn("SA-13", PHASE_1_CASE_IDS)
        self.assertEqual(CASE_INDEX["SA-13"].expected_result, "SUCCESS_INIT")

    def test_sa_14_stays_in_phase_2(self) -> None:
        self.assertIn("SA-14", PHASE_2_CASE_IDS)
        self.assertEqual(CASE_INDEX["SA-14"].expected_result, "SUCCESS_REPLACE_TEMPLATE")

    def test_cts_13_tracks_missing_shared_context_consumption(self) -> None:
        self.assertEqual(CASE_INDEX["CTS-13"].expected_result, "STOP_AND_ASK")
        self.assertEqual(
            CASE_INDEX["CTS-13"].assert_semantics,
            ("明确指出缺失的共享上下文消费链",),
        )
        self.assertEqual(
            CASE_INDEX["CTS-13"].forbidden_behavior,
            ("跳过上下文引用继续生成最终方案",),
        )


if __name__ == "__main__":
    unittest.main()
