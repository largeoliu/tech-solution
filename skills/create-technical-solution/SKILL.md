---
name: create-technical-solution
description: "Use when 用户请求创建、补写或更新技术方案、技术设计、架构决策文档、RFC 或设计方案。当用户提到\"写方案\"\"技术方案\"\"设计方案\"\"架构评审\"\"新建能力\"\"系统改造\"\"功能重构\"\"模块拆分\"\"数据迁移\"\"能力复用\"等关键词，需要基于当前技术方案模板组织共享上下文、专家分析和协作收敛并产出正式方案文档时触发。即使未明确提及\"技术方案\"，只要涉及多模块协调、跨系统集成或需要结构化决策文档的场景也应使用本技能。"
compatibility:
  requires:
    - ".architecture/members.yml"
    - ".architecture/principles.md"
    - ".architecture/templates/technical-solution-template.md"
---

# 创建技术方案

## 技能定位

> ⚠️ Lite/Mini 模型请使用下方「简化执行循环」（基于 `run-step.py`），主力模型可使用原始执行循环或简化循环。

按当前生效模板产出正式技术方案。依赖 `.architecture/members.yml`、`.architecture/principles.md`、`.architecture/templates/technical-solution-template.md`。当前模板是唯一正文骨架来源。

- 本技能只消费当前模板结构，不得预设模板必须存在特定章节、表格、列名或固定小节。
- `复用 / 改造 / 新建` 比较与相关证据先沉淀在 working draft 和门控产物中，再映射进当前模板已有槽位；若现有槽位无法承载且必须改模板，阻塞并交由模板管理流程处理。

## 现有资产优先原则
- 默认优先复用或改造代码库中已存在的能力单元，不默认新建同类能力。
- 现有资产不限于接口，还包括 API、service、function、module、component、class、table、schema、model、config、flag、job、script、event、command、workflow、page、form、state、hook 等。
- 凡方案涉及新增、拆分、合并、迁移、平行建设、职责转移或能力增强，必须先识别现有候选资产，并比较 `复用 / 改造 / 新建` 三种路径。
- 若选择 `新建`，必须给出代码证据、职责边界证据和兼容性证据，证明前两者不可接受；否则不得作为推荐方案。
- 不得以"更清晰""更优雅"等空泛表述替代代码证据——这些主观判断无法验证，且容易跳过实际的代码搜索，导致方案建立在假设而非事实上。
- `低风险复用/改造` 至少同时满足：职责边界无需重写、兼容性影响可控、主要调用方可保持兼容或低成本迁移。

<HARD-GATE>
执行前提：本技能会创建状态文件、working draft、最终技术方案文档，并在流程完成后清理中间产物。若当前处于只读模式或 Plan Mode，必须立即停止，并提示切换到可写执行模式后再运行。
</HARD-GATE>

若 `.architecture/members.yml`、`.architecture/principles.md` 或 `.architecture/templates/technical-solution-template.md` 不存在，先调用 `bootstrap-architecture` 技能初始化，再继续本流程。

## 执行循环
1. 读取状态文件
2. 定位当前步骤
3. **先加载对应 step card**

<HARD-GATE>
每步执行前必须 Read 对应的 `steps/NN-*.md` 文件。step card 包含该步骤的具体操作命令、参数格式和完成标准。未读取 step card 就执行操作视为流程违规。
</HARD-GATE>

4. **先运行当前步骤 validator 门禁**
5. 执行本步操作
6. 用确定性脚本更新状态 / 模板快照 / produced_artifacts
7. 再次运行门禁验证，通过则进入下一步

## 简化执行循环（推荐）

使用 `run-step.py` 统一编排器，自动处理验证、receipt 刷新、参数推导和 step card 加载，Agent 只需关注创作工作。

1. **查看任务**：`python /path/to/run-step.py --state <状态文件>` → 输出当前步骤、验证状态、操作指引、下一步命令
2. **只读 scaffold**：`python /path/to/run-step.py --state <状态文件> --emit-scaffold` → 仅向 `stdout` 输出当前步骤 scaffold；不修改 state、working draft 或 receipt，且 `--emit-scaffold 与 --complete 不能同时使用`；scaffold 目标步骤遵循当前 auto-skip 语义
3. **执行并提交**：`python /path/to/run-step.py --state <状态文件> --complete --summary "..." [--content-file /tmp/xxx.md]`
4. **重复**直到步骤 12 完成

各步骤的完整命令示例：

| 步骤 | 命令 |
|------|------|
| 1 | `--complete --summary "..." --slug <slug>` |
| 2, 3, 6 | `--complete --summary "..."` |
| 4 | `--complete --summary "..." --flow-tier <tier> --solution-type "..." --signal <signal>` |
| 5 | `--complete --summary "..." --member <ID> [--member ...]` |
| 7, 8, 10 | `--complete --summary "..." --content-file /tmp/<block>.md` |
| 9 | `--complete --summary "..." --content-file /tmp/wd-exp-<MEMBER>.md [--content-file ...]` |
| 11, 12 | `--complete --summary "..."` |

全自动步骤（2、3、6、11、12）无需额外输入，直接 `--complete` 即可。`light`/`moderate` 流程的跳步会自动处理。

## 状态文件初始化
只能通过 `run-step.py` 完成步骤 1 初始化 `.architecture/.state/create-technical-solution/[slug].yaml`。它会在 state 缺失时自动创建文件、写入 step-1 最小 checkpoint、派生路径并刷新 receipt；不得再手工 `cp templates/_template.yaml` 后补 YAML。

## 运行入口与内部脚本
- `python /path/to/run-step.py --state <状态文件> [--complete --summary "..." ...]`
  - 唯一受支持的对外入口。统一封装验证、receipt 刷新、参数推导、step card 加载、working draft 写入、最终文档成稿与清理
- `python /path/to/run-step.py --state <状态文件> --emit-scaffold`
  - 同一入口下的只读辅助模式；仅输出 scaffold 到 `stdout`，不是第二条写入路径，也不会替代 `--complete`
- `python /path/to/runtime_doctor.py --state <状态文件> [--step N] [--flow-tier <tier>] [--apply-safe-fixes]`
  - 运行时 repair helper，不是主执行路径；默认 `dry-run`，只有 `--apply-safe-fixes` 才允许做结构性安全修复（规范目录、旧 draft 路径/状态迁移、语义安全的 receipt 修复）
- 其他脚本（如 `initialize-state.py`、`extract-template-snapshot.py`、`upsert-draft-block.py`、`set-flow-tier.py`、`advance-state-step.py`、`render-final-document.py`、`finalize-cleanup.py`）
  - 仅保留给 `run-step.py`、测试与内部兼容流程使用；不再作为用户公开操作入口
- 创作型步骤的 `content-file`
  - 只能包含目标 block 的区块体内容；不得再包含 `## WD-*`、`## Template Metadata`、`## Template Slots` 或 `# Working Draft`

## 状态更新规则
- 每步完成后写入 `checkpoints.step-N` 并追加 `completed_steps`
- 回退时从 `completed_steps` 移除受影响步骤，重置 `current_step`
- **state / draft 职责固定**：state 只保留 `current_step`、`completed_steps`、`skipped_steps`、`flow_tier`、`required_artifacts`、`produced_artifacts`、gate flags、路径字段、最小 checkpoint、cleanup 状态
- **正文只允许写入 working draft**：`WD-CTX`、`WD-TASK`、`WD-EXP-*`、`WD-SYN / WD-SYN-LIGHT`、`WD-IMPACT-*` 一律只存在于 working draft；共享上下文、专家判断、收敛结论、详细设计正文不得写进 state
- **checkpoint 必须结构化且瘦身**：`checkpoints.step-N.summary` 只能写流程摘要，不得复述正文
- **流程摘要只允许描述**：本步是否完成/跳过、写入了什么区块、区块数量/槽位数量、下一步 gate 是否齐备
- **严禁手写 produced_artifacts**：必须以 `run-step.py` 在块写入后的同步结果为准，不得口头宣称某个 `WD-*` 已存在
- **严禁把被跳过步骤记为已完成**：`light/moderate` 流程允许跳过的步骤必须写入 `skipped_steps` 与结构化 checkpoint，不得写入 `completed_steps`
- **step-4 必须通过 `run-step.py` 原子完成**：`flow_tier`、`required_artifacts`、`skipped_steps` 必须在同一次步骤提交中同步写入，禁止先推进再手改 YAML
- **step-3 先验只检查前置，不检查产物**：步骤 3 的 validator 只确认 step 1/2、模板文件与路径前置条件；`template_fingerprint`、`slot_count`、`working_draft_path` 必须由 `run-step.py` 的 step-3 受控流程首次生成，禁止因为 step 3 校验失败而手改 state
- **所有写状态动作都要求 receipt**：`run-step.py` 在进入当前步骤前必须先完成 validator 门禁并刷新 receipt；不得绕过该流程直接写 state、draft、final document 或 cleanup 结果
- **receipt 必须跟随 current_step 原子刷新**：任何 mutating script 成功后都必须把 `gate_receipt.step` 刷新到最新 `current_step`；若 `receipt.step` 落后于 `current_step`，视为非法状态，必须停下修复，不能继续写 draft、render 或 cleanup
- **working draft 只能块级写入**：step 7/8/9/10 只能通过 `run-step.py` 的受控写入路径更新 `WD-*` 区块，禁止整份覆盖 draft；任何覆盖导致旧 block 消失，视为流程失败
- **block body 不能再带 block 标题**：传给 `run-step.py --content-file` 的文件只允许是区块体内容；如果再次包含 `## WD-*` 或 draft 容器标题，视为无效输入
- **state 中路径必须相对化**：`solution_root` 固定为 `.architecture/technical-solutions`，`working_draft_path` 固定为 `.architecture/.state/create-technical-solution/[slug].working.md`；不得把绝对路径写回 state
- **最终文档目录固定**：`final_document_path` 只能位于 `.architecture/technical-solutions/`，不得写入 `docs/`、项目根目录或其他自定义目录
- **目录策略固定为双读单写**：可以读取历史 `.architecture/solutions/`，但本次流程的新 working draft 统一写入 `.architecture/.state/create-technical-solution/`，最终文档统一写入 `.architecture/technical-solutions/`
- **禁止外部脚本补状态**：不得用 inline Python、手工 Edit YAML、直接 `rm` 文件来伪造 receipt、fingerprint、checkpoint、cleanup 结果；一旦 gate fail，必须停在当前步修复脚本要求的最小前置
- **禁止先写 final 再追认**：step 11 只能通过 `run-step.py` 的成稿流程生成最终文档；不得先 `Write` 最终文档，再补跑内部脚本追认
- **render 不接受外部整文**：step 11 只能从 working draft 渲染；不得先拼 `/tmp/final-document.md` 再传给脚本
- **cleanup 失败只允许脚本化 repair**：step 12 失败时只能回到 `run-step.py` 给出的修复步骤重跑；不得阅读 validator 源码逆向补字段
- **禁止把现成 `docs/技术方案*.md` 当主路径**：若仓库内已有历史方案，只能当背景参考；不得先重写 `docs/` 再回头补 `.architecture` 流程

## 自动推进与过程证据
- 流程默认自动连续执行，不要求用户逐步回复确认
- 每步必须输出 `checkpoints.step-N` 摘要；凡写入 working draft 的步骤，必须同步展示对应 `WD-*` 区块摘要
- 每步 checkpoint 至少包含：本步新增区块、本步新增条目数量、下一步门控所需产物是否齐备；若无法列出，视为本步未完成
- 不得仅以”已完成””已读取””已写入””已删除”等口头表述推进步骤，必须给出本步结果摘要
- 参与成员必须来自 `.architecture/members.yml` 的实际条目——虚构角色会导致后续专家分析步骤加载不到真实视角，产出无效。
- 步骤 9 必须实际加载对应专家的角色和视角，不得模拟 `WD-EXP-*` 产出——跳过专家分析等于跳过多视角验证，方案会遗漏关键风险。
- `full` 流程的 `WD-EXP-*` 必须是按成员拆分的独立稳定区块，例如 `WD-EXP-SYSTEMS_ARCHITECT`；不得用单个总块冒充多个专家产物。
- 步骤 10 必须保留 `WD-SYN` 收敛区块，不得以最终文档替代——中间产物和最终文档职责不同，缺少 WD-SYN 会导致回退时无法追溯决策依据。
- `moderate` 流程的 step-9 必须显式 skip，而不是“先推进 step-9 再口头说明直接做 step-10”。
- 步骤 1-12 进入前必须先通过 `run-step.py` 触发 validator 门禁并写 receipt；若未通过，优先消费 `--format json` 返回的 `repair_plan[]`，按 `repair_plan[].step` 与 `repair_plan[].depends_on_steps` 安排修复顺序，按 `repair_plan[].action_type` 判断是否需要重跑对应步骤，并用 `repair_plan[].script_command` 作为首选重试命令；产物闭合以 `repair_plan[].expected_artifacts_after_fix` 为准，再结合 `summary.recommended_repair_sequence`、`summary.recommended_rollback_step`、`summary.missing_artifacts`、`summary.skip_instead_of_retry` 与 `issues[*].repair_guidance` 补充判断，直到通过后继续

<HARD-GATE>
步骤门控强制要求：步骤 1-12 进入前必须先通过 `run-step.py` 触发对应步骤的 validator 门禁与 receipt 刷新。内部 validator 会检查：
1. 状态文件字段完整性
2. working draft 中 `WD-*` 区块与状态声明是否一致
3. 门控标志位正确性
4. 当前模板快照是否仍与 `.architecture/templates/technical-solution-template.md` 一致
5. `WD-TASK` 是否覆盖当前模板全部槽位
6. `full` 流程是否存在逐专家 `WD-EXP-*` 独立区块
7. step-12 前最终文档与模板槽位顺序是否一致
8. `working_draft_path` / `final_document_path` 是否仍位于白名单目录

若未通过，优先消费 `--format json` 返回的 `repair_plan[]` 修复后重试；重点看 `repair_plan[].step`、`repair_plan[].action_type`、`repair_plan[].depends_on_steps`、`repair_plan[].expected_artifacts_after_fix` 与 `repair_plan[].script_command`，并结合 `summary.*` 和 `issues[*].repair_guidance`。严禁跳过验证直接进入下一步；严禁把“我认为门控已通过”当成通过依据。
</HARD-GATE>

## 复杂度评估与流程裁剪
- 步骤 4 必须产出 `flow_tier`，并据此决定本次流程需要的最小中间产物集合
- `light`：适用于单模块小改动、无新建核心能力、无职责迁移、无高风险兼容性问题；最小产物为 `WD-CTX`、`WD-SYN-LIGHT`
- `moderate`：适用于多模块协调或现有资产改造，但不涉及新建核心能力、拆分/迁移/平行建设、多系统集成或高风险兼容性改造；最小产物为 `WD-CTX`、`WD-TASK`、`WD-SYN`
- `full`：适用于新建核心能力、拆分、迁移、平行建设、职责转移、多系统集成或高风险兼容性改造；最小产物为 `WD-CTX`、`WD-TASK`、`WD-EXP-*`、`WD-SYN`
- 明确反例：在现有抽检系统上新增“按比例抽审能力 / 新抽样方式 / 新审核治理维度 / 新判定模式”属于 `introduces-core-capability`，必须判为 `full`
- 任一流程级别都不得跳过本级别要求的最小产物；缺失时必须阻塞，不得成稿或清理
- `full` 流程中的步骤 9 必须按槽位组织专家判断，不得要求每位专家完整覆盖所有槽位；步骤 10 必须支持按槽位增量收敛并落盘，避免全量中间产物滚雪球
- step 8 必须按当前模板的真实槽位逐项生成任务单，不得只按“背景/总体设计/详细设计/测试/上线”这类粗粒度章节分配
- `WD-TASK` 必须与模板槽位一一对应且顺序一致，不得多写 `SLOT-20`、不得把 `CTX-*` 混入任务单
- `WD-SYN` 必须按模板槽位逐项收敛，不接受用一段“总体结论”替代逐槽位收敛
- step 4 必须原子写入 `flow_tier`、`checkpoints.step-4.flow_tier`、`required_artifacts` 与 `skipped_steps`；不得先推进到下一步再手改 tier

## 中间产物文档完整性
- 一次流程只维护一份 working draft；其 slug 必须与最终技术方案文件一致。若主题变化导致 slug 变化，必须终止当前流程并以新 slug 重启，不得并行保留多份草稿
- 下游步骤只能消费已经写入 working draft 的稳定 `WD-*` 区块；未写入的区块视为不存在，不得预支后续结论
- 展示层可以只给摘要，但 `WD-*` 中间产物必须保留完整字段、证据追溯、阻塞条件、冲突处理和失效标记，不得因展示层精简而减配
- working draft 只保存稳定、可复用、可回退的结论，不保存 scratchpad、原始推理片段或临时口径
- 回退或重进时，必须先写 `WD-IMPACT-[n]`；已失效内容必须显式标注作废范围，无可复用内容时 `保持有效内容` 写 `无`
- 状态文件中的 `required_artifacts` 与 `produced_artifacts` 是流程推进的唯一产物依据；不得以口头描述替代产物存在性
- 凡 `required_artifacts` 未齐、`pending_questions` 未清空、`absorption_check_passed = false`、存在未解决阻塞槽位，或存在未经 `flow_tier` 明确允许的跳步时，禁止清理 working draft 和状态文件

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

<HARD-GATE>
最终成稿门控：步骤 11 完成前不得生成最终文档。必须满足以下全部条件才可进入步骤 11：
1. 所有非阻塞槽位均已写入 WD-SYN 或 WD-SYN-LIGHT 收敛产物
2. 所有新建结论的关键证据引用已覆盖不可复用、不可改造与新建必要性说明
3. 不存在未解决的模板承载缺口
4. validate-state.py 步骤 11 门控检查通过（退出码 0）
</HARD-GATE>

<HARD-GATE>
清理门控：步骤 12 完成后必须删除 working draft 和状态文件。必须满足以下全部条件才可删除：
1. `absorption_check_passed: true`
2. `cleanup_allowed: true`
3. validate-state.py 步骤 12 门控检查通过（退出码 0）
4. 最终技术方案文档已生成且内容完整
5. 若步骤 11 曾失败，已先停留在步骤 11 完成 repair loop，而不是直接推进到步骤 12

删除后必须验证文件不存在，否则视为清理失败。
</HARD-GATE>

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

## 示例

**输入**：为订单系统增加退款功能
**输出**：`.architecture/technical-solutions/2025-04-refund-system.md`，包含背景、范围、方案设计、迁移计划、风险评估

## 故障排除

| 问题 | 原因 | 解决 |
|------|------|------|
| validator 门禁失败 | 状态文件缺少必需产物或步骤跳跃 | 运行 `python /path/to/run-step.py --state <状态文件>` 查看 repair 指引，并按 `repair_plan[]` 修复 |
| members.yml 不存在 | `.architecture/` 未初始化 | 先调用 `bootstrap-architecture` 技能 |
| 模板文件不存在 | 模板未创建或路径错误 | 检查 `.architecture/templates/technical-solution-template.md`，缺失则调用 `manage-technical-solution-template` |
| working draft 内容丢失 | slug 不一致导致多份草稿 | 终止当前流程，以正确 slug 重启 |
| fingerprint 反复不一致 | 手动修改 YAML 导致 receipt 失效 | 不要使用 inline Python 修改 state；重新运行 `python /path/to/run-step.py --state <状态文件>`，按当前步骤的 repair 指引重新生成合法 receipt |

## 相关技能
- `bootstrap-architecture`：初始化 `.architecture/` 目录、成员名册、原则文档和技术方案模板。

## 常见陷阱
- 步骤 2-3 的 `--flow-tier` 必须使用 `pending`，因为步骤 4 才正式判定流程级别；使用 `light` 会导致后续 receipt 中的 `flow_tier` 与步骤 4 判定结果不一致
- `python /path/to/run-step.py --state <状态文件>` 会给出面向执行的 repair 指引；对外流程只消费这里返回的修复建议，不要绕过 `run-step.py` 自己拼接修复动作
- 参与成员必须来自 `.architecture/members.yml` 实际条目——虚构角色会导致步骤 9 专家分析加载失败，产出无效。
- 步骤 9 不得模拟 `WD-EXP-*` 产出或直接跳到最终文档，必须实际加载对应专家的角色和视角
- 步骤 8 不得只生成粗粒度章节任务单，必须按当前模板真实槽位逐项分配
- 步骤 10、11 不得以最终文档替代 `WD-SYN` 收敛区块；中间产物和最终文档是两回事
- 复制 state 模板后仍处于 step 1 初始态；若还没写 step-1 checkpoint、`final_document_path`、receipt，就不能开始写方案正文
- 只读了 `members.yml` 不等于完成 step 5；只有 `checkpoints.step-5.selected_members` 真正落盘才算
- 不得把最终文档写到 `docs/`；step 11 只允许通过 `run-step.py` 的成稿流程落盘到 `.architecture/technical-solutions/`
- 选择 `新建` 路径时，`关键证据引用` 必须覆盖不可复用和不可改造两方面证据，缺少任一项即为阻塞
- `light` 流程不得生成 `WD-TASK` 和 `WD-EXP`，必须显式记录跳过并在 checkpoint 中注明原因
- working draft 全流程只维护一份，若主题变化导致 slug 变化，必须终止当前流程并以新 slug 重启，不得并行保留多份草稿
- 不得以"更清晰""更优雅"等空泛表述替代代码证据——这些主观判断无法验证，且容易跳过实际的代码搜索，导致方案建立在假设而非事实上。
- 若现有模板槽位无法承载必要结论且必须改模板，必须阻塞并交由模板管理流程，不得擅自增删模板章节
- **状态与模板指纹必须同源**：步骤 3 后如果模板被替换或修改，必须回退到步骤 3 重新提取模板指纹与 draft 骨架，不能继续沿用旧槽位定义。
- step 11 若发生推理失败、写文件失败或标题顺序校验失败，必须停留在步骤 11 并先走 validator repair loop，禁止直接推进步骤 12。
- step 12 只能通过 `run-step.py` 的清理流程完成；禁止手工先改 `absorption_check_passed=true`、再 `rm` 文件、再尝试推进状态。
- 仓库里即使已有 `docs/技术方案*.md` 或其他分析 agent，也不能替代 `create-technical-solution` 主路径；最终产物仍必须落在 `.architecture/technical-solutions/`
- 若某一步脚本失败，不得改成“一次性写完整 WD-CTX + WD-TASK + WD-SYN 再回填步骤”；这会让 receipt、checkpoint、produced_artifacts 脱节
