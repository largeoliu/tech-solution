# create-technical-solution 参考

> SKILL.md 已触发时，按需加载本文件中的详细参考。

## 产物 Schema 速查

- 所有 `WD-*` 都是 **working draft 目录内的稳定文件**，状态文件中的 `produced_artifacts` 仅表示这些文件已经落盘到 `working_draft_path` 目录。
- `solution_root` 固定采用双读单写策略：兼容读取历史 `.architecture/solutions/`，但新 working draft 统一写入 `.architecture/.state/create-technical-solution/[slug]/`，最终文档统一写入 `.architecture/technical-solutions/`。
- `meta.yaml` 只保留流程控制字段、路径字段、gate flags、最小 checkpoint 与 cleanup 状态；不得承载正文。
- `checkpoints.step-N.summary` 只能写单行流程摘要，不得复述 CTX、专家分析、收敛结论或详细设计正文。

- **共享上下文（WD-CTX）**：默认只保留 `上下文编号`、`来源`、`结论或约束`、`适用槽位`、`可信度或缺口`（必填）；仅当涉及新增、拆分、迁移、平行建设或职责转移时，才补充 `资产类型`、`资产标识`、`位置`、`当前职责`、`当前能力`、`可扩展点`、`已知限制`、`调用方/依赖方`、`相关证据路径`；若结论为"未发现候选"，还必须补 `搜索范围`、`搜索关键词`、`已排除目录或对象`、`未发现结论`
- **模板任务单（WD-TASK）**：只保留 `槽位标识`、`必须消费的共享上下文`、`参与专家`、`每位专家必答问题`、`建议落位槽位`、`落位表达要求`、`缺口或阻塞项`（必填）；不重复抄写 CTX 事实详情，统一通过 CTX 编号引用
- **专家分析（WD-EXP-SLOT-*）**：默认只保留 `参与槽位`、`决策类型`、`核心理由`、`关键证据引用`、`未决点`（必填）；每个槽位文件内再按专家小节展开；仅 `新建` 时强制补充不可复用 / 不可改造证据说明
- **协作收敛（WD-SYN-SLOT-*）**：
  `目标能力`、`候选方案对比`、`选定路径`、`选定写法`、`关键证据引用`、`建议落位槽位`、`模板承载缺口`、`未决问题`
- **变更影响（WD-IMPACT）**：`触发变更`、`受影响内容`、`受影响阶段边界`、`保持有效内容`、`作废内容或标记`、`下一步动作`（必填）

## WD-SYN-SLOT-* 示例

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
FULL checkpoint.step-8 摘要示例：
`完成；写入 WD-TASK；slots=5；gate: step-9 ready`

FULL checkpoint.step-9 摘要示例：
`完成；写入 WD-EXP-SLOT-*；slots=5；gate: step-10 ready`

FULL checkpoint.step-10 摘要示例：
`完成；写入 WD-SYN-SLOT-*；slots=5；gate: step-11 ready`
```

## 结果汇报格式

```text
技术方案已创建或更新：[标题]
位置：.architecture/technical-solutions/[文件名].md
参与成员：[参与成员]
过程可见产物：working draft 1 份；模板槽位数 [n]；CTX 条目数 [n]；WD-TASK 条目数 [n]；WD-EXP-SLOT 数量 [n]；WD-SYN-SLOT 数量 [n]
关键点：[3-5 个核心槽位结论]
吸收检查：[通过|未通过]；仅在通过后删除 working draft 和状态文件。
```

## 验证脚本

对外使用时，步骤 1-12 都应先通过 `run-step.py` 查看当前门禁与修复建议：

```bash
python /path/to/run-step.py --state <状态文件路径>
```

`run-step.py` 内部会调用 validator；若门禁失败，不应结束流程，而应先补齐缺失的 working draft 区块、修正状态字段或重建最终文档，再重新检查。

标准主路径优先使用：

```bash
python /path/to/run-step.py --state <状态文件路径> --advance
```

`--advance` 会根据当前步骤自动推进：

- 空状态时自动初始化步骤 1，并返回 `business_task`、`required_output_shape`、`next_action`
- 自动步骤（2、3、6、11、12）在一次调用内完成
- 业务决策步骤（1、4、5）会自动完成 entry，并在返回 payload 中给出 `business_task`、`required_output_shape`、`next_action`
- 创作步骤（7、8、9、10）会自动完成 entry，并在返回 payload 中给出 `artifact`、`business_task`、`required_output_shape`、`next_action`

只有业务决策步骤或创作步骤真正提交正文时，才使用显式提交：

```bash
python /path/to/run-step.py --state <状态文件路径> --complete --ticket <ticket> --summary "..."
```

此时的 `ticket` 来自前一次 `--advance` 返回或写入的 `pending_ticket`。若发 ticket 后 state、working draft、final document 或提交 block 范围发生变化，旧 ticket 会失效，必须重新执行 `--advance`。

`--prepare`、`--mark-step-card-read` 属于低层接口，仅保留给测试、内部调试和兼容路径，不再作为主流程说明。

若需要调试或测试内部 validator，可直接运行 `validate-state.py --format json`，但这属于内部诊断接口，不是公开执行入口。

### validate-state.py JSON contract（当前实现）

- **失败 payload** 顶层键：`step`、`passed`、`summary`、`repair_plan`、`issues`
- **通过 payload** 顶层键：`step`、`passed`、`summary`
- 仅当传入 `--write-pass-receipt` 时，通过 payload 才会额外包含 `gate_receipt`

`summary`（由 `build_summary(...)` 生成）当前包含：
- `summary.error_count`
- `summary.recommended_rollback_step`
- `summary.recommended_repair_sequence`
- `summary.missing_artifacts`
- `summary.skip_instead_of_retry`

`repair_plan`（由 `build_repair_plan(...)` 生成）当前每项字段：
- `repair_plan[].step`
- `repair_plan[].action_type`
- `repair_plan[].script_command`
- `repair_plan[].depends_on_steps`
- `repair_plan[].expected_artifacts_after_fix`
- `repair_plan[].revalidate_step`

`issues[*]` 继续沿用 `make_issue(...)` 产出的标准字段，并包含 `issues[*].repair_guidance`。

Agent 收到失败 JSON 后，优先消费 `repair_plan[]` 与 `summary.recommended_repair_sequence`，再结合 `summary.recommended_rollback_step`、`summary.missing_artifacts`、`summary.skip_instead_of_retry` 与 `issues[*].repair_guidance` 做修复。

### run-step.py --emit-scaffold

- `python /path/to/run-step.py --state <状态文件路径> --emit-scaffold`
- 只读辅助入口：仅向 `stdout` 输出当前步骤 scaffold
- 不是第二条写入路径
- 不修改 state
- 不修改 working draft
- 不修改 receipt
- `--emit-scaffold 与 --complete 不能同时使用`；同理也不能与 `--advance` 或 `--prepare` 同时使用
- scaffold 步骤选择遵循当前 auto-skip 语义（`light` 的 8/9/10、`moderate` 的 9/10 会映射到 step-10 scaffold）

### runtime_doctor.py（运行时修复助手）

- `runtime_doctor.py` 是运行时 repair helper，不是主执行路径；主路径仍是 `run-step.py`
- 默认 `dry-run`，仅诊断和给出 `safe_fixes` 计划
- 只有显式传 `--apply-safe-fixes` 才会修改文件
- safe fixes 仅限结构性修复：规范目录创建、旧 working draft 路径/状态迁移、以及仅在语义安全时的 receipt 修复

`runtime_doctor.py --format json` 当前 payload 顶层键：
- `step`
- `apply_safe_fixes`
- `passed`
- `summary`
- `issues`
- `repair_plan`
- `safe_fixes`
- `state_path`
- `mutated`
