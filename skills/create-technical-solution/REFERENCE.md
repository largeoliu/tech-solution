# create-technical-solution 参考

> SKILL.md 已触发时，按需加载本文件中的详细参考。

## 产物 Schema 速查

- 所有 `WD-*` 都是 **working draft 目录内的稳定文件**，状态文件中的 `produced_artifacts` 仅表示这些文件已经落盘到 `working_draft_path` 目录。
- `solution_root` 固定采用双读单写策略：兼容读取历史 `.architecture/solutions/`，但新 working draft 统一写入 `.architecture/.state/create-technical-solution/[slug]/`，最终文档统一写入 `.architecture/technical-solutions/`。
- `meta.yaml` 只保留流程控制字段、路径字段、gate flags、最小 checkpoint 与 cleanup 状态；不得承载正文。
- `checkpoints.step-N.summary` 只能写单行流程摘要，不得复述 CTX、专家分析、收敛结论或详细设计正文。
- step 7/8/9/10 的 canonical 输入格式是 **结构化 JSON payload**，Markdown 只作为脚本渲染产物落到 working draft。

- **共享上下文（WD-CTX）**：默认只保留 `上下文编号`、`来源`、`结论或约束`、`适用槽位`、`可信度或缺口`（必填）；仅当涉及新增、拆分、迁移、平行建设或职责转移时，才补充 `资产类型`、`资产标识`、`位置`、`当前职责`、`当前能力`、`可扩展点`、`已知限制`、`调用方/依赖方`、`相关证据路径`；若结论为"未发现候选"，还必须补 `搜索范围`、`搜索关键词`、`已排除目录或对象`、`未发现结论`
- **模板任务单（WD-TASK）**：只保留 `槽位标识`、`必须消费的共享上下文`、`参与专家`、`每位专家必答问题`、`建议落位槽位`、`落位表达要求`、`缺口或阻塞项`（必填）；不重复抄写 CTX 事实详情，统一通过 CTX 编号引用
- **专家分析（WD-EXP-SLOT-*）**：默认只保留 `参与槽位`、`决策类型`、`核心理由`、`关键证据引用`、`未决点`（必填）；每个槽位文件内再按专家小节展开；仅 `新建` 时强制补充不可复用 / 不可改造证据说明
- **协作收敛（WD-SYN-SLOT-*）**：
  `目标能力`、`候选方案对比`、`选定路径`、`选定写法`、`关键证据引用`、`建议落位槽位`、`模板承载缺口`、`未决问题`
  其中 `选定写法` 支持多段落 Markdown，是最终技术方案该槽位正文的直接来源，应写完该槽位需要的全部正式内容；`候选方案对比`、`关键证据引用`、`模板承载缺口`、`未决问题` 仅保留在 working draft 中，不进入最终技术方案文档

## 结构化提交示例

### Step 7: WD-CTX payload

```json
[
  {
    "id": "CTX-01",
    "source": "services/a.py, models/a.py",
    "conclusion": "需求概述沿用现有入口。",
    "applicable_slots": ["1.1 需求概述", "1.2 核心目标"],
    "confidence": "已验证"
  },
  {
    "id": "CTX-02",
    "source": "services/order_service.go, services/payment_service.go",
    "conclusion": "现有订单服务不支持按比例抽取，需新增 SpotCheckService。",
    "applicable_slots": ["2.1 方案设计"],
    "confidence": "已验证",
    "asset_type": "领域服务",
    "asset_id": "SpotCheckService",
    "location": "services/spot_check/",
    "current_duty": "当前仅支持按数量抽取",
    "current_capability": "抽取规则固定，不可配置",
    "extensibility": "可通过扩展配置实现比例配置",
    "known_limits": "不支持动态比例调整，需改表",
    "callers_deps": "OrderService(调用方)",
    "evidence_path": "services/order_service.go:120"
  }
]
```

### Step 8: WD-TASK payload

```json
[
  {
    "slot": "1.1 需求概述",
    "required_ctx": ["CTX-01"],
    "participating_experts": ["ARCH"],
    "expert_questions": [
      "当前需求概述的现有资产是什么？复用/改造/新建分别的可行性？",
      "落位到模板 1.1 槽位需要承载的最小闭环是什么？"
    ],
    "suggested_slot": "1.1 需求概述",
    "expression_requirements": "写明需求来源、核心目标和约束条件",
    "blockers": "无"
  }
]
```

### Step 9: WD-EXP-SLOT-* payload

```json
[
  {
    "slot": "2.1 方案设计",
    "decision_type": "改造",
    "rationale": "复用现有骨架并补齐专家分析。",
    "evidence_refs": ["CTX-01"],
    "open_questions": ["无"]
  }
]
```

### Step 10: WD-SYN-SLOT-* payload

```json
[
  {
    "slot": "2.1 方案设计",
    "target_capability": "收敛 2.1 方案设计 的最终写法。",
    "comparisons": [
      {"path": "复用", "feasibility": "❌", "evidence": "CTX-01", "reason": "不足"},
      {"path": "改造", "feasibility": "✅", "evidence": "CTX-01", "reason": "推荐"}
    ],
    "selected_path": "改造",
    "selected_writeup": "整体采用改造路径，在现有 OrderService 上扩展。

新增字段 `spotRuleConfig` 存储比例配置，向后兼容。

服务层增加策略分发逻辑，根据配置选择抽取方式。",
    "evidence_refs": ["CTX-01"],
    "template_gap": "无",
    "open_question": "无"
  }
]
```
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

失败后继续使用 `python /path/to/run-step.py --state <状态文件路径>` 或 `--advance`。对外只消费 `run-step.py` 返回的恢复动作，不直接调用 validator 或其他内部脚本。

### run-step.py --emit-scaffold

- `python /path/to/run-step.py --state <状态文件路径> --emit-scaffold`
- 只读辅助入口：仅向 `stdout` 输出当前步骤 scaffold
- 不是第二条写入路径
- 不修改 state
- 不修改 working draft
- 不修改 receipt
- `--emit-scaffold 与 --complete 不能同时使用`；同理也不能与 `--advance` 同时使用
