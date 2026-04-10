# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
"""验证 create-technical-solution 的最小状态机与 draft/final 产物。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Optional

import yaml

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from protocol_runtime import compute_state_fingerprint, dump_yaml as dump_state, iso_now, load_yaml as load_state
from protocol_runtime import (
    SOLUTION_ROOT,
    final_document_relative_path,
    render_repair_command,
    working_draft_relative_path,
)
from wd_syn_contract import missing_slot_fragments as missing_wd_syn_slot_fragments
from wd_syn_contract import target_capability_present


ALLOWED_TOP_LEVEL_FIELDS = {
    "current_step",
    "completed_steps",
    "skipped_steps",
    "required_artifacts",
    "produced_artifacts",
    "pending_questions",
    "gate_receipt",
    "solution_root",
    "template_path",
    "members_path",
    "principles_path",
    "repowiki_path",
    "working_draft_path",
    "final_document_path",
    "checkpoints",
    "can_enter_step_8",
    "can_enter_step_9",
    "can_enter_step_10",
    "can_enter_step_11",
    "can_enter_step_12",
    "absorption_check_passed",
    "cleanup_allowed",
    "slots",
}

SUMMARY_MAX_LEN = 120
SUMMARY_FORBIDDEN_PATTERNS = [
    re.compile(r"\n"),
    re.compile(r"CTX-\d+"),
    re.compile(r"WD-EXP"),
    re.compile(r"^#{1,6}\s", re.MULTILINE),
    re.compile(r"```"),
    re.compile(r"^\s*\|.+\|\s*$", re.MULTILINE),
]

ARTIFACT_REPAIR_STEP = {
    "WD-CTX": 7,
    "WD-TASK": 8,
    "WD-EXP-*": 9,
    "final_document": 11,
}

GATE_REPAIR_STEP = {
    "can_enter_step_8": 7,
    "can_enter_step_9": 8,
    "can_enter_step_10": 8,
    "can_enter_step_11": 10,
    "can_enter_step_12": 11,
}

VALID_STEP4_SIGNALS = {
    "introduces-core-capability",
    "cross-system",
    "boundary-redraw",
    "high-compat-risk",
    "split-or-migrate",
    "cross-module",
    "existing-asset-refactor",
    "medium-compat-risk",
    "single-module",
    "low-compat-risk",
}


def extract_named_block(markdown: str, heading: str) -> str:
    pattern = re.compile(rf"^\s*##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^\s*##\s+.+$", markdown[start:], re.MULTILINE)
    end = start + next_match.start() if next_match else len(markdown)
    return markdown[start:end].strip()


def extract_block_headings(block: str) -> list[str]:
    return [normalize_text(match.group(1)) for match in re.finditer(r"^\s*###\s+(.+?)\s*$", block, re.MULTILINE)]


def normalize_task_heading(title: str) -> str:
    normalized = normalize_text(title)
    return re.sub(r"^SLOT-\d+\s*:\s*", "", normalized)


def normalize_syn_heading(title: str) -> str:
    normalized = normalize_text(title)
    return re.sub(r"^槽位：\s*", "", normalized)


def extract_syn_slot_block(block: str, title: str) -> str:
    pattern = re.compile(rf"^\s*###\s+槽位：\s*{re.escape(title)}\s*$", re.MULTILINE)
    match = pattern.search(block)
    if not match:
        return ""
    start = match.start()
    next_match = re.search(r"^\s*###\s+槽位：\s*.+$", block[match.end():], re.MULTILINE)
    end = match.end() + next_match.start() if next_match else len(block)
    return block[start:end].strip()

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
    slot_index = 1
    for level, title in headings:
        if level != slot_level:
            continue
        slots.append({"slot": f"SLOT-{slot_index:02d}", "level": level, "title": title, "normalized_title": title})
        slot_index += 1
    return slots


def compute_template_fingerprint(markdown: str, headings: list[dict[str, Any]]) -> str:
    normalized = "\n".join(item["title"] for item in headings)
    payload = f"{normalize_text(markdown)}\n--slot-headings--\n{normalized}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_markdown(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def resolve_path(value: Any, base: Path) -> Optional[Path]:
    if not value or not str(value).strip():
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    return (base / path).resolve()


def parse_iso_datetime(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def remediation_for_issue(issue: dict[str, Any]) -> str:
    code = issue["code"]
    if code == "forbidden_state_field":
        return "删除 state 中的正文型或冗余字段，仅保留最小流程控制字段后重试。"
    if code == "verbose_summary":
        return "将 checkpoints.step-N.summary 改为单行短摘要，只写流程结果、区块数量和 gate 状态。"
    if code == "missing_step1_scope":
        return "回到步骤 1，通过 run-step.py 重新完成定题并写入 slug 与最终文档路径。"
    if code == "missing_artifact":
        artifact = issue.get("missing_artifacts", ["未知产物"])[0]
        if artifact == "final_document":
            return "回到步骤 11，通过 run-step.py 完成成稿步骤并生成最终文档。"
        return f"回到步骤 {ARTIFACT_REPAIR_STEP.get(artifact, issue['step'])} 补齐 {artifact} 并同步 produced_artifacts。"
    if code == "missing_working_draft_block":
        artifact = issue.get("missing_artifacts", ["未知产物"])[0]
        return f"将 {artifact} 真正写入 working draft，对应正文不得只留在 state 摘要中。"
    if code == "task_slots_incomplete":
        return "回到步骤 8，按当前模板真实槽位补齐 WD-TASK。"
    if code == "step_skipped_without_checkpoint":
        return "回到对应步骤流，通过 run-step.py 让跳步记录按协议自动落盘。"
    if code == "repowiki_not_consumed":
        return "回到步骤 7，实际读取并引用 repowiki，再把来源条目写入 WD-CTX。"
    if code == "invalid_working_draft_path":
        return "回到步骤 3，重新生成 .architecture/.state/create-technical-solution/[slug]/ 目录。"
    if code == "invalid_final_document_path":
        return "回到步骤 1 或 11，把 final_document_path 固定到 .architecture/technical-solutions/[slug].md。"
    if code == "final_document_headings_mismatch":
        return "回到步骤 11，按当前模板顺序重生成最终文档。"
    if code == "step_order_violation":
        return "回到步骤 10，先把 WD-SYN 落盘，再进入步骤 11。"
    if code == "cleanup_attempt_before_validation":
        return "步骤 12 必须先通过门禁，再通过 run-step.py 完成清理步骤。"
    return "修复对应状态字段或草稿区块后重试。"


def make_issue(
    *,
    code: str,
    message: str,
    step: int,
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
            field=field,
            missing_artifacts=missing_artifacts,
            recommended_rollback_step=recommended_rollback_step,
            recommended_repair_step=recommended_repair_step,
            skip_instead_of_retry=skip_instead_of_retry,
            details=details,
        ),
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


def build_repair_plan(
    issues: list[dict[str, Any]],
    *,
    state_path: Optional[Path] = None,
    state: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    plan: dict[int, dict[str, Any]] = {}
    for issue in issues:
        repair_step = issue.get("recommended_repair_step")
        if repair_step is None:
            continue
        entry = plan.setdefault(
            repair_step,
            {
                "step": repair_step,
                "action_type": "",
                "script_command": "",
                "depends_on_steps": [],
                "expected_artifacts_after_fix": [],
                "revalidate_step": repair_step,
            },
        )
        code = issue["code"]
        if code in {"missing_artifact", "missing_working_draft_block", "draft_block_overwritten"}:
            entry["action_type"] = "rerun_run_step"
            for missing in issue.get("missing_artifacts", []):
                if missing not in entry["expected_artifacts_after_fix"]:
                    entry["expected_artifacts_after_fix"].append(missing)
        else:
            entry["action_type"] = "rerun_run_step"
        if state_path is not None:
            entry["script_command"] = render_repair_command(
                state_path=state_path,
                repair_step=repair_step,
                state=state,
            )
        else:
            entry["script_command"] = "<通过当前安装位置的 run-step.py 重新执行对应步骤>"
    return [plan[key] for key in sorted(plan)]


class GateValidator:
    def __init__(self, state: dict[str, Any], state_path: Optional[Path] = None):
        self.state = state
        self.state_path = state_path or Path("state.yaml")
        self.state_dir = self.state_path.parent.resolve()
        resolved = self.state_path.resolve()
        if resolved.name == "meta.yaml":
            self.repo_root = resolved.parents[4]
        else:
            self.repo_root = self.state_dir.parents[3] if len(self.state_dir.parents) >= 3 else self.state_dir.parent
        self.arch_root = self.repo_root / ".architecture" if (self.repo_root / ".architecture").exists() else self.repo_root

    def checkpoint(self, step_num: int, errors: list[dict[str, Any]]) -> dict[str, Any]:
        checkpoints = self.state.get("checkpoints", {})
        if not isinstance(checkpoints, dict):
            add_issue(
                errors,
                make_issue(
                    code="schema_mismatch",
                    message="checkpoints 必须为对象",
                    step=step_num,
                    field="checkpoints",
                    recommended_rollback_step=step_num,
                    recommended_repair_step=step_num,
                ),
            )
            return {}
        checkpoint = checkpoints.get(f"step-{step_num}", {})
        if checkpoint is None:
            return {}
        if not isinstance(checkpoint, dict):
            add_issue(
                errors,
                make_issue(
                    code="schema_mismatch",
                    message=f"checkpoints.step-{step_num} 必须为对象",
                    step=step_num,
                    field=f"checkpoints.step-{step_num}",
                    recommended_rollback_step=step_num,
                    recommended_repair_step=step_num,
                ),
            )
            return {}
        return checkpoint

    def template_path(self) -> Optional[Path]:
        return resolve_path(self.state.get("template_path"), self.repo_root)

    def members_path(self) -> Optional[Path]:
        return resolve_path(self.state.get("members_path"), self.repo_root)

    def principles_path(self) -> Optional[Path]:
        return resolve_path(self.state.get("principles_path"), self.repo_root)

    def solution_root_path(self) -> Optional[Path]:
        return resolve_path(self.state.get("solution_root"), self.repo_root)

    def working_draft_path(self) -> Optional[Path]:
        return resolve_path(self.state.get("working_draft_path"), self.repo_root)

    def final_document_path(self) -> Optional[Path]:
        return resolve_path(self.state.get("final_document_path"), self.repo_root)

    def template_headings(self) -> list[dict[str, Any]]:
        template_path = self.template_path()
        if not template_path or not template_path.exists():
            return []
        return extract_slot_headings(read_markdown(template_path))

    def template_fingerprint(self) -> str:
        template_path = self.template_path()
        if not template_path or not template_path.exists():
            return ""
        markdown = read_markdown(template_path)
        headings = extract_slot_headings(markdown)
        if not headings:
            return ""
        return compute_template_fingerprint(markdown, headings)

    def selected_members(self) -> list[str]:
        checkpoints = self.state.get("checkpoints", {})
        step5 = checkpoints.get("step-5", {}) if isinstance(checkpoints, dict) else {}
        raw = step5.get("selected_members", []) if isinstance(step5, dict) else []
        return [str(item) for item in raw if str(item).strip()] if isinstance(raw, list) else []

    def pending_questions(self) -> list[dict[str, Any]]:
        raw = self.state.get("pending_questions", [])
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)]

    def check_pending_questions(self, errors: list[dict[str, Any]], step_num: int) -> None:
        require(
            not self.pending_questions(),
            errors,
            code="pending_questions_blocking_progress",
            message=f"步骤 {step_num}: 存在待回答问题，必须先清空 pending_questions",
            step=step_num,
                        field="pending_questions",
            skip_instead_of_retry=True,
            recommended_rollback_step=step_num,
            recommended_repair_step=step_num,
        )

    def check_state_shape(self, errors: list[dict[str, Any]], step_num: int) -> None:
        for key in self.state:
            if key not in ALLOWED_TOP_LEVEL_FIELDS:
                add_issue(
                    errors,
                    make_issue(
                        code="forbidden_state_field",
                        message=f"步骤 {step_num}: state 不应包含 {key}",
                        step=step_num,
                                                field=key,
                        recommended_rollback_step=step_num,
                        recommended_repair_step=step_num,
                    ),
                )

    def check_receipt_integrity(self, errors: list[dict[str, Any]], step_num: int) -> None:
        receipt = self.state.get("gate_receipt")
        if not isinstance(receipt, dict):
            return
        receipt_step = int(receipt.get("step") or 0)
        current_step = int(self.state.get("current_step") or 0)
        if current_step > 1 and receipt_step != current_step:
            add_issue(
                errors,
                make_issue(
                    code="invalid_gate_receipt",
                    message=f"步骤 {step_num}: gate_receipt.step={receipt_step} 与 current_step={current_step} 不一致",
                    step=step_num,
                                        field="gate_receipt.step",
                    recommended_rollback_step=min(step_num, current_step),
                    recommended_repair_step=min(step_num, current_step),
                ),
            )
            if receipt_step <= 0:
                return
        if receipt_step <= 0:
            return
        fingerprint = str(receipt.get("state_fingerprint") or "").strip()
        validated_at = str(receipt.get("validated_at") or "").strip()
        if not fingerprint or not validated_at:
            add_issue(
                errors,
                make_issue(
                    code="invalid_gate_receipt",
                    message=f"步骤 {step_num}: gate_receipt 不完整，禁止手工伪造 receipt",
                    step=step_num,
                                        field="gate_receipt",
                    recommended_rollback_step=min(step_num, receipt_step),
                    recommended_repair_step=min(step_num, receipt_step),
                ),
            )
            return
        if fingerprint != compute_state_fingerprint(self.state):
            add_issue(
                errors,
                make_issue(
                    code="invalid_gate_receipt",
                    message=f"步骤 {step_num}: gate_receipt.state_fingerprint 与当前状态不一致",
                    step=step_num,
                                        field="gate_receipt.state_fingerprint",
                    recommended_rollback_step=min(step_num, receipt_step),
                    recommended_repair_step=min(step_num, receipt_step),
                ),
            )

    def check_summary(self, checkpoint: dict[str, Any], step_num: int, errors: list[dict[str, Any]]) -> None:
        summary = str(checkpoint.get("summary") or "")
        require(
            bool(summary.strip()),
            errors,
            code="missing_step_summary",
            message=f"步骤 {step_num}: checkpoints.step-{step_num}.summary 不能为空",
            step=step_num,
                        field=f"checkpoints.step-{step_num}.summary",
            recommended_rollback_step=step_num,
            recommended_repair_step=step_num,
        )
        if not summary.strip():
            return
        if len(summary) > SUMMARY_MAX_LEN or any(pattern.search(summary) for pattern in SUMMARY_FORBIDDEN_PATTERNS):
            add_issue(
                errors,
                make_issue(
                    code="verbose_summary",
                    message=f"步骤 {step_num}: summary 必须为单行流程摘要，不得承载正文",
                    step=step_num,
                                        field=f"checkpoints.step-{step_num}.summary",
                    recommended_rollback_step=step_num,
                    recommended_repair_step=step_num,
                ),
            )

    def check_completed_steps(self, errors: list[dict[str, Any]], step_num: int) -> None:
        completed = self.state.get("completed_steps", [])
        skipped = self.state.get("skipped_steps", [])
        require(
            isinstance(completed, list),
            errors,
            code="schema_mismatch",
            message="completed_steps 必须为数组",
            step=step_num,
                        field="completed_steps",
            recommended_rollback_step=step_num,
            recommended_repair_step=step_num,
        )
        if not isinstance(completed, list):
            return
        skipped_set = {item for item in skipped if isinstance(item, int)} if isinstance(skipped, list) else set()
        current_step = int(self.state.get("current_step") or 0)
        expected_sequence = [step for step in range(1, max(completed, default=0) + 1) if step not in skipped_set]
        for index, item in enumerate(completed, start=1):
            expected = expected_sequence[index - 1] if index - 1 < len(expected_sequence) else None
            if item != expected:
                add_issue(
                    errors,
                    make_issue(
                        code="completed_steps_invalid",
                        message=f"步骤 {step_num}: completed_steps 必须按未跳过步骤连续，当前位置期望 {expected} 实际为 {item}",
                        step=step_num,
                                                field="completed_steps",
                        recommended_rollback_step=step_num,
                        recommended_repair_step=step_num,
                    ),
                )
                break
            if item >= current_step + 1:
                add_issue(
                    errors,
                    make_issue(
                        code="completed_steps_invalid",
                        message=f"步骤 {step_num}: completed_steps 中存在超过 current_step 的步骤 {item}",
                        step=step_num,
                                                field="completed_steps",
                        recommended_rollback_step=step_num,
                        recommended_repair_step=step_num,
                    ),
                )
                break

    def check_step1_ready(self, errors: list[dict[str, Any]], step_num: int) -> None:
        step1 = self.checkpoint(1, errors)
        require(
            step1.get("scope_ready") is True and bool(str(step1.get("slug") or "").strip()),
            errors,
            code="missing_step1_scope",
            message=f"步骤 {step_num}: 步骤 1 尚未完成最小定题与 slug 初始化",
            step=step_num,
                        field="checkpoints.step-1.scope_ready",
            recommended_rollback_step=1,
            recommended_repair_step=1,
        )

    def check_prerequisite_files(self, errors: list[dict[str, Any]], step_num: int) -> None:
        for field, resolver in {
            "members_path": self.members_path,
            "principles_path": self.principles_path,
            "template_path": self.template_path,
        }.items():
            path = resolver()
            require(
                path is not None and path.exists(),
                errors,
                code="missing_prerequisite_file",
                message=f"步骤 {step_num}: {field} 不存在或不可读",
                step=step_num,
                                field=field,
                recommended_rollback_step=2,
                recommended_repair_step=2,
            )

    def check_working_draft_path_contract(self, errors: list[dict[str, Any]], step_num: int) -> None:
        raw_path = str(self.state.get("working_draft_path") or "").strip()
        draft_path = self.working_draft_path()
        slug = str(self.checkpoint(1, errors).get("slug") or "").strip()
        require(
            draft_path is not None,
            errors,
            code="invalid_working_draft_path",
            message=f"步骤 {step_num}: working_draft_path 不能为空",
            step=step_num,
                        field="working_draft_path",
            recommended_rollback_step=3,
            recommended_repair_step=3,
        )
        if not draft_path or not slug:
            return
        expected_relative = working_draft_relative_path(slug)
        valid = draft_path == (self.repo_root / expected_relative).resolve() and draft_path.is_dir()
        valid = valid and not Path(raw_path).is_absolute()
        require(
            valid,
            errors,
            code="invalid_working_draft_path",
            message=f"步骤 {step_num}: working_draft_path 必须固定为 {expected_relative}",
            step=step_num,
                        field="working_draft_path",
            recommended_rollback_step=3,
            recommended_repair_step=3,
        )

    def check_final_document_path_contract(self, errors: list[dict[str, Any]], step_num: int) -> None:
        final_document = self.final_document_path()
        slug = str(self.checkpoint(1, errors).get("slug") or "").strip()
        require(
            final_document is not None,
            errors,
            code="invalid_final_document_path",
            message=f"步骤 {step_num}: final_document_path 不能为空",
            step=step_num,
                        field="final_document_path",
            recommended_rollback_step=1,
            recommended_repair_step=1,
        )
        if not final_document or not slug:
            return
        expected_relative = final_document_relative_path(slug)
        valid = final_document == (self.repo_root / expected_relative).resolve()
        require(
            valid,
            errors,
            code="invalid_final_document_path",
            message=f"步骤 {step_num}: final_document_path 必须固定为 {expected_relative}",
            step=step_num,
                        field="final_document_path",
            recommended_rollback_step=1 if step_num < 11 else 11,
            recommended_repair_step=1 if step_num < 11 else 11,
        )

    def check_solution_root_contract(self, errors: list[dict[str, Any]], step_num: int) -> None:
        require(
            str(self.state.get("solution_root") or "").strip() == str(SOLUTION_ROOT),
            errors,
            code="invalid_solution_root",
            message=f"步骤 {step_num}: solution_root 必须固定为 {SOLUTION_ROOT}",
            step=step_num,
                        field="solution_root",
            recommended_rollback_step=1 if step_num < 3 else 3,
            recommended_repair_step=1 if step_num < 3 else 3,
        )

    def check_template_loaded(self, errors: list[dict[str, Any]], step_num: int) -> None:
        checkpoint = self.checkpoint(3, errors)
        current_headings = self.template_headings()
        require(
            checkpoint.get("template_loaded") is True,
            errors,
            code="template_not_loaded",
            message="步骤 3: 模板未加载",
            step=step_num,
                        field="checkpoints.step-3.template_loaded",
            recommended_rollback_step=3,
            recommended_repair_step=3,
        )
        require(
            bool(current_headings),
            errors,
            code="missing_template_snapshot",
            message=f"步骤 {step_num}: 当前模板未提取到槽位",
            step=step_num,
                        field="template_path",
            recommended_rollback_step=3,
            recommended_repair_step=3,
        )
        self.check_working_draft_path_contract(errors, step_num)
        if current_headings:
            require(
                checkpoint.get("slot_count") == len(current_headings),
                errors,
                code="template_changed_since_snapshot",
                message=f"步骤 {step_num}: slot_count 与当前模板不一致",
                step=step_num,
                                field="checkpoints.step-3.slot_count",
                recommended_rollback_step=3,
                recommended_repair_step=3,
            )
            require(
                checkpoint.get("template_fingerprint") == self.template_fingerprint(),
                errors,
                code="template_changed_since_snapshot",
                message=f"步骤 {step_num}: template_fingerprint 与当前模板不一致",
                step=step_num,
                                field="checkpoints.step-3.template_fingerprint",
                recommended_rollback_step=3,
                recommended_repair_step=3,
            )

    def check_working_draft_block(self, artifact: str, errors: list[dict[str, Any]], step_num: int) -> None:
        draft_path = self.working_draft_path()
        require(
            draft_path is not None and draft_path.is_dir(),
            errors,
            code="missing_working_draft_path",
            message=f"步骤 {step_num}: working draft 目录不存在",
            step=step_num,
                        field="working_draft_path",
            recommended_rollback_step=3,
            recommended_repair_step=3,
        )
        if not draft_path or not draft_path.is_dir():
            return
        target_file = self._resolve_artifact_file(draft_path, artifact)
        present = target_file is not None and target_file.exists() and target_file.stat().st_size > 0
        if not present:
            checkpoint_step = ARTIFACT_REPAIR_STEP.get(artifact, step_num)
            if artifact.startswith("WD-EXP-"):
                checkpoint_step = 9
            elif artifact.startswith("WD-SYN-"):
                checkpoint_step = 10
            prior_checkpoint = self.checkpoint(checkpoint_step, errors)
            overwritten = False
            if artifact == "WD-CTX":
                overwritten = prior_checkpoint.get("wd_ctx_written") is True
            elif artifact == "WD-TASK":
                overwritten = prior_checkpoint.get("wd_task_written") is True
            elif artifact.startswith("WD-SYN"):
                overwritten = prior_checkpoint.get("wd_syn_written") is True
            code = "draft_block_overwritten" if overwritten else "missing_working_draft_block"
            add_issue(
                errors,
                make_issue(
                    code=code,
                    message=f"步骤 {step_num}: working draft 缺少 {artifact}",
                    step=step_num,
                                        field="produced_artifacts",
                    missing_artifacts=[artifact],
                    recommended_rollback_step=checkpoint_step,
                    recommended_repair_step=checkpoint_step,
                ),
            )

    def _resolve_artifact_file(self, working_dir: Path, artifact: str) -> Optional[Path]:
        if artifact == "WD-CTX":
            return working_dir / "ctx.md"
        if artifact == "WD-TASK":
            return working_dir / "task.md"
        exp_match = re.match(r"^WD-EXP-(SLOT-\d+)$", artifact)
        if exp_match:
            return working_dir / "slots" / exp_match.group(1) / "experts.md"
        syn_match = re.match(r"^WD-SYN-(SLOT-\d+)$", artifact)
        if syn_match:
            return working_dir / "slots" / syn_match.group(1) / "synthesis.md"
        if artifact == "WD-EXP-*":
            slots_dir = working_dir / "slots"
            if slots_dir.is_dir():
                for slot_dir in sorted(slots_dir.iterdir()):
                    exp = slot_dir / "experts.md"
                    if exp.exists() and exp.stat().st_size > 0:
                        return exp
            return None
        if artifact in {"WD-SYN", "WD-SYN-LIGHT"}:
            slots_dir = working_dir / "slots"
            if slots_dir.is_dir():
                for slot_dir in sorted(slots_dir.iterdir()):
                    syn = slot_dir / "synthesis.md"
                    if syn.exists() and syn.stat().st_size > 0:
                        return syn
            return None
        return None

    def check_block_state_sync(self, artifact: str, errors: list[dict[str, Any]], step_num: int) -> None:
        draft_path = self.working_draft_path()
        if not draft_path or not draft_path.is_dir():
            return
        target_file = self._resolve_artifact_file(draft_path, artifact)
        present = target_file is not None and target_file.exists() and target_file.stat().st_size > 0
        if not present:
            return

        checkpoint_step = ARTIFACT_REPAIR_STEP.get(artifact, step_num)
        if artifact.startswith("WD-EXP-"):
            checkpoint_step = 9
        elif artifact.startswith("WD-SYN-"):
            checkpoint_step = 10
        checkpoint = self.checkpoint(checkpoint_step, errors)
        expected_field = {
            "WD-CTX": "wd_ctx_written",
            "WD-TASK": "wd_task_written",
        }.get(artifact)
        if artifact.startswith("WD-SYN-"):
            expected_field = "wd_syn_written"
        checkpoint_ok = checkpoint.get(expected_field) is True if expected_field else True
        artifact_ok = artifact in self.state.get("produced_artifacts", [])
        if not artifact_ok or not checkpoint_ok:
            add_issue(
                errors,
                make_issue(
                    code="artifact_state_desync",
                    message=f"步骤 {step_num}: {artifact} 已写入 draft，但 state 未同步",
                    step=step_num,
                                        field="produced_artifacts",
                    missing_artifacts=[artifact],
                    recommended_rollback_step=checkpoint_step,
                    recommended_repair_step=checkpoint_step,
                ),
            )

    def check_task_slots_cover_template(self, errors: list[dict[str, Any]], step_num: int) -> None:
        draft_path = self.working_draft_path()
        if not draft_path or not draft_path.is_dir():
            return
        headings = [item["title"] for item in self.template_headings()]
        task_path = draft_path / "task.md"
        if not task_path.exists():
            return
        content = read_markdown(task_path)
        if not content.strip():
            return
        actual_headings = [normalize_task_heading(title) for title in extract_block_headings(content)]
        if any(title.startswith("CTX-") for title in actual_headings):
            add_issue(
                errors,
                make_issue(
                    code="task_block_structure_invalid",
                    message=f"步骤 {step_num}: WD-TASK 不得混入 CTX 条目",
                    step=step_num,
                                        field="working_draft_path",
                    recommended_rollback_step=8,
                    recommended_repair_step=8,
                ),
            )
        if actual_headings != headings:
            add_issue(
                errors,
                make_issue(
                    code="task_slots_incomplete",
                    message=f"步骤 {step_num}: WD-TASK 必须与模板槽位一一对应且顺序一致",
                    step=step_num,
                                        field="working_draft_path",
                    recommended_rollback_step=8,
                    recommended_repair_step=8,
                    details={"expected_slots": headings, "actual_slots": actual_headings},
                ),
            )

    def check_skip_record(self, skipped_step: int, errors: list[dict[str, Any]], step_num: int) -> None:
        skipped_steps = self.state.get("skipped_steps", [])
        completed_steps = self.state.get("completed_steps", [])
        checkpoint = self.checkpoint(skipped_step, errors)
        has_skip = checkpoint.get("skipped") is True and bool(str(checkpoint.get("reason") or "").strip())
        if (
            not isinstance(skipped_steps, list)
            or skipped_step not in skipped_steps
            or (isinstance(completed_steps, list) and skipped_step in completed_steps)
            or not has_skip
        ):
            add_issue(
                errors,
                make_issue(
                    code="step_skipped_without_checkpoint",
                    message=f"步骤 {step_num}: step-{skipped_step} 跳过时必须显式记录，且不得写入 completed_steps",
                    step=step_num,
                                        field="skipped_steps",
                    recommended_rollback_step=skipped_step,
                    recommended_repair_step=skipped_step,
                ),
            )

    def check_repowiki_consumed(self, errors: list[dict[str, Any]], step_num: int) -> None:
        checkpoint6 = self.checkpoint(6, errors)
        if checkpoint6.get("repowiki_exists") is True and int(checkpoint6.get("repowiki_source_count") or 0) <= 0:
            add_issue(
                errors,
                make_issue(
                    code="repowiki_not_consumed",
                    message=f"步骤 {step_num}: repowiki 已存在但未记录实际消费来源",
                    step=step_num,
                                        field="checkpoints.step-6.repowiki_source_count",
                    recommended_rollback_step=7,
                    recommended_repair_step=7,
                ),
            )

    def check_wd_syn_quality(self, errors: list[dict[str, Any]], step_num: int) -> None:
        draft_path = self.working_draft_path()
        if not draft_path or not draft_path.is_dir():
            return
        slots_dir = draft_path / "slots"
        if not slots_dir.is_dir():
            return
        template_titles = [item["title"] for item in self.template_headings()]
        state_slots = self.state.get("slots") or []
        slot_title_map = {s.get("slot", ""): s.get("title", "") for s in state_slots}
        actual_titles: list[str] = []
        missing: list[str] = []
        for slot_info in state_slots:
            slot_id = slot_info.get("slot", "")
            slot_title = slot_info.get("title", "")
            syn_path = slots_dir / slot_id / "synthesis.md"
            if not syn_path.exists() or syn_path.stat().st_size == 0:
                continue
            actual_titles.append(slot_title)
            slot_content = read_markdown(syn_path)
            if not target_capability_present(slot_content):
                if "#### 目标能力" not in missing:
                    missing.append("#### 目标能力")
            for fragment in missing_wd_syn_slot_fragments(slot_content, slot_title):
                if fragment not in missing:
                    missing.append(fragment)
        if actual_titles != template_titles:
            add_issue(
                errors,
                make_issue(
                    code="wd_syn_slots_incomplete",
                    message=f"步骤 {step_num}: WD-SYN 必须按模板槽位逐项收敛",
                    step=step_num,
                                        field="working_draft_path",
                    missing_artifacts=["WD-SYN"],
                    recommended_rollback_step=10,
                    recommended_repair_step=10,
                    details={"expected_slots": template_titles, "actual_slots": actual_titles},
                ),
            )
        if missing:
            add_issue(
                errors,
                make_issue(
                    code="missing_working_draft_block",
                    message=f"步骤 {step_num}: WD-SYN 缺少最小收敛结构",
                    step=step_num,
                                        field="working_draft_path",
                    missing_artifacts=["WD-SYN"],
                    recommended_rollback_step=10,
                    recommended_repair_step=10,
                    details={"missing_fragments": missing},
                ),
            )

    def check_final_document(self, errors: list[dict[str, Any]], step_num: int) -> None:
        self.check_final_document_path_contract(errors, step_num)
        final_document = self.final_document_path()
        require(
            final_document is not None and final_document.exists(),
            errors,
            code="missing_artifact",
            message=f"步骤 {step_num}: 最终文档不存在",
            step=step_num,
                        field="final_document_path",
            missing_artifacts=["final_document"],
            recommended_rollback_step=11,
            recommended_repair_step=11,
        )
        if not final_document or not final_document.exists():
            return
        template_headings = self.template_headings()
        expected_titles = [item["normalized_title"] for item in template_headings]
        expected_level = template_headings[0]["level"] if template_headings else None
        actual_titles = [
            item["normalized_title"]
            for item in extract_slot_headings(read_markdown(final_document), slot_level=expected_level)
        ]
        if expected_titles != actual_titles:
            add_issue(
                errors,
                make_issue(
                    code="final_document_headings_mismatch",
                    message=f"步骤 {step_num}: 最终文档槽位顺序与模板不一致",
                    step=step_num,
                                        field="final_document_path",
                    recommended_rollback_step=11,
                    recommended_repair_step=11,
                    details={"expected_headings": expected_titles, "actual_headings": actual_titles},
                ),
            )

    def check_final_document_not_premature(self, errors: list[dict[str, Any]], step_num: int) -> None:
        self.check_final_document_path_contract(errors, step_num)
        final_document = self.final_document_path()
        if not final_document or not final_document.exists():
            return
        step10 = self.checkpoint(10, errors)
        completed_at = parse_iso_datetime(step10.get("completed_at"))
        if not completed_at:
            return
        final_doc_mtime = datetime.fromtimestamp(final_document.stat().st_mtime, tz=completed_at.tzinfo)
        if final_doc_mtime < completed_at:
            add_issue(
                errors,
                make_issue(
                    code="step_order_violation",
                    message="步骤 11: 最终文档生成时间早于 step-10 完成时间",
                    step=step_num,
                                        field="final_document_path",
                    recommended_rollback_step=10,
                    recommended_repair_step=10,
                ),
            )

    def common(self, step_num: int, errors: list[dict[str, Any]]) -> None:
        self.check_state_shape(errors, step_num)
        self.check_receipt_integrity(errors, step_num)
        self.check_completed_steps(errors, step_num)
        checkpoint = self.checkpoint(step_num, errors)
        if checkpoint:
            self.check_summary(checkpoint, step_num, errors)
        if step_num >= 2:
            self.check_step1_ready(errors, step_num)
            self.check_solution_root_contract(errors, step_num)
            self.check_final_document_path_contract(errors, step_num)
        if step_num >= 3:
            self.check_prerequisite_files(errors, step_num)
        if step_num >= 4:
            self.check_template_loaded(errors, step_num)
        if step_num >= 7:
            self.check_block_state_sync("WD-CTX", errors, step_num)
        if step_num >= 8:
            self.check_block_state_sync("WD-TASK", errors, step_num)
        if step_num >= 10:
            for slot_info in self.state.get("slots") or []:
                slot_id = slot_info.get("slot", "")
                if slot_id:
                    self.check_block_state_sync(f"WD-SYN-{slot_id}", errors, step_num)

    def step_1(self, errors: list[dict[str, Any]]) -> None:
        self.check_state_shape(errors, 1)
        self.check_completed_steps(errors, 1)

    def step_2(self, errors: list[dict[str, Any]]) -> None:
        self.common(2, errors)
        checkpoint = self.checkpoint(2, errors)
        require(
            checkpoint.get("prerequisites_checked") is True,
            errors,
            code="prerequisites_not_checked",
            message="步骤 2: 前置文件检查未完成",
            step=2,
                        field="checkpoints.step-2.prerequisites_checked",
            recommended_rollback_step=2,
            recommended_repair_step=2,
        )

    def step_3(self, errors: list[dict[str, Any]]) -> None:
        self.common(3, errors)
        self.check_prerequisite_files(errors, 3)

    def step_4(self, errors: list[dict[str, Any]]) -> None:
        self.common(4, errors)
        checkpoint = self.checkpoint(4, errors)
        require(
            checkpoint.get("summary") is not None and str(checkpoint.get("summary") or "").strip() != "",
            errors,
            code="missing_step_summary",
            message="步骤 4: checkpoints.step-4.summary 不能为空",
            step=4,
            field="checkpoints.step-4.summary",
            recommended_rollback_step=4,
            recommended_repair_step=4,
        )

    def step_5(self, errors: list[dict[str, Any]]) -> None:
        self.common(5, errors)
        checkpoint = self.checkpoint(5, errors)
        require(
            checkpoint.get("members_checked") is True and bool(self.selected_members()),
            errors,
            code="missing_selected_members",
            message="步骤 5: 未记录 selected_members",
            step=5,
                        field="checkpoints.step-5.selected_members",
            recommended_rollback_step=5,
            recommended_repair_step=5,
        )

    def step_6(self, errors: list[dict[str, Any]]) -> None:
        self.common(6, errors)
        checkpoint = self.checkpoint(6, errors)
        require(
            checkpoint.get("repowiki_checked") is True,
            errors,
            code="repowiki_not_checked",
            message="步骤 6: repowiki 检测未完成",
            step=6,
                        field="checkpoints.step-6.repowiki_checked",
            recommended_rollback_step=6,
            recommended_repair_step=6,
        )

    def step_7(self, errors: list[dict[str, Any]]) -> None:
        self.common(7, errors)
        self.check_repowiki_consumed(errors, 7)
        require(
            "WD-CTX" in self.state.get("produced_artifacts", []),
            errors,
            code="missing_artifact",
            message="步骤 7: produced_artifacts 缺少 WD-CTX",
            step=7,
                        field="produced_artifacts",
            missing_artifacts=["WD-CTX"],
            recommended_rollback_step=7,
            recommended_repair_step=7,
        )
        require(
            self.state.get("can_enter_step_8") is True,
            errors,
            code="gate_flag_false",
            message="步骤 7: can_enter_step_8 为 false",
            step=7,
            field="can_enter_step_8",
            recommended_rollback_step=7,
            recommended_repair_step=7,
        )
        self.check_working_draft_block("WD-CTX", errors, 7)

    def step_8(self, errors: list[dict[str, Any]]) -> None:
        self.common(8, errors)
        require(
            self.state.get("can_enter_step_8") is True,
            errors,
            code="gate_flag_false",
            message="步骤 8: can_enter_step_8 为 false",
            step=8,
                        field="can_enter_step_8",
            recommended_rollback_step=7,
            recommended_repair_step=7,
        )
        self.check_working_draft_block("WD-CTX", errors, 8)
        self.check_working_draft_block("WD-TASK", errors, 8)
        self.check_task_slots_cover_template(errors, 8)

    def step_9(self, errors: list[dict[str, Any]]) -> None:
        self.common(9, errors)
        require(
            self.state.get("can_enter_step_9") is True,
            errors,
            code="gate_flag_false",
            message="步骤 9: can_enter_step_9 为 false",
            step=9,
                        field="can_enter_step_9",
            recommended_rollback_step=8,
            recommended_repair_step=8,
        )
        self.check_working_draft_block("WD-CTX", errors, 9)
        self.check_working_draft_block("WD-TASK", errors, 9)
        state_slots = self.state.get("slots") or []
        for slot_info in state_slots:
            slot_id = slot_info.get("slot", "")
            if slot_id:
                self.check_working_draft_block(f"WD-EXP-{slot_id}", errors, 9)

    def step_10(self, errors: list[dict[str, Any]]) -> None:
        self.common(10, errors)
        self.check_pending_questions(errors, 10)
        require(
            self.state.get("can_enter_step_10") is True,
            errors,
            code="gate_flag_false",
            message="步骤 10: can_enter_step_10 为 false",
            step=10,
                        field="can_enter_step_10",
            recommended_rollback_step=8,
            recommended_repair_step=8,
        )
        self.check_working_draft_block("WD-CTX", errors, 10)
        self.check_working_draft_block("WD-TASK", errors, 10)
        state_slots = self.state.get("slots") or []
        for slot_info in state_slots:
            slot_id = slot_info.get("slot", "")
            if slot_id:
                self.check_working_draft_block(f"WD-SYN-{slot_id}", errors, 10)
        self.check_wd_syn_quality(errors, 10)

    def step_11(self, errors: list[dict[str, Any]]) -> None:
        self.common(11, errors)
        self.check_pending_questions(errors, 11)
        require(
            self.state.get("can_enter_step_11") is True,
            errors,
            code="gate_flag_false",
            message="步骤 11: can_enter_step_11 为 false",
            step=11,
                        field="can_enter_step_11",
            recommended_rollback_step=10,
            recommended_repair_step=10,
        )
        self.check_working_draft_block("WD-CTX", errors, 11)
        self.check_working_draft_block("WD-TASK", errors, 11)
        state_slots = self.state.get("slots") or []
        for slot_info in state_slots:
            slot_id = slot_info.get("slot", "")
            if slot_id:
                self.check_working_draft_block(f"WD-SYN-{slot_id}", errors, 11)
        self.check_wd_syn_quality(errors, 11)
        self.check_final_document_not_premature(errors, 11)
        checkpoint = self.checkpoint(11, errors)
        final_document_path = self.final_document_path()
        if final_document_path and final_document_path.exists():
            require(
                checkpoint.get("rendered_via_script") is True,
                errors,
                code="final_document_not_rendered_via_script",
                message="步骤 11: 最终文档必须通过 run-step.py 的步骤 11 流程生成",
                step=11,
                                field="checkpoints.step-11.rendered_via_script",
                recommended_rollback_step=11,
                recommended_repair_step=11,
            )

    def step_12(self, errors: list[dict[str, Any]]) -> None:
        self.common(12, errors)
        self.check_pending_questions(errors, 12)
        require(
            self.state.get("can_enter_step_12") is True,
            errors,
            code="gate_flag_false",
            message="步骤 12: can_enter_step_12 为 false",
            step=12,
                        field="can_enter_step_12",
            recommended_rollback_step=11,
            recommended_repair_step=11,
        )
        self.check_working_draft_block("WD-CTX", errors, 12)
        self.check_working_draft_block("WD-TASK", errors, 12)
        self.check_final_document(errors, 12)
        step11 = self.checkpoint(11, errors)
        require(
            step11.get("rendered_via_script") is True,
            errors,
            code="final_document_not_rendered_via_script",
            message="步骤 12: 最终文档必须来自 run-step.py 的步骤 11 成稿流程",
            step=12,
                        field="checkpoints.step-11.rendered_via_script",
            recommended_rollback_step=11,
            recommended_repair_step=11,
        )
        checkpoint = self.checkpoint(12, errors)
        if self.state.get("absorption_check_passed") or self.state.get("cleanup_allowed"):
            require(
                checkpoint.get("validator_passed") is True,
                errors,
                code="cleanup_attempt_before_validation",
                message="步骤 12: cleanup 标志不能先于 validator_passed=true",
                step=12,
                                field="checkpoints.step-12.validator_passed",
                recommended_rollback_step=12,
                recommended_repair_step=12,
            )


def format_issue(issue: dict[str, Any]) -> str:
    lines = [f"  ✗ {issue['message']}", f"    → 建议：{issue['repair_guidance']}"]
    return "\n".join(lines)


def format_issue_with_command(
    issue: dict[str, Any],
    *,
    state_path: Path,
    state: dict[str, Any],
) -> str:
    lines = [f"  ✗ {issue['message']}", f"    → 建议：{issue['repair_guidance']}"]
    repair_step = issue.get("recommended_repair_step")
    if repair_step:
        lines.append(
            "    → 修复命令："
            + render_repair_command(
                state_path=state_path,
                repair_step=repair_step,
                                state=state,
            )
        )
    return "\n".join(lines)


def write_pass_receipt(path: Path, state: dict[str, Any], step: int) -> dict[str, Any]:
    fingerprint = compute_state_fingerprint(state)
    receipt = {
        "step": step,
        "state_fingerprint": fingerprint,
        "validated_at": iso_now(),
    }
    state["gate_receipt"] = receipt
    dump_state(path, state)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="验证 create-technical-solution 状态文件")
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--step", type=int, required=True, help="要校验的步骤号")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="输出格式")
    parser.add_argument("--write-pass-receipt", action="store_true", help="校验通过后写入 gate_receipt")
    args = parser.parse_args()

    state_path = Path(args.state).resolve()
    state = load_state(state_path)
    validator = GateValidator(state, state_path)
    errors: list[dict[str, Any]] = []
    getattr(validator, f"step_{args.step}")(errors)

    if errors:
        payload = {
            "step": args.step,
            "passed": False,
            "summary": build_summary(errors),
            "repair_plan": build_repair_plan(errors, state_path=state_path, state=state),
            "issues": errors,
        }
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"步骤 {args.step} 门禁未通过:")
            for issue in errors:
                print(format_issue_with_command(issue, state_path=state_path, state=state))
        return 2

    payload = {"step": args.step, "passed": True, "summary": {"error_count": 0}}
    if args.write_pass_receipt:
        payload["gate_receipt"] = write_pass_receipt(state_path, state, args.step)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"步骤 {args.step} 门禁通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
