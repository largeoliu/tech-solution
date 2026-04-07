# create-technical-solution 参考

> SKILL.md 已触发时，按需加载本文件中的详细参考。

## 产物 Schema 速查

- 所有 `WD-*` 都是 **working draft 内的稳定区块**，不是独立文件名约定。状态文件中的 `produced_artifacts` 仅表示这些区块已经落盘到 `working_draft_path`。
- `solution_root` 固定采用双读单写策略：兼容读取历史 `.architecture/solutions/`，但新 working draft 和最终文档统一写入 `.architecture/technical-solutions/`。

- **共享上下文（WD-CTX）**：默认只保留 `上下文编号`、`来源`、`结论或约束`、`适用槽位`、`可信度或缺口`（必填）；仅当涉及新增、拆分、迁移、平行建设或职责转移时，才补充 `资产类型`、`资产标识`、`位置`、`当前职责`、`当前能力`、`可扩展点`、`已知限制`、`调用方/依赖方`、`相关证据路径`；若结论为"未发现候选"，还必须补 `搜索范围`、`搜索关键词`、`已排除目录或对象`、`未发现结论`
- **模板任务单（WD-TASK）**：只保留 `槽位标识`、`必须消费的共享上下文`、`参与专家`、`每位专家必答问题`、`建议落位槽位`、`落位表达要求`、`缺口或阻塞项`（必填）；不重复抄写 CTX 事实详情，统一通过 CTX 编号引用
- **专家分析（WD-EXP-*）**：默认只保留 `参与槽位`、`决策类型`、`核心理由`、`关键证据引用`、`未决点`（必填）；仅 `新建` 时强制补充不可复用 / 不可改造证据说明
- **协作收敛（WD-SYN / WD-SYN-LIGHT）**：
  - `light`：`目标能力`、`候选路径对比`、`选定路径`、`关键证据`、`建议落位槽位`、`未决问题或阻塞`
  - `moderate` / `full`：`目标能力`、`候选方案对比`、`选定路径`、`选定写法`、`关键证据引用`、`建议落位槽位`、`模板承载缺口`、`未决问题`
- **变更影响（WD-IMPACT）**：`触发变更`、`受影响内容`、`受影响阶段边界`、`保持有效内容`、`作废内容或标记`、`下一步动作`（必填）

## WD-SYN示例

### 示例1：数据方案收敛

#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | 现有spotRules字段不支持违规类型比例配置 | 无法满足需求 |
| 改造 | ✅ | spotRules为JSON字段，可扩展结构 | 向后兼容，无需改表 |
| 新建 | ❌ | 新增字段需改表，影响范围大 | 成本过高 |

#### 选定路径
- **路径**：改造
- **理由**：扩展JSON结构即可满足需求，向后兼容，无需改表
- **关键证据引用**：CTX-03, CTX-05

### 示例2：服务层改造收敛

#### 候选方案对比
| 路径 | 可行性 | 关键证据 | 选择理由 |
|------|--------|----------|----------|
| 复用 | ❌ | 现有calcSpotNumber()只支持按数量抽取 | 无法满足按比例抽取需求 |
| 改造 | ✅ | 可在现有方法中增加策略分发逻辑 | 向后兼容，代码复用度高 |
| 新建 | ❌ | 新建方法会导致代码重复 | 维护成本高 |

#### 选定路径
- **路径**：改造
- **理由**：在现有方法中增加策略分发，既满足新需求又保持向后兼容
- **关键证据引用**：CTX-07, CTX-08

## 最小执行示例

```text
LIGHT checkpoint.step-10 摘要示例：
- 新增区块：WD-SYN-LIGHT
- 消费输入：WD-CTX
- 新增条目数：SLOT-01 ~ SLOT-03 共 3 条轻量收敛
- 下一步门控：WD-CTX、WD-SYN-LIGHT 已齐备，可进入 step-11

MODERATE checkpoint.step-8 摘要示例：
- 新增区块：WD-TASK
- 消费输入：WD-CTX、模板结构快照
- 新增条目数：SLOT-01 ~ SLOT-05 共 5 条任务单
- 下一步门控：WD-TASK 已落盘，可进入 step-10

FULL checkpoint.step-9 摘要示例：
- 新增区块：WD-EXP-systems_architect、WD-EXP-domain_expert
- 消费输入：当前槽位任务单、相关 CTX、当前槽位前序摘要
- 新增条目数：SLOT-02 共 2 位专家判断片段
- 下一步门控：当前需要专家判断的槽位均已具备 WD-EXP 片段，可进入 step-10
```

## 结果汇报格式

```text
技术方案已创建或更新：[标题]
位置：.architecture/technical-solutions/[文件名].md
流程级别：[light|moderate|full]
参与成员：[参与成员]
过程可见产物：working draft 1 份；模板槽位数 [n]；CTX 条目数 [n]；WD-TASK 条目数 [n/如跳过写 0]；WD-EXP 数量 [n/如跳过写 0]；WD-SYN 或 WD-SYN-LIGHT 数量 [n]
关键点：[3-5 个核心槽位结论]
吸收检查：[通过|未通过]；仅在通过后删除 working draft 和状态文件。
```

## 验证脚本

步骤 1-12 进入前必须调用验证脚本：

```bash
python scripts/validate-state.py --state <状态文件路径> --step <1-12> --flow-tier <light|moderate|full>
```

退出码：0=通过，2=门控检查失败（详见 stderr 输出与修复建议）。
Agent 收到退出码 2 后，不应结束流程，而应先补齐缺失的 working draft 区块、修正状态字段或重建最终文档，再重新运行验证。
也支持 `--format json` 输出结构化结果。

### JSON 输出 contract

`--format json` 返回以下顶层字段：
- `step`
- `flow_tier`
- `passed`
- `summary`
- `repair_plan`
- `state_snapshot`
- `issues`

其中 Agent 应优先消费：
- `repair_plan[]`
- `repair_plan[].depends_on_steps`
- `repair_plan[].completion_checks`
- `repair_plan[].retry_command`
- `summary.recommended_repair_sequence`
- `summary.recommended_rollback_step`
- `summary.missing_artifacts`
- `summary.skip_instead_of_retry`
- `issues[*].repair_guidance`
- `issues[*].recommended_repair_step`

#### Repair contract

`repair_plan[]` 是校验失败后的主修复协议，建议按以下顺序消费：
1. `action_types`：先判断本项属于生成产物、更新状态、跳步还是重跑校验
2. `depends_on_steps`：确认前置修复项是否已闭合
3. `state_patch_hint`：按建议更新状态字段
4. `artifact_write_hint`：按建议落盘缺失产物
5. `working_draft_context_hint`：仅消费允许的上游稳定区块与外部输入
6. `completion_checks`：确认本修复项已经闭合
7. `retry_command`：重跑校验

字段速查：
- `action_types`：动作类别；当前支持 `generate_artifact`、`update_state`、`skip_step`、`rerun_validation`、`investigate`
- `depends_on_steps`：前置修复步骤
- `generate_artifacts`：本项应补齐的产物名
- `fix_fields`：本项涉及的状态字段
- `state_patch_hint`：状态字段补丁建议；`operation` 支持 `set`、`set_non_empty`、`append_unique`、`update`
- `artifact_write_hint`：产物落盘提示；包含 `artifact`、`target`、`block`、`write_mode`、`status_sync_field`、`status_sync_operation`、`summary`
- `working_draft_context_hint`：生成产物时允许消费的 `required_blocks`、`external_inputs` 与禁止预支的 `forbidden_blocks`
- `completion_checks`：修复闭合检查；`type` 支持 `field_equals`、`field_non_empty`、`artifact_present`、`artifact_prefix_present`、`custom`
- `retry_command`：结构化重试命令；包含 `command`、`args`、`format`、`target_step`、`flow_tier`、`display`
- `retry_validation`：是否应在修复后立即重跑校验

示例：

```json
{
  "step": 10,
  "flow_tier": "full",
  "passed": false,
  "summary": {
    "error_count": 2,
    "recommended_rollback_step": 8,
    "recommended_repair_sequence": [8, 9],
    "missing_artifacts": ["WD-TASK", "WD-EXP-*"]
  },
  "repair_plan": [
    {
      "step": 8,
      "action_types": ["generate_artifact", "update_state", "rerun_validation"],
      "depends_on_steps": [],
      "generate_artifacts": ["WD-TASK"],
      "fix_fields": ["produced_artifacts"],
      "state_patch_hint": [
        {
          "field": "produced_artifacts",
          "operation": "append_unique",
          "value": "WD-TASK",
          "summary": "将 WD-TASK 追加到 produced_artifacts"
        }
      ],
      "artifact_write_hint": [
        {
          "artifact": "WD-TASK",
          "target": "working_draft",
          "block": "WD-TASK",
          "write_mode": "append_section",
          "status_sync_field": "produced_artifacts",
          "status_sync_operation": "append_unique",
          "summary": "将 WD-TASK 写入 working draft，并同步到 produced_artifacts"
        }
      ],
      "working_draft_context_hint": [
        {
          "artifact": "WD-TASK",
          "required_blocks": ["WD-CTX"],
          "external_inputs": ["current_template"],
          "forbidden_blocks": ["WD-EXP-*", "WD-SYN", "WD-SYN-LIGHT"],
          "summary": "生成 WD-TASK 时仅消费当前模板与已落盘 WD-CTX，不得预支下游收敛结论"
        }
      ],
      "issues": ["missing_artifact"],
      "guidance": ["先回到步骤 8，生成并写入 WD-TASK，再更新 produced_artifacts。"],
      "completion_checks": [
        {
          "type": "artifact_present",
          "artifact": "WD-TASK",
          "summary": "WD-TASK 已生成"
        },
        {
          "type": "field_equals",
          "field": "can_enter_step_10",
          "expected": true,
          "summary": "can_enter_step_10 已为 true"
        }
      ],
      "retry_command": {
        "command": "python scripts/validate-state.py",
        "args": ["--state", "<状态文件路径>", "--step", "10", "--flow-tier", "full", "--format", "json"],
        "format": "json",
        "target_step": 10,
        "flow_tier": "full",
        "display": "python scripts/validate-state.py --state <状态文件路径> --step 10 --flow-tier full --format json"
      },
      "retry_validation": true
    }
  ],
  "issues": [
    {
      "code": "missing_artifact",
      "message": "步骤 10 (full): 缺少 WD-TASK",
      "missing_artifacts": ["WD-TASK"],
      "recommended_rollback_step": 8,
      "recommended_repair_step": 8,
      "repair_guidance": "先回到步骤 8，生成并写入 WD-TASK，再更新 produced_artifacts。"
    }
  ]
}
```

Agent 收到 JSON 失败结果后，应优先按上面的 repair contract 顺序消费 `repair_plan[]`，而不是只解析 stderr 文本；若仍需细化，再结合 `issues` 和 `summary` 补充判断。
