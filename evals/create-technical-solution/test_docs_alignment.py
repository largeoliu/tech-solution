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


def test_reference_doc_matches_current_validator_json_contract() -> None:
    text = read("skills/create-technical-solution/REFERENCE.md")

    assert "state_snapshot" not in text
    assert "action_types" not in text
    assert "retry_command" not in text
    assert "completion_checks" not in text
    assert "artifact_write_hint" not in text
    assert "working_draft_context_hint" not in text

    assert "--write-pass-receipt" in text
    assert "gate_receipt" in text
    assert "repair_plan" in text
    assert "issues" in text
    assert "summary" in text
    assert "summary.recommended_repair_sequence" in text
    assert "summary.recommended_rollback_step" in text
    assert "summary.missing_artifacts" in text
    assert "summary.skip_instead_of_retry" in text
    assert "repair_plan[].step" in text
    assert "repair_plan[].action_type" in text
    assert "repair_plan[].script_command" in text
    assert "repair_plan[].depends_on_steps" in text
    assert "repair_plan[].expected_artifacts_after_fix" in text
    assert "repair_plan[].revalidate_step" in text
    assert "issues[*].repair_guidance" in text


def test_docs_cover_emit_scaffold_read_only_contract() -> None:
    ref_text = read("skills/create-technical-solution/REFERENCE.md")
    skill_text = read("skills/create-technical-solution/SKILL.md")

    assert "--emit-scaffold" in ref_text
    assert "stdout" in ref_text
    assert "不修改 state" in ref_text
    assert "不修改 working draft" in ref_text
    assert "不修改 receipt" in ref_text
    assert "不是第二条写入路径" in ref_text
    assert "--emit-scaffold 与 --complete 不能同时使用" in ref_text
    assert "auto-skip" in ref_text

    assert "--emit-scaffold" in skill_text
    assert "stdout" in skill_text
    assert "只读" in skill_text
    assert "--emit-scaffold 与 --complete 不能同时使用" in skill_text


def test_skill_doc_keeps_run_step_as_only_supported_public_entry() -> None:
    text = read("skills/create-technical-solution/SKILL.md")

    assert "唯一受支持的对外入口" in text
    assert "run-step.py" in text


def test_no_top_level_run_step_wrapper_exists() -> None:
    wrapper = ROOT / "skills" / "create-technical-solution" / "run-step.py"
    assert not wrapper.exists()


def test_run_step_script_docstring_avoids_low_level_public_flags() -> None:
    text = "\n".join(
        read("skills/create-technical-solution/scripts/run-step.py").splitlines()[:40]
    )

    assert "--mark-step-card-read" not in text
    assert "--solution-type" not in text
    assert "--member" not in text
    assert "--slug" not in text


def test_docs_cover_runtime_doctor_contract() -> None:
    ref_text = read("skills/create-technical-solution/REFERENCE.md")
    skill_text = read("skills/create-technical-solution/SKILL.md")

    assert "runtime_doctor.py" in ref_text
    assert "dry-run" in ref_text
    assert "--apply-safe-fixes" in ref_text
    assert "结构性" in ref_text
    assert "step" in ref_text
    assert "apply_safe_fixes" in ref_text
    assert "passed" in ref_text
    assert "summary" in ref_text
    assert "issues" in ref_text
    assert "repair_plan" in ref_text
    assert "safe_fixes" in ref_text
    assert "state_path" in ref_text
    assert "mutated" in ref_text

    assert "runtime_doctor.py" in skill_text
    assert "dry-run" in skill_text
    assert "--apply-safe-fixes" in skill_text
    assert "结构性" in skill_text
    assert "不是主执行路径" in skill_text


def test_step_docs_drop_stale_completion_checks_language() -> None:
    step_dir = ROOT / "skills" / "create-technical-solution" / "steps"
    for step_file in sorted(step_dir.glob("*.md")):
        text = step_file.read_text(encoding="utf-8")
        assert "completion_checks" not in text, f"{step_file.name} still references removed completion_checks"
        assert "retry_command" not in text, f"{step_file.name} still references removed retry_command"
        assert "artifact_write_hint" not in text, f"{step_file.name} still references removed artifact_write_hint"


def test_no_stale_repair_fields_anywhere() -> None:
    stale_fields = [
        "completion_checks",
        "artifact_write_hint",
        "working_draft_context_hint",
        "state_patch_hint",
    ]
    skill_dir = ROOT / "skills" / "create-technical-solution"
    for md_file in sorted(skill_dir.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        for field in stale_fields:
            assert field not in text, f"{md_file.relative_to(ROOT)} still contains stale field {field}"


def test_skill_doc_references_current_repair_fields() -> None:
    text = read("skills/create-technical-solution/SKILL.md")

    assert "action_types" not in text
    assert "state_patch_hint" not in text
    assert "artifact_write_hint" not in text
    assert "working_draft_context_hint" not in text
    assert "completion_checks" not in text
    assert "retry_command" not in text

    assert "repair_plan[].step" in text
    assert "repair_plan[].action_type" in text
    assert "repair_plan[].depends_on_steps" in text
    assert "repair_plan[].expected_artifacts_after_fix" in text
    assert "repair_plan[].script_command" in text
    assert "summary.recommended_repair_sequence" in text
    assert "summary.recommended_rollback_step" in text
    assert "summary.missing_artifacts" in text
    assert "summary.skip_instead_of_retry" in text
    assert "issues[*].repair_guidance" in text
