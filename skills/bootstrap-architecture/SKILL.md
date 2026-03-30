---
name: bootstrap-architecture
description: 在项目中初始化或补跑 `.architecture/` 基础结构，或在初始化已完成后替换技术方案模板时使用。
---

# Bootstrap Architecture

为当前项目建立或修复 `.architecture/` 基础结构，并管理当前生效的技术方案模板。

## 定位

- `bootstrap-architecture` 只负责 `.architecture/` 初始化与技术方案模板管理。
- 如果用户要创建、补写或更新正式技术方案文档，转到 `create-technical-solution`。

## 完成标准

- 路径 A：`.architecture/members.yml`、`.architecture/principles.md`、`.architecture/templates/technical-solution-template.md` 已存在，且内容已按项目现实完成初始化或补跑。
- 最终输出必须明确当前生效模板是默认模板还是用户自定义模板。

- 路径 B：`.architecture/templates/technical-solution-template.md` 已被整体替换为用户提供的完整输入，且不会改写 `.architecture/members.yml` 与 `.architecture/principles.md`。

## 高层工作流

### 1. 选择执行路径

- 输入：用户请求、当前项目上下文，以及 `.architecture/` 是否已经建立。
- 动作：
  - 若目标是首次建立 `.architecture/`、补跑初始化，或当前缺少 `.architecture/members.yml`、`.architecture/principles.md`、`.architecture/templates/technical-solution-template.md` 中的任一文件，走路径 A。
  - 若目标只是整体替换技术方案模板，且上述三个文件都已存在，走路径 B。
- 完成条件：已明确当前请求只能进入路径 A 或路径 B 之一。
- 停止条件：若用户目标在“完整初始化”和“仅替换模板”之间仍不明确，则返回 `STOP_AND_ASK`，停在路径判定，不得进入后续步骤。

### 2. 分析项目（路径 A）

- 输入：当前仓库的语言、框架、测试/CI、部署方式和目录结构。
- 动作：识别宿主项目的基础上下文，作为成员和原则初始化的依据。
- 完成条件：已经形成足以支撑成员定制和原则定制的项目上下文摘要。
- 停止条件：若仓库上下文明显不足，无法安全判断成员或原则取向，则返回 `STOP_AND_ASK`，停在第 2 步。

### 3. 定制架构团队（路径 A）

- 输入：第 2 步形成的项目上下文，以及 [references/member-customization.md](references/member-customization.md) 与 `templates/members-template.yml`。
- 动作：直接生成定制后的 `.architecture/members.yml`，必要时同时创建 `.architecture/` 目录；不预先复制模板文件。
- 完成条件：`.architecture/members.yml` 已形成，且成员集合能覆盖当前项目需要的关键专家角色。
- 停止条件：若当前项目上下文仍不足以完成成员定制，则返回 `STOP_AND_ASK`，继续等待。未完成第 3 步，不得进入第 4 步。

### 4. 定制架构原则（路径 A）

- 输入：第 2 步形成的项目上下文，以及 [references/principles-customization.md](references/principles-customization.md) 与 `templates/principles-template.md`。
- 动作：直接根据模板定制生成 `.architecture/principles.md`，不预先复制模板文件。
- 完成条件：`.architecture/principles.md` 已成为宿主项目的判断基线，后续技术方案编写与架构评审可以直接消费。
- 停止条件：若当前项目上下文仍不足以完成原则定制，则返回 `STOP_AND_ASK`，继续等待。未完成第 4 步，不得进入第 5 步。

### 5. 确认当前生效模板并收尾（路径 A）

- 输入：`.architecture/` 基础结构、默认模板文件，以及用户是否要定制模板的明确回答。
- 动作：
  - 必须先询问用户是否需要定制技术方案模板。
  - 若用户明确表示保留当前模板，按需创建 `.architecture/templates/` 目录，并复制默认模板到 `.architecture/templates/technical-solution-template.md`。
  - 若用户明确表示需要替换模板，只接受完整 Markdown、文件路径或链接地址，并整体写入 `.architecture/templates/technical-solution-template.md`。
- 完成条件：当前生效模板已经明确落位，且最终状态可被表述为“默认模板”或“已替换为用户自定义模板”之一。
- 停止条件：
  - 若用户尚未明确回答是否需要定制模板，则返回 `STOP_AND_ASK`，此时不允许输出最终初始化摘要。
  - 若用户提供的不是完整 Markdown、文件路径或链接地址，则继续索要，不得自动生成、局部编辑或内容合并。

### 6. 整体替换技术方案模板（路径 B）

- 输入：`.architecture/templates/technical-solution-template.md`、`.architecture/members.yml`、`.architecture/principles.md` 均已存在，且用户已提供完整 Markdown、文件路径或链接地址。
- 动作：不重跑初始化流程，只整体替换 `.architecture/templates/technical-solution-template.md`。
- 完成条件：模板文件已被整体替换，且输出已明确目标文件和输入来源。
- 停止条件：
  - 若任一前置文件缺失，则必须停止，并要求用户先完成完整初始化。
  - 若用户未提供完整 Markdown、文件路径或链接地址，则继续索要；不允许自动生成模板、局部编辑或内容合并。

## 行为契约

1. `bootstrap-architecture` 不是安装入口；不得承担运行时识别、目标目录解析或复制 skill 目录的职责。
2. 主路径只有两条：完整初始化（路径 A）和整体替换模板（路径 B）；不得在两条路径之间隐式混跑。
3. 模板替换分支只接受完整 Markdown、文件路径或链接地址。
4. 只允许整体替换 `.architecture/templates/technical-solution-template.md`；不允许自动生成模板、局部编辑、内容合并或“恢复默认模板”这类隐式变体。
5. 路径 B 不得重跑 `.architecture/members.yml` 和 `.architecture/principles.md` 的初始化。
6. 只有在模板最终状态已经明确后，才允许输出初始化完成摘要或模板更新摘要。
7. 主文件与引用文件中的规则必须保持一致；若出现冲突，以主文件为准并应立即修正文档。

## 结果汇报格式

路径 A：

```text
Tech Solution 设置完成

技术方案模板：默认模板 / 已替换为用户自定义模板

接下来你可以：
- 编写技术方案文档
```

路径 B：

```text
技术方案模板已更新

位置：.architecture/templates/technical-solution-template.md
来源：用户提供的完整 Markdown / 文件路径 / 链接地址
```

## 详细说明

- [成员定制说明](references/member-customization.md)
- [原则定制说明](references/principles-customization.md)
- [模板替换细则](references/technical-solution-template-customization.md)
