---
name: create-technical-solution
description: 在用户请求创建、补写或更新技术方案，需要基于架构成员协作形成正式方案时使用。
---

# 创建技术方案

按当前项目模板产出正式技术方案。主技能文件只定义职责边界和高层流程；详细过程、模板适配和分析重点分别放在参考文档中。

## 技能定位

- 负责把主题、约束、架构成员观点和阶段性中间产物收敛为可评审的正式技术方案文档。
- 依赖项目约定文件，而不是临时口头约定：
  - `.architecture/members.yml`
  - `.architecture/principles.md`
  - `.architecture/templates/technical-solution-template.md`
- 当前 `.architecture/templates/technical-solution-template.md` 是唯一正文骨架来源；它可能是默认模板，也可能是用户替换后的自定义模板。
- 必须先读取当前生效模板，再判断方案类型，再选择参与成员。
- 主 skill 负责唯一主路径、关键停机规则、最小信息块摘要、最小质量门槛和完成标准；引用文档负责完整细则。
- 只在需要正式技术方案文档时使用；如果只是初始化 `.architecture/`、补跑安装或替换模板，转到 `setup-architect`。

## 主文档可见的最小信息块

- 问题与背景
- 目标与非目标
- 约束与依赖
- 推荐方案
- 备选方案与权衡
- 详细设计
- 风险与缓解
- 实施建议
- 评审关注点
- 未决问题

这些是最小必须覆盖的语义内容，而不是固定章节名。

如果当前生效模板没有与这些信息块一一对应的显式章节，也不能跳过它们；必须按模板语义把内容落到现有章节、小节、表格或列表中。

如果某个必需信息块无法在不破坏模板意图、且不新增新的一级章节的前提下安全落位，立即停止并向用户确认。

## 主文档可见的最小质量门槛

- 每个标准信息块都已生成。
- 分阶段中间产物已按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示。
- 至少存在一个被认真比较过的备选方案，并写明未选原因。
- 每个主要风险都包含影响、概率判断和缓解方向。
- 已体现边界与职责、依赖关系、实施建议和评审关注点。
- 未决问题写明缺什么信息、由谁补齐。
- 最终内容已按当前生效模板完成落位，而不是退回默认模板章节。

## 完成标准

- 主题、目标、非目标、约束、影响范围已经明确。
- 参与成员选择与方案类型一致，且至少包含系统架构师。
- 共享上下文已覆盖原则、现状、已有实现、关键约束和当前生效模板结构。
- 成员独立输入与协作收敛结果完整，并已抽象为标准信息块。
- 分阶段中间产物已按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示：每位参与成员各 1 份结构化 `专家产物`，以及 1 份结构化 `协作收敛纪要`；这些中间产物默认不作为侧车文档落盘。
- 文档已覆盖关键标准信息块，并体现备选方案、未选原因、风险判断与缓解方向。
- 已体现边界与职责、依赖关系、实施建议、评审关注点和未决问题。
- 最终内容已按当前生效模板完成落位，且保存行为符合覆盖确认规则。

## 高层工作流

### 1. 定题与范围判断

输入可以是方案主题、需求描述、已有文档路径，或用户给出的上下文片段。

先明确：问题、目标与非目标、约束与依赖、影响范围、相关需求。主题模糊时先澄清，再生成安全的短横线风格文件名。

### 2. 检查语义前置文件

确认以下文件全部存在：

- `.architecture/members.yml`
- `.architecture/principles.md`
- `.architecture/templates/technical-solution-template.md`

任一缺失时立即停止，明确说明初始化未完成，并引导用户先使用 `setup-architect`。

### 3. 读取当前生效模板

读取当前 `.architecture/templates/technical-solution-template.md` 的标题、章节层级、说明文字和现有结构。它可能是默认模板，也可能是用户替换后的自定义模板；后续正文必须服从它的实际结构。

### 4. 判断方案类型

先按 [references/solution-analysis-guide.md](references/solution-analysis-guide.md) 判断主题命中哪一类方案，再据此确定必答问题、易漏风险、评审重点和推荐参与成员。

### 5. 加载成员名册并选择参与者

读取 `.architecture/members.yml`。

默认至少包含系统架构师；再根据上一步的方案类型与名册中的自定义专家决定最终参与成员集合。

### 6. 构建共享上下文

整合 `.architecture/principles.md`、代码与配置、Repo Wiki、现有实现、相关文档和外部约束。原则文档是判断标准，不是可选背景。

### 7. 组织成员独立输入

要求每个参与成员基于共享上下文，按统一字段独立产出自己的判断，不要直接重复别人的结论。

每个成员完成独立输入后，立即按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示该成员的结构化 `专家产物`。

详细格式见 [references/solution-process.md](references/solution-process.md)。

### 8. 收敛为标准信息块

把成员输入收敛成共同结论、争议点、候选方案对比、选定方向、原则冲突与取舍、未决问题，再整理成标准信息块。

完成收敛后、生成最终文档前，必须先按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示 1 份结构化 `协作收敛纪要`。如果用户在 `专家产物` 或 `协作收敛纪要` 展示后新增约束、修正目标或调整范围，先说明失效范围，再从最近受影响的阶段边界重进。

### 9. 将信息块落位到当前模板并通过质量门槛

把标准信息块无侵入落到当前生效模板；若模板没有同名章节，则按现有结构语义落位。若无法安全落位则停止并向用户确认。生成最终文档前，逐项检查主文档可见的最小质量门槛和 [references/solution-process.md](references/solution-process.md) 的完整质量门槛。

标准信息块见 [references/solution-process.md](references/solution-process.md)。

模板落位规则见 [references/template-adaptation.md](references/template-adaptation.md)。

方案类型的分析重点见 [references/solution-analysis-guide.md](references/solution-analysis-guide.md)。

### 10. 保存并汇报结果

若三个关键文件齐全但 `.architecture/technical-solutions/` 缺失，则自动创建该目录后继续。

将最终文档写入 `.architecture/technical-solutions/[主题-短横线文件名].md`。

若目标文件已存在且用户未明确要求更新，先确认覆盖还是另存；不要静默覆盖无关文档。

## 详细说明

- [标准产出流程](references/solution-process.md)
- [阶段性播报协议](references/progress-transparency.md)
- [模板适配规则](references/template-adaptation.md)
- [方案类型分析指引](references/solution-analysis-guide.md)

## 行为契约

执行此技能时，始终遵守以下契约：

1. 先读取当前生效模板。
2. 再判断方案类型。
3. 再选择参与成员。
4. 分阶段在对话中展示 `专家产物` 与 `协作收敛纪要`。
5. 先生成标准信息块，再把它们无侵入落到当前生效模板。
6. 缺少语义前置、无法展示稳定中间产物或无法安全落位时停止并确认。

## 结果汇报格式

```text
技术方案已创建或更新：[标题]

位置：.architecture/technical-solutions/[文件名].md
参与成员：[参与成员]
过程可见产物：已展示 [成员数] 份专家产物与 1 份协作收敛纪要

关键点：
- 选定方向：[选定方向]
- 主要权衡：[主要权衡]
- 关键风险：[关键风险]
- 未决问题：[未决问题]
- 建议下一步：[建议下一步]
```

## 相关技能

- `setup-architect`：初始化 `.architecture/` 目录、成员名册、原则文档和技术方案模板。
