from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_skill_doc_uses_current_cleanup_gate_language() -> None:
    text = read("skills/create-technical-solution/SKILL.md")

    assert "blocked = true" not in text
    assert "pending_questions" in text


def test_step11_doc_describes_default_overwrite() -> None:
    text = read("skills/create-technical-solution/steps/11-严格模板成稿并保存结果.md")

    assert "默认另存" not in text
    assert "时间戳后缀" not in text
    assert "默认覆盖" in text


def test_eval_docs_drop_legacy_blocked_and_alt_save_language() -> None:
    paths = [
        "evals/create-technical-solution/cases/T01.json",
        "evals/create-technical-solution/tests/D01-D04-描述边界.md",
        "evals/create-technical-solution/tests/E01-E06-边缘用例.md",
        "evals/create-technical-solution/tests/T03-moderate-鉴权重构.md",
        "evals/create-technical-solution/tests/T04-full-repowiki-多租户数据隔离.md",
    ]

    for path in paths:
        text = read(path)
        assert "blocked=true" not in text, path
        assert "block_reason" not in text, path
        assert "默认另存" not in text, path
        assert "时间戳后缀" not in text, path


def test_eval_docs_use_python3_not_uv_run() -> None:
    paths = [
        "evals/create-technical-solution/README.md",
        "evals/create-technical-solution/eval_runner.py",
    ]

    for path in paths:
        text = read(path)
        assert "uv run" not in text, path
        assert "python3" in text, path
