from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load_yaml(path: str) -> dict:
    return yaml.safe_load(read(path))


def test_bootstrap_state_template_tracks_artifacts_and_template_mode() -> None:
    state = load_yaml("skills/bootstrap-architecture/templates/_template.yaml")

    assert state["template_mode"] == "default"
    assert state["required_artifacts"] == [
        ".architecture/members.yml",
        ".architecture/principles.md",
        ".architecture/templates/technical-solution-template.md",
    ]
    assert state["produced_artifacts"] == []
    assert state["cleanup_allowed"] is False


def test_skill_doc_requires_checkpoint_files_and_true_completion() -> None:
    text = read("skills/bootstrap-architecture/SKILL.md")

    assert "checkpoints.step-<N>.yaml" in text
    assert "只有在全部 required_artifacts 已落盘后" in text
    assert "current_step 必须等于最终步骤" in text


def test_step4_materializes_default_template_without_prompting() -> None:
    text = read("skills/bootstrap-architecture/steps/4-confirm-template.md")

    assert "必须询问用户" not in text
    assert "写入默认模板" in text
    assert "初始化完成后" in text
    assert "manage-technical-solution-template" in text
