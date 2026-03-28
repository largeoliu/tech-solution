# Skill 严格串行门禁加固设计

**日期**：2026-03-28

**目标**：为 `review-technical-solution` 与 `create-technical-solution` 建立严格的串行门禁契约，确保 skill 在任一前置步骤未完成时只能停在第一个未完成步骤，不能跳步生成中间结论、正式输出或销毁中间产物。

## 范围

- 收紧 `skills/review-technical-solution/SKILL.md` 与其 references，使步骤 `1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 输出前自检 -> 正式输出` 形成显式硬门禁。
- 收紧 `skills/create-technical-solution/SKILL.md` 与其 references，使步骤 `1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> absorb-check -> 删除 working draft` 形成显式硬门禁。
- 为 `tests/skill_validation/case_catalog.py` 增加 `RTS-*` 与 `CTS-*` 多轮 gating case，描述当前进度、阻塞步骤、允许动作与禁止动作。
- 为两个 skill 增加行为级门禁测试，验证“第一个未完成步骤优先”与尾流程 gate，而不只验证文档措辞。
- 更新 `docs/superpowers/testing/skill-validation.md` 与相关设计文档，使流程说明、代表性 case、验证层次与正式 contract 一致。

## 非范围

- 不把三套 skill 抽象成统一的通用 workflow framework。
- 不改变 `review-technical-solution` 的评审职责边界，也不让它负责生成技术方案正文。
- 不改变 `create-technical-solution` 的模板驱动成稿职责，也不把它改造成开放式自由写作流程。
- 不引入高成本的全量 agent E2E golden 测试；本轮重点是文档契约与行为级门禁验证。
- 不重写已经稳定的 `setup-architect` 门禁实现，只复用其修复模式。

## 背景

`setup-architect` 的问题已经证明：多步骤流程即使写了编号步骤，如果只有尾部边界是硬门禁，而中间步骤只是“推荐顺序”或“软提示”，弱模型仍然可能把几个步骤合并理解，然后直接跳到后面。真正的问题不是缺步骤，而是缺少“前一步未完成时，后一步绝对不能开始”的正式 contract 与对应行为测试。

当前仓库中：

- `review-technical-solution` 已经对输入完整性和代码证据质量有强约束，但步骤 `2` 到 `6` 之间仍主要是顺序说明，尚未全部变成显式 transition gate。
- `create-technical-solution` 已经比旧 `setup-architect` 更强，因为它有 working draft、共享上下文和任务单边界，但若没有显式 completion evidence 与 step-gating 测试，仍存在 `1 -> 4/5`、`4 -> 5`、`5 -> 8`、`8 -> 9`、`9 -> 10`、`absorb-check -> delete` 的跳步风险。

因此本轮设计要解决的不是“补充更多文案”，而是把两个 skill 都改造成：

1. 每一步都有明确完成条件。
2. 每一步都有可见、可验证的中间产物或痕迹。
3. 每一步都显式声明禁止进入哪些后续步骤。
4. 测试能够验证 skill 会停在第一个未完成步骤，而不是只验证文档包含某些关键词。

## 统一门禁模型

### 核心执行语义

- 采用“第一个未完成步骤优先”原则。
- 若第 `N` 步未完成，skill 只能停在第 `N` 步补充信息、回退重做或等待确认，不得进入第 `N+1` 步及之后的任意阶段。
- 主流程步骤与尾流程步骤一视同仁；自检、吸收检查、删除中间产物都属于正式 gate，而不是建议性收尾动作。

### 每一步必须具备的 4 类定义

每个正式步骤都必须定义以下 4 项：

1. **完成条件**：什么状态才算该步骤完成。
2. **可见产物 / 可验证痕迹**：后续步骤可以消费的稳定结果，不能只靠一句“已经完成”。
3. **禁止进入的后续步骤**：该步骤未完成时，明确禁止进入哪些后续步骤。
4. **未完成时的动作**：返回 `STOP_AND_ASK`、`无法开展正式评审`、或回退到指定前置步骤重做。

### 回退规则

- 缺少外部输入、用户确认或项目上下文时，使用 `STOP_AND_ASK` 或对应的正式停机结果。
- 已有产物被证明无效、前置判断被后续证据推翻时，必须回退到指定步骤，不允许直接在后续步骤临时修补。
- 回退目标必须明确到具体步骤，避免“重新检查一下”这类无法被测试精确判断的描述。

### 测试对齐原则

- `SKILL.md` 负责声明严格顺序、禁止跳步、停机语义、回退边界。
- references 负责定义完成条件、产物形态、证据要求与尾流程 gate。
- validation 负责把这些规则转成多轮 case、状态模型与 conversation simulation，不把“包含关键词”误当成“严格执行流程”。

## `review-technical-solution` 设计

### 总体结构

保留现有六步评审主流程，但把“输出前自检”和“正式输出”升级为正式 gate，形成如下完整链路：

`1 输入完整性 -> 2 方案类型判定 -> 3 核心主张清单 -> 4 证据核验矩阵 -> 5 归因与分级 -> 6 改进方案 -> 7 输出前自检 -> 8 正式输出`

### 步骤定义

#### Step 1：输入完整性

- 完成条件：需求详情、技术方案文档、`.architecture/principles.md`、相关项目代码四类必需输入齐全。
- 可见产物：输入完整性结论，标记已具备输入项与缺失输入项。
- 未完成时动作：只能返回 `无法开展正式评审` 或与其等价的停机结果，不得进入类型判定。
- 禁止进入：Step 2 到 Step 8。

#### Step 2：方案类型判定

- 完成条件：明确产出主类型与附加类型，并说明为何命中这些类型。
- 可见产物：类型判定结果，包含主类型、附加类型、检查并集说明。
- 未完成时动作：停在类型判定，不得进入主张提取。
- 禁止进入：Step 3 到 Step 8。

#### Step 3：核心主张清单

- 完成条件：所有关键主张都被列出，并具备最小字段集，例如主张内容、涉及对象、预期行为或约束、后续核验方式。
- 可见产物：结构化主张清单。
- 未完成时动作：停在主张提取，不得进入代码取证或正式结论。
- 禁止进入：Step 4 到 Step 8。

#### Step 4：证据核验矩阵

- 完成条件：每条关键主张都有 `已证实`、`已证伪` 或 `待核验` 状态，且附文件证据或缺证原因。
- 可见产物：主张到证据状态的核验矩阵。
- 未完成时动作：停在证据核验，不得进入归因分级、改进建议或正式结论。
- 禁止进入：Step 5 到 Step 8。

#### Step 5：归因与分级

- 完成条件：每个已证伪问题或待核验风险都有归因维度与严重级别。
- 可见产物：问题清单，包含维度、级别、证据引用与影响说明。
- 未完成时动作：停在归因分级，不得进入改进方案或正式输出。
- 禁止进入：Step 6 到 Step 8。

#### Step 6：改进方案

- 完成条件：每个 `阻塞` / `严重` 项都绑定可执行改进建议与验证方法。
- 可见产物：问题与改进动作的关联表。
- 未完成时动作：停在改进方案，不得进入输出前自检或正式输出。
- 禁止进入：Step 7 到 Step 8。

#### Step 7：输出前自检

- 完成条件：所有关键主张都有证据状态，所有高优先级问题都有改进动作，多类型并集检查已经闭合，输出区块满足正式契约。
- 可见产物：自检通过结论，或明确列出未通过项。
- 未完成时动作：停在自检并回到对应未完成步骤修正，不得输出正式评审。
- 禁止进入：Step 8。

#### Step 8：正式输出

- 完成条件：仅消费前七步已经闭合的正式结果，按输出契约生成正式评审。
- 限制：不得在正式输出阶段临时补充新的证据判断、类型判断或改进动作。

### 关键文档改动方向

- 在 `skills/review-technical-solution/SKILL.md` 中为步骤 `2` 到 `6` 逐条补上“未完成前不得进入下一步”的硬门禁句式。
- 在 `skills/review-technical-solution/references/review-process.md` 中把输出前自检从 advisory checklist 改成 release gate，并为每一步补 completion criteria。
- 在 `skills/review-technical-solution/references/review-analysis-guide.md` 中把多类型并集检查要求前置成可验证义务，而不是建议性说明。
- 在 `skills/review-technical-solution/references/review-output-contract.md` 中明确正式输出只能消费前面已经闭合的结果。

## `create-technical-solution` 设计

### 总体结构

保留现有十步主流程与 `absorb-check -> 删除 working draft` 尾流程，但将整个链条改造成严格串行门禁：

`1 定题与范围判断 -> 2 语义前置校验 -> 3 当前模板读取 -> 4 方案类型判定 -> 5 成员选择 -> 6 共享上下文构建 -> 7 模板任务单生成 -> 8 专家逐槽位分析 -> 9 协作收敛 -> 10 严格模板成稿 -> 11 absorb-check -> 12 删除 working draft`

### 步骤定义

#### Step 1：定题与范围判断

- 完成条件：主题、目标、边界足够明确，能够判断本次方案要解决的问题和非目标。
- 可见产物：定题结论与范围说明。
- 未完成时动作：停在定题澄清，不得进入模板读取、类型判断或成员选择。
- 禁止进入：Step 2 到 Step 12。

#### Step 2：语义前置校验

- 完成条件：语义前置文件已定位，或明确缺失项并请求用户补充。
- 可见产物：前置文件清单与缺失项结论。
- 未完成时动作：`STOP_AND_ASK`，不得继续后续方案流程。
- 禁止进入：Step 3 到 Step 12。

#### Step 3：当前模板读取

- 完成条件：形成稳定的模板结构摘要，而不是只口头声明“已阅读模板”。
- 可见产物：模板结构摘要，包含模板版本、必填槽位、关键约束。
- 未完成时动作：停在模板读取，不得进入方案类型判定。
- 禁止进入：Step 4 到 Step 12。

#### Step 4：方案类型判定

- 完成条件：产出主类型与附加类型结论，并记录判定依据。
- 可见产物：类型判定记录。
- 未完成时动作：停在类型判定，不得进入成员选择。
- 禁止进入：Step 5 到 Step 12。

#### Step 5：成员选择

- 完成条件：形成参与成员名单，并说明每位成员覆盖的槽位与参与理由。
- 可见产物：参与成员名单与覆盖关系。
- 未完成时动作：停在成员选择，不得进入共享上下文、任务单或专家分析。
- 禁止进入：Step 6 到 Step 12。

#### Step 6：共享上下文构建

- 完成条件：关键证据都已有编号、来源、适用槽位与缺口状态。
- 可见产物：共享上下文清单。
- 未完成时动作：停在共享上下文构建，不得进入模板任务单。
- 禁止进入：Step 7 到 Step 12。

#### Step 7：模板任务单生成

- 完成条件：每个模板槽位都有明确状态，例如已分配、待补证、阻塞原因、依赖证据。
- 可见产物：模板任务单。
- 未完成时动作：停在任务单生成，不得进入专家逐槽位分析。
- 禁止进入：Step 8 到 Step 12。

#### Step 8：专家逐槽位分析

- 完成条件：所有已选专家都完成了各自负责槽位的分析，缺证项已明确标注。
- 可见产物：按槽位组织的专家分析结果。
- 未完成时动作：停在专家分析，不得进入协作收敛。
- 禁止进入：Step 9 到 Step 12。

#### Step 9：协作收敛

- 完成条件：每个模板槽位都有收敛结论，说明采用何种判断、保留哪些证据编号、冲突如何处理、是否仍处于阻塞状态。
- 可见产物：按槽位整理的收敛结果。
- 未完成时动作：停在收敛，不得进入正式成稿。
- 禁止进入：Step 10 到 Step 12。

#### Step 10：严格模板成稿

- 完成条件：正式文档仅由已经收敛的槽位生成，不新增未经验证的判断。
- 可见产物：正式技术方案文档。
- 未完成时动作：回退到 Step 9，而不是继续硬写。
- 禁止进入：Step 11 到 Step 12。

#### Step 11：absorb-check

- 完成条件：working draft 中需要保留的关键信息已被正式文档吸收，或明确记录为未吸收项。
- 可见产物：absorb-check 结论。
- 未完成时动作：停在 absorb-check，不得删除 working draft。
- 禁止进入：Step 12。

#### Step 12：删除 working draft

- 完成条件：只有 absorb-check 通过后，才允许删除 working draft。
- 限制：若 absorb-check 未完成或未通过，working draft 必须保留，作为可追溯依据。

### 关键文档改动方向

- 在 `skills/create-technical-solution/SKILL.md` 中为步骤 `1` 到 `10` 与尾流程 gate 明确补上禁止跳步语义。
- 在 `skills/create-technical-solution/references/solution-process.md` 中为类型判定、成员选择、共享上下文、任务单、专家完成、收敛结果补 completion evidence。
- 在 `skills/create-technical-solution/references/progress-transparency.md` 中把中间产物展示边界改成正式门禁边界。
- 在 `skills/create-technical-solution/references/working-draft-protocol.md` 中补上 absorb-check 与 deletion 的生命周期要求。

## 验证设计

### 验证层次

本轮维持五层验证矩阵：

1. **文档 contract 测试**：锁定步骤顺序、禁止跳步语义、`STOP_AND_ASK` 或回退语义。
2. **case catalog 测试**：锁定多轮 case 元数据、步骤进度、阻塞步骤与禁止动作。
3. **conversation simulation 测试**：验证对话在多轮中是否停在第一个未完成步骤。
4. **step-gating / 状态机测试**：验证文档定义的 gate、catalog 定义的进度与允许动作是否一致。
5. **尾流程生命周期测试**：专门锁定 `review` 的输出前自检与 `create` 的 absorb-check / working draft 删除边界。

### case 组织策略

- 不引入一个覆盖全部 skill 的共享 workflow engine。
- 采用“共享概念 + 分 skill 元数据”的方式：
  - 共享概念：`blocked_steps`、`required_step`、`turn_action`、多轮 `turns`。
  - skill 专属进度对象：保留 `SetupProgress`，新增 `ReviewProgress` 与 `CreateProgress`。
- 继续保留静态 contract tests；新增行为测试不是替代，而是补齐“是否严格执行流程”的验证缺口。

### `review-technical-solution` 新增 case 重点

- 卡在类型判定，不能进入主张提取。
- 卡在主张提取，不能进入代码取证。
- 卡在证据状态判定，不能进入归因分级或正式结论。
- 卡在归因与分级，不能进入改进建议或正式输出。
- 卡在输出前自检，不能生成正式评审。

### `create-technical-solution` 新增 case 重点

- 卡在定题澄清，不能提前进入模板读取、类型判定或成员选择。
- 卡在模板读取或类型判定，不能进入成员选择。
- 卡在成员选择，不能进入共享上下文、任务单或专家分析。
- 卡在任务单完整性，不能进入专家逐槽位分析。
- 卡在专家未全量完成，不能进入协作收敛。
- 卡在槽位未收敛，不能进入正式成稿。
- 卡在 absorb-check，不能删除 working draft。

### 测试文件规划

- `tests/skill_validation/test_review_technical_solution_contracts.py`：补强顺序与硬门禁断言。
- `tests/skill_validation/test_review_technical_solution_conversation_simulation.py`：新增多轮 gating 行为验证。
- `tests/skill_validation/test_review_technical_solution_step_gating.py`：新增 step-gating / 状态机测试。
- `tests/skill_validation/test_create_technical_solution_contracts.py`：补强顺序与硬门禁断言。
- `tests/skill_validation/test_create_technical_solution_conversation_simulation.py`：新增多轮 gating 行为验证。
- `tests/skill_validation/test_create_technical_solution_step_gating.py`：新增 step-gating / 状态机测试。
- `tests/skill_validation/case_catalog.py`：新增 `RTS-*` 与 `CTS-*` 多轮 case 及其进度元数据。

## 数据流

### `review-technical-solution`

1. 校验四类正式输入是否齐全。
2. 形成主类型与附加类型的判定结果。
3. 从需求与方案中提取关键主张清单。
4. 用代码与原则文档为每条主张赋予证据状态。
5. 汇总问题并完成归因与分级。
6. 为高优先级问题生成可执行改进动作。
7. 执行输出前自检，确认前面结果已闭合。
8. 按正式输出契约生成评审报告。

### `create-technical-solution`

1. 明确定题与范围。
2. 校验语义前置。
3. 读取当前模板并形成模板结构摘要。
4. 判定方案类型。
5. 选择参与成员并固定覆盖关系。
6. 构建共享上下文。
7. 生成模板任务单。
8. 组织专家逐槽位分析。
9. 对每个槽位完成协作收敛。
10. 生成严格模板成稿。
11. 执行 absorb-check。
12. 仅在 absorb-check 通过后删除 working draft。

## 错误处理与回退

- 缺少正式输入、用户确认或项目上下文时，必须停在当前步骤并说明阻塞原因，不能带着不完整上下文继续后续步骤。
- 若后续发现前置判断无效，必须回退到对应步骤重做，而不是在后置阶段临时补丁式修复。
- `review` 的正式输出前自检未通过时，只允许回退到自检发现的第一个未完成步骤。
- `create` 的正式成稿若发现槽位未闭合，必须回退到协作收敛；absorb-check 未通过时必须保留 working draft。

## 实施顺序

### 第一阶段：先收紧 `review-technical-solution`

- 原因：风险最高，步骤较短，适合作为门禁模式模板。
- 产出：文档硬门禁、自检 release gate、`RTS` 多轮 case、review step-gating 测试。

### 第二阶段：再收紧 `create-technical-solution`

- 原因：可复用 `review` 已验证的写法与测试模式。
- 重点：`8 -> 9 -> 10` 与 `absorb-check -> delete` 的强门禁。

### 第三阶段：统一验证文档

- 更新 `docs/superpowers/testing/skill-validation.md`。
- 如有必要，更新已有设计文档对验证层次与代表性 case 的描述。

## 验收标准

- `review-technical-solution` 与 `create-technical-solution` 的 `SKILL.md` 和 references 都显式声明每一步的完成条件、禁止跳步语义与未完成动作。
- `RTS` 与 `CTS` 都具备多轮 gating case，能够表示当前停在哪一步、为什么不能进入下一步。
- 两个 skill 都具备 conversation simulation 与 step-gating 测试，不再只依赖静态文档断言。
- `review` 的输出前自检与 `create` 的 absorb-check / working draft 删除都有专门的尾流程门禁测试。
- 全部相关验证可以通过受影响子集运行与 `tests/skill_validation` 全量运行共同证明。

## 风险与取舍

- 本轮不抽象通用 workflow engine，因此会有少量重复的 progress 元数据与状态机测试逻辑；这是为了降低本次改动风险并保留按 skill 定制的清晰边界。
- 行为测试增加后，case catalog 与测试文件会变大，但这是用显式验证换取流程稳定性的必要成本。
- 若未来三套 skill 都稳定采用相同门禁模型，再考虑提炼共享 helper；本轮不提前做该抽象。
