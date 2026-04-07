# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""验证 create-technical-solution 状态文件完整性。

供 Agent 在步骤间门控检查时调用，替代人工阅读判断。
检查失败不代表流程终止，而是提示 Agent 先补齐缺失产物或修正状态，再重试。

用法：
    uv run scripts/validate-state.py --state <path_to_state_yaml> --step <step_number> [--flow-tier light|moderate|full]

退出码：
    0  — 所有检查通过
    1  — 参数或文件错误
    2  — 门控检查失败（Agent 应先修复再重试）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    print("缺少 pyyaml。运行: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ARTIFACT_REPAIR_STEP = {
    "WD-CTX": 7,
    "WD-TASK": 8,
    "WD-EXP-*": 9,
    "WD-SYN": 10,
    "WD-SYN-LIGHT": 10,
}

GATE_REPAIR_STEP = {
    "can_enter_step_8": 7,
    "can_enter_step_9": 8,
    "can_enter_step_10": 8,
    "can_enter_step_11": 10,
    "can_enter_step_12": 11,
}


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        print(f"状态文件不存在: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        print(f"状态文件必须是 YAML 对象: {path}", file=sys.stderr)
        sys.exit(1)
    return data


def normalize_text(value: str) -> str:
    return " ".join(str(value).replace("\xa0", " ").split())


def extract_slot_headings(markdown: str, slot_level: Optional[int] = None) -> list[dict[str, Any]]:
    headings: list[tuple[int, str]] = []
    for line in markdown.splitlines():
        match = re.match(r"^(#{2,6})\s+(.+?)\s*$", line)
        if not match:
            continue
        level = len(match.group(1))
        title = normalize_text(match.group(2))
        if title:
            headings.append((level, title))

    if not headings:
        return []

    if slot_level is None:
        counts: dict[int, int] = {}
        for level, _title in headings:
            counts[level] = counts.get(level, 0) + 1
        slot_level = max(counts.items(), key=lambda item: (item[1], item[0]))[0]

    slots: list[dict[str, Any]] = []
    for index, (level, title) in enumerate(headings, start=1):
        if level != slot_level:
            continue
        slots.append(
            {
                "slot": f"SLOT-{index:02d}",
                "level": level,
                "title": title,
                "normalized_title": normalize_text(title),
            }
        )
    return slots


def read_markdown(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def find_heading_titles(markdown: str, prefix: str) -> list[str]:
    titles: list[str] = []
    pattern = re.compile(rf"^\s*#{{2,6}}\s+{re.escape(prefix)}(.+?)\s*$", re.MULTILINE)
    for match in pattern.finditer(markdown):
        titles.append(normalize_text(match.group(1)))
    return titles


def looks_like_legacy_solution_path(path: Path) -> bool:
    return "/.architecture/solutions" in path.as_posix()


def resolve_path(value: Any, base: Path) -> Optional[Path]:
    if not value or not str(value).strip():
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    return (base / path).resolve()


def remediation_for_issue(issue: dict[str, Any]) -> str:
    code = issue["code"]
    missing_artifacts = issue.get("missing_artifacts", [])
    field = issue.get("field")

    if code == "missing_artifact":
        artifact = missing_artifacts[0] if missing_artifacts else "未知产物"
        if artifact == "WD-CTX":
            return "先回到步骤 7，补齐 WD-CTX 区块并同步 produced_artifacts。"
        if artifact == "WD-TASK":
            return "先回到步骤 8，补齐 WD-TASK 区块并同步 produced_artifacts。"
        if artifact == "WD-EXP-*":
            return "先确认步骤 5 已落 selected_members，再回到步骤 9 生成 WD-EXP-* 区块。"
        if artifact in {"WD-SYN", "WD-SYN-LIGHT"}:
            return "先回到步骤 10，补齐收敛区块并同步 produced_artifacts。"
    if code == "missing_working_draft_block":
        artifact = missing_artifacts[0] if missing_artifacts else "未知产物"
        return f"working draft 已存在，但缺少 {artifact} 区块。请回到对应步骤把该区块写入 working draft。"
    if code == "schema_mismatch":
        return "将状态文件中的对应字段改成结构化对象，至少保留 summary 和该步门禁字段后再重试。"
    if code == "missing_selected_members":
        return "先回到步骤 5 生成非空 selected_members；若为 full 流程，再执行步骤 9 生成 WD-EXP-*。"
    if code == "gate_flag_false":
        return f"检查前一步是否已完成，并正确更新状态文件中的 {field}。"
    if code == "invalid_step_for_tier":
        return "不要重试当前步骤；记录显式跳过原因，然后进入当前 flow_tier 允许的下一步。"
    if code == "invalid_flow_tier":
        return "回到步骤 4 重新判断 flow_tier，并同步 required_artifacts 与允许跳过步骤集合。"
    if code == "blocked_state":
        return "先根据 block_reason 解除阻塞，再修正缺失状态或产物。"
    if code == "completed_steps_invalid":
        return "修正 completed_steps 与 current_step 的连续性和一致性，再重试验证。"
    if code == "premature_cleanup_flags":
        return "步骤 12 前不得提前置 absorption_check_passed 或 cleanup_allowed；请先回退这些标志。"
    if code == "missing_slug":
        return "回到步骤 1，生成 ASCII kebab-case slug 并写入状态文件。"
    if code == "missing_topic_summary":
        return "回到步骤 1，明确方案主题并写入 topic_summary。"
    if code == "prerequisites_not_checked":
        return "回到步骤 2，检查前置文件后把 checkpoints.step-2.prerequisites_checked 置为 true。"
    if code == "template_not_loaded":
        return "回到步骤 3，读取当前模板并把 checkpoints.step-3.template_loaded 置为 true。"
    if code == "missing_solution_root":
        return "回到步骤 3，确定方案根目录并写入 solution_root。新产物默认写入 .architecture/technical-solutions/。"
    if code == "missing_working_draft_path":
        return "回到步骤 3，创建 working draft 文件并写入 working_draft_path。"
    if code == "missing_template_snapshot":
        return "回到步骤 3，重新提取当前模板槽位快照并写入 template_snapshot。"
    if code == "missing_solution_type":
        return "回到步骤 4，明确方案类型并写入 checkpoints.step-4.solution_type。"
    if code == "repowiki_not_checked":
        return "回到步骤 6，执行 repowiki 检测并把 checkpoints.step-6.repowiki_checked 置为 true。"
    if code == "legacy_path_detected":
        return "兼容读取历史 .architecture/solutions，但当前流程的新产物必须写入 .architecture/technical-solutions。请回到对应步骤修正路径字段。"
    if code == "template_changed_since_snapshot":
        return "当前模板在步骤 3 之后发生变化，请回退到步骤 3 重新提取模板快照和 working draft 骨架。"
    if code == "final_document_missing":
        return "回到步骤 11，生成最终文档并写入 final_document_path。"
    if code == "final_document_headings_mismatch":
        return "回到步骤 11，按当前模板快照重新成稿，确保最终文档槽位顺序与模板一致。"
    if code == "flow_tier_state_mismatch":
        return "回到步骤 4，原子修正 flow_tier、checkpoints.step-4.flow_tier、required_artifacts 与 skipped_steps，避免先推进后补状态。"
    if code == "step_skipped_without_checkpoint":
        return "回到被跳过的步骤，补齐 skipped_steps 与 checkpoints.step-N 的显式 skip 记录；若误记为 completed_steps，需同步移除。"
    if code == "cleanup_attempt_before_validation":
        return "步骤 12 必须先通过 validator，再置 absorption_check_passed/cleanup_allowed。请先回退这些标志，并使用 finalize-cleanup.py 完成清理。"
    if code == "task_slots_incomplete":
        return "回到步骤 8，按 template_snapshot 为每个真实槽位生成任务条目，并把缺失槽位补进 WD-TASK。"
    if code == "missing_step_summary":
        return "补齐对应 step checkpoint 的结构化 summary 后再重试。"
    return "根据错误条目补齐缺失产物或修正状态文件后重试。"


def make_issue(
    *,
    code: str,
    message: str,
    step: int,
    flow_tier: str,
    field: Optional[str] = None,
    missing_artifacts: Optional[list[str]] = None,
    recommended_rollback_step: Optional[int] = None,
    recommended_repair_step: Optional[int] = None,
    skip_instead_of_retry: bool = False,
    details: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    issue = {
        "code": code,
        "message": message,
        "step": step,
        "flow_tier": flow_tier,
        "field": field,
        "missing_artifacts": missing_artifacts or [],
        "recommended_rollback_step": recommended_rollback_step,
        "recommended_repair_step": recommended_repair_step,
        "skip_instead_of_retry": skip_instead_of_retry,
    }
    if details:
        issue.update(details)
    issue["repair_guidance"] = remediation_for_issue(issue)
    return issue


def add_issue(errors: list[dict[str, Any]], issue: dict[str, Any]) -> None:
    errors.append(issue)


def require(
    condition: bool,
    errors: list[dict[str, Any]],
    *,
    code: str,
    message: str,
    step: int,
    flow_tier: str,
    field: Optional[str] = None,
    missing_artifacts: Optional[list[str]] = None,
    recommended_rollback_step: Optional[int] = None,
    recommended_repair_step: Optional[int] = None,
    skip_instead_of_retry: bool = False,
    details: Optional[dict[str, Any]] = None,
) -> None:
    if condition:
        return
    add_issue(
        errors,
        make_issue(
            code=code,
            message=message,
            step=step,
            flow_tier=flow_tier,
            field=field,
            missing_artifacts=missing_artifacts,
            recommended_rollback_step=recommended_rollback_step,
            recommended_repair_step=recommended_repair_step,
            skip_instead_of_retry=skip_instead_of_retry,
            details=details,
        ),
    )


def format_issue(issue: dict[str, Any]) -> str:
    return f"  ✗ {issue['message']}\n    → 建议：{issue['repair_guidance']}"


def expected_artifacts_for_step(step: int, flow_tier: str) -> list[str]:
    mapping = {
        (7, "light"): ["WD-CTX"],
        (7, "moderate"): ["WD-CTX"],
        (7, "full"): ["WD-CTX"],
        (8, "moderate"): ["WD-CTX"],
        (8, "full"): ["WD-CTX"],
        (9, "full"): ["WD-CTX", "WD-TASK"],
        (10, "light"): ["WD-CTX"],
        (10, "moderate"): ["WD-CTX", "WD-TASK"],
        (10, "full"): ["WD-CTX", "WD-TASK", "WD-EXP-*"],
        (11, "light"): ["WD-CTX", "WD-SYN-LIGHT"],
        (11, "moderate"): ["WD-CTX", "WD-TASK", "WD-SYN"],
        (11, "full"): ["WD-CTX", "WD-TASK", "WD-SYN"],
    }
    return mapping.get((step, flow_tier), [])


def expected_required_artifacts(flow_tier: str) -> dict[str, Any]:
    if flow_tier == "light":
        return {"required": ["WD-CTX", "WD-SYN-LIGHT"], "forbidden_prefixes": ["WD-EXP-"], "forbidden_exact": ["WD-TASK", "WD-SYN"]}
    if flow_tier == "moderate":
        return {"required": ["WD-CTX", "WD-TASK", "WD-SYN"], "forbidden_prefixes": ["WD-EXP-"], "forbidden_exact": ["WD-SYN-LIGHT"]}
    return {"required": ["WD-CTX", "WD-TASK", "WD-SYN"], "forbidden_prefixes": [], "forbidden_exact": ["WD-SYN-LIGHT"]}


class GateValidator:
    def __init__(self, state: dict[str, Any], state_path: Optional[Path] = None):
        self.state = state
        self.state_path = state_path or Path("state.yaml")
        self.state_dir = self.state_path.parent.resolve()
        self.arch_root = self.state_dir.parents[1] if len(self.state_dir.parents) >= 2 else self.state_dir
        self.repo_root = self.arch_root.parent if self.arch_root.name == ".architecture" else self.state_dir.parent

    def checkpoint(self, step_num: int, errors: list[dict[str, Any]], flow_tier: str) -> dict[str, Any]:
        checkpoints = self.state.get("checkpoints", {})
        if checkpoints is None:
            checkpoints = {}
        if not isinstance(checkpoints, dict):
            add_issue(
                errors,
                make_issue(
                    code="schema_mismatch",
                    message="状态文件中的 checkpoints 必须为对象",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="checkpoints",
                    recommended_rollback_step=step_num,
                    recommended_repair_step=step_num,
                    details={"expected_type": "dict", "actual_type": type(checkpoints).__name__},
                ),
            )
            return {}
        key = f"step-{step_num}"
        checkpoint = checkpoints.get(key, {})
        if checkpoint is None:
            return {}
        if not isinstance(checkpoint, dict):
            add_issue(
                errors,
                make_issue(
                    code="schema_mismatch",
                    message=f"{key} 必须为对象，当前是 {type(checkpoint).__name__}",
                    step=step_num,
                    flow_tier=flow_tier,
                    field=f"checkpoints.{key}",
                    recommended_rollback_step=step_num,
                    recommended_repair_step=step_num,
                    details={"expected_type": "dict", "actual_type": type(checkpoint).__name__},
                ),
            )
            return {}
        return checkpoint

    def solution_root(self) -> Optional[Path]:
        path = resolve_path(self.state.get("solution_root"), self.repo_root)
        if path:
            return path
        default_root = self.arch_root / "technical-solutions"
        legacy_root = self.arch_root / "solutions"
        if default_root.exists():
            return default_root
        if legacy_root.exists():
            return legacy_root
        return default_root

    def working_draft_path(self, require_explicit: bool = True) -> Optional[Path]:
        explicit = resolve_path(self.state.get("working_draft_path"), self.repo_root)
        if explicit:
            return explicit
        if require_explicit:
            return None
        slug = str(self.state.get("slug") or "").strip()
        if not slug:
            return None
        solution_root = resolve_path(self.state.get("solution_root"), self.repo_root) or self.solution_root()
        if not solution_root:
            return None
        return solution_root / "working-drafts" / f"{slug}.working.md"

    def final_document_path(self, require_explicit: bool = True) -> Optional[Path]:
        explicit = resolve_path(self.state.get("final_document_path"), self.repo_root)
        if explicit:
            return explicit
        if require_explicit:
            return None
        slug = str(self.state.get("slug") or "").strip()
        if not slug:
            return None
        solution_root = resolve_path(self.state.get("solution_root"), self.repo_root) or self.solution_root()
        if not solution_root:
            return None
        exact = solution_root / f"{slug}.md"
        if exact.exists():
            return exact
        matches = sorted(solution_root.glob(f"{slug}*.md"))
        return matches[0] if matches else exact

    def template_path(self) -> Optional[Path]:
        snapshot = self.state.get("template_snapshot") or {}
        if isinstance(snapshot, dict):
            path = resolve_path(snapshot.get("path"), self.repo_root)
            if path:
                return path
        default_path = self.arch_root / "templates" / "technical-solution-template.md"
        return default_path if default_path.exists() else default_path

    def template_snapshot(self, errors: list[dict[str, Any]], step_num: int, flow_tier: str) -> dict[str, Any]:
        snapshot = self.state.get("template_snapshot") or {}
        if snapshot == {}:
            return {}
        if not isinstance(snapshot, dict):
            add_issue(
                errors,
                make_issue(
                    code="schema_mismatch",
                    message=f"步骤 {step_num}: template_snapshot 必须为对象",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="template_snapshot",
                    recommended_rollback_step=3,
                    recommended_repair_step=3,
                    details={"expected_type": "dict", "actual_type": type(snapshot).__name__},
                ),
            )
            return {}
        return snapshot

    def snapshot_headings(self, errors: list[dict[str, Any]], step_num: int, flow_tier: str) -> list[dict[str, Any]]:
        snapshot = self.template_snapshot(errors, step_num, flow_tier)
        headings = snapshot.get("headings") if isinstance(snapshot, dict) else None
        if isinstance(headings, list) and headings:
            normalized: list[dict[str, Any]] = []
            for index, item in enumerate(headings, start=1):
                if isinstance(item, dict):
                    title = normalize_text(item.get("normalized_title") or item.get("title") or "")
                    level = item.get("level")
                else:
                    title = normalize_text(str(item))
                    level = snapshot.get("slot_level")
                if title:
                    normalized.append(
                        {
                            "slot": item.get("slot", f"SLOT-{index:02d}") if isinstance(item, dict) else f"SLOT-{index:02d}",
                            "level": level,
                            "title": title,
                            "normalized_title": title,
                        }
                    )
            if normalized:
                return normalized
        template_slots = self.state.get("template_slots")
        if isinstance(template_slots, list) and template_slots:
            return [
                {
                    "slot": f"SLOT-{index:02d}",
                    "level": None,
                    "title": normalize_text(str(title)),
                    "normalized_title": normalize_text(str(title)),
                }
                for index, title in enumerate(template_slots, start=1)
                if normalize_text(str(title))
            ]
        return []

    def current_template_headings(self, slot_level: Optional[int]) -> list[dict[str, Any]]:
        path = self.template_path()
        if not path or not path.exists():
            return []
        return extract_slot_headings(read_markdown(path), slot_level=slot_level)

    def check_template_snapshot(self, errors: list[dict[str, Any]], step_num: int, flow_tier: str) -> list[dict[str, Any]]:
        snapshot = self.snapshot_headings(errors, step_num, flow_tier)
        require(
            bool(snapshot),
            errors,
            code="missing_template_snapshot",
            message=f"步骤 {step_num}: template_snapshot 缺失或未记录槽位快照",
            step=step_num,
            flow_tier=flow_tier,
            field="template_snapshot",
            recommended_rollback_step=3,
            recommended_repair_step=3,
        )
        return snapshot

    def check_template_still_matches_snapshot(self, errors: list[dict[str, Any]], step_num: int, flow_tier: str) -> None:
        snapshot = self.check_template_snapshot(errors, step_num, flow_tier)
        if not snapshot:
            return
        current_auto = self.current_template_headings(None)
        if not current_auto:
            return
        snapshot_titles = [item["normalized_title"] for item in snapshot]
        current_titles = [item["normalized_title"] for item in current_auto]
        snapshot_level = snapshot[0].get("level") if snapshot else None
        current_level = current_auto[0].get("level") if current_auto else None
        if snapshot_titles != current_titles:
            add_issue(
                errors,
                make_issue(
                    code="template_changed_since_snapshot",
                    message=f"步骤 {step_num}: 当前模板与步骤 3 记录的 template_snapshot 不一致",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="template_snapshot",
                    recommended_rollback_step=3,
                    recommended_repair_step=3,
                    details={
                        "snapshot_headings": snapshot_titles,
                        "current_headings": current_titles,
                        "snapshot_slot_level": snapshot_level,
                        "current_slot_level": current_level,
                    },
                ),
            )

    def check_solution_paths(self, errors: list[dict[str, Any]], step_num: int, flow_tier: str) -> None:
        solution_root = self.solution_root()
        require(
            solution_root is not None,
            errors,
            code="missing_solution_root",
            message=f"步骤 {step_num}: solution_root 缺失",
            step=step_num,
            flow_tier=flow_tier,
            field="solution_root",
            recommended_rollback_step=3,
            recommended_repair_step=3,
        )
        working_draft = self.working_draft_path(require_explicit=True)
        require(
            working_draft is not None,
            errors,
            code="missing_working_draft_path",
            message=f"步骤 {step_num}: working_draft_path 缺失",
            step=step_num,
            flow_tier=flow_tier,
            field="working_draft_path",
            recommended_rollback_step=3,
            recommended_repair_step=3,
        )
        for field_name, path_obj, repair_step in [
            ("solution_root", solution_root, 3),
            ("working_draft_path", working_draft, 3),
            ("final_document_path", self.final_document_path(require_explicit=True), 11),
        ]:
            if path_obj and looks_like_legacy_solution_path(path_obj):
                add_issue(
                    errors,
                    make_issue(
                        code="legacy_path_detected",
                        message=f"步骤 {step_num}: {field_name} 仍指向历史目录 .architecture/solutions",
                        step=step_num,
                        flow_tier=flow_tier,
                        field=field_name,
                        recommended_rollback_step=repair_step,
                        recommended_repair_step=repair_step,
                        details={"path": str(path_obj)},
                    ),
                )

    def check_working_draft(self, artifacts: list[str], errors: list[dict[str, Any]], step_num: int, flow_tier: str) -> None:
        working_draft = self.working_draft_path(require_explicit=True)
        if not working_draft:
            return
        if not working_draft.exists():
            add_issue(
                errors,
                make_issue(
                    code="missing_working_draft_path",
                    message=f"步骤 {step_num}: working draft 文件不存在: {working_draft}",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="working_draft_path",
                    recommended_rollback_step=3,
                    recommended_repair_step=3,
                    details={"path": str(working_draft)},
                ),
            )
            return
        content = read_markdown(working_draft)
        for artifact in artifacts:
            if artifact == "WD-EXP-*":
                present = re.search(r"WD-EXP-[A-Za-z0-9_-]+", content) is not None
            else:
                present = re.search(rf"\b{re.escape(artifact)}\b", content) is not None
            if not present:
                add_issue(
                    errors,
                    make_issue(
                        code="missing_working_draft_block",
                        message=f"步骤 {step_num}: working draft 缺少 {artifact} 区块",
                        step=step_num,
                        flow_tier=flow_tier,
                        field="produced_artifacts",
                        missing_artifacts=[artifact],
                        recommended_rollback_step=ARTIFACT_REPAIR_STEP.get(artifact, step_num),
                        recommended_repair_step=ARTIFACT_REPAIR_STEP.get(artifact, step_num),
                        details={"working_draft_path": str(working_draft)},
                    ),
                )

    def expert_artifacts(self) -> list[str]:
        selected = self.state.get("selected_members") or []
        if not isinstance(selected, list):
            return []
        artifacts: list[str] = []
        for member in selected:
            slug = str(member).strip()
            if slug:
                artifacts.append(f"WD-EXP-{slug.upper()}")
        return artifacts

    def skipped_steps(self, errors: list[dict[str, Any]], step_num: int, flow_tier: str) -> list[int]:
        raw = self.state.get("skipped_steps", [])
        if raw is None:
            return []
        if not isinstance(raw, list):
            add_issue(
                errors,
                make_issue(
                    code="schema_mismatch",
                    message=f"步骤 {step_num}: skipped_steps 必须为数组",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="skipped_steps",
                    recommended_rollback_step=4,
                    recommended_repair_step=4,
                    details={"expected_type": "list", "actual_type": type(raw).__name__},
                ),
            )
            return []
        normalized: list[int] = []
        for index, item in enumerate(raw):
            if isinstance(item, int):
                normalized.append(item)
            else:
                add_issue(
                    errors,
                    make_issue(
                        code="schema_mismatch",
                        message=f"步骤 {step_num}: skipped_steps[{index}] 必须为整数",
                        step=step_num,
                        flow_tier=flow_tier,
                        field="skipped_steps",
                        recommended_rollback_step=4,
                        recommended_repair_step=4,
                        details={"expected_type": "int", "actual_type": type(item).__name__},
                    ),
                )
        return normalized

    def check_flow_tier_contract(self, errors: list[dict[str, Any]], step_num: int, flow_tier: str) -> None:
        state_tier = self.state.get("flow_tier")
        if state_tier not in {"light", "moderate", "full"}:
            return
        if step_num >= 4 and flow_tier != state_tier:
            add_issue(
                errors,
                make_issue(
                    code="flow_tier_state_mismatch",
                    message=f"步骤 {step_num}: 传入的 flow_tier={flow_tier} 与状态文件中的 flow_tier={state_tier} 不一致",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="flow_tier",
                    recommended_rollback_step=4,
                    recommended_repair_step=4,
                    details={"state_flow_tier": state_tier, "requested_flow_tier": flow_tier},
                ),
            )

        checkpoint4 = self.checkpoint(4, errors, flow_tier)
        checkpoint_tier = checkpoint4.get("flow_tier")
        if step_num >= 4 and checkpoint_tier not in {None, "", state_tier}:
            add_issue(
                errors,
                make_issue(
                    code="flow_tier_state_mismatch",
                    message=f"步骤 {step_num}: checkpoints.step-4.flow_tier 与顶层 flow_tier 不一致",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="checkpoints.step-4.flow_tier",
                    recommended_rollback_step=4,
                    recommended_repair_step=4,
                    details={"state_flow_tier": state_tier, "checkpoint_flow_tier": checkpoint_tier},
                ),
            )

        if step_num >= 4:
            contract = expected_required_artifacts(state_tier)
            required_artifacts = [str(item) for item in self.state.get("required_artifacts", [])]
            missing = [artifact for artifact in contract["required"] if artifact not in required_artifacts]
            forbidden = [
                artifact
                for artifact in required_artifacts
                if artifact in contract["forbidden_exact"] or any(str(artifact).startswith(prefix) for prefix in contract["forbidden_prefixes"])
            ]
            if missing or forbidden:
                add_issue(
                    errors,
                    make_issue(
                        code="flow_tier_state_mismatch",
                        message=f"步骤 {step_num}: required_artifacts 与 flow_tier={state_tier} 不一致",
                        step=step_num,
                        flow_tier=flow_tier,
                        field="required_artifacts",
                        recommended_rollback_step=4,
                        recommended_repair_step=4,
                        details={"missing_required_artifacts": missing, "forbidden_artifacts": forbidden, "state_flow_tier": state_tier},
                    ),
                )

    def check_skip_record(self, skipped_step: int, errors: list[dict[str, Any]], step_num: int, flow_tier: str) -> None:
        skipped_steps = self.skipped_steps(errors, step_num, flow_tier)
        checkpoint = self.checkpoint(skipped_step, errors, flow_tier)
        completed_steps = self.state.get("completed_steps", [])
        if not isinstance(completed_steps, list):
            completed_steps = []

        has_checkpoint_skip = checkpoint.get("skipped") is True and bool(str(checkpoint.get("reason") or checkpoint.get("summary") or "").strip())
        if skipped_step in completed_steps or skipped_step not in skipped_steps or not has_checkpoint_skip:
            add_issue(
                errors,
                make_issue(
                    code="step_skipped_without_checkpoint",
                    message=f"步骤 {step_num}: step-{skipped_step} 被 flow_tier={flow_tier} 跳过时，必须显式记录 skip，且不得写入 completed_steps",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="skipped_steps",
                    recommended_rollback_step=skipped_step,
                    recommended_repair_step=skipped_step,
                    details={
                        "skipped_step": skipped_step,
                        "skipped_steps": skipped_steps,
                        "completed_steps": completed_steps,
                        "checkpoint": checkpoint,
                    },
                ),
            )

    def check_expert_blocks(self, errors: list[dict[str, Any]], step_num: int, flow_tier: str) -> None:
        working_draft = self.working_draft_path(require_explicit=True)
        if not working_draft or not working_draft.exists():
            return
        content = read_markdown(working_draft)
        expected = self.expert_artifacts()
        for artifact in expected:
            present_in_state = artifact in self.state.get("produced_artifacts", [])
            present_in_draft = re.search(rf"^\s*#{{2,6}}\s+{re.escape(artifact)}\b", content, re.MULTILINE) is not None
            if present_in_state and not present_in_draft:
                add_issue(
                    errors,
                    make_issue(
                        code="missing_working_draft_block",
                        message=f"步骤 {step_num}: working draft 缺少 {artifact} 区块",
                        step=step_num,
                        flow_tier=flow_tier,
                        field="produced_artifacts",
                        missing_artifacts=[artifact],
                        recommended_rollback_step=9,
                        recommended_repair_step=9,
                        details={"working_draft_path": str(working_draft)},
                    ),
                )

    def check_task_slots_cover_snapshot(self, errors: list[dict[str, Any]], step_num: int, flow_tier: str) -> None:
        working_draft = self.working_draft_path(require_explicit=True)
        if not working_draft or not working_draft.exists():
            return
        snapshot = self.check_template_snapshot(errors, step_num, flow_tier)
        if not snapshot:
            return
        content = read_markdown(working_draft)
        expected_titles = [item["normalized_title"] for item in snapshot]
        missing_titles = [title for title in expected_titles if title not in normalize_text(content)]
        if missing_titles:
            add_issue(
                errors,
                make_issue(
                    code="task_slots_incomplete",
                    message=f"步骤 {step_num}: WD-TASK 未覆盖当前模板全部槽位",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="template_snapshot",
                    recommended_rollback_step=8,
                    recommended_repair_step=8,
                    details={"missing_slots": missing_titles},
                ),
            )

    def check_final_document(self, errors: list[dict[str, Any]], step_num: int, flow_tier: str) -> None:
        final_document = self.final_document_path(require_explicit=True)
        require(
            final_document is not None,
            errors,
            code="final_document_missing",
            message=f"步骤 {step_num}: final_document_path 缺失",
            step=step_num,
            flow_tier=flow_tier,
            field="final_document_path",
            recommended_rollback_step=11,
            recommended_repair_step=11,
        )
        if not final_document:
            return
        if not final_document.exists():
            add_issue(
                errors,
                make_issue(
                    code="final_document_missing",
                    message=f"步骤 {step_num}: 最终文档不存在: {final_document}",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="final_document_path",
                    recommended_rollback_step=11,
                    recommended_repair_step=11,
                    details={"path": str(final_document)},
                ),
            )
            return

        snapshot = self.check_template_snapshot(errors, step_num, flow_tier)
        if not snapshot:
            return
        slot_level = snapshot[0].get("level") if snapshot else None
        final_headings = extract_slot_headings(read_markdown(final_document), slot_level if isinstance(slot_level, int) else None)
        expected_titles = [item["normalized_title"] for item in snapshot]
        final_titles = [item["normalized_title"] for item in final_headings]
        if expected_titles != final_titles:
            add_issue(
                errors,
                make_issue(
                    code="final_document_headings_mismatch",
                    message=f"步骤 {step_num}: 最终文档槽位顺序与 template_snapshot 不一致",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="final_document_path",
                    recommended_rollback_step=11,
                    recommended_repair_step=11,
                    details={"expected_headings": expected_titles, "actual_headings": final_titles},
                ),
            )

    def common(self, step_num: int, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        state = self.state
        self.check_flow_tier_contract(errors, step_num, flow_tier)
        require(
            state.get("blocked") is False,
            errors,
            code="blocked_state",
            message=f"step-{step_num}: 状态文件标记为阻塞",
            step=step_num,
            flow_tier=flow_tier,
            field="blocked",
            recommended_rollback_step=step_num,
            recommended_repair_step=step_num,
        )

        completed = state.get("completed_steps", [])
        if not isinstance(completed, list):
            add_issue(
                errors,
                make_issue(
                    code="schema_mismatch",
                    message=f"step-{step_num}: completed_steps 必须为数组",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="completed_steps",
                    recommended_rollback_step=step_num,
                    recommended_repair_step=step_num,
                    details={"expected_type": "list", "actual_type": type(completed).__name__},
                ),
            )
        else:
            current_step = state.get("current_step") or 0
            seen: set[int] = set()
            for index, raw in enumerate(completed):
                if not isinstance(raw, int):
                    add_issue(
                        errors,
                        make_issue(
                            code="schema_mismatch",
                            message=f"step-{step_num}: completed_steps[{index}] 必须为整数",
                            step=step_num,
                            flow_tier=flow_tier,
                            field="completed_steps",
                            recommended_rollback_step=step_num,
                            recommended_repair_step=step_num,
                            details={"expected_type": "int", "actual_type": type(raw).__name__},
                        ),
                    )
                    continue
                if raw in seen:
                    add_issue(
                        errors,
                        make_issue(
                            code="completed_steps_invalid",
                            message=f"step-{step_num}: completed_steps 中存在重复步骤 step-{raw}",
                            step=step_num,
                            flow_tier=flow_tier,
                            field="completed_steps",
                            recommended_rollback_step=step_num,
                            recommended_repair_step=step_num,
                        ),
                    )
                seen.add(raw)
                if raw >= current_step + 1:
                    add_issue(
                        errors,
                        make_issue(
                            code="completed_steps_invalid",
                            message=f"step-{step_num}: completed_steps[{index}]=step-{raw} 超过 current_step={current_step}",
                            step=step_num,
                            flow_tier=flow_tier,
                            field="completed_steps",
                            recommended_rollback_step=step_num,
                            recommended_repair_step=step_num,
                        ),
                    )

        current_step = int(state.get("current_step") or 0)
        if current_step < 12 and (state.get("absorption_check_passed") or state.get("cleanup_allowed")):
            add_issue(
                errors,
                make_issue(
                    code="premature_cleanup_flags",
                    message=f"step-{step_num}: 步骤 12 前不应提前设置 absorption_check_passed/cleanup_allowed",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="cleanup_allowed",
                    recommended_rollback_step=max(current_step, 11),
                    recommended_repair_step=max(current_step, 11),
                ),
            )

    def step_1(self, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        self.common(1, flow_tier, errors)
        require(
            bool(str(self.state.get("slug") or "").strip()),
            errors,
            code="missing_slug",
            message="步骤 1: slug 未生成或为空",
            step=1,
            flow_tier=flow_tier,
            field="slug",
            recommended_rollback_step=1,
            recommended_repair_step=1,
        )
        require(
            bool(str(self.state.get("topic_summary") or "").strip()),
            errors,
            code="missing_topic_summary",
            message="步骤 1: topic_summary 缺失或为空",
            step=1,
            flow_tier=flow_tier,
            field="topic_summary",
            recommended_rollback_step=1,
            recommended_repair_step=1,
        )

    def step_2(self, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        self.common(2, flow_tier, errors)
        checkpoint = self.checkpoint(2, errors, flow_tier)
        require(
            checkpoint.get("prerequisites_checked") is True,
            errors,
            code="prerequisites_not_checked",
            message="步骤 2: 前置文件检查未完成",
            step=2,
            flow_tier=flow_tier,
            field="checkpoints.step-2.prerequisites_checked",
            recommended_rollback_step=2,
            recommended_repair_step=2,
        )

    def step_3(self, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        self.common(3, flow_tier, errors)
        checkpoint = self.checkpoint(3, errors, flow_tier)
        require(
            checkpoint.get("template_loaded") is True,
            errors,
            code="template_not_loaded",
            message="步骤 3: 模板未加载",
            step=3,
            flow_tier=flow_tier,
            field="checkpoints.step-3.template_loaded",
            recommended_rollback_step=3,
            recommended_repair_step=3,
        )
        self.check_solution_paths(errors, 3, flow_tier)
        self.check_template_snapshot(errors, 3, flow_tier)
        self.check_template_still_matches_snapshot(errors, 3, flow_tier)

    def step_4(self, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        self.common(4, flow_tier, errors)
        checkpoint = self.checkpoint(4, errors, flow_tier)
        require(
            self.state.get("flow_tier") in {"light", "moderate", "full"},
            errors,
            code="invalid_flow_tier",
            message="步骤 4: flow_tier 必须为 light/moderate/full",
            step=4,
            flow_tier=flow_tier,
            field="flow_tier",
            recommended_rollback_step=4,
            recommended_repair_step=4,
        )
        require(
            bool(str(checkpoint.get("solution_type") or "").strip()),
            errors,
            code="missing_solution_type",
            message="步骤 4: 方案类型未确定",
            step=4,
            flow_tier=flow_tier,
            field="checkpoints.step-4.solution_type",
            recommended_rollback_step=4,
            recommended_repair_step=4,
        )
        require(
            checkpoint.get("flow_tier") == self.state.get("flow_tier"),
            errors,
            code="flow_tier_state_mismatch",
            message="步骤 4: checkpoints.step-4.flow_tier 必须与顶层 flow_tier 一致",
            step=4,
            flow_tier=flow_tier,
            field="checkpoints.step-4.flow_tier",
            recommended_rollback_step=4,
            recommended_repair_step=4,
            details={"state_flow_tier": self.state.get("flow_tier"), "checkpoint_flow_tier": checkpoint.get("flow_tier")},
        )
        self.check_template_still_matches_snapshot(errors, 4, flow_tier)

    def step_5(self, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        self.common(5, flow_tier, errors)
        require(
            isinstance(self.state.get("selected_members"), list) and bool(self.state.get("selected_members")),
            errors,
            code="missing_selected_members",
            message="步骤 5: selected_members 为空",
            step=5,
            flow_tier=flow_tier,
            field="selected_members",
            recommended_rollback_step=5,
            recommended_repair_step=5,
        )
        self.check_template_still_matches_snapshot(errors, 5, flow_tier)

    def step_6(self, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        self.common(6, flow_tier, errors)
        checkpoint = self.checkpoint(6, errors, flow_tier)
        require(
            checkpoint.get("repowiki_checked") is True,
            errors,
            code="repowiki_not_checked",
            message="步骤 6: repowiki 检测未完成",
            step=6,
            flow_tier=flow_tier,
            field="checkpoints.step-6.repowiki_checked",
            recommended_rollback_step=6,
            recommended_repair_step=6,
        )
        self.check_template_still_matches_snapshot(errors, 6, flow_tier)

    def step_7(self, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        self.common(7, flow_tier, errors)
        self.check_solution_paths(errors, 7, flow_tier)
        self.check_template_still_matches_snapshot(errors, 7, flow_tier)
        require(
            "WD-CTX" in self.state.get("produced_artifacts", []),
            errors,
            code="missing_artifact",
            message="步骤 7: produced_artifacts 缺少 WD-CTX",
            step=7,
            flow_tier=flow_tier,
            field="produced_artifacts",
            missing_artifacts=["WD-CTX"],
            recommended_rollback_step=7,
            recommended_repair_step=7,
        )
        gate_field = "can_enter_step_10" if flow_tier == "light" else "can_enter_step_8"
        require(
            self.state.get(gate_field) is True,
            errors,
            code="gate_flag_false",
            message=f"步骤 7: {gate_field} 为 false",
            step=7,
            flow_tier=flow_tier,
            field=gate_field,
            recommended_rollback_step=GATE_REPAIR_STEP[gate_field],
            recommended_repair_step=GATE_REPAIR_STEP[gate_field],
        )
        self.check_working_draft(["WD-CTX"], errors, 7, flow_tier)

    def step_8(self, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        self.common(8, flow_tier, errors)
        if flow_tier == "light":
            add_issue(
                errors,
                make_issue(
                    code="invalid_step_for_tier",
                    message="步骤 8: light 流程不应进入此步骤，必须显式记录跳过",
                    step=8,
                    flow_tier=flow_tier,
                    skip_instead_of_retry=True,
                ),
            )
            return
        self.check_solution_paths(errors, 8, flow_tier)
        self.check_template_still_matches_snapshot(errors, 8, flow_tier)
        require(
            "WD-CTX" in self.state.get("produced_artifacts", []),
            errors,
            code="missing_artifact",
            message="步骤 8: produced_artifacts 缺少 WD-CTX",
            step=8,
            flow_tier=flow_tier,
            field="produced_artifacts",
            missing_artifacts=["WD-CTX"],
            recommended_rollback_step=7,
            recommended_repair_step=7,
        )
        require(
            self.state.get("can_enter_step_8") is True,
            errors,
            code="gate_flag_false",
            message="步骤 8: can_enter_step_8 为 false",
            step=8,
            flow_tier=flow_tier,
            field="can_enter_step_8",
            recommended_rollback_step=7,
            recommended_repair_step=7,
        )
        self.check_working_draft(["WD-CTX"], errors, 8, flow_tier)
        self.check_task_slots_cover_snapshot(errors, 8, flow_tier)

    def step_9(self, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        self.common(9, flow_tier, errors)
        if flow_tier in {"light", "moderate"}:
            add_issue(
                errors,
                make_issue(
                    code="invalid_step_for_tier",
                    message=f"步骤 9: {flow_tier} 流程不应进入此步骤，必须显式记录跳过",
                    step=9,
                    flow_tier=flow_tier,
                    skip_instead_of_retry=True,
                ),
            )
            return
        self.check_solution_paths(errors, 9, flow_tier)
        self.check_template_still_matches_snapshot(errors, 9, flow_tier)
        require(
            self.state.get("flow_tier") == "full",
            errors,
            code="invalid_flow_tier",
            message="步骤 9: flow_tier 必须为 full",
            step=9,
            flow_tier=flow_tier,
            field="flow_tier",
            recommended_rollback_step=4,
            recommended_repair_step=4,
        )
        require(
            "WD-CTX" in self.state.get("produced_artifacts", []),
            errors,
            code="missing_artifact",
            message="步骤 9: produced_artifacts 缺少 WD-CTX",
            step=9,
            flow_tier=flow_tier,
            field="produced_artifacts",
            missing_artifacts=["WD-CTX"],
            recommended_rollback_step=7,
            recommended_repair_step=7,
        )
        require(
            "WD-TASK" in self.state.get("produced_artifacts", []),
            errors,
            code="missing_artifact",
            message="步骤 9: produced_artifacts 缺少 WD-TASK",
            step=9,
            flow_tier=flow_tier,
            field="produced_artifacts",
            missing_artifacts=["WD-TASK"],
            recommended_rollback_step=8,
            recommended_repair_step=8,
        )
        require(
            self.state.get("can_enter_step_9") is True,
            errors,
            code="gate_flag_false",
            message="步骤 9: can_enter_step_9 为 false",
            step=9,
            flow_tier=flow_tier,
            field="can_enter_step_9",
            recommended_rollback_step=8,
            recommended_repair_step=8,
        )
        self.check_working_draft(["WD-CTX", "WD-TASK"], errors, 9, flow_tier)
        self.check_task_slots_cover_snapshot(errors, 9, flow_tier)
        self.check_expert_blocks(errors, 9, flow_tier)

    def step_10(self, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        self.common(10, flow_tier, errors)
        self.check_solution_paths(errors, 10, flow_tier)
        self.check_template_still_matches_snapshot(errors, 10, flow_tier)
        if flow_tier == "light":
            self.check_skip_record(8, errors, 10, flow_tier)
            self.check_skip_record(9, errors, 10, flow_tier)
        elif flow_tier == "moderate":
            self.check_skip_record(9, errors, 10, flow_tier)
        require(
            self.state.get("can_enter_step_10") is True,
            errors,
            code="gate_flag_false",
            message="步骤 10: can_enter_step_10 为 false",
            step=10,
            flow_tier=flow_tier,
            field="can_enter_step_10",
            recommended_rollback_step=GATE_REPAIR_STEP["can_enter_step_10"],
            recommended_repair_step=GATE_REPAIR_STEP["can_enter_step_10"],
        )
        require(
            "WD-CTX" in self.state.get("produced_artifacts", []),
            errors,
            code="missing_artifact",
            message="步骤 10: produced_artifacts 缺少 WD-CTX",
            step=10,
            flow_tier=flow_tier,
            field="produced_artifacts",
            missing_artifacts=["WD-CTX"],
            recommended_rollback_step=7,
            recommended_repair_step=7,
        )
        if flow_tier == "light":
            self.check_working_draft(["WD-CTX"], errors, 10, flow_tier)
            return
        require(
            "WD-TASK" in self.state.get("produced_artifacts", []),
            errors,
            code="missing_artifact",
            message=f"步骤 10 ({flow_tier}): produced_artifacts 缺少 WD-TASK",
            step=10,
            flow_tier=flow_tier,
            field="produced_artifacts",
            missing_artifacts=["WD-TASK"],
            recommended_rollback_step=8,
            recommended_repair_step=8,
        )
        artifacts = ["WD-CTX", "WD-TASK"]
        if flow_tier == "full":
            exp_artifacts = [artifact for artifact in self.state.get("produced_artifacts", []) if str(artifact).startswith("WD-EXP-")]
            require(
                bool(exp_artifacts),
                errors,
                code="missing_artifact",
                message="步骤 10 (full): 缺少 WD-EXP-* 产物",
                step=10,
                flow_tier=flow_tier,
                field="produced_artifacts",
                missing_artifacts=["WD-EXP-*"] ,
                recommended_rollback_step=9,
                recommended_repair_step=9,
            )
            artifacts.extend(self.expert_artifacts() or ["WD-EXP-*"])
        self.check_working_draft(artifacts, errors, 10, flow_tier)
        if flow_tier == "full":
            self.check_expert_blocks(errors, 10, flow_tier)

    def step_11(self, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        self.common(11, flow_tier, errors)
        self.check_solution_paths(errors, 11, flow_tier)
        self.check_template_still_matches_snapshot(errors, 11, flow_tier)
        if flow_tier == "light":
            self.check_skip_record(8, errors, 11, flow_tier)
            self.check_skip_record(9, errors, 11, flow_tier)
        elif flow_tier == "moderate":
            self.check_skip_record(9, errors, 11, flow_tier)
        require(
            self.state.get("can_enter_step_11") is True,
            errors,
            code="gate_flag_false",
            message="步骤 11: can_enter_step_11 为 false",
            step=11,
            flow_tier=flow_tier,
            field="can_enter_step_11",
            recommended_rollback_step=10,
            recommended_repair_step=10,
        )
        artifacts = expected_artifacts_for_step(11, flow_tier)
        for artifact in artifacts:
            require(
                artifact in self.state.get("produced_artifacts", []),
                errors,
                code="missing_artifact",
                message=f"步骤 11 ({flow_tier}): produced_artifacts 缺少 {artifact}",
                step=11,
                flow_tier=flow_tier,
                field="produced_artifacts",
                missing_artifacts=[artifact],
                recommended_rollback_step=ARTIFACT_REPAIR_STEP.get(artifact, 9 if str(artifact).startswith("WD-EXP-") else 11),
                recommended_repair_step=ARTIFACT_REPAIR_STEP.get(artifact, 9 if str(artifact).startswith("WD-EXP-") else 11),
            )
        self.check_working_draft(artifacts, errors, 11, flow_tier)
        if flow_tier == "full":
            self.check_expert_blocks(errors, 11, flow_tier)

    def step_12(self, flow_tier: str, errors: list[dict[str, Any]]) -> None:
        self.common(12, flow_tier, errors)
        self.check_solution_paths(errors, 12, flow_tier)
        self.check_template_still_matches_snapshot(errors, 12, flow_tier)
        if flow_tier == "light":
            self.check_skip_record(8, errors, 12, flow_tier)
            self.check_skip_record(9, errors, 12, flow_tier)
        elif flow_tier == "moderate":
            self.check_skip_record(9, errors, 12, flow_tier)
        require(
            self.state.get("can_enter_step_12") is True,
            errors,
            code="gate_flag_false",
            message="步骤 12: can_enter_step_12 为 false",
            step=12,
            flow_tier=flow_tier,
            field="can_enter_step_12",
            recommended_rollback_step=11,
            recommended_repair_step=11,
        )
        self.check_final_document(errors, 12, flow_tier)
        checkpoint = self.checkpoint(12, errors, flow_tier)
        if self.state.get("absorption_check_passed") or self.state.get("cleanup_allowed"):
            require(
                checkpoint.get("validator_passed") is True,
                errors,
                code="cleanup_attempt_before_validation",
                message="步骤 12: 未记录 validator_passed=true 就提前设置了 cleanup 标志",
                step=12,
                flow_tier=flow_tier,
                field="checkpoints.step-12.validator_passed",
                recommended_rollback_step=12,
                recommended_repair_step=12,
            )
        require(
            bool(str(checkpoint.get("summary") or "").strip()),
            errors,
            code="missing_step_summary",
            message="步骤 12: checkpoints.step-12.summary 不能为空",
            step=12,
            flow_tier=flow_tier,
            field="checkpoints.step-12.summary",
            recommended_rollback_step=12,
            recommended_repair_step=12,
        )


def build_summary(issues: list[dict[str, Any]]) -> dict[str, Any]:
    rollback_steps = [item["recommended_rollback_step"] for item in issues if item.get("recommended_rollback_step") is not None]
    repair_steps = [item["recommended_repair_step"] for item in issues if item.get("recommended_repair_step") is not None]
    missing_artifacts: list[str] = []
    for issue in issues:
        for artifact in issue.get("missing_artifacts", []):
            if artifact not in missing_artifacts:
                missing_artifacts.append(artifact)
    return {
        "error_count": len(issues),
        "recommended_rollback_step": min(rollback_steps) if rollback_steps else None,
        "recommended_repair_sequence": sorted(dict.fromkeys(repair_steps)),
        "missing_artifacts": missing_artifacts,
        "skip_instead_of_retry": any(issue.get("skip_instead_of_retry") for issue in issues),
    }


def check_field_equals(field: str, value: object, summary: str) -> dict[str, Any]:
    return {"type": "field_equals", "field": field, "expected": value, "summary": summary}


def check_field_non_empty(field: str, summary: str) -> dict[str, Any]:
    return {"type": "field_non_empty", "field": field, "summary": summary}


def check_artifact_present(artifact: str, summary: str) -> dict[str, Any]:
    return {"type": "artifact_present", "artifact": artifact, "summary": summary}


def completion_checks_for_issue(issue: dict[str, Any]) -> list[dict[str, Any]]:
    code = issue.get("code")
    field = issue.get("field")
    checks: list[dict[str, Any]] = []

    if code in {"missing_artifact", "missing_working_draft_block"}:
        for artifact in issue.get("missing_artifacts", []):
            checks.append(check_artifact_present(artifact, f"{artifact} 已写入 working draft 并完成状态同步"))
    elif code == "missing_selected_members":
        checks.append(check_field_non_empty("selected_members", "selected_members 已写入且非空"))
    elif code == "gate_flag_false" and field:
        checks.append(check_field_equals(field, True, f"{field} 已置为 true"))
    elif code == "schema_mismatch" and field:
        checks.append({"type": "custom", "summary": f"{field} 已改为结构化对象或正确类型"})
    elif code == "missing_topic_summary":
        checks.append(check_field_non_empty("topic_summary", "topic_summary 已写入且非空"))
    elif code == "missing_slug":
        checks.append(check_field_non_empty("slug", "slug 已写入且非空"))
    elif code == "missing_solution_root":
        checks.append(check_field_non_empty("solution_root", "solution_root 已写入"))
    elif code == "missing_working_draft_path":
        checks.append(check_field_non_empty("working_draft_path", "working_draft_path 已写入且文件已创建"))
    elif code == "missing_template_snapshot":
        checks.append(check_field_non_empty("template_snapshot", "template_snapshot 已写入并包含槽位快照"))
    elif code == "missing_solution_type":
        checks.append(check_field_non_empty("checkpoints.step-4.solution_type", "solution_type 已写入"))
    elif code == "repowiki_not_checked":
        checks.append(check_field_equals("checkpoints.step-6.repowiki_checked", True, "repowiki_checked 已置为 true"))
    elif code == "final_document_missing":
        checks.append(check_field_non_empty("final_document_path", "final_document_path 已写入且最终文档已生成"))
    elif code == "final_document_headings_mismatch":
        checks.append({"type": "custom", "summary": "最终文档槽位顺序已与 template_snapshot 对齐"})
    elif code == "template_changed_since_snapshot":
        checks.append({"type": "custom", "summary": "template_snapshot 已按最新模板重新提取"})
    elif code == "legacy_path_detected" and field:
        checks.append({"type": "custom", "summary": f"{field} 已改为 .architecture/technical-solutions 路径"})
    elif code == "premature_cleanup_flags":
        checks.append(check_field_equals("absorption_check_passed", False, "absorption_check_passed 已回退为 false"))
        checks.append(check_field_equals("cleanup_allowed", False, "cleanup_allowed 已回退为 false"))
    elif code == "cleanup_attempt_before_validation":
        checks.append(check_field_equals("checkpoints.step-12.validator_passed", True, "step-12.validator_passed 已为 true"))
    elif code == "completed_steps_invalid":
        checks.append({"type": "custom", "summary": "completed_steps 已恢复连续且与 current_step 一致"})
    elif code == "flow_tier_state_mismatch":
        checks.append({"type": "custom", "summary": "flow_tier、step-4 checkpoint、required_artifacts 与 skipped_steps 已保持同源"})
    elif code == "step_skipped_without_checkpoint":
        checks.append({"type": "custom", "summary": "被跳过步骤已写入 skipped_steps 与结构化 checkpoint，且不在 completed_steps 中"})
    elif code == "task_slots_incomplete":
        checks.append({"type": "custom", "summary": "WD-TASK 已覆盖 template_snapshot 的全部槽位"})
    elif code == "missing_step_summary":
        checks.append(check_field_non_empty("checkpoints.step-12.summary", "step-12.summary 已补齐"))

    if not checks:
        checks.append({"type": "custom", "summary": "相关状态与产物已修正，再次验证不再报该问题"})
    return checks


def merge_unique(items: list[dict[str, Any]], item: dict[str, Any]) -> None:
    if item not in items:
        items.append(item)


def build_retry_command(step: int, issue: dict[str, Any]) -> dict[str, Any]:
    flow_tier = issue.get("flow_tier", "full")
    command = "python scripts/validate-state.py"
    args = ["--state", "<状态文件路径>", "--step", str(step), "--flow-tier", flow_tier, "--format", "json"]
    return {
        "command": command,
        "args": args,
        "format": "json",
        "target_step": step,
        "flow_tier": flow_tier,
        "display": f"{command} {' '.join(args)}",
    }


def action_types_for_issue(issue: dict[str, Any]) -> list[str]:
    code = issue.get("code")
    if code == "invalid_step_for_tier":
        return ["skip_step"]
    if code in {"missing_artifact", "missing_working_draft_block", "final_document_missing", "final_document_headings_mismatch", "task_slots_incomplete"}:
        return ["generate_artifact", "update_state", "rerun_validation"]
    if code in {"schema_mismatch", "missing_working_draft_path", "missing_solution_root", "missing_template_snapshot", "template_changed_since_snapshot", "legacy_path_detected", "premature_cleanup_flags", "flow_tier_state_mismatch", "step_skipped_without_checkpoint", "cleanup_attempt_before_validation"}:
        return ["update_state", "rerun_validation"]
    if issue.get("field"):
        return ["update_state", "rerun_validation"]
    return ["investigate"]


def state_patch_hints_for_issue(issue: dict[str, Any]) -> list[dict[str, Any]]:
    code = issue.get("code")
    field = issue.get("field")
    hints: list[dict[str, Any]] = []

    if code == "gate_flag_false" and field:
        hints.append({"field": field, "operation": "set", "value": True, "summary": f"将 {field} 置为 true"})
    elif code == "missing_selected_members":
        hints.append({"field": "selected_members", "operation": "set_non_empty", "value": "<步骤 5 选定成员列表>", "summary": "写入非空 selected_members"})
    elif code == "invalid_flow_tier":
        hints.append({"field": "flow_tier", "operation": "set", "value": "<light|moderate|full>", "summary": "修正 flow_tier"})
    elif code == "flow_tier_state_mismatch":
        hints.append({"field": "flow_tier", "operation": "set", "value": "<light|moderate|full>", "summary": "统一 flow_tier"})
        hints.append({"field": "checkpoints.step-4.flow_tier", "operation": "set", "value": "<与顶层 flow_tier 一致>", "summary": "同步 step-4.flow_tier"})
        hints.append({"field": "required_artifacts", "operation": "set", "value": "<与 flow_tier 匹配的产物列表>", "summary": "同步 required_artifacts"})
        hints.append({"field": "skipped_steps", "operation": "set", "value": "<与 flow_tier 匹配的显式跳过步骤列表>", "summary": "同步 skipped_steps"})
    elif code == "missing_slug":
        hints.append({"field": "slug", "operation": "set", "value": "<ASCII kebab-case slug>", "summary": "写入 slug"})
    elif code == "missing_topic_summary":
        hints.append({"field": "topic_summary", "operation": "set", "value": "<方案主题一句话摘要>", "summary": "写入 topic_summary"})
    elif code == "prerequisites_not_checked":
        hints.append({"field": "checkpoints.step-2.prerequisites_checked", "operation": "set", "value": True, "summary": "标记步骤 2 前置检查完成"})
    elif code == "template_not_loaded":
        hints.append({"field": "checkpoints.step-3.template_loaded", "operation": "set", "value": True, "summary": "标记模板已加载"})
    elif code == "missing_solution_root":
        hints.append({"field": "solution_root", "operation": "set", "value": ".architecture/technical-solutions", "summary": "写入统一方案目录"})
    elif code == "missing_working_draft_path":
        hints.append({"field": "working_draft_path", "operation": "set", "value": ".architecture/technical-solutions/working-drafts/<slug>.working.md", "summary": "写入 working_draft_path"})
    elif code == "missing_template_snapshot":
        hints.append({"field": "template_snapshot", "operation": "set_non_empty", "value": "<当前模板快照>", "summary": "写入 template_snapshot"})
    elif code == "missing_solution_type":
        hints.append({"field": "checkpoints.step-4.solution_type", "operation": "set_non_empty", "value": "<方案类型>", "summary": "写入方案类型"})
    elif code == "repowiki_not_checked":
        hints.append({"field": "checkpoints.step-6.repowiki_checked", "operation": "set", "value": True, "summary": "标记 repowiki 检测完成"})
    elif code == "legacy_path_detected" and field:
        value = ".architecture/technical-solutions"
        if field == "working_draft_path":
            value = ".architecture/technical-solutions/working-drafts/<slug>.working.md"
        elif field == "final_document_path":
            value = ".architecture/technical-solutions/<slug>.md"
        hints.append({"field": field, "operation": "set", "value": value, "summary": f"将 {field} 改为新目录路径"})
    elif code == "template_changed_since_snapshot":
        hints.append({"field": "template_snapshot", "operation": "update", "value": None, "summary": "按当前模板重新生成 template_snapshot"})
    elif code == "premature_cleanup_flags":
        hints.append({"field": "absorption_check_passed", "operation": "set", "value": False, "summary": "回退 absorption_check_passed"})
        hints.append({"field": "cleanup_allowed", "operation": "set", "value": False, "summary": "回退 cleanup_allowed"})
    elif code == "cleanup_attempt_before_validation":
        hints.append({"field": "absorption_check_passed", "operation": "set", "value": False, "summary": "先回退 absorption_check_passed"})
        hints.append({"field": "cleanup_allowed", "operation": "set", "value": False, "summary": "先回退 cleanup_allowed"})
        hints.append({"field": "checkpoints.step-12.validator_passed", "operation": "set", "value": True, "summary": "在 validator 通过后写入 step-12.validator_passed"})
    elif code == "step_skipped_without_checkpoint":
        skipped_step = issue.get("skipped_step", "<step>")
        hints.append({"field": "skipped_steps", "operation": "set", "value": f"<包含 {skipped_step} 的步骤列表>", "summary": "补齐 skipped_steps"})
        hints.append({"field": f"checkpoints.step-{skipped_step}.skipped", "operation": "set", "value": True, "summary": f"标记 step-{skipped_step} 为显式跳过"})
        hints.append({"field": f"checkpoints.step-{skipped_step}.reason", "operation": "set_non_empty", "value": "<跳过原因>", "summary": f"补齐 step-{skipped_step} 的跳过原因"})
        hints.append({"field": "completed_steps", "operation": "update", "value": None, "summary": f"若误将 step-{skipped_step} 记为完成，需从 completed_steps 移除"})
    elif code in {"missing_artifact", "missing_working_draft_block"} and field == "produced_artifacts":
        for artifact in issue.get("missing_artifacts", []):
            hints.append({"field": "produced_artifacts", "operation": "append_unique", "value": artifact, "summary": f"同步 {artifact} 到 produced_artifacts"})
    elif code == "final_document_missing":
        hints.append({"field": "final_document_path", "operation": "set", "value": ".architecture/technical-solutions/<slug>.md", "summary": "写入 final_document_path"})
    elif code == "task_slots_incomplete":
        hints.append({"field": "checkpoints.step-8", "operation": "update", "value": None, "summary": "按 template_snapshot 补齐 WD-TASK 槽位任务单"})
    elif code == "missing_step_summary":
        hints.append({"field": "checkpoints.step-12.summary", "operation": "set_non_empty", "value": "<步骤12摘要>", "summary": "补齐 step-12.summary"})
    elif field:
        hints.append({"field": field, "operation": "update", "value": None, "summary": f"按当前问题修正 {field}"})

    return hints


def artifact_write_hints_for_issue(issue: dict[str, Any]) -> list[dict[str, Any]]:
    code = issue.get("code")
    hints: list[dict[str, Any]] = []
    if code in {"missing_artifact", "missing_working_draft_block"}:
        for artifact in issue.get("missing_artifacts", []):
            hints.append(
                {
                    "artifact": artifact,
                    "target": "working_draft",
                    "block": artifact,
                    "write_mode": "append_or_replace_block",
                    "status_sync_field": "produced_artifacts",
                    "status_sync_operation": "append_unique",
                    "summary": f"将 {artifact} 区块写入 working draft，并同步 produced_artifacts",
                }
            )
    if code == "final_document_missing":
        hints.append(
            {
                "artifact": "final_document",
                "target": "final_document",
                "block": "final_markdown",
                "write_mode": "replace_file",
                "status_sync_field": "final_document_path",
                "status_sync_operation": "set",
                "summary": "生成最终技术方案文档并写入 final_document_path",
            }
        )
    if code == "task_slots_incomplete":
        hints.append(
            {
                "artifact": "WD-TASK",
                "target": "working_draft",
                "block": "WD-TASK",
                "write_mode": "replace_block",
                "status_sync_field": "produced_artifacts",
                "status_sync_operation": "append_unique",
                "summary": "按 template_snapshot 补齐 WD-TASK 的槽位任务单并同步 produced_artifacts",
            }
        )
    return hints


def working_draft_context_hints_for_issue(issue: dict[str, Any]) -> list[dict[str, Any]]:
    code = issue.get("code")
    flow_tier = issue.get("flow_tier", "full")
    hints: list[dict[str, Any]] = []
    if code not in {"missing_artifact", "missing_working_draft_block", "final_document_missing", "final_document_headings_mismatch"}:
        return hints

    for artifact in issue.get("missing_artifacts", []):
        required_blocks: list[str] = []
        external_inputs: list[str] = []
        forbidden_blocks: list[str] = []
        summary = ""

        if artifact == "WD-CTX":
            external_inputs = ["repo_inputs", "members_yml", "principles_md", "current_template"]
            forbidden_blocks = ["WD-TASK", "WD-EXP-*", "WD-SYN", "WD-SYN-LIGHT", "final_document"]
            summary = "生成 WD-CTX 时只消费外部输入与当前模板，不得预支下游 WD-* 或最终文档。"
        elif artifact == "WD-TASK":
            required_blocks = ["WD-CTX"]
            external_inputs = ["current_template"]
            forbidden_blocks = ["WD-EXP-*", "WD-SYN", "WD-SYN-LIGHT", "final_document"]
            summary = "生成 WD-TASK 时仅消费当前模板与已落盘 WD-CTX，不得预支下游结论。"
        elif artifact == "WD-EXP-*":
            required_blocks = ["WD-CTX", "WD-TASK"]
            external_inputs = ["selected_members"]
            forbidden_blocks = ["WD-SYN", "WD-SYN-LIGHT", "final_document"]
            summary = "生成 WD-EXP-* 时仅消费 WD-CTX、WD-TASK 与已选成员。"
        elif artifact in {"WD-SYN", "WD-SYN-LIGHT"}:
            required_blocks = ["WD-CTX"]
            if flow_tier in {"moderate", "full"}:
                required_blocks.append("WD-TASK")
            if flow_tier == "full":
                required_blocks.append("WD-EXP-*")
            external_inputs = ["current_template"]
            forbidden_blocks = ["final_document"]
            summary = "生成收敛区块时只消费上游稳定 WD-* 与当前模板，不得以最终文档替代。"

        if summary:
            hints.append(
                {
                    "artifact": artifact,
                    "required_blocks": required_blocks,
                    "external_inputs": external_inputs,
                    "forbidden_blocks": forbidden_blocks,
                    "summary": summary,
                }
            )

    if code in {"final_document_missing", "final_document_headings_mismatch"}:
        hints.append(
            {
                "artifact": "final_document",
                "required_blocks": ["WD-SYN", "WD-SYN-LIGHT"],
                "external_inputs": ["template_snapshot", "current_template"],
                "forbidden_blocks": ["template_extension"],
                "summary": "生成最终文档时只能消费已收敛区块，并严格映射回当前模板快照。",
            }
        )
    return hints


def build_repair_plan(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan_by_step: dict[int, dict[str, Any]] = {}
    for issue in issues:
        repair_step = issue.get("recommended_repair_step")
        if not repair_step or issue.get("skip_instead_of_retry"):
            continue
        item = plan_by_step.setdefault(
            repair_step,
            {
                "step": repair_step,
                "action_types": [],
                "depends_on_steps": [],
                "generate_artifacts": [],
                "fix_fields": [],
                "state_patch_hint": [],
                "artifact_write_hint": [],
                "working_draft_context_hint": [],
                "issues": [],
                "guidance": [],
                "completion_checks": [],
                "retry_command": build_retry_command(issue.get("step", repair_step), issue),
                "retry_validation": True,
            },
        )
        for action_type in action_types_for_issue(issue):
            if action_type not in item["action_types"]:
                item["action_types"].append(action_type)
        for artifact in issue.get("missing_artifacts", []):
            if artifact not in item["generate_artifacts"]:
                item["generate_artifacts"].append(artifact)
        if issue.get("code") == "final_document_missing" and "final_document" not in item["generate_artifacts"]:
            item["generate_artifacts"].append("final_document")
        field = issue.get("field")
        if field and field not in item["fix_fields"]:
            item["fix_fields"].append(field)
        if issue["code"] not in item["issues"]:
            item["issues"].append(issue["code"])
        guidance = issue.get("repair_guidance")
        if guidance and guidance not in item["guidance"]:
            item["guidance"].append(guidance)
        for hint in state_patch_hints_for_issue(issue):
            if hint not in item["state_patch_hint"]:
                item["state_patch_hint"].append(hint)
        for hint in artifact_write_hints_for_issue(issue):
            if hint not in item["artifact_write_hint"]:
                item["artifact_write_hint"].append(hint)
        for hint in working_draft_context_hints_for_issue(issue):
            if hint not in item["working_draft_context_hint"]:
                item["working_draft_context_hint"].append(hint)
        for check in completion_checks_for_issue(issue):
            merge_unique(item["completion_checks"], check)

    ordered_steps = sorted(plan_by_step)
    for index, step in enumerate(ordered_steps):
        plan_by_step[step]["depends_on_steps"] = ordered_steps[:index]
    return [plan_by_step[step] for step in ordered_steps]


def build_state_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "current_step": state.get("current_step"),
        "flow_tier": state.get("flow_tier"),
        "completed_steps": state.get("completed_steps", []),
        "skipped_steps": state.get("skipped_steps", []),
        "required_artifacts": state.get("required_artifacts", []),
        "produced_artifacts": state.get("produced_artifacts", []),
        "selected_members": state.get("selected_members", []),
        "blocked": state.get("blocked"),
        "block_reason": state.get("block_reason"),
        "solution_root": state.get("solution_root"),
        "working_draft_path": state.get("working_draft_path"),
        "final_document_path": state.get("final_document_path"),
        "can_enter_step_8": state.get("can_enter_step_8"),
        "can_enter_step_9": state.get("can_enter_step_9"),
        "can_enter_step_10": state.get("can_enter_step_10"),
        "can_enter_step_11": state.get("can_enter_step_11"),
        "can_enter_step_12": state.get("can_enter_step_12"),
        "absorption_check_passed": state.get("absorption_check_passed"),
        "cleanup_allowed": state.get("cleanup_allowed"),
        "step_12_validator_passed": ((state.get("checkpoints") or {}).get("step-12") or {}).get("validator_passed") if isinstance(state.get("checkpoints"), dict) else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="验证 create-technical-solution 状态文件")
    parser.add_argument("--state", required=True, help="状态文件 YAML 路径")
    parser.add_argument("--step", type=int, required=True, help="当前步骤号 (1-12)")
    parser.add_argument("--flow-tier", choices=["light", "moderate", "full"], default="full", help="流程级别")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    args = parser.parse_args()

    if not 1 <= args.step <= 12:
        print(f"不支持验证步骤 {args.step}。仅支持 1-12 的门控检查。", file=sys.stderr)
        sys.exit(1)

    state_path = Path(args.state).resolve()
    state = load_state(state_path)
    validator = GateValidator(state, state_path)
    issues: list[dict[str, Any]] = []

    dispatch = {
        1: validator.step_1,
        2: validator.step_2,
        3: validator.step_3,
        4: validator.step_4,
        5: validator.step_5,
        6: validator.step_6,
        7: validator.step_7,
        8: validator.step_8,
        9: validator.step_9,
        10: validator.step_10,
        11: validator.step_11,
        12: validator.step_12,
    }
    dispatch[args.step](args.flow_tier, issues)

    result = {
        "step": args.step,
        "flow_tier": args.flow_tier,
        "passed": len(issues) == 0,
        "summary": build_summary(issues),
        "repair_plan": build_repair_plan(issues),
        "state_snapshot": build_state_snapshot(state),
        "issues": issues,
    }

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if issues:
            print(f"步骤 {args.step} 门控检查未通过 ({len(issues)} 项):", file=sys.stderr)
            print("请先按建议补齐缺失产物或修正状态，然后重新运行验证。", file=sys.stderr)
            for issue in issues:
                print(format_issue(issue), file=sys.stderr)
        else:
            print(f"步骤 {args.step} ({args.flow_tier}) 门控检查通过")

    if issues:
        sys.exit(2)


if __name__ == "__main__":
    main()
