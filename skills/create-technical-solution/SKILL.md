---
name: create-technical-solution
description: 在用户请求创建、补写或更新技术方案，需要基于架构成员协作形成正式方案时使用。
---

# 创建技术方案

按当前项目模板产出正式技术方案。主技能文件只定义职责边界和高层流程；详细过程、模板适配和分析重点分别放在参考文档中。

## 技能定位

- 负责把主题、约束和架构成员观点收敛为可评审的技术方案文档。
- 依赖项目约定文件，而不是临时口头约定：
  - `.architecture/members.yml`
  - `.architecture/principles.md`
  - `.architecture/templates/technical-solution-template.md`
- 始终先读取当前 `.architecture/templates/technical-solution-template.md`，不得假设固定章节名、固定顺序或默认模板结构。
- 参考文档定义的是必需信息、分析重点和落位规则，不是默认模板章节清单。
- 技术方案正文结构始终以当前模板为准，不再发明第二套章节。
- 若当前模板无法承载必需信息，且又不能在不破坏模板结构的前提下自然落位，则停止并向用户确认，不得擅自发明新顶级章节。
- 只在需要正式技术方案文档时使用；如果只是初始化 `.architecture/`、补跑安装或替换模板，转到 `setup-architect`。

## 完成标准

- 主题、目标、非目标、约束、影响范围已经明确。
- 参与成员选择有依据，且至少包含系统架构师。
- 共享上下文已覆盖原则、现状、已有实现、关键约束和当前模板结构。
- 成员独立输入与协作收敛结果完整，并已抽象为标准信息块。
- 分阶段中间产物已按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示：每位参与成员各 1 份结构化 `专家产物`，以及 1 份结构化 `协作收敛纪要`；这些中间产物默认不作为侧车文档落盘。
- 最终文档在不破坏当前模板结构的前提下承载全部必需信息，并显式写出边界与职责、依赖关系。
- 结果已保存到 `.architecture/technical-solutions/[文件名].md`，且没有未经确认覆盖已有文件。

## 高层工作流

### 1. 定题与范围判断

输入可以是方案主题、需求描述、已有文档路径，或用户给出的上下文片段。

先明确：问题、目标与非目标、约束与依赖、影响范围、相关需求。主题模糊时先澄清，再生成安全的短横线风格文件名。

### 2. 检查前置条件

确保 `.architecture/technical-solutions/` 存在。

确认以下文件全部存在：

- `.architecture/members.yml`
- `.architecture/principles.md`
- `.architecture/templates/technical-solution-template.md`

任一缺失时立即停止，明确说明初始化未完成，并引导用户先使用 `setup-architect`。

### 3. 加载成员并选择参与者

读取 `.architecture/members.yml`。

默认至少包含系统架构师。非简单方案通常加入可维护性专家；涉及业务语义加入领域专家；涉及认证、权限、隐私、数据保护或合规时加入安全专家；涉及延迟、吞吐、容量或成本效率时加入性能专家。跨系统、高风险或平台级主题升级为当前名册中的全部核心成员；如 `.architecture/members.yml` 中存在贴合主题的自定义专家，也一并纳入。

### 4. 构建共享上下文并读取当前模板

整合 `.architecture/principles.md`、代码与配置、Repo Wiki、现有实现、相关文档和外部约束，并读取当前模板的标题、章节层级和已有结构。原则文档是判断标准，不是可选背景；当前模板是唯一正文骨架来源。

### 5. 组织成员独立输入

要求每个参与成员基于共享上下文，按统一字段独立产出自己的判断，不要直接重复别人的结论。

每个成员完成独立输入后，立即按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示该成员的结构化 `专家产物`。

详细格式见 [references/solution-process.md](references/solution-process.md)。

### 6. 协作收敛、生成信息块并落位到模板

把成员输入收敛成共同结论、争议点、候选方案对比、选定方向、原则冲突与取舍、未决问题，再整理成标准信息块，并无侵入落位到当前模板。

完成收敛后、生成最终文档前，必须先按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示 1 份结构化 `协作收敛纪要`。如果用户在 `专家产物` 或 `协作收敛纪要` 展示后新增约束、修正目标或调整范围，先说明失效范围，再从该文档定义的最近受影响阶段边界重进。

标准信息块见 [references/solution-process.md](references/solution-process.md)。

模板落位规则见 [references/template-adaptation.md](references/template-adaptation.md)。

方案类型的分析重点见 [references/solution-analysis-guide.md](references/solution-analysis-guide.md)。

### 7. 生成、保存并汇报

将最终文档写入 `.architecture/technical-solutions/[主题-短横线文件名].md`。

若目标文件已存在且用户未明确要求更新，先确认覆盖还是另存；不要静默覆盖无关文档。

## 详细说明

- [标准产出流程](references/solution-process.md)
- [阶段性播报协议](references/progress-transparency.md)
- [模板适配规则](references/template-adaptation.md)
- [方案类型分析指引](references/solution-analysis-guide.md)

## 行为契约

执行此技能时，始终遵守以下契约：

1. 读取当前模板
2. 生成标准信息块
3. 分阶段在对话中展示 `专家产物` 与 `协作收敛纪要`
4. 将信息块无侵入落到当前模板
5. 无法展示稳定、可解释、可归因的中间产物，或无法安全落位时停止并确认

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
