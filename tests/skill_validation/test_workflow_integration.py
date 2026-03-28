import unittest
from pathlib import Path

from tests.skill_validation.case_catalog import CASE_INDEX, PHASE_1_CASE_IDS, PHASE_2_CASE_IDS, PHASE_3_CASE_IDS


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/skills-integration-tests.yml"
RUNBOOK_PATH = REPO_ROOT / "docs/superpowers/testing/skill-validation.md"
INSTALLATION_PATH = REPO_ROOT / "INSTALLATION.md"


def section_body(markdown: str, heading: str) -> str:
    marker = f"### {heading}\n"
    start = markdown.index(marker) + len(marker)
    next_heading = markdown.find("\n### ", start)
    if next_heading == -1:
        next_heading = len(markdown)
    return markdown[start:next_heading]


class WorkflowIntegrationTests(unittest.TestCase):
    def test_installation_doc_keeps_skill_copy_scope_generic(self) -> None:
        installation = INSTALLATION_PATH.read_text(encoding="utf-8")

        self.assertIn("全部一级 skill 目录", installation)
        self.assertIn("不要只复制后续将要执行的某一个 skill", installation)
        self.assertIn('for skill_dir in ./tech-solution-tmp/skills/*; do', installation)
        self.assertIn("不是 Stage 2 的安装范围", installation)
        self.assertNotIn("3 个 skill", installation)

    def test_workflow_runs_skill_validation_contract_suite(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("- name: Run skill validation contract suite", workflow)
        self.assertIn(
            'python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v',
            workflow,
        )

    def test_workflow_derives_expected_skill_set_from_repo_directory(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn('repo_root="$(git rev-parse --show-toplevel)"', workflow)
        self.assertIn('for skill_dir in "$repo_root"/skills/*; do', workflow)
        self.assertIn('skill_name="$(basename "$skill_dir")"', workflow)
        self.assertNotIn(
            "printf '%s\\n' create-technical-solution review-technical-solution setup-architect",
            workflow,
        )

    def test_runbook_documents_local_skill_validation_flow(self) -> None:
        runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("# Skill Validation Runbook", runbook)
        self.assertIn("静态契约层", runbook)
        self.assertIn("流程场景层", runbook)
        self.assertIn("行为回归层", runbook)
        self.assertIn("对抗边界层", runbook)
        self.assertIn("review-technical-solution", runbook)
        self.assertIn(
            'python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v',
            runbook,
        )
        self.assertIn("SA-01", runbook)
        self.assertIn("CTS-08", runbook)
        self.assertIn("RTS-01", runbook)
        self.assertIn("RTS-09", runbook)

    def test_runbook_includes_phase_rollout_guidance(self) -> None:
        runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("## Phase rollout", runbook)
        self.assertIn("### Phase 1", runbook)
        self.assertIn("### Phase 2", runbook)
        self.assertIn("### Phase 3", runbook)

        for case_id in PHASE_1_CASE_IDS:
            self.assertIn(case_id, runbook)
        for case_id in PHASE_2_CASE_IDS:
            self.assertIn(case_id, runbook)
        for case_id in PHASE_3_CASE_IDS:
            self.assertIn(case_id, runbook)

    def test_runbook_case_layer_examples_match_catalog(self) -> None:
        runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

        expected_layer_examples = {
            "静态契约层": ("SA-11", "SA-12", "RTS-09"),
            "流程场景层": ("SA-01", "CTS-01", "CTS-11", "RTS-01", "RTS-02"),
            "行为回归层": ("SA-03", "CTS-04", "CTS-09", "RTS-04", "RTS-05", "RTS-06"),
            "对抗边界层": ("SA-07", "SA-08", "CTS-07", "CTS-08", "RTS-03", "RTS-07", "RTS-08"),
        }

        for layer, case_ids in expected_layer_examples.items():
            layer_section = section_body(runbook, layer)
            for case_id in case_ids:
                self.assertEqual(CASE_INDEX[case_id].layer, layer)
                self.assertIn(case_id, layer_section)


if __name__ == "__main__":
    unittest.main()
