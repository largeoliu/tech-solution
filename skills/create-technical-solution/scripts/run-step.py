# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""统一步骤编排器：封装验证、状态推进和 step card 加载，降低 Agent 协调负荷。

两种操作模式：
  status  ：查看当前步骤、验证状态、step card 操作指引
  complete：完成当前步骤并推进（自动处理验证、receipt、gate flags）

用法示例：
  # 查看当前状态
  python /path/to/run-step.py --state <状态文件>

  # 完成全自动步骤
  python /path/to/run-step.py --state <状态文件> --complete --summary "前置文件检查通过"

  # 完成半自动步骤（step 1）
  python /path/to/run-step.py --state <状态文件> --complete --summary "定题完成" --slug my-feature

  # 完成半自动步骤（step 4）
  python /path/to/run-step.py --state <状态文件> --complete --summary "类型判定" \\
    --solution-type "新功能方案"

  # 完成半自动步骤（step 5）
  python /path/to/run-step.py --state <状态文件> --complete --summary "成员选定" \\
    --member SYSTEMS_ARCHITECT --member DOMAIN_EXPERT

  # 完成创作型步骤（step 7/8）
  python /path/to/run-step.py --state <状态文件> --complete --summary "WD-CTX 完成" <<'HEREDOC'
  <WD-CTX 内容>
  HEREDOC

  # 完成创作型步骤（step 9，按槽位）
  python /path/to/run-step.py --state <状态文件> --complete --summary "专家分析完成" <<'HEREDOC'
  ---BLOCK:WD-EXP-SLOT-01
  <专家分析内容>
  HEREDOC
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("缺少 pyyaml。运行: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import (
    dump_yaml,
    iso_now,
    require_receipt,
    refresh_receipt,
    render_run_step_command,
    run_step_base_command,
    working_draft_path_for_slug,
    workflow_default_block,
    workflow_step_card_path,
    workflow_step_name,
)
from runtime_snapshot import RuntimeSnapshot, load_runtime_snapshot


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {}
    data = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def seed_checkpoint_summary(state_path: Path, step: int, summary: str) -> None:
    state = load_state(state_path)
    if not state:
        return
    checkpoints = state.get("checkpoints")
    if not isinstance(checkpoints, dict):
        return
    checkpoint = checkpoints.get(f"step-{step}")
    if not isinstance(checkpoint, dict):
        checkpoint = {}
        checkpoints[f"step-{step}"] = checkpoint
    if str(checkpoint.get("summary") or "").strip():
        return
    checkpoint["summary"] = summary
    refresh_receipt(state)
    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def get_current_step(state: dict[str, Any]) -> int:
    return int(state.get("current_step") or 1)


def get_repo_root(state_path: Path) -> Path:
    return load_runtime_snapshot(state_path).repo_root


def get_slug(state_path: Path) -> str:
    return load_runtime_snapshot(state_path).slug


def get_step_name(step: int) -> str:
    try:
        return workflow_step_name(step)
    except KeyError:
        return "未知"


def get_step_card_path(step: int) -> Path:
    return workflow_step_card_path(step)


def default_block_for_step(step: int) -> str | None:
    try:
        return workflow_default_block(step)
    except KeyError:
        return None


def run_script(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """运行子进程脚本，返回 (exit_code, stdout, stderr)。"""
    result = subprocess.run(
        [sys.executable] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.returncode, result.stdout, result.stderr


@lru_cache(maxsize=1)
def load_initialize_state_module() -> Any:
    spec = importlib.util.spec_from_file_location("create_technical_solution_initialize_state", SCRIPTS_DIR / "initialize-state.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_validate_state_module() -> Any:
    spec = importlib.util.spec_from_file_location("create_technical_solution_validate_state", SCRIPTS_DIR / "validate-state.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_upsert_draft_block_module() -> Any:
    spec = importlib.util.spec_from_file_location("create_technical_solution_upsert_draft_block", SCRIPTS_DIR / "upsert-draft-block.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_render_final_document_module() -> Any:
    spec = importlib.util.spec_from_file_location("create_technical_solution_render_final_document", SCRIPTS_DIR / "render-final-document.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_finalize_cleanup_module() -> Any:
    spec = importlib.util.spec_from_file_location("create_technical_solution_finalize_cleanup", SCRIPTS_DIR / "finalize-cleanup.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_advance_state_step_module() -> Any:
    spec = importlib.util.spec_from_file_location("create_technical_solution_advance_state_step", SCRIPTS_DIR / "advance-state-step.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_extract_template_snapshot_module() -> Any:
    spec = importlib.util.spec_from_file_location("create_technical_solution_extract_template_snapshot", SCRIPTS_DIR / "extract-template-snapshot.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_block_scaffolds_module() -> Any:
    spec = importlib.util.spec_from_file_location("create_technical_solution_block_scaffolds", SCRIPTS_DIR / "block_scaffolds.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_validator(state_path: Path, step: int, write_receipt: bool = False) -> tuple[bool, str]:
    """运行 validate-state.py，返回 (passed, output)。"""
    module = load_validate_state_module()
    state = module.load_state(state_path)
    validator = module.GateValidator(state, state_path)
    errors: list[dict[str, Any]] = []
    getattr(validator, f"step_{step}")(errors)

    if errors:
        payload = {
            "step": step,
            "passed": False,
            "summary": module.build_summary(errors),
            "repair_plan": module.build_repair_plan(errors, state_path=state_path, state=state),
            "issues": errors,
        }
        return False, json.dumps(payload, ensure_ascii=False, indent=2)

    payload: dict[str, Any] = {
        "step": step,
        "passed": True,
        "summary": {"error_count": 0},
    }
    if write_receipt:
        payload["gate_receipt"] = module.write_pass_receipt(state_path, validator.state, step)
    return True, json.dumps(payload, ensure_ascii=False, indent=2)


def upsert_block_in_process(
    state_path: Path,
    working_dir: Path,
    block_name: str,
    content: str,
    summary: str,
    require_receipt_step: int | None,
) -> tuple[int, str]:
    module = load_upsert_draft_block_module()
    try:
        payload = module.upsert_with_sync(
            working_dir=working_dir,
            state_path=state_path,
            block_updates=[(block_name, content)],
            summary=summary,
            require_receipt_step=require_receipt_step or 0,
        )
    except SystemExit as exc:
        return 1, str(exc)
    return 0, json.dumps(payload, ensure_ascii=False, indent=2)


def upsert_blocks_in_process(
    state_path: Path,
    working_dir: Path,
    summary: str,
    block_updates: list[tuple[str, str]],
    *,
    validate_step: int | None = None,
) -> tuple[int, str]:
    module = load_upsert_draft_block_module()
    original_state_text = state_path.read_text(encoding="utf-8")
    state = load_state(state_path)
    try:
        if validate_step is not None:
            require_receipt(state, expected_step=validate_step)
        slots = state.get("slots") or []
        for block_name, content in block_updates:
            module.write_working_draft_file(working_dir, block_name, content, slots)
        module.sync_state_for_blocks(state, block_updates, summary)
        refresh_receipt(state)
        dump_yaml(state_path, state)
        if validate_step is not None:
            passed, validator_output = run_validator(
                state_path,
                validate_step,
                write_receipt=False,
            )
            if not passed:
                raise RuntimeError(f"步骤 {validate_step} 验证失败:\n{validator_output}")
    except SystemExit as exc:
        try:
            state_path.write_text(original_state_text, encoding="utf-8")
        except Exception:
            pass
        return 1, str(exc)
    except Exception as exc:
        try:
            state_path.write_text(original_state_text, encoding="utf-8")
        except Exception:
            pass
        exit_code = 2 if isinstance(exc, RuntimeError) and str(exc).startswith("步骤 ") else 1
        return exit_code, f"批量写入失败，已回滚: {exc}"
    return 0, json.dumps(
        {
            "working_dir": str(working_dir),
            "blocks": [name for name, _content in block_updates],
            "current_step": state.get("current_step"),
            "gate_receipt_step": state.get("gate_receipt", {}).get("step"),
        },
        ensure_ascii=False,
        indent=2,
    )


def render_final_document_in_process(state_path: Path, summary: str) -> tuple[int, str]:
    module = load_render_final_document_module()
    try:
        payload = module.render_final_document(
            state_path=state_path,
            content_path=None,
            summary=summary,
        )
    except SystemExit as exc:
        return 1, str(exc)
    return 0, json.dumps(payload, ensure_ascii=False, indent=2)


def finalize_cleanup_in_process(state_path: Path, summary: str) -> tuple[int, str]:
    module = load_finalize_cleanup_module()
    try:
        exit_code, payload = module.run_cleanup(state_path, summary)
    except SystemExit as exc:
        return 1, str(exc)
    return exit_code, json.dumps(payload, ensure_ascii=False, indent=2)


def advance_state_step_in_process(
    state_path: Path,
    step: int,
    summary: str,
    field: list[str] | None = None,
    field_json: list[str] | None = None,
    state_fields: list[str] | None = None,
    state_fields_json: list[str] | None = None,
    append_completed: bool = False,
    next_step: int | None = None,
    require_receipt_step: int | None = None,
) -> tuple[int, str]:
    module = load_advance_state_step_module()
    try:
        payload = module.advance_state_step(
            state_path=state_path,
            step=step,
            summary=summary,
            field=field,
            field_json=field_json,
            state_fields=state_fields,
            state_fields_json=state_fields_json,
            append_completed=append_completed,
            next_step=next_step,
            require_receipt_step=require_receipt_step,
        )
    except SystemExit as exc:
        return 1, str(exc)
    return 0, json.dumps(payload, ensure_ascii=False, indent=2)


def initialize_state_in_process(state_path: Path, slug: str, summary: str) -> tuple[int, str]:
    module = load_initialize_state_module()
    try:
        payload = module.initialize_state(
            state_path=state_path,
            slug=slug,
            summary=summary,
            next_step=2,
        )
    except SystemExit as exc:
        return 1, str(exc)
    return 0, json.dumps(payload, ensure_ascii=False, indent=2)


def extract_template_snapshot_in_process(
    *,
    state_path: Path,
    template_path: str,
    slug: str,
    draft_path: str,
    repo_root: Path,
) -> tuple[int, str]:
    module = load_extract_template_snapshot_module()
    template_file = (repo_root / template_path).resolve()
    if not template_file.exists():
        return 1, f"模板文件不存在: {template_file}"

    template_markdown = template_file.read_text(encoding="utf-8")
    headings = module.extract_slot_headings(template_markdown)
    if not headings:
        return 1, f"模板未提取到任何槽位: {template_file}"

    fingerprint = module.compute_template_fingerprint(template_markdown, headings)
    working_draft = (repo_root / draft_path).resolve()
    working_draft.parent.mkdir(parents=True, exist_ok=True)
    working_draft.write_text(module.build_working_draft(template_file, headings, slug), encoding="utf-8")
    try:
        module.update_state(
            state_path=state_path.resolve(),
            template_path=template_file,
            working_draft=working_draft,
            headings=headings,
            fingerprint=fingerprint,
        )
    except SystemExit as exc:
        return 1, str(exc)

    payload = {
        "template_path": str(template_file),
        "template_fingerprint": fingerprint,
        "slot_count": len(headings),
        "slot_titles": [item["title"] for item in headings],
        "working_draft_path": str(working_draft),
    }
    return 0, json.dumps(payload, ensure_ascii=False, indent=2)


def extract_step_card_operations(step: int) -> str:
    """提取 step card 的'操作'段落。"""
    try:
        card_path = get_step_card_path(step)
    except KeyError:
        return ""
    if not card_path.exists():
        return f"（step card 文件不存在: {card_path}）"
    content = card_path.read_text(encoding="utf-8")
    # 提取 ## 操作 到下一个 ## 之间的内容
    match = re.search(r"^## 操作\s*\n(.*?)(?=^## |\Z)", content, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return content


def print_status(state_path: Path, snapshot: RuntimeSnapshot | None = None) -> int:
    """打印当前步骤状态和操作指引。"""
    snapshot = snapshot or load_runtime_snapshot(state_path)
    assert snapshot is not None
    state = snapshot.state
    if not state:
        print("=" * 60)
        print("状态文件不存在或为空。")
        print(f"请先运行: {run_step_base_command(snapshot.state_path)} --complete --summary \"<主题摘要>\" --slug <slug>")
        print("=" * 60)
        return 0

    step = snapshot.current_step
    completed = state.get("completed_steps", [])
    slug = snapshot.slug

    print("=" * 60)
    print(f"  当前步骤: {step} - {get_step_name(step)}")
    print(f"  已完成:   {completed}")
    print(f"  Slug:     {slug}")
    print("=" * 60)

    # 运行 validator
    passed, output = run_validator(snapshot.state_path, step)
    if passed:
        print(f"\n✅ 步骤 {step} 验证通过。可以继续执行或推进到下一步。")
    else:
        print(f"\n⚠️  步骤 {step} 验证未通过：")
        try:
            result = json.loads(output)
            for issue in result.get("issues", []):
                print(f"  ✗ {issue.get('message', '')}")
                guidance = issue.get("repair_guidance", "")
                if guidance:
                    print(f"    → {guidance}")
        except json.JSONDecodeError:
            print(f"  {output[:500]}")

    # 打印 step card 操作指引
    print(f"\n{'─' * 40}")
    print(f"📋 步骤 {step} 操作指引：")
    print(f"{'─' * 40}")
    ops = extract_step_card_operations(step)
    if ops:
        print(ops)

    # 打印下一步命令
    print(f"\n{'─' * 40}")
    print("📌 下一步命令：")
    print(f"{'─' * 40}")
    _print_next_command(snapshot.state_path, step, state)

    return 0


def _print_next_command(state_path: Path, step: int, state: dict[str, Any]) -> None:
    """根据步骤类型输出推荐的 complete 命令。"""
    for line in render_run_step_command(state_path=state_path, step=step, state=state):
        print(line)


# ── complete 模式：各步骤的实现 ──────────────────────────────


def complete_step_1(state_path: Path, summary: str, slug: str | None, **_: Any) -> tuple[int, str]:
    if not slug:
        return 1, "步骤 1 需要 --slug 参数。"
    code, stdout = initialize_state_in_process(state_path, slug, summary)
    if code != 0:
        return code, f"initialize-state.py 失败:\n{stdout}"
    return 0, f"✅ 步骤 1 完成。slug={slug}，已推进到步骤 2。\n{stdout}"


def complete_step_2(state_path: Path, summary: str, **_: Any) -> tuple[int, str]:
    snapshot = load_runtime_snapshot(state_path)
    state = snapshot.state
    repo_root = snapshot.repo_root
    # 检查前置文件（这是步骤 2 的核心操作）
    missing = []
    for field in ("members_path", "principles_path", "template_path"):
        path_val = str(state.get(field) or "").strip()
        if not path_val or not (repo_root / path_val).exists():
            missing.append(field)
    if missing:
        return 2, f"前置文件缺失: {missing}。请先运行 bootstrap-architecture。"
    # 推进（advance-state-step 内部会自动补 prerequisites_checked=true）
    code, stdout = advance_state_step_in_process(
        state_path=state_path,
        step=2,
        summary=summary,
        field=["prerequisites_checked=true"],
        field_json=None,
        state_fields=None,
        state_fields_json=None,
        append_completed=True,
        next_step=3,
        require_receipt_step=None,
    )
    if code != 0:
        return code, f"advance-state-step.py 失败:\n{stdout}"
    return 0, f"✅ 步骤 2 完成。前置文件检查通过，已推进到步骤 3。"


def complete_step_3(state_path: Path, summary: str, **_: Any) -> tuple[int, str]:
    snapshot = load_runtime_snapshot(state_path)
    state = snapshot.state
    slug = snapshot.slug
    repo_root = snapshot.repo_root
    template_path = str(state.get("template_path") or ".architecture/templates/technical-solution-template.md")
    draft_path = str(working_draft_path_for_slug(repo_root=repo_root, slug=slug).relative_to(repo_root))
    code, stdout = extract_template_snapshot_in_process(
        state_path=state_path,
        template_path=template_path,
        slug=slug,
        draft_path=draft_path,
        repo_root=repo_root,
    )
    if code != 0:
        return code, f"extract-template-snapshot.py 失败:\n{stdout}"
    return 0, f"✅ 步骤 3 完成。模板已读取，working draft 已创建。\n{stdout}"


FULL_REQUIRED_ARTIFACTS = ["WD-CTX", "WD-TASK", "WD-EXP-*", "WD-SYN-*"]


def complete_step_4(
    state_path: Path, summary: str,
    solution_type: str | None = None,
    **_: Any,
) -> tuple[int, str]:
    if not solution_type:
        return 1, "步骤 4 需要 --solution-type 参数。"
    code, stdout = advance_state_step_in_process(
        state_path=state_path,
        step=4,
        summary=summary,
        field=[f"solution_type={solution_type}"],
        field_json=None,
        state_fields_json=[f"required_artifacts={json.dumps(FULL_REQUIRED_ARTIFACTS)}"],
        append_completed=True,
        next_step=5,
        require_receipt_step=None,
    )
    if code != 0:
        return code, f"advance-state-step.py 失败:\n{stdout}"
    return 0, f"✅ 步骤 4 完成。方案类型={solution_type}，已推进到步骤 5。\n{stdout}"


def complete_step_5(
    state_path: Path, summary: str, members: list[str] | None = None, **_: Any,
) -> tuple[int, str]:
    if not members:
        return 1, "步骤 5 需要至少一个 --member 参数。"
    members_json = json.dumps(members)
    code, stdout = advance_state_step_in_process(
        state_path=state_path,
        step=5,
        summary=summary,
        field=["members_checked=true"],
        field_json=[f"selected_members={members_json}", f"selected_member_count={len(members)}"],
        state_fields=None,
        state_fields_json=None,
        append_completed=True,
        next_step=6,
        require_receipt_step=None,
    )
    if code != 0:
        return code, f"advance-state-step.py 失败:\n{stdout}"
    return 0, f"✅ 步骤 5 完成。参与成员: {members}，已推进到步骤 6。"


def complete_step_6(state_path: Path, summary: str, **_: Any) -> tuple[int, str]:
    snapshot = load_runtime_snapshot(state_path)
    state = snapshot.state
    repo_root = snapshot.repo_root
    # 检测 repowiki
    repowiki_path = str(state.get("repowiki_path") or ".qoder/repowiki")
    repowiki_exists = (repo_root / repowiki_path).exists()
    source_count = 0
    if repowiki_exists:
        content_dir = repo_root / repowiki_path / "zh" / "content"
        if content_dir.exists():
            source_count = sum(1 for _ in content_dir.rglob("*.md"))
    code, stdout = advance_state_step_in_process(
        state_path=state_path,
        step=6,
        summary=summary,
        field=[
            "repowiki_checked=true",
            f"repowiki_exists={'true' if repowiki_exists else 'false'}",
        ],
        field_json=[f"repowiki_source_count={source_count}"],
        state_fields=None,
        state_fields_json=None,
        append_completed=True,
        next_step=7,
        require_receipt_step=None,
    )
    if code != 0:
        return code, f"advance-state-step.py 失败:\n{stdout}"
    status = "存在" if repowiki_exists else "不存在"
    return 0, f"✅ 步骤 6 完成。repowiki {status}，已推进到步骤 7。"


def complete_creative_step(
    state_path: Path,
    summary: str,
    step: int,
    stdin_content: str | None,
    snapshot: RuntimeSnapshot | None = None,
    **_: Any,
) -> tuple[int, str]:
    """处理步骤 7/8/9/10 的创作型步骤。内容通过 stdin 传入。"""
    if not stdin_content:
        return 1, f"步骤 {step} 需要通过 stdin 传入内容。"
    snapshot = snapshot or load_runtime_snapshot(state_path)
    assert snapshot is not None
    working_dir = snapshot.working_draft_path

    module = load_upsert_draft_block_module()
    block_updates = module.parse_stdin_blocks(stdin_content, step)
    if not block_updates:
        return 1, f"步骤 {step} 传入的内容为空。"

    code, output = upsert_blocks_in_process(
        state_path,
        working_dir,
        summary,
        block_updates,
        validate_step=step,
    )
    if code != 0:
        return code, f"写入 working draft 失败:\n{output}"

    results = [f"  ✓ {block_name} 已写入 working draft" for block_name, _body in block_updates]
    detail = "\n".join(results)
    new_snapshot = load_runtime_snapshot(state_path)
    new_step = new_snapshot.current_step
    return 0, f"✅ 步骤 {step} 完成。\n{detail}\n已推进到步骤 {new_step}。"



def complete_step_11(state_path: Path, summary: str, snapshot: RuntimeSnapshot | None = None, **_: Any) -> tuple[int, str]:
    snapshot = snapshot or load_runtime_snapshot(state_path)
    assert snapshot is not None
    seed_checkpoint_summary(state_path, 11, summary)
    passed, output = run_validator(state_path, 11, write_receipt=True)
    if not passed:
        return 2, f"步骤 11 验证失败:\n{output}"
    code, stdout = render_final_document_in_process(state_path, summary)
    if code != 0:
        return code, f"render-final-document.py 失败:\n{stdout}"
    return 0, f"✅ 步骤 11 完成。最终文档已渲染。\n{stdout}"


def complete_step_12(state_path: Path, summary: str, snapshot: RuntimeSnapshot | None = None, **_: Any) -> tuple[int, str]:
    snapshot = snapshot or load_runtime_snapshot(state_path)
    assert snapshot is not None
    seed_checkpoint_summary(state_path, 12, summary)
    passed, output = run_validator(state_path, 12, write_receipt=True)
    if not passed:
        return 2, f"步骤 12 验证失败:\n{output}"
    code, stdout = finalize_cleanup_in_process(state_path, summary)
    if code != 0:
        return code, f"finalize-cleanup.py 失败:\n{stdout}"
    return 0, f"✅ 步骤 12 完成。working draft 与状态文件已清理。\n{stdout}"


def emit_scaffold(state_path: Path, members: list[str] | None = None) -> int:
    snapshot = load_runtime_snapshot(state_path)
    if not snapshot.state:
        print("❌ 状态文件不存在。请先用 --slug 参数执行步骤 1。")
        return 1
    module = load_block_scaffolds_module()
    print(module.emit_scaffold(snapshot, members=members or []))
    return 0


def complete_step(args: argparse.Namespace) -> int:
    """根据当前步骤分发到对应的 complete 处理函数。"""
    state_path = Path(args.state).resolve()
    summary = args.summary

    # 步骤 1 特殊处理：state 可能还不存在
    if args.slug and (not state_path.exists() or get_current_step(load_state(state_path)) == 1):
        code, msg = complete_step_1(state_path, summary, args.slug)
        print(msg)
        return code

    snapshot = load_runtime_snapshot(state_path)
    state = snapshot.state
    if not state:
        print("❌ 状态文件不存在。请先用 --slug 参数执行步骤 1。")
        return 1

    step = snapshot.current_step

    stdin_content = getattr(args, '_stdin_content', None)
    dispatch = {
        1: lambda: complete_step_1(state_path, summary, args.slug),
        2: lambda: complete_step_2(state_path, summary),
        3: lambda: complete_step_3(state_path, summary),
        4: lambda: complete_step_4(
            state_path, summary,
            solution_type=args.solution_type,
        ),
        5: lambda: complete_step_5(state_path, summary, members=args.member),
        6: lambda: complete_step_6(state_path, summary),
        7: lambda: complete_creative_step(state_path, summary, 7, stdin_content, snapshot=snapshot),
        8: lambda: complete_creative_step(state_path, summary, 8, stdin_content, snapshot=snapshot),
        9: lambda: complete_creative_step(state_path, summary, 9, stdin_content, snapshot=snapshot),
        10: lambda: complete_creative_step(state_path, summary, 10, stdin_content, snapshot=snapshot),
        11: lambda: complete_step_11(state_path, summary, snapshot=snapshot),
        12: lambda: complete_step_12(state_path, summary, snapshot=snapshot),
    }

    handler = dispatch.get(step)
    if not handler:
        print(f"❌ 未知步骤: {step}")
        return 1

    code, msg = handler()
    print(msg)

    # 打印下一步提示
    if code == 0 and step < 12:
        new_snapshot = load_runtime_snapshot(state_path)
        new_state = new_snapshot.state
        new_step = new_snapshot.current_step
        if new_step <= 12:
            print(f"\n📌 下一步（步骤 {new_step} - {get_step_name(new_step)}）：")
            _print_next_command(new_snapshot.state_path, new_step, new_state)

    return code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="统一步骤编排器：封装验证、状态推进和 step card 加载",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--complete", action="store_true", help="完成当前步骤并推进")
    parser.add_argument("--emit-scaffold", action="store_true", help="输出当前步骤 scaffold 到 stdout")
    parser.add_argument("--summary", help="步骤完成摘要（--complete 时必需）")

    # 步骤特定参数
    parser.add_argument("--slug", help="步骤 1: 方案 slug")
    parser.add_argument("--solution-type", help="步骤 4: 方案类型")
    parser.add_argument("--member", action="append", default=[], help="步骤 5: 参与成员（可重复）")

    args = parser.parse_args()

    if not sys.stdin.isatty():
        args._stdin_content = sys.stdin.read()
    else:
        args._stdin_content = None

    if args.complete and args.emit_scaffold:
        parser.error("--emit-scaffold 与 --complete 不能同时使用。")

    if args.complete:
        if not args.summary:
            parser.error("--complete 需要 --summary 参数。")
        return complete_step(args)
    if args.emit_scaffold:
        return emit_scaffold(Path(args.state).resolve(), members=args.member)
    else:
        return print_status(Path(args.state).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
