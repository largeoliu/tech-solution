from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_step1_signal_taxonomy_includes_domain_facts() -> None:
    text = read("skills/bootstrap-architecture/steps/1-analyze-project.md")

    assert "`domain`" in text


def test_step2_requires_signal_ids_not_context_ids() -> None:
    text = read("skills/bootstrap-architecture/steps/2-customize-team.md")

    assert "`S1`" in text
    assert "`C1`" in text
    assert "只能引用 signal 编号" in text


def test_step3_treats_principles_mapping_table_as_appendix() -> None:
    step_text = read("skills/bootstrap-architecture/steps/3-customize-principles.md")
    template_text = read("skills/bootstrap-architecture/templates/principles-template.md")

    assert "## 原则映射表" in template_text
    assert "附录" in step_text
    assert "`原则映射表`" in step_text


def test_installation_stage2_prose_matches_no_backup_replace_only_contract() -> None:
    text = read("INSTALLATION.md")

    assert "Stage 2 不保留安装备份" in text
    assert "仅替换仓库当前 canonical skills 的同名目录" in text
    assert "额外残留的旧 skill 目录不会删除" in text
