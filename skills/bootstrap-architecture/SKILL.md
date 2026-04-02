---
name: bootstrap-architecture
description: 用于初始化或修复项目中的 `.architecture/` 目录结构——包括成员、原则和技术方案模板的初始化。
---

# 初始化架构

为当前项目建立或修复 `.architecture/` 目录结构。

## 定位

- 负责 `.architecture/` 初始化。

## 完成标准

- `.architecture/members.yml` 存在并反映项目的实际成员组成
- `.architecture/principles.md` 存在并作为项目的决策基线
- `.architecture/templates/technical-solution-template.md` 存在，可以是默认技术方案模板或自定义模板
- 最终输出必须明确说明模板是默认的还是自定义的

## 高层工作流

### 1. 分析项目

- 输入：当前仓库的语言、框架、测试/CI、部署方式和目录结构。
- 操作：识别项目的基础上下文，作为成员和原则初始化的依据。
- 完成：形成项目上下文摘要，每项结论必须标注来源类型（代码结构/目录语义/现有文档）和具体依据。不允许"常识推断"类结论。
  输出格式：结构化的项目上下文清单，带上下文编号，供第 2 步和第 3 步直接引用。
  覆盖检查：分析完成后，明确标注哪些成员角色和原则章节在当前项目上下文中找到了依据，哪些没有。不因"有缺口"而停止分析。这些标注将指导第 2 步（跳过无依据的角色）和第 3 步（跳过无依据的章节）。
- 停止条件：如果仓库上下文不足以安全确定成员或原则，返回 `STOP_AND_ASK`。

### 2. 定制架构团队

- 输入：步骤 1 的项目上下文，加上 [references/member-customization.md](references/member-customization.md) 和 `templates/members-template.yml`。
- 操作：生成定制的 `.architecture/members.yml`。
  每位成员生成时必须在角色级别标注 `依据`，格式为：
  ```yaml
  - id: xxx
    name: "xxx"
    依据: [引用第1步上下文编号]
    specialties: [...]
    disciplines: [...]
  ```
  逐项验证流程：
  - 遍历模板中的每个成员角色
  - 对每个角色，检查第 1 步项目上下文中是否存在相关依据
  - 如果存在 → 生成该角色，并引用该依据的上下文编号
  - 如果不存在 → 跳过该角色，不生成
  - 最终 members.yml 只保留有项目上下文依据的角色（角色数量取决于项目上下文，不固定）
  - 第 2 步本身必须完整执行，不可跳过
  - 最终来源汇总中记录：模板中有 N 个角色，M 个有依据并生成，X 个因无依据已跳过
- 完成：`.architecture/members.yml` 存在，成员集合涵盖当前项目的关键专家角色。
- 停止条件：如果项目上下文不足以进行成员定制，返回 `STOP_AND_ASK`。步骤 2 必须在步骤 3 之前完成。

### 3. 定制架构原则

- 输入：步骤 1 的项目上下文，加上 [references/principles-customization.md](references/principles-customization.md) 和 `templates/principles-template.md`。
- 操作：从模板生成定制的 `.architecture/principles.md`。
  每个"本项目事实"条目必须包含 `依据` 字段：
  ```markdown
  - [条目] — 依据：[第1步上下文编号]（来源类型：代码结构/目录语义/现有文档）
  ```
  逐章节验证流程：
  - 遍历模板七个章节中的每个章节
  - 对每个章节，检查第 1 步项目上下文中是否存在相关依据
  - 如果存在 → 生成该章节，并引用各条目的依据编号
  - 如果不存在 → 跳过该章节，不生成
  - 最终 principles.md 只保留有项目上下文依据的章节（章节数量取决于项目上下文，不固定）
  - 第 3 步本身必须完整执行，不可跳过
  - 最终来源汇总中记录：模板有 7 个章节，M 个有依据并生成，X 个因无依据已跳过
- 完成：`.architecture/principles.md` 可以作为后续技术方案编写和架构评审的项目决策基线。
- 停止条件：如果项目上下文不足以进行原则定制，返回 `STOP_AND_ASK`。步骤 3 必须在步骤 4 之前完成。

### 4. 确认技术方案模板处理并完成

- 输入：用户关于技术方案模板定制的明确答复。
- 操作：
  - 必须询问用户："是否要自定义技术方案模板？"
  - 如果用户明确表示不要自定义：
    - 如有需要创建 `.architecture/templates/` 目录
    - 将默认模板写入 `.architecture/templates/technical-solution-template.md`
  - 如果用户明确表示要自定义：
    - 调用 `manage-technical-solution-template` 技能
    - 用户会提供自定义模板内容
- 完成：模板状态明确声明为"默认模板"或"自定义模板"，同时展示上下文依据汇总：
  ```
  上下文依据汇总：
  - members.yml：模板 N 个角色中，M 个有项目上下文依据并生成，X 个因无依据已跳过
  - principles.md：模板 7 个章节中，M 个有项目上下文依据并生成，X 个因无依据已跳过

  所有生成项的依据均已追溯到第 1 步项目上下文，无模板填充、无待确认项。
  已跳过的项：该章节在当前项目上下文中无依据，无需生成。
  ```
- 停止条件：
  - 如果用户尚未明确回答是否自定义模板，返回 `STOP_AND_ASK`

## 默认模板

默认模板位于 [templates/technical-solution-template.md](templates/technical-solution-template.md)。

## 行为约定

1. 主路径仅为初始化；不得隐式混合模板替换。
2. 仅在模板状态确认后才输出初始化完成摘要。

## 结果格式

```text
Tech Solution 设置完成

技术方案模板：默认模板 / 已替换为用户自定义模板

接下来你可以：
- 编写技术方案文档（使用 create-technical-solution）
- 定制技术方案模板（使用 manage-technical-solution-template）
```

## 详细参考

- [成员定制说明](references/member-customization.md)
- [原则定制说明](references/principles-customization.md)
