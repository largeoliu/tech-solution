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
  python scripts/run-step.py --state <状态文件>

  # 完成全自动步骤
  python scripts/run-step.py --state <状态文件> --complete --summary "前置文件检查通过"

  # 完成半自动步骤（step 1）
  python scripts/run-step.py --state <状态文件> --complete --summary "定题完成" --slug my-feature

  # 完成半自动步骤（step 4）
  python scripts/run-step.py --state <状态文件> --complete --summary "类型判定" \\
    --flow-tier full --solution-type "新功能方案" --signal introduces-core-capability

  # 完成半自动步骤（step 5）
  python scripts/run-step.py --state <状态文件> --complete --summary "成员选定" \\
    --member SYSTEMS_ARCHITECT --member DOMAIN_EXPERT

  # 完成创作型步骤（step 7/8/10）
  python scripts/run-step.py --state <状态文件> --complete --summary "WD-CTX 完成" \\
    --content-file /tmp/wd-ctx.md

  # 完成创作型步骤（step 9，多文件）
  python scripts/run-step.py --state <状态文件> --complete --summary "专家分析完成" \\
    --content-file /tmp/wd-exp-SYSTEMS_ARCHITECT.md \\
    --content-file /tmp/wd-exp-DOMAIN_EXPERT.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("缺少 pyyaml。运行: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


SCRIPTS_DIR = Path(__file__).resolve().parent

STEP_CARD_FILES = {
    1: "01-定题与范围判断.md",
    2: "02-检查语义前置文件.md",
    3: "03-读取当前生效模板.md",
    4: "04-判断方案类型.md",
    5: "05-加载成员名册并选择参与者.md",
    6: "06-检测repowiki目录.md",
    7: "07-构建共享上下文.md",
    8: "08-生成模板任务单.md",
    9: "09-组织专家按模板逐槽位分析.md",
    10: "10-按模板逐槽位协作收敛.md",
    11: "11-严格模板成稿并保存结果.md",
    12: "12-吸收检查与清理.md",
}

STEP_NAMES = {
    1: "定题与范围判断",
    2: "检查前置文件",
    3: "读取当前生效模板",
    4: "判断方案类型",
    5: "加载成员名册",
    6: "检测 repowiki",
    7: "构建共享上下文 (WD-CTX)",
    8: "生成模板任务单 (WD-TASK)",
    9: "专家分析 (WD-EXP-*)",
    10: "协作收敛 (WD-SYN)",
    11: "严格模板成稿",
    12: "吸收检查与清理",
}

# 步骤 -> 需要的 block 名称
STEP_BLOCK_MAP = {
    7: "WD-CTX",
    8: "WD-TASK",
    10: None,  # WD-SYN or WD-SYN-LIGHT, depends on flow_tier
}


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {}
    data = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def get_flow_tier(state: dict[str, Any]) -> str:
    tier = str(state.get("flow_tier") or "").strip()
    return tier if tier in {"light", "moderate", "full", "pending"} else "pending"


def get_current_step(state: dict[str, Any]) -> int:
    return int(state.get("current_step") or 1)


def get_repo_root(state_path: Path) -> Path:
    return state_path.parent.parent.parent.parent


def get_slug(state_path: Path) -> str:
    return state_path.stem.replace(".yaml", "").replace(".yml", "")


def run_script(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """运行子进程脚本，返回 (exit_code, stdout, stderr)。"""
    result = subprocess.run(
        [sys.executable] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.returncode, result.stdout, result.stderr


def run_validator(state_path: Path, step: int, flow_tier: str, write_receipt: bool = False) -> tuple[bool, str]:
    """运行 validate-state.py，返回 (passed, output)。"""
    cmd = [
        str(SCRIPTS_DIR / "validate-state.py"),
        "--state", str(state_path),
        "--step", str(step),
        "--flow-tier", flow_tier,
        "--format", "json",
    ]
    if write_receipt:
        cmd.append("--write-pass-receipt")
    code, stdout, stderr = run_script(cmd)
    return code == 0, stdout or stderr


def extract_step_card_operations(step: int) -> str:
    """提取 step card 的'操作'段落。"""
    steps_dir = SCRIPTS_DIR.parent / "steps"
    filename = STEP_CARD_FILES.get(step)
    if not filename:
        return ""
    card_path = steps_dir / filename
    if not card_path.exists():
        return f"（step card 文件不存在: {card_path}）"
    content = card_path.read_text(encoding="utf-8")
    # 提取 ## 操作 到下一个 ## 之间的内容
    match = re.search(r"^## 操作\s*\n(.*?)(?=^## |\Z)", content, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return content


def print_status(state_path: Path) -> int:
    """打印当前步骤状态和操作指引。"""
    state = load_state(state_path)
    if not state:
        print("=" * 60)
        print("状态文件不存在或为空。")
        print(f"请先运行: python scripts/run-step.py --state {state_path} --complete --summary \"<主题摘要>\" --slug <slug>")
        print("=" * 60)
        return 0

    step = get_current_step(state)
    flow_tier = get_flow_tier(state)
    completed = state.get("completed_steps", [])
    slug = get_slug(state_path)

    print("=" * 60)
    print(f"  当前步骤: {step} - {STEP_NAMES.get(step, '未知')}")
    print(f"  流程级别: {flow_tier}")
    print(f"  已完成:   {completed}")
    print(f"  Slug:     {slug}")
    print("=" * 60)

    # 运行 validator
    passed, output = run_validator(state_path, step, flow_tier)
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
    _print_next_command(state_path, step, flow_tier, state)

    return 0


def _print_next_command(state_path: Path, step: int, flow_tier: str, state: dict[str, Any]) -> None:
    """根据步骤类型输出推荐的 complete 命令。"""
    base = f"python scripts/run-step.py --state {state_path}"

    if step == 1:
        print(f'{base} --complete --summary "<主题摘要>" --slug <slug>')
    elif step in {2, 3, 6}:
        print(f'{base} --complete --summary "<完成摘要>"')
    elif step == 4:
        print(f'{base} --complete --summary "<类型判定>" --flow-tier <light|moderate|full> --solution-type "<方案类型>" --signal <信号>')
    elif step == 5:
        print(f'{base} --complete --summary "<成员选定>" --member <MEMBER_ID> [--member ...]')
    elif step == 7:
        print(f"# 先将 WD-CTX 内容写入临时文件，然后：")
        print(f'{base} --complete --summary "<WD-CTX 完成>" --content-file /tmp/wd-ctx.md')
    elif step == 8:
        print(f"# 先将 WD-TASK 内容写入临时文件，然后：")
        print(f'{base} --complete --summary "<WD-TASK 完成>" --content-file /tmp/wd-task.md')
    elif step == 9:
        members = state.get("checkpoints", {}).get("step-5", {}).get("selected_members", [])
        if members:
            files = " ".join(f"--content-file /tmp/wd-exp-{m}.md" for m in members)
            print(f"# 为每位专家生成内容文件，然后：")
            print(f'{base} --complete --summary "<专家分析完成>" {files}')
        else:
            print(f'{base} --complete --summary "<专家分析完成>" --content-file /tmp/wd-exp-<MEMBER>.md')
    elif step == 10:
        block = "WD-SYN-LIGHT" if flow_tier == "light" else "WD-SYN"
        print(f"# 先将 {block} 内容写入临时文件，然后：")
        print(f'{base} --complete --summary "<收敛完成>" --content-file /tmp/wd-syn.md')
    elif step == 11:
        print(f'{base} --complete --summary "<成稿完成>"')
    elif step == 12:
        print(f'{base} --complete --summary "<清理完成>"')


# ── complete 模式：各步骤的实现 ──────────────────────────────


def complete_step_1(state_path: Path, summary: str, slug: str | None, **_: Any) -> tuple[int, str]:
    if not slug:
        return 1, "步骤 1 需要 --slug 参数。"
    # 先验证（可能是新建 state，失败是预期的）
    # 直接调用 initialize-state.py
    code, stdout, stderr = run_script([
        str(SCRIPTS_DIR / "initialize-state.py"),
        "--state", str(state_path),
        "--slug", slug,
        "--summary", summary,
        "--next-step", "2",
    ])
    if code != 0:
        return code, f"initialize-state.py 失败:\n{stderr or stdout}"
    return 0, f"✅ 步骤 1 完成。slug={slug}，已推进到步骤 2。\n{stdout}"


def complete_step_2(state_path: Path, summary: str, **_: Any) -> tuple[int, str]:
    state = load_state(state_path)
    repo_root = get_repo_root(state_path)
    # 检查前置文件（这是步骤 2 的核心操作）
    missing = []
    for field in ("members_path", "principles_path", "template_path"):
        path_val = str(state.get(field) or "").strip()
        if not path_val or not (repo_root / path_val).exists():
            missing.append(field)
    if missing:
        return 2, f"前置文件缺失: {missing}。请先运行 bootstrap-architecture。"
    # 推进（advance-state-step 内部会自动补 prerequisites_checked=true）
    code, stdout, stderr = run_script([
        str(SCRIPTS_DIR / "advance-state-step.py"),
        "--state", str(state_path),
        "--step", "2",
        "--summary", summary,
        "--field", "prerequisites_checked=true",
        "--append-completed",
        "--next-step", "3",
    ])
    if code != 0:
        return code, f"advance-state-step.py 失败:\n{stderr or stdout}"
    return 0, f"✅ 步骤 2 完成。前置文件检查通过，已推进到步骤 3。"


def complete_step_3(state_path: Path, summary: str, **_: Any) -> tuple[int, str]:
    state = load_state(state_path)
    slug = get_slug(state_path)
    repo_root = get_repo_root(state_path)
    template_path = str(state.get("template_path") or ".architecture/templates/technical-solution-template.md")
    draft_path = f".architecture/technical-solutions/working-drafts/{slug}.working.md"
    # 调用 extract-template-snapshot（脚本内部会 require_receipt）
    code, stdout, stderr = run_script([
        str(SCRIPTS_DIR / "extract-template-snapshot.py"),
        "--template", template_path,
        "--slug", slug,
        "--working-draft", draft_path,
        "--state", str(state_path),
        "--write",
    ], cwd=repo_root)
    if code != 0:
        return code, f"extract-template-snapshot.py 失败:\n{stderr or stdout}"
    return 0, f"✅ 步骤 3 完成。模板已读取，working draft 已创建。\n{stdout}"


def complete_step_4(
    state_path: Path, summary: str,
    flow_tier_arg: str | None = None,
    solution_type: str | None = None,
    signals: list[str] | None = None,
    **_: Any,
) -> tuple[int, str]:
    if not flow_tier_arg:
        return 1, "步骤 4 需要 --flow-tier 参数（light/moderate/full）。"
    if not solution_type:
        return 1, "步骤 4 需要 --solution-type 参数。"
    if not signals:
        return 1, "步骤 4 需要至少一个 --signal 参数。"
    cmd = [
        str(SCRIPTS_DIR / "set-flow-tier.py"),
        "--state", str(state_path),
        "--flow-tier", flow_tier_arg,
        "--solution-type", solution_type,
        "--summary", summary,
        "--next-step", "5",
        "--append-completed",
    ]
    for sig in signals:
        cmd.extend(["--signal", sig])
    code, stdout, stderr = run_script(cmd)
    if code != 0:
        return code, f"set-flow-tier.py 失败:\n{stderr or stdout}"
    return 0, f"✅ 步骤 4 完成。flow_tier={flow_tier_arg}，已推进到步骤 5。\n{stdout}"


def complete_step_5(
    state_path: Path, summary: str, members: list[str] | None = None, **_: Any,
) -> tuple[int, str]:
    if not members:
        return 1, "步骤 5 需要至少一个 --member 参数。"
    members_json = json.dumps(members)
    code, stdout, stderr = run_script([
        str(SCRIPTS_DIR / "advance-state-step.py"),
        "--state", str(state_path),
        "--step", "5",
        "--summary", summary,
        "--field", "members_checked=true",
        "--field-json", f"selected_members={members_json}",
        "--field", f"selected_member_count={len(members)}",
        "--append-completed",
        "--next-step", "6",
    ])
    if code != 0:
        return code, f"advance-state-step.py 失败:\n{stderr or stdout}"
    return 0, f"✅ 步骤 5 完成。参与成员: {members}，已推进到步骤 6。"


def complete_step_6(state_path: Path, summary: str, **_: Any) -> tuple[int, str]:
    state = load_state(state_path)
    repo_root = get_repo_root(state_path)
    # 检测 repowiki
    repowiki_path = str(state.get("repowiki_path") or ".qoder/repowiki")
    repowiki_exists = (repo_root / repowiki_path).exists()
    source_count = 0
    if repowiki_exists:
        content_dir = repo_root / repowiki_path / "zh" / "content"
        if content_dir.exists():
            source_count = sum(1 for _ in content_dir.rglob("*.md"))
    code, stdout, stderr = run_script([
        str(SCRIPTS_DIR / "advance-state-step.py"),
        "--state", str(state_path),
        "--step", "6",
        "--summary", summary,
        "--field", "repowiki_checked=true",
        "--field", f"repowiki_exists={'true' if repowiki_exists else 'false'}",
        "--field", f"repowiki_source_count={source_count}",
        "--append-completed",
        "--next-step", "7",
    ])
    if code != 0:
        return code, f"advance-state-step.py 失败:\n{stderr or stdout}"
    status = "存在" if repowiki_exists else "不存在"
    return 0, f"✅ 步骤 6 完成。repowiki {status}，已推进到步骤 7。"


def _resolve_content_block(step: int, flow_tier: str, content_files: list[str]) -> list[tuple[str, Path]]:
    """根据步骤和文件名推断 block 名称。返回 [(block_name, file_path), ...]。"""
    pairs: list[tuple[str, Path]] = []
    for fpath in content_files:
        p = Path(fpath)
        name_lower = p.stem.lower()
        if step == 7 or "wd-ctx" in name_lower or "ctx" in name_lower:
            pairs.append(("WD-CTX", p))
        elif step == 8 or "wd-task" in name_lower or "task" in name_lower:
            pairs.append(("WD-TASK", p))
        elif step == 9 or "wd-exp" in name_lower or "exp" in name_lower:
            # 从文件名推断成员 ID: wd-exp-SYSTEMS_ARCHITECT.md → WD-EXP-SYSTEMS_ARCHITECT
            match = re.search(r"(?:wd-?exp-?)(.+?)(?:\.md)?$", p.stem, re.IGNORECASE)
            member = match.group(1).upper().replace("-", "_") if match else p.stem.upper()
            pairs.append((f"WD-EXP-{member}", p))
        elif step == 10 or "wd-syn" in name_lower or "syn" in name_lower:
            block = "WD-SYN-LIGHT" if flow_tier == "light" else "WD-SYN"
            pairs.append((block, p))
        else:
            # 根据步骤默认
            default_blocks = {7: "WD-CTX", 8: "WD-TASK", 10: "WD-SYN"}
            block = default_blocks.get(step, "WD-CTX")
            if step == 10 and flow_tier == "light":
                block = "WD-SYN-LIGHT"
            pairs.append((block, p))
    return pairs


def complete_creative_step(
    state_path: Path, summary: str, step: int, content_files: list[str], **_: Any,
) -> tuple[int, str]:
    """处理步骤 7/8/9/10 的创作型步骤。"""
    if not content_files:
        return 1, f"步骤 {step} 需要 --content-file 参数。请先将内容写入临时文件。"
    state = load_state(state_path)
    flow_tier = get_flow_tier(state)
    draft_path = str(state.get("working_draft_path") or "")
    if not draft_path:
        return 1, "working_draft_path 为空，请确保步骤 3 已完成。"
    repo_root = get_repo_root(state_path)
    abs_draft = (repo_root / draft_path).resolve() if not Path(draft_path).is_absolute() else Path(draft_path)

    blocks = _resolve_content_block(step, flow_tier, content_files)
    results = []

    for block_name, content_path in blocks:
        if not content_path.exists():
            return 1, f"内容文件不存在: {content_path}"
        # 先验证并写 receipt
        passed, output = run_validator(state_path, step, flow_tier, write_receipt=True)
        if not passed:
            # 尝试重新加载 state（可能已部分推进）
            state = load_state(state_path)
            flow_tier = get_flow_tier(state)
            current = get_current_step(state)
            if current != step:
                passed, output = run_validator(state_path, current, flow_tier, write_receipt=True)
                if not passed:
                    return 2, f"步骤 {step} 验证失败:\n{output}"
                step = current

        # 对于 WD-EXP-* 类型的 block，upsert-draft-block 不直接支持
        # 需要用 step 9 的特殊处理
        receipt_step = get_current_step(load_state(state_path))

        if block_name.startswith("WD-EXP-"):
            # WD-EXP-* 块不在 upsert-draft-block 的 STEP_FOR_BLOCK 中
            # 直接手动追加到 working draft
            existing = abs_draft.read_text(encoding="utf-8") if abs_draft.exists() else ""
            block_content = content_path.read_text(encoding="utf-8").strip()
            new_section = f"\n\n## {block_name}\n\n{block_content}\n"
            abs_draft.write_text(existing.rstrip() + new_section, encoding="utf-8")
            results.append(f"  ✓ {block_name} 已写入 working draft")
        else:
            code, stdout, stderr = run_script([
                str(SCRIPTS_DIR / "upsert-draft-block.py"),
                "--working-draft", str(abs_draft),
                "--state", str(state_path),
                "--block", block_name,
                "--content-file", str(content_path),
                "--summary", summary,
                "--require-receipt-step", str(receipt_step),
            ])
            if code != 0:
                return code, f"upsert-draft-block.py 失败 ({block_name}):\n{stderr or stdout}"
            results.append(f"  ✓ {block_name} 已写入 working draft")

    # 步骤 9 需要额外处理：sync artifacts + advance
    if step == 9:
        # sync artifacts
        code, stdout, stderr = run_script([
            str(SCRIPTS_DIR / "sync-artifacts-from-draft.py"),
            "--working-draft", str(abs_draft),
            "--state", str(state_path),
            "--write",
        ])
        if code != 0:
            return code, f"sync-artifacts-from-draft.py 失败:\n{stderr or stdout}"
        # 步骤 9 完成后设置 gate flags
        state = load_state(state_path)
        state["can_enter_step_10"] = True
        state["current_step"] = 10
        completed = state.setdefault("completed_steps", [])
        if not isinstance(completed, list):
            completed = []
            state["completed_steps"] = completed
        if 9 not in completed:
            completed.append(9)
            completed.sort()
        checkpoints = state.setdefault("checkpoints", {})
        checkpoints["step-9"] = {
            "summary": summary,
            "skipped": False,
            "reason": "",
            "wd_exp_count": len([b for b, _ in blocks if b.startswith("WD-EXP-")]),
            "completed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat(),
        }
        # refresh receipt
        _refresh_receipt_inline(state)
        dump_path = state_path
        dump_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    detail = "\n".join(results)
    new_state = load_state(state_path)
    new_step = get_current_step(new_state)
    return 0, f"✅ 步骤 {step} 完成。\n{detail}\n已推进到步骤 {new_step}。"


def _refresh_receipt_inline(state: dict[str, Any]) -> None:
    """内联刷新 receipt，避免额外 import。"""
    import hashlib
    flow_tier = str(state.get("flow_tier") or "").strip() or "pending"
    step = int(state.get("current_step") or 0) or 1
    state["gate_receipt"] = {
        "step": step,
        "flow_tier": flow_tier,
        "state_fingerprint": "",
        "validated_at": "",
    }
    scrubbed = dict(state)
    scrubbed["gate_receipt"] = {
        "step": step,
        "flow_tier": flow_tier,
        "state_fingerprint": "",
        "validated_at": "",
    }
    payload = yaml.safe_dump(scrubbed, allow_unicode=True, sort_keys=True)
    fp = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    from datetime import datetime, timezone
    state["gate_receipt"]["state_fingerprint"] = fp
    state["gate_receipt"]["validated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def complete_step_skip(state_path: Path, step: int, flow_tier: str, reason: str, next_step: int, summary: str) -> tuple[int, str]:
    """处理跳步（light/moderate 流程）。"""
    receipt_step = get_current_step(load_state(state_path))
    code, stdout, stderr = run_script([
        str(SCRIPTS_DIR / "mark-step-skipped.py"),
        "--state", str(state_path),
        "--step", str(step),
        "--summary", summary,
        "--reason", reason,
        "--next-step", str(next_step),
        "--require-receipt-step", str(receipt_step),
    ])
    if code != 0:
        return code, f"mark-step-skipped.py 失败:\n{stderr or stdout}"
    return 0, f"  ✓ 步骤 {step} 已显式跳过（{reason}）"


def complete_step_11(state_path: Path, summary: str, **_: Any) -> tuple[int, str]:
    state = load_state(state_path)
    flow_tier = get_flow_tier(state)
    if flow_tier not in {"light", "moderate", "full"}:
        return 1, f"步骤 11 需要正式的 flow_tier（当前: {flow_tier}）。请确保步骤 4 已完成。"
    # 先验证并写 receipt
    passed, output = run_validator(state_path, 11, flow_tier, write_receipt=True)
    if not passed:
        return 2, f"步骤 11 验证失败:\n{output}"
    code, stdout, stderr = run_script([
        str(SCRIPTS_DIR / "render-final-document.py"),
        "--state", str(state_path),
        "--flow-tier", flow_tier,
        "--summary", summary,
    ])
    if code != 0:
        return code, f"render-final-document.py 失败:\n{stderr or stdout}"
    return 0, f"✅ 步骤 11 完成。最终文档已渲染。\n{stdout}"


def complete_step_12(state_path: Path, summary: str, **_: Any) -> tuple[int, str]:
    state = load_state(state_path)
    flow_tier = get_flow_tier(state)
    if flow_tier not in {"light", "moderate", "full"}:
        return 1, f"步骤 12 需要正式的 flow_tier（当前: {flow_tier}）。"
    # 先验证并写 receipt
    passed, output = run_validator(state_path, 12, flow_tier, write_receipt=True)
    if not passed:
        return 2, f"步骤 12 验证失败:\n{output}"
    code, stdout, stderr = run_script([
        str(SCRIPTS_DIR / "finalize-cleanup.py"),
        "--state", str(state_path),
        "--flow-tier", flow_tier,
        "--summary", summary,
        "--format", "json",
    ])
    if code != 0:
        return code, f"finalize-cleanup.py 失败:\n{stderr or stdout}"
    return 0, f"✅ 步骤 12 完成。working draft 与状态文件已清理。\n{stdout}"


def handle_skip_steps(state_path: Path, step: int, flow_tier: str, summary: str) -> tuple[int, str]:
    """处理进入某步骤前需要先跳过的步骤。"""
    skip_results = []

    if step == 10 and flow_tier == "light":
        # light: 跳过 8, 9
        for skip_step, next_s in [(8, 9), (9, 10)]:
            state = load_state(state_path)
            current = get_current_step(state)
            if current == skip_step:
                passed, _ = run_validator(state_path, skip_step, flow_tier, write_receipt=True)
                code, msg = complete_step_skip(
                    state_path, skip_step, flow_tier,
                    f"{flow_tier} 流程不需要步骤 {skip_step}", next_s,
                    f"跳过；{flow_tier} 流程",
                )
                if code != 0:
                    return code, msg
                skip_results.append(msg)

    elif step == 10 and flow_tier == "moderate":
        # moderate: 跳过 9
        state = load_state(state_path)
        current = get_current_step(state)
        if current == 9:
            passed, _ = run_validator(state_path, 9, flow_tier, write_receipt=True)
            code, msg = complete_step_skip(
                state_path, 9, flow_tier,
                "moderate 流程不需要步骤 9", 10,
                "跳过；moderate 流程",
            )
            if code != 0:
                return code, msg
            skip_results.append(msg)

    if skip_results:
        return 0, "\n".join(skip_results)
    return 0, ""


def complete_step(args: argparse.Namespace) -> int:
    """根据当前步骤分发到对应的 complete 处理函数。"""
    state_path = Path(args.state).resolve()
    summary = args.summary

    # 步骤 1 特殊处理：state 可能还不存在
    if args.slug and (not state_path.exists() or get_current_step(load_state(state_path)) == 1):
        code, msg = complete_step_1(state_path, summary, args.slug)
        print(msg)
        return code

    state = load_state(state_path)
    if not state:
        print("❌ 状态文件不存在。请先用 --slug 参数执行步骤 1。")
        return 1

    step = get_current_step(state)
    flow_tier = get_flow_tier(state)

    # 自动跳步处理
    if step in {8, 9} and flow_tier == "light":
        code, msg = handle_skip_steps(state_path, 10, flow_tier, summary)
        if code != 0:
            print(msg)
            return code
        if msg:
            print(msg)
        state = load_state(state_path)
        step = get_current_step(state)
        flow_tier = get_flow_tier(state)

    if step == 9 and flow_tier == "moderate":
        code, msg = handle_skip_steps(state_path, 10, flow_tier, summary)
        if code != 0:
            print(msg)
            return code
        if msg:
            print(msg)
        state = load_state(state_path)
        step = get_current_step(state)
        flow_tier = get_flow_tier(state)

    dispatch = {
        1: lambda: complete_step_1(state_path, summary, args.slug),
        2: lambda: complete_step_2(state_path, summary),
        3: lambda: complete_step_3(state_path, summary),
        4: lambda: complete_step_4(
            state_path, summary,
            flow_tier_arg=args.flow_tier,
            solution_type=args.solution_type,
            signals=args.signal,
        ),
        5: lambda: complete_step_5(state_path, summary, members=args.member),
        6: lambda: complete_step_6(state_path, summary),
        7: lambda: complete_creative_step(state_path, summary, 7, args.content_file or []),
        8: lambda: complete_creative_step(state_path, summary, 8, args.content_file or []),
        9: lambda: complete_creative_step(state_path, summary, 9, args.content_file or []),
        10: lambda: complete_creative_step(state_path, summary, 10, args.content_file or []),
        11: lambda: complete_step_11(state_path, summary),
        12: lambda: complete_step_12(state_path, summary),
    }

    handler = dispatch.get(step)
    if not handler:
        print(f"❌ 未知步骤: {step}")
        return 1

    code, msg = handler()
    print(msg)

    # 打印下一步提示
    if code == 0 and step < 12:
        new_state = load_state(state_path)
        new_step = get_current_step(new_state)
        new_tier = get_flow_tier(new_state)
        if new_step <= 12:
            print(f"\n📌 下一步（步骤 {new_step} - {STEP_NAMES.get(new_step, '')}）：")
            _print_next_command(state_path, new_step, new_tier, new_state)

    return code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="统一步骤编排器：封装验证、状态推进和 step card 加载",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--complete", action="store_true", help="完成当前步骤并推进")
    parser.add_argument("--summary", help="步骤完成摘要（--complete 时必需）")

    # 步骤特定参数
    parser.add_argument("--slug", help="步骤 1: 方案 slug")
    parser.add_argument("--flow-tier", choices=["light", "moderate", "full"], help="步骤 4: 流程级别")
    parser.add_argument("--solution-type", help="步骤 4: 方案类型")
    parser.add_argument("--signal", action="append", default=[], help="步骤 4: 分类信号（可重复）")
    parser.add_argument("--member", action="append", default=[], help="步骤 5: 参与成员（可重复）")
    parser.add_argument("--content-file", action="append", default=[], help="步骤 7/8/9/10: 内容文件路径（可重复）")

    args = parser.parse_args()

    if args.complete:
        if not args.summary:
            parser.error("--complete 需要 --summary 参数。")
        return complete_step(args)
    else:
        return print_status(Path(args.state).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
