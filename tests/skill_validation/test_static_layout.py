import unittest

from tests.skill_validation.helpers import ASSISTANT_TARGETS, bootstrapped_project


class StaticLayoutTests(unittest.TestCase):
    def test_bootstrap_rejects_unknown_assistant(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown assistant"):
            with bootstrapped_project("unknown"):
                self.fail("context manager should not yield for an unknown assistant")

    def test_bootstrap_creates_minimum_architecture(self) -> None:
        for assistant in ASSISTANT_TARGETS:
            with self.subTest(assistant=assistant):
                with bootstrapped_project(assistant) as project_dir:
                    self.assertTrue((project_dir / ".architecture").is_dir())
                    self.assertTrue((project_dir / ".architecture/technical-solutions").is_dir())
                    self.assertTrue((project_dir / ".architecture/templates").is_dir())
                    self.assertTrue(
                        (project_dir / ".architecture/templates/technical-solution-template.md").is_file()
                    )
                    self.assertTrue((project_dir / ".architecture/members.yml").is_file())
                    self.assertTrue((project_dir / ".architecture/principles.md").is_file())
                    self.assertFalse((project_dir / ".architecture/.architecture").exists())
                    self.assertFalse((project_dir / ".architecture/agent_docs").exists())
                    self.assertFalse((project_dir / "CLAUDE.md").exists())
                    self.assertFalse((project_dir / ".architecture/solutions").exists())
                    self.assertFalse((project_dir / ".architecture/plans").exists())
                    self.assertFalse((project_dir / ".architecture/reviews").exists())
                    self.assertFalse((project_dir / "ai-architect-tmp").exists())
                    self.assertFalse((project_dir / ".architecture/config.yml").exists())
                    self.assertFalse(
                        (project_dir / ".architecture/templates/review-template.md").exists()
                    )
                    self.assertFalse(
                        (project_dir / ".architecture/templates/implementation-plan-template.md").exists()
                    )
                    self.assertFalse(
                        (project_dir / ".architecture/reviews/initial-system-analysis.md").exists()
                    )

    def test_only_selected_assistant_target_exists(self) -> None:
        for assistant, selected_target in ASSISTANT_TARGETS.items():
            with self.subTest(assistant=assistant):
                with bootstrapped_project(assistant) as project_dir:
                    for target in ASSISTANT_TARGETS.values():
                        target_path = project_dir / target
                        if target == selected_target:
                            self.assertTrue(target_path.is_dir())
                            self.assertFalse(target_path.is_symlink())
                            self.assertFalse((target_path / ".git").exists())
                            self.assertTrue((target_path / "setup-architect" / "SKILL.md").is_file())
                            self.assertTrue(
                                (target_path / "create-technical-solution" / "SKILL.md").is_file()
                            )
                        else:
                            self.assertFalse(target_path.exists())


if __name__ == "__main__":
    unittest.main()
