from contextlib import contextmanager
from pathlib import Path
import shutil
import tempfile
from typing import Iterable, Iterator


REPO_ROOT = Path(__file__).resolve().parents[2]

ASSISTANT_TARGETS = {
    "claude": ".claude/skills",
    "qoder": ".qoder/skills",
    "lingma": ".lingma/skills",
    "trae": ".trae/skills",
    "generic": ".agents/skills",
}


def repo_path(*parts: str) -> Path:
    return REPO_ROOT.joinpath(*parts)


def read_repo_text(relative_path: str) -> str:
    return repo_path(relative_path).read_text(encoding="utf-8")


def skill_directory_names() -> list[str]:
    skills_root = repo_path("skills")
    return sorted(path.name for path in skills_root.iterdir() if path.is_dir())


def load_setup_contract_sources() -> dict[str, str]:
    return {
        "main": read_repo_text("skills/setup-architect/SKILL.md"),
        "installation": read_repo_text(
            "skills/setup-architect/references/installation-procedures.md"
        ),
        "member_customization": read_repo_text(
            "skills/setup-architect/references/member-customization.md"
        ),
        "principles_customization": read_repo_text(
            "skills/setup-architect/references/principles-customization.md"
        ),
        "principles_template": read_repo_text(
            "skills/setup-architect/templates/principles-template.md"
        ),
        "template_customization": read_repo_text(
            "skills/setup-architect/references/technical-solution-template-customization.md"
        ),
    }


def load_create_solution_contract_sources() -> dict[str, str]:
    return {
        "main": read_repo_text("skills/create-technical-solution/SKILL.md"),
        "solution_process": read_repo_text(
            "skills/create-technical-solution/references/solution-process.md"
        ),
        "template_adaptation": read_repo_text(
            "skills/create-technical-solution/references/template-adaptation.md"
        ),
        "progress_transparency": read_repo_text(
            "skills/create-technical-solution/references/progress-transparency.md"
        ),
        "working_draft_protocol": read_repo_text(
            "skills/create-technical-solution/references/working-draft-protocol.md"
        ),
        "analysis_guide": read_repo_text(
            "skills/create-technical-solution/references/solution-analysis-guide.md"
        ),
    }


def load_review_solution_contract_sources() -> dict[str, str]:
    return {
        "main": read_repo_text("skills/review-technical-solution/SKILL.md"),
        "review_process": read_repo_text(
            "skills/review-technical-solution/references/review-process.md"
        ),
        "analysis_guide": read_repo_text(
            "skills/review-technical-solution/references/review-analysis-guide.md"
        ),
        "output_contract": read_repo_text(
            "skills/review-technical-solution/references/review-output-contract.md"
        ),
    }


def testdata_path(name: str) -> Path:
    return repo_path("tests", "skill_validation", "testdata", name)


def top_level_headings(markdown: str) -> list[str]:
    """Extract template section headings from normal markdown document content.

    This helper treats markdown `## ` headings as top-level template sections and
    ignores fenced code block content so example snippets do not become false
    positives.
    """
    headings: list[str] = []
    in_fence = False
    for line in markdown.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("## "):
            headings.append(line[3:].strip())
    return headings


def require_all_snippets(testcase, text: str, snippets: Iterable[str]) -> None:
    for snippet in snippets:
        testcase.assertIn(snippet, text)


def require_snippets_in_order(testcase, text: str, snippets: Iterable[str]) -> None:
    start = 0
    for snippet in snippets:
        index = text.find(snippet, start)
        testcase.assertNotEqual(index, -1, f"Snippet not found after offset {start}: {snippet!r}")
        start = index + len(snippet)


def validate_assistant(assistant: str) -> str:
    if assistant not in ASSISTANT_TARGETS:
        supported = ", ".join(sorted(ASSISTANT_TARGETS))
        raise ValueError(f"Unknown assistant '{assistant}'. Expected one of: {supported}")
    return ASSISTANT_TARGETS[assistant]


def copy_repo_asset(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def install_validation_skills(target_root: Path) -> None:
    for skill_name in skill_directory_names():
        copy_repo_asset(repo_path("skills", skill_name), target_root / skill_name)


@contextmanager
def bootstrapped_project(assistant: str) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir_name:
        project_dir = Path(temp_dir_name) / assistant
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "README.md").write_text("# Skill-only test project\n", encoding="utf-8")

        selected_target = project_dir / validate_assistant(assistant)
        selected_target.parent.mkdir(parents=True, exist_ok=True)

        install_validation_skills(selected_target)

        skill_root = selected_target / "setup-architect"
        (project_dir / ".architecture" / "technical-solutions").mkdir(parents=True, exist_ok=True)
        (project_dir / ".architecture" / "templates").mkdir(parents=True, exist_ok=True)

        shutil.copyfile(
            skill_root / "templates" / "technical-solution-template.md",
            project_dir / ".architecture" / "templates" / "technical-solution-template.md",
        )
        shutil.copyfile(
            skill_root / "templates" / "members-template.yml",
            project_dir / ".architecture" / "members.yml",
        )
        shutil.copyfile(
            skill_root / "templates" / "principles-template.md",
            project_dir / ".architecture" / "principles.md",
        )

        yield project_dir
