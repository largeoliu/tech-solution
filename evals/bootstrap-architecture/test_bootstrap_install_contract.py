from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_prefers_repo_local_installation_doc() -> None:
    text = read("README.md")

    assert "读取当前仓库中的 `INSTALLATION.md`" in text


def test_installation_uses_unique_temp_clone_dir() -> None:
    text = read("INSTALLATION.md")

    assert "./tech-solution-tmp" not in text
    assert "mktemp -d" in text


def test_installation_does_not_create_skill_backups() -> None:
    text = read("INSTALLATION.md")

    assert ".skill-backups" not in text
    assert "backup_root=" not in text


def test_installation_replaces_canonical_skills_by_delete_then_copy() -> None:
    text = read("INSTALLATION.md")

    assert 'rm -rf "$TARGET/$skill_name"' in text
    assert 'cp -r "$skill_dir" "$TARGET/"' in text


def test_installation_reports_extra_skills_without_deleting_them() -> None:
    text = read("INSTALLATION.md")

    assert "发现额外 skill（保留未删除）" in text
    assert "发现 stale skill" not in text


def test_installation_moves_template_customization_to_follow_up_flow() -> None:
    text = read("INSTALLATION.md")

    assert "默认模板写入 `.architecture/templates/technical-solution-template.md`" in text
    assert "初始化完成后" in text
    assert "manage-technical-solution-template" in text
