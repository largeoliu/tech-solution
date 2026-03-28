# Skill 验证设计

## 概述

本设计定义 `setup-architect` 与 `create-technical-solution` 的长期验证方案，目标是把“两个 skill 是否稳定、是否会流程跑偏、是否能在边界条件下守住规则”收敛成一套可重复执行的测试流程和用例矩阵。

这份设计只以正式契约为基线，不依赖临时分析文件。长期规范来源限定为：

- `skills/setup-architect/SKILL.md`
- `skills/setup-architect/references/installation-procedures.md`
- `skills/setup-architect/references/member-customization.md`
- `skills/setup-architect/references/principles-customization.md`
- `skills/setup-architect/references/technical-solution-template-customization.md`
- `skills/create-technical-solution/SKILL.md`
- `skills/create-technical-solution/references/solution-process.md`
- `skills/create-technical-solution/references/template-adaptation.md`
- `skills/create-technical-solution/references/solution-analysis-guide.md`
- `/.github/workflows/skills-integration-tests.yml`

## 背景

当前仓库已经有一层基础验证：`/.github/workflows/skills-integration-tests.yml` 能检查 skill 安装结果、目标目录、必要文件和禁止产物。这层能够回答“装得对不对”，但还不能稳定回答：

- skill 是否在缺前置时正确停机
- skill 是否会偷偷脑补环境或覆盖已有文件
- skill 是否真的围绕当前模板工作，而不是退回默认结构
- 可选分支、幂等执行、模板替换、多类型主题等高风险路径是否稳定

因此需要把验证扩成“静态契约 + 流程场景 + 行为回归 + 对抗边界”的分层体系，并配一套统一的 case 模板和优先级顺序。

## 目标

- 定义两个 skill 的长期测试流程，而不是一次性的检查动作。
- 建立统一的断言模型，避免每个 case 各写各的、口径漂移。
- 为 `setup-architect` 与 `create-technical-solution` 各给出可落地的用例矩阵。
- 明确哪些用例应优先补齐，哪些可作为第二阶段和第三阶段扩展。
- 让后续每次修改 `SKILL.md` 或 references 时，都能知道最少必须回归哪些测试。

## 非目标

- 本设计不直接实现测试脚本。
- 本设计不把整段自然语言输出做全文 golden file 比对。
- 本设计不要求第一阶段就引入高成本的全量 agent E2E。
- 本设计不把临时分析文档当作长期测试基线。

## 验证架构

### 第 1 层：静态契约层

这一层继续以 `/.github/workflows/skills-integration-tests.yml` 为基础，聚焦“安装和产物契约”。

主要检查：

- assistant 安装目标是否正确
- 安装后的 skill 列表是否正确
- `.architecture/` 最小结构和关键文件是否存在
- 禁止产物、legacy 路径、临时目录、嵌套 `.git` 是否不存在
- 安装结果是否没有产生额外副作用

这层回答：`skill 是否被正确安装并建立了静态目录契约`。

### 第 2 层：流程场景层

这一层验证正式流程是否成立，不关注语言措辞是否一字不差，而关注：

- 是否在正确节点停机
- 是否在正确节点回指 `setup-architect`
- 是否区分完整 setup 与模板替换分支
- 是否在缺前置时阻止后续步骤继续发生
- 是否在成功路径上把结果写到正确位置

这层回答：`skill 的主流程和关键分支是否稳定`。

### 第 3 层：行为回归层

这一层为关键路径准备固定 prompt 和固定 fixture，长期重放。断言重点不放在回复措辞，而放在行为不变量：

- 是否读取当前模板
- 是否遵守当前模板顶层结构
- 是否覆盖了强制信息块
- 是否在已有目标文件时要求确认
- 是否保留核心成员和核心原则

这层回答：`以前保证过的关键行为是否回退`。

### 第 4 层：对抗边界层

这一层专门喂模糊、危险、半完整、容易诱导 skill 乱补的输入，例如：

- 只给模板片段，不给完整模板
- 只缺一个前置文件
- 已有目标方案文件但用户没有同意覆盖
- 自定义模板无法安全承载必填信息块
- 主题同时命中多个 solution type

这层回答：`高压和模糊输入下，skill 是否还能守住硬规则`。

## 执行节奏

- `提交前`：至少通过静态契约层，以及受影响 skill 的关键流程场景层。
- `合并前`：补齐关键行为回归层。
- `发布前`：加跑对抗边界层。
- `修改 SKILL.md 或 references 后`：必须重跑对应 skill 的流程场景层和行为回归层，因为这类改动最容易造成规则漂移。

## 夹具策略

测试不直接依赖真实业务仓库，而是使用小型 fixture 仓库组合出稳定前置条件。至少保留以下几类：

- `empty-project`：无 `.architecture/`
- `complete-architecture-default-template`：前置完整，使用默认模板
- `complete-architecture-custom-template`：前置完整，使用明显不同的自定义模板
- `partial-architecture-missing-one-file`：三类关键前置文件按参数化方式各缺一个
- `existing-solution-file`：目标 slug 已存在
- `template-replacement-inputs`：完整 Markdown、路径、链接、片段输入、口头描述输入

fixture 的目标是稳定复现“环境状态”，而不是模拟真实生产规模。

## 统一断言模型

每个测试先判断结果分类，再断言不变量。推荐统一使用以下结果类型：

- `STOP_AND_REDIRECT`：停止并回指其他 skill 或前置动作
- `STOP_AND_ASK`：停止并向用户补问、确认或要求补充材料
- `SUCCESS_INIT`：成功初始化或补齐环境
- `SUCCESS_REPLACE_TEMPLATE`：成功整体替换模板
- `SUCCESS_CREATE`：成功创建新 solution 文档
- `SUCCESS_SAVE_AS`：已有文件存在时，改为另存或等待另存决定

统一断言分 4 组：

### 1. 路径不变量

- 是否写到了指定目录
- 是否误写到 legacy 路径或无关路径
- 是否出现嵌套目录或多余副产物

### 2. 结构不变量

- `.architecture/` 结构是否完整
- 当前模板的顶层结构是否被保留
- 是否新增了模板外的顶层章节

### 3. 语义不变量

- 是否包含必需语义块
- 是否保留核心成员和核心原则
- 是否在多类型主题下选择了成员并集

### 4. 安全不变量

- 缺前置时是否停止，而不是自动脑补
- 已有目标文件时是否禁止直接覆盖
- 模板映射不安全时是否停止询问
- 只替换模板时是否避免重跑完整 setup

## Case 模板

每个测试用例统一使用下面结构，避免后续扩展时风格漂移：

catalog 也允许可选的多轮 `turns` 定义，用来明确回合边界；未声明 `turns` 的 case 仍按单轮模型处理。

```markdown
### CASE-ID

- Skill: `setup-architect` | `create-technical-solution`
- Layer: `静态契约层` | `流程场景层` | `行为回归层` | `对抗边界层`
- Fixture: `<fixture-name>`
- Purpose: `<这个 case 想锁住的规则>`
- Prompt: `<固定输入或对话条件>`
- Expected Result: `STOP_AND_REDIRECT` | `STOP_AND_ASK` | `SUCCESS_INIT` | `SUCCESS_REPLACE_TEMPLATE` | `SUCCESS_CREATE` | `SUCCESS_SAVE_AS`
- Assert Paths: `<路径不变量>`
- Assert Structure: `<结构不变量>`
- Assert Semantics: `<语义不变量>`
- Assert Safety: `<安全不变量>`
- Forbidden Behavior: `<明确禁止发生的行为>`
```

## `setup-architect` 用例矩阵

### 第一阶段必补

- `SA-01 新仓初始化`
  - 目的：锁定最基础的 setup 成功路径。
  - 关键断言：创建 `.architecture/technical-solutions/`、`.architecture/templates/`、`.architecture/templates/technical-solution-template.md`、`.architecture/members.yml`、`.architecture/principles.md`。
- `SA-02 重复执行幂等`
  - 目的：防止重复 setup 产生嵌套目录、重复模板、legacy 产物。
  - 关键断言：不生成 `.architecture/.architecture`，不生成重复模板，不出现 legacy 路径或临时副产物。
- `SA-07 模板替换前置不满足`
  - 目的：防止模板替换路径偷偷补环境。
  - 关键断言：缺 `.architecture/templates/`、模板、成员或原则文件时必须停机，要求先完成完整 setup。
- `SA-08 模板输入不完整`
  - 目的：防止局部 merge、默认补全和自动生成。
  - 关键断言：只给 section 片段、patch 或口头描述时必须拒绝；不能自动补剩余模板。
- `SA-13 初始化尾声未回答时必须停下`
  - 目的：锁定初始化尾声的多轮停机边界。
  - 关键断言：第一轮在模板定制问题处必须停为 `STOP_AND_ASK`；未收到回答前不能继续进入成功分支。
- `SA-15 成员定制未完成时优先停在第 3 步`
  - 目的：防止把成员、原则、结构复核合并成一个整体检查后继续往下跳。
  - 关键断言：当成员定制所需上下文不足时，只能停在第 3 步，且不得进入第 4 至 6 步。
- `SA-16 原则定制未完成时优先停在第 4 步`
  - 目的：锁定“第一个未完成步骤优先”的串行门禁。
  - 关键断言：当成员已完成但原则定制所需上下文不足时，只能停在第 4 步，且不得进入第 5 至 6 步。
- `SA-17 结构复核未完成时优先停在第 5 步`
  - 目的：防止在结构尚未复核通过时提前进入模板确认。
  - 关键断言：当第 5 步未完成时，只能停在结构复核，且不得进入第 6 步。

### 第二阶段补齐

- `SA-03 仅缺部分文件`
  - 关键断言：只补缺失项，已有项不应被无提示覆盖。
- `SA-04 用户不自定义模板`
  - 关键断言：用户明确“不需要/保持当前模板”时，当前模板内容保持不变。
- `SA-05 初始化尾声替换模板`
  - 关键断言：接受完整 Markdown 后做整文件替换，不做局部 merge。
- `SA-06 安装后单独替换模板`
  - 关键断言：只处理模板替换，不重跑完整 setup。
- `SA-14 初始化尾声第二轮接受完整模板替换`
  - 关键断言：使用多轮 `turns` 表达第二轮输入后，允许进入 `SUCCESS_REPLACE_TEMPLATE`，且仍保持整文件替换语义。

### 第三阶段扩展

- `SA-09 成员定制不破坏核心成员`
  - 关键断言：核心成员保留，只允许增补专家角色。
- `SA-10 原则定制不破坏核心原则`
  - 关键断言：核心原则保留，并覆盖边界、测试、安全合规、决策标准等最低范围。
- `SA-11 完成后结构校验`
  - 关键断言：总结前关键文件均已存在，且无 legacy `.architecture/solutions`、`.architecture/plans`、`.architecture/reviews`。
- `SA-12 不应引入无关产物`
  - 关键断言：不会生成 `CLAUDE.md`、`agent_docs`、嵌套 `.git`、随机 temp 目录。

## `create-technical-solution` 用例矩阵

### 第一阶段必补

- `CTS-01 前置全缺失`
  - 目的：锁定最关键停机行为。
  - 关键断言：立即停止；明确回指 `setup-architect`；不能自动创建 `.architecture/*`。
- `CTS-02 单项前置缺失`
  - 目的：避免“少一个也先跑”这种半继续行为。
  - 关键断言：`.architecture/members.yml`、`.architecture/principles.md`、`.architecture/templates/technical-solution-template.md` 任缺其一都必须停机。
- `CTS-04 自定义模板优先`
  - 目的：验证 skill 真正围绕当前模板，而不是默认模板。
  - 关键断言：输出遵守当前自定义模板顶层结构，不偷偷回退默认结构。
- `CTS-07 模板语义无法安全映射`
  - 目的：防止在模板承载不了必填信息块时擅自写文档。
  - 关键断言：必须停下来问用户；不能擅自加新顶层章节。
- `CTS-08 已有目标文件`
  - 目的：防止直接覆盖已有技术方案。
  - 关键断言：必须先询问覆盖或另存；不能直接覆盖。

### 第二阶段补齐

- `CTS-03 标准成功路径`
  - 关键断言：在 `.architecture/technical-solutions/<slug>.md` 产出正式方案文档，而不是聊天式文本。
- `CTS-05 不新增模板外的顶层章节`
  - 关键断言：允许加小节、表格，但不能新增模板外顶层章节。
- `CTS-06 必填信息块完整映射`
  - 关键断言：覆盖问题背景、目标/非目标、约束依赖、推荐方案、备选与权衡、详细设计、风险缓解、实施建议、评审关注点、未决问题。
- `CTS-09 用户不确认覆盖`
  - 关键断言：原文件保持不变；应停止或转入 save-as 路径。

### 第三阶段扩展

- `CTS-10 多类型主题成员并集`
  - 关键断言：按并集选择成员，且 `system architect` 必须参与。
- `CTS-11 单独运行也能成立`
  - 关键断言：在前置完整时，不依赖“刚刚执行过 setup-architect”这一隐含上下文。
- `CTS-12 不伪造前置内容`
  - 关键断言：当前置不完整时，不脑补成员、原则、模板，不边补环境边写 solution。

## 优先级与落地顺序

### Phase 1：先锁硬规则

优先补以下 case：

- `SA-01`
- `SA-02`
- `SA-07`
- `SA-08`
- `SA-13`
- `CTS-01`
- `CTS-02`
- `CTS-04`
- `CTS-07`
- `CTS-08`

这一阶段优先解决“会不会乱跑、会不会乱补、会不会乱覆盖”。

### Phase 2：补主成功路径和稳定回归

- `SA-03`
- `SA-04`
- `SA-05`
- `SA-06`
- `SA-14`
- `CTS-03`
- `CTS-05`
- `CTS-06`
- `CTS-09`

这一阶段把成功路径、模板适配和语义完整性补齐。

### Phase 3：补治理型与压力型测试

- `SA-09`
- `SA-10`
- `SA-11`
- `SA-12`
- `CTS-10`
- `CTS-11`
- `CTS-12`

这一阶段补成员/原则治理、多类型主题和边界防御。

## 错误分类

测试失败后统一按下面类别归因，方便后续修正文档或脚本：

- `契约破坏`：目录、文件、安装目标、路径不符合约定
- `流程漂移`：该停不停、该问不问、该回指不回指
- `行为回退`：曾保证的模板、覆盖、停机、保留规则不再成立
- `边界失守`：在模糊或危险输入下擅自脑补、覆盖、扩展结构

## 待决契约

以下两点在实现测试前应先被正式规则确认，否则脚本断言会分叉：

- 当 `.architecture/members.yml`、`.architecture/principles.md`、`.architecture/templates/technical-solution-template.md` 都存在，但 `.architecture/technical-solutions/` 缺失时，`create-technical-solution` 应该自动创建输出目录，还是停机提示。
- `<slug>` 的规范化规则是否需要固定，否则同一主题可能出现不同文件名，导致路径断言不稳定。

## 验收标准

当这套设计落地后，应能稳定达到以下状态：

- 修改 skill 主文档或引用文档后，测试能快速指出是契约问题、流程问题、行为回退还是边界问题。
- 两个 skill 的核心成功路径、关键停机路径和高风险分支都有固定回归 case。
- 测试断言以不变量为核心，而不是以整段自然语言相似度为核心。
- 临时分析文档不会再被误当成长期测试基线。
