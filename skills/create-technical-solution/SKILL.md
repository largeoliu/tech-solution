---
name: create-technical-solution
description: 在用户请求创建、补写或更新技术方案，需要基于当前技术方案模板组织共享上下文、专家分析和协作收敛，并产出正式方案文档时使用。
---

# 创建技术方案

## 技能定位
按当前生效模板产出正式技术方案。依赖 `.architecture/members.yml`、`.architecture/principles.md`、`.architecture/templates/technical-solution-template.md`。当前模板是唯一正文骨架来源。

- 本技能只消费当前模板结构，不得预设模板必须存在特定章节、表格、列名或固定小节。
- `复用 / 改造 / 新建` 比较与相关证据先沉淀在 working draft 和门控产物中，再映射进当前模板已有槽位；若现有槽位无法承载且必须改模板，阻塞并交由模板管理流程处理。

## 现有资产优先原则
- 默认优先复用或改造代码库中已存在的能力单元，不默认新建同类能力。
- 现有资产不限于接口，还包括 API、service、function、module、component、class、table、schema、model、config、flag、job、script、event、command、workflow、page、form、state、hook 等。
- 凡方案涉及新增、拆分、合并、迁移、平行建设、职责转移或能力增强，必须先识别现有候选资产，并比较 `复用 / 改造 / 新建` 三种路径。
- 若选择 `新建`，必须给出代码证据、职责边界证据和兼容性证据，证明前两者不可接受；否则不得作为推荐方案。
- 不得以“更清晰”“更优雅”“隔离更方便”等空泛表述替代上述证据。
- `低风险复用/改造` 至少同时满足：职责边界无需重写、兼容性影响可控、主要调用方可保持兼容或低成本迁移。

## 执行前提
本技能会创建状态文件、working draft、最终技术方案文档，并在流程完成后清理中间产物。若当前处于只读模式或 Plan Mode，必须立即停止，并提示切换到可写执行模式后再运行。

## 执行循环
1. 读取状态文件 → 2. 定位当前步骤 → 3. 加载对应 step card → 4. 执行操作 → 5. 更新状态 → 6. 检查门控，通过则进入下一步

## 状态文件初始化
从 `templates/_template.yaml` 复制为 `.architecture/.state/create-technical-solution/[slug].yaml`，填充 slug 与时间戳。若目标目录不存在，先创建 `.architecture/.state/create-technical-solution/`。

## 状态更新规则
- 每步完成后写入 `checkpoints.step-N`，追加 `completed_steps`，更新 `updated_at`
- 阻塞时设 `blocked: true` 并填写 `block_reason`
- 回退时从 `completed_steps` 移除受影响步骤，重置 `current_step`

## 自动推进与过程证据
- 流程默认自动连续执行，不要求用户逐步回复确认
- 每步必须输出 `checkpoints.step-N` 摘要；凡写入 working draft 的步骤，必须同步展示对应 `WD-*` 区块摘要
- 每步 checkpoint 至少包含：本步新增文件或区块、本步消费的输入区块、本步新增条目数量、下一步门控所需产物是否齐备；若无法列出，视为本步未完成
- 不得仅以”已完成””已读取””已写入””已删除”等口头表述推进步骤，必须给出本步结果摘要
- 参与成员必须来自 `.architecture/members.yml` 的实际条目，不得虚构角色
- 步骤 9 不得模拟专家产物或跳过 `WD-EXP-*`
- 步骤 10 不得以最终文档替代 `WD-SYN`
- 步骤 8/10/11/12 进入前必须运行 `python scripts/validate-state.py` 验证门禁；若未通过，优先消费 `--format json` 返回的 `repair_plan[]`，并按其中 `action_types` 判断修复动作类别、按 `depends_on_steps` 指定的前置关系执行修复、按 `state_patch_hint` 更新状态字段、按 `artifact_write_hint` 落盘缺失产物、按 `working_draft_context_hint` 选择允许消费的上游稳定区块、按结构化 `completion_checks` 确认每项修复已闭合，并优先使用结构化 `retry_command` 重跑校验；其次再参考 `summary.recommended_repair_sequence`、`summary.recommended_rollback_step`、`summary.missing_artifacts` 与 `issues[*].repair_guidance` 后重试，直到通过后继续

## 复杂度评估与流程裁剪
- 步骤 4 必须产出 `flow_tier`，并据此决定本次流程需要的最小中间产物集合
- `light`：适用于单模块小改动、无新建核心能力、无职责迁移、无高风险兼容性问题；最小产物为 `WD-CTX`、`WD-SYN-LIGHT`
- `moderate`：适用于多模块协调或现有资产改造，但不涉及新建核心能力、拆分/迁移/平行建设、多系统集成或高风险兼容性改造；最小产物为 `WD-CTX`、`WD-TASK`、`WD-SYN`
- `full`：适用于新建核心能力、拆分、迁移、平行建设、职责转移、多系统集成或高风险兼容性改造；最小产物为 `WD-CTX`、`WD-TASK`、`WD-EXP-*`、`WD-SYN`
- 任一流程级别都不得跳过本级别要求的最小产物；缺失时必须阻塞，不得成稿或清理
- `full` 流程中的步骤 9 必须按槽位组织专家判断，不得要求每位专家完整覆盖所有槽位；步骤 10 必须支持按槽位增量收敛并落盘，避免全量中间产物滚雪球

## 中间产物文档完整性
- 一次流程只维护一份 working draft；其 slug 必须与最终技术方案文件一致。若主题变化导致 slug 变化，必须终止当前流程并以新 slug 重启，不得并行保留多份草稿
- 下游步骤只能消费已经写入 working draft 的稳定 `WD-*` 区块；未写入的区块视为不存在，不得预支后续结论
- 展示层可以只给摘要，但 `WD-*` 中间产物必须保留完整字段、证据追溯、阻塞条件、冲突处理和失效标记，不得因展示层精简而减配
- working draft 只保存稳定、可复用、可回退的结论，不保存 scratchpad、原始推理片段或临时口径
- 回退或重进时，必须先写 `WD-IMPACT-[n]`；已失效内容必须显式标注作废范围，无可复用内容时 `保持有效内容` 写 `无`
- 状态文件中的 `required_artifacts` 与 `produced_artifacts` 是流程推进的唯一产物依据；不得以口头描述替代产物存在性
- 凡 `required_artifacts` 未齐、`blocked = true`、`absorption_check_passed = false`、存在未解决阻塞槽位，或存在未经 `flow_tier` 明确允许的跳步时，禁止清理 working draft 和状态文件

## 回退规则
收到用户变更后先写 `WD-IMPACT-[n]`，再回到最早受影响步骤：
| 触发变更 | 回退到 |
|---|---|
| 主题/目标/非目标/影响范围 | 步骤 1 |
| 当前模板变化 | 步骤 3 |
| 方案类型判断 | 步骤 4 |
| 参与成员集合 | 步骤 5 |
| repowiki 检测 | 步骤 6 |
| 共享事实/原则/约束 | 步骤 7 |
| 槽位定义/边界/专家分配 | 步骤 8 |
| 专家分析/建议/补证 | 步骤 9 |
| 收敛结论/分歧/未采纳 | 步骤 10 |
| 最终模板落位 | 步骤 11 |

## 产物 Schema 速查
参见 `REFERENCE.md` 中的「产物 Schema 速查」。执行示例、汇报格式以及 repair contract 参见 `REFERENCE.md`。

## 步骤索引
| # | 步骤 | 文件 |
|---|---|---|
| 1 | 定题与范围判断 | `steps/01-定题与范围判断.md` |
| 2 | 检查 .architecture 前置文件 | `steps/02-检查语义前置文件.md` |
| 3 | 读取当前生效模板 | `steps/03-读取当前生效模板.md` |
| 4 | 判断方案类型 | `steps/04-判断方案类型.md` |
| 5 | 加载成员名册并选择参与者 | `steps/05-加载成员名册并选择参与者.md` |
| 6 | 检测 repowiki 目录 | `steps/06-检测repowiki目录.md` |
| 7 | 构建共享上下文 | `steps/07-构建共享上下文.md` |
| 8 | 生成模板任务单 | `steps/08-生成模板任务单.md` |
| 9 | 组织专家按模板逐槽位分析 | `steps/09-组织专家按模板逐槽位分析.md` |
| 10 | 按模板逐槽位协作收敛 | `steps/10-按模板逐槽位协作收敛.md` |
| 11 | 严格模板成稿并保存结果 | `steps/11-严格模板成稿并保存结果.md` |
| 12 | 吸收检查与清理 | `steps/12-吸收检查与清理.md` |

## 相关技能
- `bootstrap-architecture`：初始化 `.architecture/` 目录、成员名册、原则文档和技术方案模板。

## 常见陷阱
- 参与成员必须来自 `.architecture/members.yml` 实际条目，不得虚构角色或凭空编造专家名称
- 步骤 9 不得模拟 `WD-EXP-*` 产出或直接跳到最终文档，必须实际加载对应专家的角色和视角
- 步骤 10、11 不得以最终文档替代 `WD-SYN` 收敛区块；中间产物和最终文档是两回事
- 选择 `新建` 路径时，`关键证据引用` 必须覆盖不可复用和不可改造两方面证据，缺少任一项即为阻塞
- `light` 流程不得生成 `WD-TASK` 和 `WD-EXP`，必须显式记录跳过并在 checkpoint 中注明原因
- working draft 全流程只维护一份，若主题变化导致 slug 变化，必须终止当前流程并以新 slug 重启，不得并行保留多份草稿
- 不得以"更清晰""更优雅""隔离更方便"等空泛表述替代代码证据、职责边界证据和兼容性证据
- 若现有模板槽位无法承载必要结论且必须改模板，必须阻塞并交由模板管理流程，不得擅自增删模板章节
