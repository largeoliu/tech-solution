# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""统一步骤编排器：封装验证、状态推进和 step card 加载，降低 Agent 协调负荷。

公共操作模式：
  status  ：查看当前步骤、验证状态、step card 操作指引
  advance ：高层推进当前步骤；自动步骤直接推进，业务/创作步骤返回提交契约
  complete：提交当前步骤业务内容或创作内容，并在通过校验后推进

公共用法示例：
  # 查看当前状态
  python /path/to/run-step.py --state <状态文件>

  # 进入当前步骤（空状态、自动步骤、业务步骤、创作步骤统一走这个入口）
  python /path/to/run-step.py --state <状态文件> --advance

  # 提交业务 JSON 或创作正文
  python /path/to/run-step.py --state <状态文件> --complete --ticket <ticket> --summary "<步骤完成>" <<'HEREDOC'
  {"title": "方案标题"}
  HEREDOC

低层 flags 仅供脚本、测试、调试使用，不属于公共主路径。
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

os.environ["__CTS_INTERNAL_CALL"] = "1"

try:
    import yaml
except ImportError:
    print("缺少 pyyaml。运行: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import (
    build_canonical_state_payload,
    canonical_step_defs,
    SOLUTION_ROOT,
    compute_artifact_fingerprint,
    dump_yaml,
    final_document_relative_path,
    iso_now,
    repo_root_from_state_path,
    require_receipt,
    refresh_receipt,
    render_run_step_command,
    run_step_base_command,
    working_draft_path_for_slug,
    working_draft_relative_path,
    workflow_default_block,
    workflow_step,
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
    state_path.write_text(
        yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


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


def allowed_block_pattern_for_step(step: int) -> str | None:
    workflow = workflow_step(step)
    if workflow.get("content_block"):
        return str(workflow["content_block"])
    if workflow.get("produces_pattern"):
        return str(workflow["produces_pattern"])
    produces = workflow.get("produces")
    if isinstance(produces, list) and len(produces) == 1:
        return str(produces[0])
    return None


STEP_DEFS: dict[int, dict[str, Any]] = canonical_step_defs()


def step_mode(step: int) -> str:
    return str(STEP_DEFS.get(step, {}).get("mode") or "manual")


def business_task_for_step(step: int) -> str:
    tasks = {
        1: "明确方案标题、slug、问题、目标、非目标与影响范围，完成定题与范围判断。",
        4: "基于需求文档和步骤 1 的定题与范围判断方案类型（新功能方案/改造方案/复用方案）。只做轻量分类，不需要搜索或阅读业务实现代码——现有资产盘点属于步骤 7。",
        5: "从成员名册中选择本次技术方案必须参与的参与成员，并确保覆盖必要视角。",
        7: "产出结构化共享上下文条目，沉淀需求目标、约束、影响范围与复用线索。",
        8: "产出逐槽位任务拆解，确保每个槽位绑定必须消费的上下文。",
        9: "按槽位补齐专家分析，明确决策类型、理由、证据与未决点。",
        10: "按槽位收敛综合结论，形成最终建议路径与落位写法。",
    }
    return tasks.get(step, f"推进步骤 {step}。")


def quality_contract_for_step(step: int) -> list[str]:
    contracts = {
        1: [
            '提交 JSON，至少包含字段 "slug"、"title"、"problem"、"goals"、"non_goals"、"scope"',
            'slug 必须是 ASCII kebab-case',
            "goals 和 non_goals 必须是数组",
            "不要提交命令或流程说明，只提交业务内容",
        ],
        4: [
            '提交 JSON，包含字段 "solution_type"',
            'solution_type 只能是："复用方案"、"新功能方案"、"改造方案"',
            "结论要与步骤 4 的证据分析一致",
            "本步骤只做轻量类型分类，不需要搜索或阅读业务实现代码",
            "现有资产盘点和复用/改造/新建路径比较属于步骤 7 和步骤 9/10，不属于本步骤",
        ],
        5: [
            '提交 JSON，包含字段 "selected_members"',
            'selected_members 必须是数组，元素来自 members.yml',
            "至少覆盖完成当前方案所需的关键角色",
        ],
        7: [
            "每条结论都要有 source",
            "每条结论都要有 conclusion",
            "每条结论都要有 applicable_slots",
            "每条结论都要有 confidence",
            "不要写自由摘要",
        ],
        8: [
            "每个槽位都要出现",
            "必须绑定共享上下文",
            "槽位标题必须与模板一致",
        ],
        9: [
            "每个槽位都要有专家分析",
            "必须包含决策类型、理由、证据、未决点",
            "不要只重复同一条证据",
        ],
        10: [
            "每个槽位都要有目标能力",
            "必须给出候选方案对比和选定路径",
            "不要保留模板占位词",
        ],
    }
    return contracts.get(step, [])


def structured_output_shape_for_step(step: int) -> dict[str, Any]:
    if step == 7:
        return {
            "type": "array",
            "item_schema": "ctx_entry",
            "required_fields": [
                "id",
                "source",
                "conclusion",
                "applicable_slots",
                "confidence",
            ],
        }
    if step == 8:
        return {
            "type": "array",
            "item_schema": "slot_task",
            "required_fields": ["slot", "required_ctx"],
        }
    if step == 9:
        return {
            "type": "array",
            "item_schema": "slot_analysis",
            "required_fields": [
                "slot",
                "decision_type",
                "rationale",
                "evidence_refs",
                "open_questions",
            ],
        }
    if step == 10:
        return {
            "type": "array",
            "item_schema": "slot_synthesis",
            "required_fields": [
                "slot",
                "target_capability",
                "comparisons",
                "selected_path",
                "selected_writeup",
                "evidence_refs",
            ],
        }
    return {"type": "contract_list", "items": quality_contract_for_step(step)}


def auto_summary_for_step(step: int) -> str:
    summaries = {
        2: "自动推进：前置文件检查通过",
        3: "自动推进：模板读取完成",
        6: "自动推进：repowiki 检查完成",
        11: "自动推进：最终文档成稿",
        12: "自动推进：收尾清理完成",
    }
    return summaries.get(step, f"自动推进：步骤 {step} 完成")


def build_initial_state_payload(state_path: Path, *, slug: str | None = None) -> dict[str, Any]:
    return build_canonical_state_payload(state_path=state_path, slug=slug)


def ensure_initial_state(state_path: Path, *, slug: str | None = None) -> dict[str, Any]:
    state = load_state(state_path)
    if state:
        return state
    state = build_initial_state_payload(state_path, slug=slug)
    dump_yaml(state_path, state, ensure_parent=True)
    return state


def block_matches_pattern(block_name: str, pattern: str) -> bool:
    if pattern.endswith("*"):
        return block_name.startswith(pattern[:-1])
    return block_name == pattern


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
    spec = importlib.util.spec_from_file_location(
        "create_technical_solution_initialize_state",
        SCRIPTS_DIR / "initialize-state.py",
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_validate_state_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "create_technical_solution_validate_state", SCRIPTS_DIR / "validate-state.py"
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_upsert_draft_block_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "create_technical_solution_upsert_draft_block",
        SCRIPTS_DIR / "upsert-draft-block.py",
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_render_final_document_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "create_technical_solution_render_final_document",
        SCRIPTS_DIR / "render-final-document.py",
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_finalize_cleanup_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "create_technical_solution_finalize_cleanup",
        SCRIPTS_DIR / "finalize-cleanup.py",
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_advance_state_step_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "create_technical_solution_advance_state_step",
        SCRIPTS_DIR / "advance-state-step.py",
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_extract_template_snapshot_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "create_technical_solution_extract_template_snapshot",
        SCRIPTS_DIR / "extract-template-snapshot.py",
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_block_scaffolds_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "create_technical_solution_block_scaffolds", SCRIPTS_DIR / "block_scaffolds.py"
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_validator(
    state_path: Path, step: int, write_receipt: bool = False
) -> tuple[bool, str]:
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
            "repair_plan": module.build_repair_plan(
                errors, state_path=state_path, state=state
            ),
            "issues": errors,
        }
        return False, json.dumps(payload, ensure_ascii=False, indent=2)

    payload: dict[str, Any] = {
        "step": step,
        "passed": True,
        "summary": {"error_count": 0},
    }
    if write_receipt:
        payload["gate_receipt"] = module.write_pass_receipt(
            state_path, validator.state, step
        )
    return True, json.dumps(payload, ensure_ascii=False, indent=2)


def _load_json_payload(raw: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(raw)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def format_step_failure(
    *,
    step: int,
    prefix: str,
    raw_output: str,
    keep_draft_note: bool = False,
    forbid_manual_bypass: bool = False,
) -> str:
    lines = [f"步骤 {step} {prefix}:", raw_output]
    payload = _load_json_payload(raw_output)
    repair_plan = payload.get("repair_plan") if isinstance(payload, dict) else None
    if isinstance(repair_plan, list) and repair_plan:
        actions = [
            str(item.get("action_type") or "").strip()
            for item in repair_plan
            if isinstance(item, dict) and str(item.get("action_type") or "").strip()
        ]
        commands = [
            str(item.get("script_command") or "").strip()
            for item in repair_plan
            if isinstance(item, dict) and str(item.get("script_command") or "").strip()
        ]
        if actions:
            lines.append("恢复动作：")
            for action in actions:
                lines.append(f"- {action}")
        if commands:
            lines.append("修复路径：")
            for command in commands:
                lines.append(f"- {command}")
    if keep_draft_note:
        lines.append("working draft 已保留。")
    if forbid_manual_bypass:
        lines.append("不要手动编写最终文档，也不要绕过流程向用户请求豁免。")
    return "\n".join(lines)


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
    staging_dir: Path | None = None
    backup_dir: Path | None = None
    promoted = False

    def cleanup_dir(path: Path | None) -> None:
        if path is None or not path.exists():
            return
        try:
            shutil.rmtree(path)
        except Exception:
            pass

    def restore_promoted_tree() -> None:
        nonlocal promoted
        if not promoted:
            return
        try:
            if working_dir.exists():
                shutil.rmtree(working_dir)
            if backup_dir is not None and backup_dir.exists():
                backup_dir.rename(working_dir)
        except Exception:
            pass
        promoted = False

    try:
        if validate_step is not None:
            require_receipt(state, expected_step=validate_step)
        slots = state.get("slots") or []
        staging_dir = Path(
            tempfile.mkdtemp(
                prefix=f".{working_dir.name}.staging-",
                dir=str(working_dir.parent),
            )
        )
        if working_dir.exists():
            shutil.copytree(working_dir, staging_dir, dirs_exist_ok=True)
        for block_name, content in block_updates:
            module.write_working_draft_file(staging_dir, block_name, content, slots)
        module.sync_state_for_blocks(state, block_updates, summary)
        refresh_receipt(state)
        dump_yaml(state_path, state)
        if working_dir.exists():
            backup_dir = working_dir.parent / (
                f".{working_dir.name}.backup-{uuid.uuid4().hex}"
            )
            working_dir.rename(backup_dir)
        staging_dir.rename(working_dir)
        promoted = True
        staging_dir = None
        if validate_step is not None:
            passed, validator_output = run_validator(
                state_path,
                validate_step,
                write_receipt=False,
            )
            if not passed:
                raise RuntimeError(
                    f"步骤 {validate_step} 验证失败:\n{validator_output}"
                )
    except SystemExit as exc:
        try:
            state_path.write_text(original_state_text, encoding="utf-8")
        except Exception:
            pass
        cleanup_dir(staging_dir)
        restore_promoted_tree()
        cleanup_dir(backup_dir)
        return 1, str(exc)
    except Exception as exc:
        try:
            state_path.write_text(original_state_text, encoding="utf-8")
        except Exception:
            pass
        cleanup_dir(staging_dir)
        restore_promoted_tree()
        cleanup_dir(backup_dir)
        exit_code = (
            2 if isinstance(exc, RuntimeError) and str(exc).startswith("步骤 ") else 1
        )
        return exit_code, f"批量写入失败，已回滚: {exc}"
    cleanup_dir(backup_dir)
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


def initialize_state_in_process(
    state_path: Path, slug: str, summary: str
) -> tuple[int, str]:
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
    match = re.search(
        r"^## 操作\s*\n(.*?)(?=^## |\Z)", content, re.MULTILINE | re.DOTALL
    )
    if match:
        return match.group(1).strip()
    return content


def step_card_hash(step: int) -> str:
    card_path = get_step_card_path(step)
    return hashlib.sha256(card_path.read_bytes()).hexdigest()


def mark_step_card_read(state_path: Path) -> int:
    snapshot = load_runtime_snapshot(state_path)
    state = snapshot.state
    if not state:
        print("❌ 状态文件不存在。请先完成步骤 1 初始化。")
        return 1
    step = snapshot.current_step
    step_cards_read = state.setdefault("step_cards_read", {})
    if not isinstance(step_cards_read, dict):
        step_cards_read = {}
        state["step_cards_read"] = step_cards_read
    card_path = get_step_card_path(step)
    step_cards_read[str(step)] = {
        "card_path": str(card_path.relative_to(card_path.parents[1])),
        "card_hash": step_card_hash(step),
        "read_at": iso_now(),
    }
    refresh_receipt(state, step=step)
    dump_yaml(state_path, state)
    print(
        json.dumps(
            {
                "step": step,
                "card": step_cards_read[str(step)]["card_path"],
                "card_hash": step_cards_read[str(step)]["card_hash"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def require_step_card_read(state: dict[str, Any], step: int) -> tuple[bool, str]:
    if step < 2:
        return True, ""
    entry = state.get("step_cards_read", {})
    record = entry.get(str(step)) if isinstance(entry, dict) else None
    if not isinstance(record, dict):
        return False, f"步骤 {step} 尚未登记 step card 已读。请重新执行 --advance。"
    current_hash = step_card_hash(step)
    if str(record.get("card_hash") or "") != current_hash:
        return False, f"步骤 {step} 的 step card 已更新。请重新执行 --advance 以刷新。"
    return True, ""


def print_status(state_path: Path, snapshot: RuntimeSnapshot | None = None) -> int:
    """打印当前步骤状态和操作指引。"""
    snapshot = snapshot or load_runtime_snapshot(state_path)
    assert snapshot is not None
    state = snapshot.state
    if not state:
        print("=" * 60)
        print("状态文件不存在或为空。")
        print(f'请先运行: {run_step_base_command(snapshot.state_path)} --advance')
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

    pending_ticket = state.get("pending_ticket")
    has_current_ticket = isinstance(pending_ticket, dict) and int(
        pending_ticket.get("step") or 0
    ) == step
    if step not in {7, 8, 9, 10} or has_current_ticket:
        return

    example_state = dict(state)
    example_state["pending_ticket"] = {"step": step, "value": "<ticket>"}
    print("\n# 拿到 ticket 后，按下面示例提交正文")
    for line in render_run_step_command(
        state_path=state_path,
        step=step,
        state=example_state,
    ):
        print(line)


# ── complete 模式：各步骤的实现 ──────────────────────────────


def complete_step_1(
    state_path: Path,
    summary: str,
    slug: str | None,
    stdin_content: str | None = None,
    **_: Any,
) -> tuple[int, str]:
    payload = parse_business_payload(stdin_content)
    if not slug:
        candidate = payload.get("slug")
        if isinstance(candidate, str):
            slug = candidate.strip() or None
    if not slug:
        return 1, '步骤 1 需要业务 JSON，至少包含字段 "slug"。'
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
    template_path = str(
        state.get("template_path")
        or ".architecture/templates/technical-solution-template.md"
    )
    draft_path = str(
        working_draft_path_for_slug(repo_root=repo_root, slug=slug).relative_to(
            repo_root
        )
    )
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


FULL_REQUIRED_ARTIFACTS = ["WD-CTX", "WD-TASK", "WD-EXP-SLOT-*", "WD-SYN-SLOT-*"]


def complete_step_4(
    state_path: Path,
    summary: str,
    solution_type: str | None = None,
    stdin_content: str | None = None,
    **_: Any,
) -> tuple[int, str]:
    if not solution_type:
        payload = parse_business_payload(stdin_content)
        candidate = payload.get("solution_type")
        if isinstance(candidate, str):
            solution_type = candidate.strip() or None
    if not solution_type:
        return 1, '步骤 4 需要业务 JSON 字段 "solution_type"。'
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
    state_path: Path,
    summary: str,
    members: list[str] | None = None,
    stdin_content: str | None = None,
    **_: Any,
) -> tuple[int, str]:
    members = list(members or [])
    if not members:
        payload = parse_business_payload(stdin_content)
        selected = payload.get("selected_members")
        if isinstance(selected, list):
            members = [str(item).strip() for item in selected if str(item).strip()]
    if not members:
        return 1, '步骤 5 需要业务 JSON 字段 "selected_members"，且至少包含一个成员。'
    members_json = json.dumps(members)
    code, stdout = advance_state_step_in_process(
        state_path=state_path,
        step=5,
        summary=summary,
        field=["members_checked=true"],
        field_json=[
            f"selected_members={members_json}",
        ],
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
            f"repowiki_path={repowiki_path}",
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
    if step == 7:
        try:
            payload = parse_json_array_payload(stdin_content, label="步骤 7 结构化内容")
            block_updates = [("WD-CTX", module.render_ctx_payload(payload))]
        except ValueError as exc:
            return 1, str(exc)
    elif step == 8:
        try:
            payload = parse_json_array_payload(stdin_content, label="步骤 8 结构化内容")
            block_updates = [("WD-TASK", module.render_task_payload(payload))]
        except ValueError as exc:
            return 1, str(exc)
    elif step == 9:
        try:
            payload = parse_json_array_payload(stdin_content, label="步骤 9 结构化内容")
            block_updates = module.render_exp_payload(payload, snapshot.state.get("slots") or [])
        except ValueError as exc:
            return 1, str(exc)
    elif step == 10:
        try:
            payload = parse_json_array_payload(stdin_content, label="步骤 10 结构化内容")
            block_updates = module.render_syn_payload(payload, snapshot.state.get("slots") or [])
        except ValueError as exc:
            return 1, str(exc)
    else:
        block_updates = module.parse_stdin_blocks(stdin_content, step)
    if not block_updates:
        return 1, f"步骤 {step} 传入的内容为空。"

    pending_ticket = snapshot.state.get("pending_ticket")
    allowed_pattern = None
    if isinstance(pending_ticket, dict) and int(pending_ticket.get("step") or 0) == step:
        allowed_pattern = str(pending_ticket.get("allowed_block_pattern") or "").strip() or None
    if allowed_pattern:
        invalid_blocks = [
            block_name
            for block_name, _content in block_updates
            if not block_matches_pattern(block_name, allowed_pattern)
        ]
        if invalid_blocks:
            return (
                1,
                f"步骤 {step} 的 ticket 仅允许写入 {allowed_pattern}，实际收到: {', '.join(invalid_blocks)}",
            )

    code, output = upsert_blocks_in_process(
        state_path,
        working_dir,
        summary,
        block_updates,
        validate_step=step,
    )
    if code != 0:
        return code, f"写入 working draft 失败:\n{output}"

    results = [
        f"  ✓ {block_name} 已写入 working draft" for block_name, _body in block_updates
    ]
    detail = "\n".join(results)
    new_snapshot = load_runtime_snapshot(state_path)
    new_step = new_snapshot.current_step
    return 0, f"✅ 步骤 {step} 完成。\n{detail}\n已推进到步骤 {new_step}。"


def complete_step_11(
    state_path: Path, summary: str, snapshot: RuntimeSnapshot | None = None, **_: Any
) -> tuple[int, str]:
    snapshot = snapshot or load_runtime_snapshot(state_path)
    assert snapshot is not None
    seed_checkpoint_summary(state_path, 11, summary)
    passed, output = run_validator(state_path, 11, write_receipt=True)
    if not passed:
        return 2, format_step_failure(
            step=11,
            prefix="验证失败",
            raw_output=output,
            keep_draft_note=True,
            forbid_manual_bypass=True,
        )
    code, stdout = render_final_document_in_process(state_path, summary)
    if code != 0:
        return code, format_step_failure(
            step=11,
            prefix="成稿失败",
            raw_output=stdout,
            keep_draft_note=True,
            forbid_manual_bypass=True,
        )
    return 0, f"✅ 步骤 11 完成。最终文档已渲染。\n{stdout}"


def complete_step_12(
    state_path: Path, summary: str, snapshot: RuntimeSnapshot | None = None, **_: Any
) -> tuple[int, str]:
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


def prepare_step(state_path: Path, *, slug: str | None = None) -> int:
    state_exists = state_path.exists() and state_path.stat().st_size > 0
    if not state_exists:
        if not slug:
            print("❌ 状态文件不存在且未提供 slug。请先执行高层入口 run-step.py --advance，再按步骤 1 的业务 JSON 提交 slug。")
            return 1
        state = build_initial_state_payload(state_path, slug=slug.strip())
        dump_yaml(state_path, state, ensure_parent=True)
    snapshot = load_runtime_snapshot(state_path)
    state = snapshot.state
    if not state:
        print("❌ 状态文件不存在。请先用 --slug 参数执行步骤 1。")
        return 1

    step = snapshot.current_step

    card_ok, card_message = require_step_card_read(state, step)
    if not card_ok:
        print(f"步骤 {step} prepare 失败:\n{card_message}")
        return 1

    if step >= 2:
        try:
            require_receipt(state, expected_step=step)
        except SystemExit as exc:
            print(f"步骤 {step} prepare 失败:\n{exc}")
            return 1

    ticket = {
        "step": step,
        "value": uuid.uuid4().hex,
        "state_fingerprint": state.get("gate_receipt", {}).get("state_fingerprint", ""),
        "artifact_fingerprint": compute_artifact_fingerprint(
            repo_root=repo_root_from_state_path(state_path),
            state=state,
        ),
        "allowed_block_pattern": allowed_block_pattern_for_step(step) or "",
        "issued_at": iso_now(),
    }
    state["pending_ticket"] = ticket
    dump_yaml(state_path, state)
    print(
        json.dumps(
            {
                "step": step,
                "ticket": ticket["value"],
                "artifact_fingerprint": ticket["artifact_fingerprint"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def validate_pending_ticket(
    state_path: Path,
    *,
    step: int,
    provided_ticket: str | None,
) -> tuple[int, str] | None:
    state = load_state(state_path)
    pending_ticket = state.get("pending_ticket")
    has_matching_ticket = isinstance(pending_ticket, dict) and int(
        pending_ticket.get("step") or 0
    ) == step
    if not has_matching_ticket:
        if step_requires_ticket(step):
            return 1, "❌ 当前步骤必须先通过 --advance 进入本步并获取 ticket，然后才能 --complete。"
        return None
    assert isinstance(pending_ticket, dict)
    if not provided_ticket:
        return 1, "❌ 当前步骤已 prepare，必须提供 --ticket 后才能 --complete。"
    if provided_ticket != str(pending_ticket.get("value") or ""):
        return 1, "❌ --ticket 无效，请重新执行 --advance 获取新的 ticket。"
    current_state_fingerprint = state.get("gate_receipt", {}).get("state_fingerprint", "")
    if current_state_fingerprint != str(pending_ticket.get("state_fingerprint") or ""):
        return 1, "❌ 状态自 ticket 发放后已变化，请重新执行 --advance。"
    if step_mode(step) != "automatic":
        current_artifact_fingerprint = compute_artifact_fingerprint(
            repo_root=repo_root_from_state_path(state_path),
            state=state,
        )
        if current_artifact_fingerprint != str(pending_ticket.get("artifact_fingerprint") or ""):
            return 1, "❌ 中间产物自 ticket 发放后已变化，请不要删除现有 draft 文件，直接重新执行 --advance。"
    return None


def has_valid_pending_ticket(state_path: Path, *, state: dict[str, Any], step: int) -> bool:
    pending_ticket = state.get("pending_ticket")
    if not isinstance(pending_ticket, dict):
        return False
    if int(pending_ticket.get("step") or 0) != step:
        return False
    current_state_fingerprint = str(state.get("gate_receipt", {}).get("state_fingerprint") or "")
    if current_state_fingerprint != str(pending_ticket.get("state_fingerprint") or ""):
        return False
    if step_mode(step) != "automatic":
        current_artifact_fingerprint = compute_artifact_fingerprint(
            repo_root=repo_root_from_state_path(state_path),
            state=state,
        )
        if current_artifact_fingerprint != str(pending_ticket.get("artifact_fingerprint") or ""):
            return False
    return True


def clear_pending_ticket(state_path: Path) -> None:
    state = load_state(state_path)
    if not state or not state.get("pending_ticket"):
        return
    state["pending_ticket"] = {}
    dump_yaml(state_path, state)


def step_requires_ticket(step: int) -> bool:
    return step >= 7


def build_creative_entry_response(state_path: Path, step: int) -> dict[str, Any]:
    state = load_state(state_path)
    step_def = STEP_DEFS.get(step, {})
    return {
        "status": "needs_input",
        "step": step,
        "artifact": step_def.get("artifact"),
        "business_task": business_task_for_step(step),
        "required_output_shape": structured_output_shape_for_step(step),
        "next_action": "submit_structured_payload",
        "current_step": int(state.get("current_step") or step),
    }


def build_business_entry_response(state_path: Path, step: int) -> dict[str, Any]:
    state = load_state(state_path)
    return {
        "status": "needs_input",
        "step": step,
        "artifact": None,
        "business_task": business_task_for_step(step),
        "required_output_shape": structured_output_shape_for_step(step),
        "next_action": "submit_business_content",
        "current_step": int(state.get("current_step") or step),
    }


def parse_business_payload(stdin_content: str | None) -> dict[str, Any]:
    raw = str(stdin_content or "").strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"stdin 业务内容不是合法 JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("stdin 业务内容必须是 JSON 对象。")
    return payload


def parse_json_array_payload(stdin_content: str | None, *, label: str) -> list[dict[str, Any]]:
    raw = str(stdin_content or "").strip()
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} 不是合法 JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise ValueError(f"{label} 必须是 JSON 数组。")
    normalized: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError(f"{label} 数组元素必须是 JSON 对象。")
        normalized.append(item)
    return normalized


def advance_step(state_path: Path) -> dict[str, Any]:
    snapshot = load_runtime_snapshot(state_path)
    state = snapshot.state
    if not state:
        ensure_initial_state(state_path)
        snapshot = load_runtime_snapshot(state_path)
        state = snapshot.state
    assert state

    step = snapshot.current_step
    mode = step_mode(step)
    if mode == "automatic":
        mark_code = mark_step_card_read(state_path)
        if mark_code != 0:
            raise RuntimeError(f"步骤 {step} 无法登记 step card 已读。")
        prepare_code = prepare_step(state_path)
        if prepare_code != 0:
            raise RuntimeError(f"步骤 {step} prepare 失败。")
        ticket = str(load_state(state_path).get("pending_ticket", {}).get("value") or "")
        if not ticket:
            raise RuntimeError(f"步骤 {step} 未生成 ticket。")
        args = argparse.Namespace(
            state=str(state_path),
            complete=True,
            summary=auto_summary_for_step(step),
            slug=None,
            solution_type=None,
            member=[],
            ticket=ticket,
            _stdin_content=None,
        )
        code = complete_step(args)
        if code != 0:
            raise RuntimeError(f"步骤 {step} 自动推进失败。")
        new_state = load_state(state_path)
        return {
            "status": "completed",
            "step": step,
            "next_step": int(new_state.get("current_step") or step),
            "next_action": "advance",
        }

    if mode == "business":
        if not has_valid_pending_ticket(state_path, state=state, step=step):
            mark_code = mark_step_card_read(state_path)
            if mark_code != 0:
                raise RuntimeError(f"步骤 {step} 无法登记 step card 已读。")
            prepare_code = prepare_step(state_path)
            if prepare_code != 0:
                raise RuntimeError(f"步骤 {step} prepare 失败。")
        return build_business_entry_response(state_path, step)

    if not has_valid_pending_ticket(state_path, state=state, step=step):
        mark_code = mark_step_card_read(state_path)
        if mark_code != 0:
            raise RuntimeError(f"步骤 {step} 无法登记 step card 已读。")
        prepare_code = prepare_step(state_path)
        if prepare_code != 0:
            raise RuntimeError(f"步骤 {step} prepare 失败。")
    return build_creative_entry_response(state_path, step)


def complete_step(args: argparse.Namespace) -> int:
    """根据当前步骤分发到对应的 complete 处理函数。"""
    state_path = Path(args.state).resolve()
    summary = args.summary

    snapshot = load_runtime_snapshot(state_path)
    state = snapshot.state
    if not state:
        ensure_initial_state(state_path, slug=getattr(args, "slug", None))
        snapshot = load_runtime_snapshot(state_path)
        state = snapshot.state

    step = snapshot.current_step
    ticket_error = validate_pending_ticket(
        state_path,
        step=step,
        provided_ticket=getattr(args, "ticket", None),
    )
    if ticket_error is not None:
        code, message = ticket_error
        print(message)
        return code

    stdin_content = getattr(args, "_stdin_content", None)
    dispatch = {
        1: lambda: complete_step_1(
            state_path, summary, args.slug, stdin_content=stdin_content
        ),
        2: lambda: complete_step_2(state_path, summary),
        3: lambda: complete_step_3(state_path, summary),
        4: lambda: complete_step_4(
            state_path,
            summary,
            solution_type=args.solution_type,
            stdin_content=stdin_content,
        ),
        5: lambda: complete_step_5(
            state_path,
            summary,
            members=args.member,
            stdin_content=stdin_content,
        ),
        6: lambda: complete_step_6(state_path, summary),
        7: lambda: complete_creative_step(
            state_path, summary, 7, stdin_content, snapshot=snapshot
        ),
        8: lambda: complete_creative_step(
            state_path, summary, 8, stdin_content, snapshot=snapshot
        ),
        9: lambda: complete_creative_step(
            state_path, summary, 9, stdin_content, snapshot=snapshot
        ),
        10: lambda: complete_creative_step(
            state_path, summary, 10, stdin_content, snapshot=snapshot
        ),
        11: lambda: complete_step_11(state_path, summary, snapshot=snapshot),
        12: lambda: complete_step_12(state_path, summary, snapshot=snapshot),
    }

    handler = dispatch.get(step)
    if not handler:
        print(f"❌ 未知步骤: {step}")
        return 1

    code, msg = handler()
    print(msg)

    if code == 0 and getattr(args, "ticket", None):
        clear_pending_ticket(state_path)

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
    parser.add_argument("--advance", action="store_true", help="高层推进当前步骤")
    parser.add_argument("--prepare", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--complete", action="store_true", help="完成当前步骤并推进")
    parser.add_argument(
        "--mark-step-card-read", action="store_true", help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--emit-scaffold", action="store_true", help="输出当前步骤 scaffold 到 stdout"
    )
    parser.add_argument("--summary", help="步骤完成摘要（--complete 时必需）")

    # 步骤特定参数
    parser.add_argument("--slug", help=argparse.SUPPRESS)
    parser.add_argument("--solution-type", help=argparse.SUPPRESS)
    parser.add_argument("--ticket", help="当前步骤的一次性凭证（从 --advance 返回值中获取）")
    parser.add_argument(
        "--member", action="append", default=[], help=argparse.SUPPRESS
    )

    args = parser.parse_args()

    if sum(
        [
            bool(args.advance),
            bool(args.prepare),
            bool(args.complete),
            bool(args.emit_scaffold),
            bool(args.mark_step_card_read),
        ]
    ) > 1:
        parser.error(
            "--advance、--prepare、--mark-step-card-read、--emit-scaffold 与 --complete 不能同时使用。"
        )

    args._stdin_content = None
    if args.complete and not sys.stdin.isatty():
        try:
            args._stdin_content = sys.stdin.read()
        except OSError:
            args._stdin_content = None

    if args.complete:
        if not args.summary:
            parser.error("--complete 需要 --summary 参数。")
        return complete_step(args)
    if args.advance:
        payload = advance_step(Path(args.state).resolve())
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.prepare:
        return prepare_step(Path(args.state).resolve(), slug=getattr(args, "slug", None))
    if args.mark_step_card_read:
        return mark_step_card_read(Path(args.state).resolve())
    if args.emit_scaffold:
        return emit_scaffold(Path(args.state).resolve(), members=args.member)
    else:
        return print_status(Path(args.state).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
