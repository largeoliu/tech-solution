import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.skill_validation import helpers as skill_helpers
from tests.skill_validation.helpers import ASSISTANT_TARGETS, bootstrapped_project


class StaticLayoutTests(unittest.TestCase):
    def test_install_validation_skills_copies_all_repo_skill_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_root = Path(temp_dir_name)
            fake_repo_root = temp_root / "repo"
            fake_skills_root = fake_repo_root / "skills"
            target_root = temp_root / "target"

            setup_skill_root = fake_skills_root / "setup-architect"
            (setup_skill_root / "references").mkdir(parents=True)
            (setup_skill_root / "templates").mkdir(parents=True)
            (setup_skill_root / "SKILL.md").write_text("setup", encoding="utf-8")
            (setup_skill_root / "references" / "installation-procedures.md").write_text(
                "install",
                encoding="utf-8",
            )
            (setup_skill_root / "templates" / "technical-solution-template.md").write_text(
                "template",
                encoding="utf-8",
            )
            (setup_skill_root / "templates" / "members-template.yml").write_text(
                "members",
                encoding="utf-8",
            )
            (setup_skill_root / "templates" / "principles-template.md").write_text(
                "principles",
                encoding="utf-8",
            )

            future_skill_root = fake_skills_root / "future-skill"
            (future_skill_root / "references").mkdir(parents=True)
            (future_skill_root / "SKILL.md").write_text("future", encoding="utf-8")
            (future_skill_root / "references" / "guide.md").write_text(
                "future guide",
                encoding="utf-8",
            )

            with patch.object(skill_helpers, "REPO_ROOT", fake_repo_root):
                skill_helpers.install_validation_skills(target_root)

            self.assertTrue((target_root / "setup-architect" / "SKILL.md").is_file())
            self.assertTrue((target_root / "future-skill" / "SKILL.md").is_file())
            self.assertTrue((target_root / "future-skill" / "references" / "guide.md").is_file())

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
        expected_skills = sorted(
            path.name for path in (skill_helpers.REPO_ROOT / "skills").iterdir() if path.is_dir()
        )

        for assistant, selected_target in ASSISTANT_TARGETS.items():
            with self.subTest(assistant=assistant):
                with bootstrapped_project(assistant) as project_dir:
                    for target in ASSISTANT_TARGETS.values():
                        target_path = project_dir / target
                        if target == selected_target:
                            self.assertTrue(target_path.is_dir())
                            self.assertFalse(target_path.is_symlink())
                            self.assertFalse((target_path / ".git").exists())
                            actual_skills = sorted(
                                child.name for child in target_path.iterdir() if child.is_dir()
                            )
                            self.assertEqual(actual_skills, expected_skills)
                            for skill_name in expected_skills:
                                self.assertTrue((target_path / skill_name / "SKILL.md").is_file())
                        else:
                            self.assertFalse(target_path.exists())

    def test_trae_bootstrap_uses_trae_target_only(self) -> None:
        with bootstrapped_project("trae") as project_dir:
            self.assertTrue((project_dir / ".trae/skills").is_dir())
            self.assertFalse((project_dir / ".qoder/skills").exists())
            self.assertFalse((project_dir / ".claude/skills").exists())
            self.assertFalse((project_dir / ".agents/skills").exists())


if __name__ == "__main__":
    unittest.main()
