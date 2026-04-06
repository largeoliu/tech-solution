# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""验证 create-technical-solution 状态文件完整性。

供 Agent 在步骤间门控检查时调用，替代人工阅读判断。
检查失败不代表流程终止，而是提示 Agent 先补齐缺失产物或修正状态，再重试验证。

用法：
    uv run scripts/validate-state.py --state <path_to_state_yaml> --step <step_number> [--flow-tier light|moderate|full]

退出码：
    0  — 所有检查通过
    1  — 参数或文件错误
    2  — 门控检查失败（Agent 应先修复再重试）
"""

import argparse
import json
import sys
from pathlib import Path

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


def load_state(path: Path) -> dict:
    if not path.exists():
        print(f"状态文件不存在: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)


def remediation_for_issue(issue: dict) -> str:
    code = issue["code"]
    missing_artifacts = issue.get("missing_artifacts", [])
    field = issue.get("field")

    if code == "missing_artifact":
        artifact = missing_artifacts[0] if missing_artifacts else "未知产物"
        if artifact == "WD-CTX":
            return "先回到步骤 7，生成并写入 WD-CTX，再更新 produced_artifacts。"
        if artifact == "WD-TASK":
            return "先回到步骤 8，生成并写入 WD-TASK，再更新 produced_artifacts。"
        if artifact == "WD-EXP-*":
            return "先确认步骤 5 已落 selected_members，再执行步骤 9 生成 WD-EXP-*。"
        if artifact in {"WD-SYN", "WD-SYN-LIGHT"}:
            return "先执行步骤 10，写入 WD-SYN 或 WD-SYN-LIGHT，再更新 produced_artifacts。"
    if code == "missing_selected_members":
        return "先回到步骤 5 落 selected_members；若为 full 流程，再执行步骤 9 生成 WD-EXP-*。"
    if code == "gate_flag_false":
        return f"检查前一步是否已完成，并正确更新状态文件中的 {field} 字段。"
    if code == "invalid_step_for_tier":
        return "不要重试当前步骤；记录跳过原因，并按当前 flow_tier 进入允许的下一步。"
    if code == "invalid_flow_tier":
        return "检查步骤 4 的 flow_tier 判断，必要时回退到步骤 4 重新分类。"
    if code == "blocked_state":
        return "先根据 block_reason 解除阻塞，修正缺失产物或错误状态后再重试。"
    if code == "absorption_incomplete":
        return "先完成吸收检查并修正未闭合项，再重试步骤 12。"
    if code == "completed_steps_invalid":
        return "修正 completed_steps 与 current_step 的一致性后再重试。"
    return "根据错误条目补齐缺失产物或修正状态文件后重试。"


def make_issue(
    *,
    code: str,
    message: str,
    step: int,
    flow_tier: str,
    field: str | None = None,
    missing_artifacts: list[str] | None = None,
    recommended_rollback_step: int | None = None,
    recommended_repair_step: int | None = None,
    skip_instead_of_retry: bool = False,
) -> dict:
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
    issue["repair_guidance"] = remediation_for_issue(issue)
    return issue


def add_issue(errors: list[dict], issue: dict) -> None:
    errors.append(issue)


def require(
    condition: bool,
    errors: list[dict],
    *,
    code: str,
    message: str,
    step: int,
    flow_tier: str,
    field: str | None = None,
    missing_artifacts: list[str] | None = None,
    recommended_rollback_step: int | None = None,
    recommended_repair_step: int | None = None,
    skip_instead_of_retry: bool = False,
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
        ),
    )


def format_issue(issue: dict) -> str:
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
        (10, "full"): ["WD-CTX", "WD-TASK", "WD-EXP-*"] ,
        (11, "light"): ["WD-CTX", "WD-SYN-LIGHT"],
        (11, "moderate"): ["WD-CTX", "WD-TASK", "WD-SYN"],
        (11, "full"): ["WD-CTX", "WD-TASK", "WD-SYN"],
    }
    return mapping.get((step, flow_tier), [])


class GateValidator:
    def __init__(self, state: dict):
        self.state = state

    def common(self, step_num: int, flow_tier: str, errors: list[dict]) -> None:
        s = self.state
        require(
            s.get("blocked") is False,
            errors,
            code="blocked_state",
            message=f"step-{step_num}: 状态文件标记为阻塞",
            step=step_num,
            flow_tier=flow_tier,
            field="blocked",
        )
        completed = sorted(s.get("completed_steps", []))
        for i, cs in enumerate(completed):
            if cs > step_num:
                require(
                    False,
                    errors,
                    code="completed_steps_invalid",
                    message=f"step-{step_num}: completed_steps[{i}]=step-{cs} 超过当前步骤",
                    step=step_num,
                    flow_tier=flow_tier,
                    field="completed_steps",
                )

    def step_7(self, flow_tier: str, errors: list[dict]) -> None:
        self.common(7, flow_tier, errors)
        s = self.state
        require(
            "WD-CTX" in s.get("produced_artifacts", []),
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
            s.get(gate_field),
            errors,
            code="gate_flag_false",
            message=f"步骤 7: {gate_field} 为 false",
            step=7,
            flow_tier=flow_tier,
            field=gate_field,
            recommended_rollback_step=GATE_REPAIR_STEP[gate_field],
            recommended_repair_step=GATE_REPAIR_STEP[gate_field],
        )

    def step_8(self, flow_tier: str, errors: list[dict]) -> None:
        self.common(8, flow_tier, errors)
        s = self.state
        if flow_tier == "light":
            add_issue(
                errors,
                make_issue(
                    code="invalid_step_for_tier",
                    message="步骤 8: light 流程不应进入此步骤，显式记录跳过",
                    step=8,
                    flow_tier=flow_tier,
                    skip_instead_of_retry=True,
                ),
            )
            return
        require(
            "WD-CTX" in s.get("produced_artifacts", []),
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
            s.get("can_enter_step_8"),
            errors,
            code="gate_flag_false",
            message="步骤 8: can_enter_step_8 为 false",
            step=8,
            flow_tier=flow_tier,
            field="can_enter_step_8",
            recommended_rollback_step=7,
            recommended_repair_step=7,
        )

    def step_9(self, flow_tier: str, errors: list[dict]) -> None:
        self.common(9, flow_tier, errors)
        s = self.state
        if flow_tier in ("light", "moderate"):
            add_issue(
                errors,
                make_issue(
                    code="invalid_step_for_tier",
                    message=f"步骤 9: {flow_tier} 流程不应进入此步骤，显式记录跳过",
                    step=9,
                    flow_tier=flow_tier,
                    skip_instead_of_retry=True,
                ),
            )
            return
        require(
            s.get("flow_tier") == "full",
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
            "WD-CTX" in s.get("produced_artifacts", []),
            errors,
            code="missing_artifact",
            message="步骤 9: 缺少 WD-CTX",
            step=9,
            flow_tier=flow_tier,
            field="produced_artifacts",
            missing_artifacts=["WD-CTX"],
            recommended_rollback_step=7,
            recommended_repair_step=7,
        )
        require(
            "WD-TASK" in s.get("produced_artifacts", []),
            errors,
            code="missing_artifact",
            message="步骤 9: 缺少 WD-TASK",
            step=9,
            flow_tier=flow_tier,
            field="produced_artifacts",
            missing_artifacts=["WD-TASK"],
            recommended_rollback_step=8,
            recommended_repair_step=8,
        )
        require(
            s.get("can_enter_step_9"),
            errors,
            code="gate_flag_false",
            message="步骤 9: can_enter_step_9 为 false",
            step=9,
            flow_tier=flow_tier,
            field="can_enter_step_9",
            recommended_rollback_step=8,
            recommended_repair_step=8,
        )

    def step_10(self, flow_tier: str, errors: list[dict]) -> None:
        self.common(10, flow_tier, errors)
        s = self.state
        require(
            s.get("can_enter_step_10"),
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
            "WD-CTX" in s.get("produced_artifacts", []),
            errors,
            code="missing_artifact",
            message="步骤 10: 缺少 WD-CTX",
            step=10,
            flow_tier=flow_tier,
            field="produced_artifacts",
            missing_artifacts=["WD-CTX"],
            recommended_rollback_step=7,
            recommended_repair_step=7,
        )
        if flow_tier == "light":
            return
        require(
            "WD-TASK" in s.get("produced_artifacts", []),
            errors,
            code="missing_artifact",
            message=f"步骤 10 ({flow_tier}): 缺少 WD-TASK",
            step=10,
            flow_tier=flow_tier,
            field="produced_artifacts",
            missing_artifacts=["WD-TASK"],
            recommended_rollback_step=8,
            recommended_repair_step=8,
        )
        if flow_tier == "full":
            exp_artifacts = [a for a in s.get("produced_artifacts", []) if a.startswith("WD-EXP-")]
            members = s.get("selected_members", [])
            require(
                len(exp_artifacts) > 0 or len(members) == 0,
                errors,
                code="missing_artifact",
                message="步骤 10 (full): 选定了成员但缺少 WD-EXP 产物",
                step=10,
                flow_tier=flow_tier,
                field="produced_artifacts",
                missing_artifacts=["WD-EXP-*"] ,
                recommended_rollback_step=9,
                recommended_repair_step=9,
            )
            require(
                bool(s.get("selected_members")),
                errors,
                code="missing_selected_members",
                message="步骤 10 (full): selected_members 为空",
                step=10,
                flow_tier=flow_tier,
                field="selected_members",
                recommended_rollback_step=5,
                recommended_repair_step=5,
            )

    def step_11(self, flow_tier: str, errors: list[dict]) -> None:
        self.common(11, flow_tier, errors)
        s = self.state
        require(
            s.get("can_enter_step_11"),
            errors,
            code="gate_flag_false",
            message="步骤 11: can_enter_step_11 为 false",
            step=11,
            flow_tier=flow_tier,
            field="can_enter_step_11",
            recommended_rollback_step=10,
            recommended_repair_step=10,
        )
        for artifact in expected_artifacts_for_step(11, flow_tier):
            require(
                artifact in s.get("produced_artifacts", []),
                errors,
                code="missing_artifact",
                message=f"步骤 11 ({flow_tier}): produced_artifacts 缺少 {artifact}",
                step=11,
                flow_tier=flow_tier,
                field="produced_artifacts",
                missing_artifacts=[artifact],
                recommended_rollback_step=ARTIFACT_REPAIR_STEP[artifact],
                recommended_repair_step=ARTIFACT_REPAIR_STEP[artifact],
            )
        if flow_tier == "full":
            require(
                bool(s.get("selected_members")),
                errors,
                code="missing_selected_members",
                message="步骤 11 (full): selected_members 为空",
                step=11,
                flow_tier=flow_tier,
                field="selected_members",
                recommended_rollback_step=5,
                recommended_repair_step=5,
            )

    def step_12(self, flow_tier: str, errors: list[dict]) -> None:
        self.common(12, flow_tier, errors)
        s = self.state
        require(
            s.get("can_enter_step_12"),
            errors,
            code="gate_flag_false",
            message="步骤 12: can_enter_step_12 为 false",
            step=12,
            flow_tier=flow_tier,
            field="can_enter_step_12",
            recommended_rollback_step=11,
            recommended_repair_step=11,
        )
        require(
            s.get("absorption_check_passed"),
            errors,
            code="absorption_incomplete",
            message="步骤 12: absorption_check_passed 为 false",
            step=12,
            flow_tier=flow_tier,
            field="absorption_check_passed",
            recommended_rollback_step=12,
            recommended_repair_step=12,
        )


def build_summary(issues: list[dict]) -> dict:
    rollback_steps = [i["recommended_rollback_step"] for i in issues if i.get("recommended_rollback_step")]
    repair_steps = [i["recommended_repair_step"] for i in issues if i.get("recommended_repair_step")]
    missing_artifacts: list[str] = []
    for issue in issues:
        for artifact in issue.get("missing_artifacts", []):
            if artifact not in missing_artifacts:
                missing_artifacts.append(artifact)
    recommended_repair_sequence = sorted(dict.fromkeys(repair_steps))
    return {
        "error_count": len(issues),
        "recommended_rollback_step": min(rollback_steps) if rollback_steps else None,
        "recommended_repair_sequence": recommended_repair_sequence,
        "missing_artifacts": missing_artifacts,
        "skip_instead_of_retry": any(i.get("skip_instead_of_retry") for i in issues),
    }


def check_field_equals(field: str, value: object, summary: str) -> dict:
    return {
        "type": "field_equals",
        "field": field,
        "expected": value,
        "summary": summary,
    }



def check_field_non_empty(field: str, summary: str) -> dict:
    return {
        "type": "field_non_empty",
        "field": field,
        "summary": summary,
    }



def check_artifact_present(artifact: str, summary: str) -> dict:
    return {
        "type": "artifact_present",
        "artifact": artifact,
        "summary": summary,
    }



def check_artifact_prefix_present(prefix: str, min_count: int, summary: str) -> dict:
    return {
        "type": "artifact_prefix_present",
        "artifact_prefix": prefix,
        "min_count": min_count,
        "summary": summary,
    }



def completion_checks_for_issue(issue: dict) -> list[dict]:
    checks: list[dict] = []
    code = issue.get("code")
    field = issue.get("field")

    if code == "missing_artifact":
        for artifact in issue.get("missing_artifacts", []):
            if artifact.endswith("*"):
                checks.append(
                    check_artifact_prefix_present(
                        artifact.removesuffix("*"),
                        1,
                        f"至少存在 1 个 {artifact} 产物",
                    )
                )
            else:
                checks.append(check_artifact_present(artifact, f"{artifact} 已生成"))
            if artifact == "WD-TASK":
                checks.append(check_field_equals("can_enter_step_10", True, "can_enter_step_10 已为 true"))
            elif artifact in {"WD-SYN", "WD-SYN-LIGHT"}:
                checks.append(check_field_equals("can_enter_step_11", True, "can_enter_step_11 已为 true"))
    elif code == "missing_selected_members":
        checks.append(check_field_non_empty("selected_members", "selected_members 已写入状态文件且非空"))
    elif code == "gate_flag_false" and field:
        checks.append(check_field_equals(field, True, f"{field} 已为 true"))
    elif code == "invalid_flow_tier":
        checks.append(check_field_equals("flow_tier", issue.get("flow_tier"), "flow_tier 已与当前步骤要求一致"))
    elif code == "blocked_state":
        checks.append(check_field_equals("blocked", False, "blocked 已为 false"))
    elif code == "absorption_incomplete":
        checks.append(check_field_equals("absorption_check_passed", True, "absorption_check_passed 已为 true"))
        checks.append(check_field_equals("cleanup_allowed", True, "cleanup_allowed 已为 true"))
    elif code == "completed_steps_invalid":
        checks.append({
            "type": "custom",
            "summary": "completed_steps 与 current_step 已恢复一致",
        })
        checks.append({
            "type": "custom",
            "summary": "completed_steps 无跳号、无越级完成",
        })

    if not checks and field:
        checks.append({
            "type": "custom",
            "summary": f"{field} 已修正为通过当前步骤门禁所需状态",
        })
    if not checks:
        checks.append({
            "type": "custom",
            "summary": "相关状态与产物已修正，且再次验证不再报该问题",
        })
    return checks



def merge_completion_check(item: dict, check: dict) -> None:
    if check not in item["completion_checks"]:
        item["completion_checks"].append(check)



def build_retry_command(step: int, issue: dict) -> dict:
    flow_tier = issue.get("flow_tier", "full")
    command = "python scripts/validate-state.py"
    args = [
        "--state",
        "<状态文件路径>",
        "--step",
        str(step),
        "--flow-tier",
        flow_tier,
        "--format",
        "json",
    ]
    return {
        "command": command,
        "args": args,
        "format": "json",
        "target_step": step,
        "flow_tier": flow_tier,
        "display": f"{command} {' '.join(args)}",
    }



def action_types_for_issue(issue: dict) -> list[str]:
    action_types: list[str] = []
    if issue.get("missing_artifacts"):
        action_types.append("generate_artifact")
    if issue.get("field"):
        action_types.append("update_state")
    if issue.get("code") == "invalid_step_for_tier":
        action_types.append("skip_step")
    if issue.get("recommended_repair_step"):
        action_types.append("rerun_validation")
    return action_types or ["investigate"]



def state_patch_hints_for_issue(issue: dict) -> list[dict]:
    hints: list[dict] = []
    code = issue.get("code")
    field = issue.get("field")

    if code == "gate_flag_false" and field:
        hints.append({
            "field": field,
            "operation": "set",
            "value": True,
            "summary": f"将 {field} 置为 true",
        })
    elif code == "missing_selected_members":
        hints.append({
            "field": "selected_members",
            "operation": "set_non_empty",
            "value": "<来自步骤 5 的参与成员列表>",
            "summary": "写入非空 selected_members",
        })
    elif code == "invalid_flow_tier":
        hints.append({
            "field": "flow_tier",
            "operation": "set",
            "value": issue.get("flow_tier"),
            "summary": "修正 flow_tier 与当前步骤要求一致",
        })
    elif code == "blocked_state":
        hints.append({
            "field": "blocked",
            "operation": "set",
            "value": False,
            "summary": "解除阻塞标记",
        })
    elif code == "absorption_incomplete":
        hints.append({
            "field": "absorption_check_passed",
            "operation": "set",
            "value": True,
            "summary": "吸收检查通过后置为 true",
        })
        hints.append({
            "field": "cleanup_allowed",
            "operation": "set",
            "value": True,
            "summary": "允许清理时置为 true",
        })
    elif code == "missing_artifact" and field == "produced_artifacts":
        for artifact in issue.get("missing_artifacts", []):
            hints.append({
                "field": "produced_artifacts",
                "operation": "append_unique",
                "value": artifact,
                "summary": f"将 {artifact} 追加到 produced_artifacts",
            })
    elif field:
        hints.append({
            "field": field,
            "operation": "update",
            "value": None,
            "summary": f"按当前问题修正 {field}",
        })
    return hints



def merge_state_patch_hint(item: dict, hint: dict) -> None:
    if hint not in item["state_patch_hint"]:
        item["state_patch_hint"].append(hint)



def artifact_write_hints_for_issue(issue: dict) -> list[dict]:
    hints: list[dict] = []
    if issue.get("code") != "missing_artifact":
        return hints

    for artifact in issue.get("missing_artifacts", []):
        target = "working_draft"
        write_mode = "append_section"
        block = artifact
        if artifact in {"WD-SYN", "WD-SYN-LIGHT"}:
            block = artifact
        elif artifact == "WD-CTX":
            block = "WD-CTX"
        elif artifact == "WD-TASK":
            block = "WD-TASK"
        elif artifact == "WD-EXP-*":
            block = "WD-EXP-*"
        hints.append({
            "artifact": artifact,
            "target": target,
            "block": block,
            "write_mode": write_mode,
            "status_sync_field": "produced_artifacts",
            "status_sync_operation": "append_unique",
            "summary": f"将 {artifact} 写入 working draft，并同步到 produced_artifacts",
        })
    return hints



def merge_artifact_write_hint(item: dict, hint: dict) -> None:
    if hint not in item["artifact_write_hint"]:
        item["artifact_write_hint"].append(hint)



def working_draft_context_hints_for_issue(issue: dict) -> list[dict]:
    hints: list[dict] = []
    if issue.get("code") != "missing_artifact":
        return hints

    flow_tier = issue.get("flow_tier", "full")
    for artifact in issue.get("missing_artifacts", []):
        required_blocks: list[str] = []
        external_inputs: list[str] = []
        forbidden_blocks: list[str] = []
        summary = ""

        if artifact == "WD-CTX":
            external_inputs = ["repo_inputs", "members_yml", "principles_md", "current_template"]
            forbidden_blocks = ["WD-TASK", "WD-EXP-*", "WD-SYN", "WD-SYN-LIGHT"]
            summary = "生成 WD-CTX 时只消费外部输入与当前模板，不得预支下游 WD-* 区块"
        elif artifact == "WD-TASK":
            required_blocks = ["WD-CTX"]
            external_inputs = ["current_template"]
            forbidden_blocks = ["WD-EXP-*", "WD-SYN", "WD-SYN-LIGHT"]
            summary = "生成 WD-TASK 时仅消费当前模板与已落盘 WD-CTX，不得预支下游收敛结论"
        elif artifact == "WD-EXP-*":
            required_blocks = ["WD-CTX", "WD-TASK"]
            external_inputs = ["selected_members"]
            forbidden_blocks = ["WD-SYN", "WD-SYN-LIGHT"]
            summary = "生成 WD-EXP-* 时仅消费已落盘 WD-CTX、WD-TASK 与已选成员，不得预支收敛结果"
        elif artifact in {"WD-SYN", "WD-SYN-LIGHT"}:
            required_blocks = ["WD-CTX"]
            if flow_tier in {"moderate", "full"}:
                required_blocks.append("WD-TASK")
            if flow_tier == "full":
                required_blocks.append("WD-EXP-*")
            external_inputs = ["current_template"]
            forbidden_blocks = ["final_document"]
            summary = "生成收敛区块时仅消费已落盘上游 WD-* 与当前模板，不得以最终文档替代中间产物"
        else:
            summary = f"生成 {artifact} 时仅消费已落盘稳定区块，不得预支下游结论"

        hints.append({
            "artifact": artifact,
            "required_blocks": required_blocks,
            "external_inputs": external_inputs,
            "forbidden_blocks": forbidden_blocks,
            "summary": summary,
        })
    return hints



def merge_working_draft_context_hint(item: dict, hint: dict) -> None:
    if hint not in item["working_draft_context_hint"]:
        item["working_draft_context_hint"].append(hint)



def build_repair_plan(issues: list[dict]) -> list[dict]:
    plan_by_step: dict[int, dict] = {}
    for issue in issues:
        step = issue.get("recommended_repair_step")
        if not step or issue.get("skip_instead_of_retry"):
            continue
        if step not in plan_by_step:
            plan_by_step[step] = {
                "step": step,
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
                "retry_command": build_retry_command(issue.get("step", step), issue),
                "retry_validation": True,
            }
        item = plan_by_step[step]
        for artifact in issue.get("missing_artifacts", []):
            if artifact and artifact not in item["generate_artifacts"]:
                item["generate_artifacts"].append(artifact)
        field = issue.get("field")
        if field and field not in item["fix_fields"]:
            item["fix_fields"].append(field)
        code = issue.get("code")
        if code and code not in item["issues"]:
            item["issues"].append(code)
        guidance = issue.get("repair_guidance")
        if guidance and guidance not in item["guidance"]:
            item["guidance"].append(guidance)
        for action_type in action_types_for_issue(issue):
            if action_type not in item["action_types"]:
                item["action_types"].append(action_type)
        for hint in state_patch_hints_for_issue(issue):
            merge_state_patch_hint(item, hint)
        for hint in artifact_write_hints_for_issue(issue):
            merge_artifact_write_hint(item, hint)
        for hint in working_draft_context_hints_for_issue(issue):
            merge_working_draft_context_hint(item, hint)
        for check in completion_checks_for_issue(issue):
            merge_completion_check(item, check)
    ordered_steps = sorted(plan_by_step)
    for index, step in enumerate(ordered_steps):
        plan_by_step[step]["depends_on_steps"] = ordered_steps[:index]
    return [plan_by_step[step] for step in ordered_steps]


def build_state_snapshot(state: dict) -> dict:
    return {
        "current_step": state.get("current_step"),
        "completed_steps": state.get("completed_steps", []),
        "required_artifacts": state.get("required_artifacts", []),
        "produced_artifacts": state.get("produced_artifacts", []),
        "selected_members": state.get("selected_members", []),
        "blocked": state.get("blocked"),
        "block_reason": state.get("block_reason"),
        "can_enter_step_8": state.get("can_enter_step_8"),
        "can_enter_step_9": state.get("can_enter_step_9"),
        "can_enter_step_10": state.get("can_enter_step_10"),
        "can_enter_step_11": state.get("can_enter_step_11"),
        "can_enter_step_12": state.get("can_enter_step_12"),
        "absorption_check_passed": state.get("absorption_check_passed"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="验证 create-technical-solution 状态文件")
    parser.add_argument("--state", required=True, help="状态文件 YAML 路径")
    parser.add_argument("--step", type=int, required=True, help="当前步骤号 (7-12)")
    parser.add_argument("--flow-tier", choices=["light", "moderate", "full"], default="full", help="流程级别")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    args = parser.parse_args()

    state = load_state(Path(args.state))
    issues: list[dict] = []

    validator = GateValidator(state)
    dispatch = {
        7: validator.step_7,
        8: validator.step_8,
        9: validator.step_9,
        10: validator.step_10,
        11: validator.step_11,
        12: validator.step_12,
    }

    if args.step not in dispatch:
        print(f"不支持验证步骤 {args.step}。仅支持 7-12 的门控检查。", file=sys.stderr)
        sys.exit(1)

    dispatch[args.step](args.flow_tier, issues)

    if args.format == "json":
        result = {
            "step": args.step,
            "flow_tier": args.flow_tier,
            "passed": len(issues) == 0,
            "summary": build_summary(issues),
            "repair_plan": build_repair_plan(issues),
            "state_snapshot": build_state_snapshot(state),
            "issues": issues,
        }
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
