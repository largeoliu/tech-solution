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
- `.architecture/templates/technical-solution-template.md` 存在，可以是默认模板或自定义模板
- 最终输出必须明确说明模板是默认的还是自定义的

## 高层工作流

### 1. 分析项目

- 输入：当前仓库的语言、框架、测试/CI、部署方式和目录结构。
- 操作：识别项目的基础上下文，作为成员和原则初始化的依据。
- 完成：形成项目上下文摘要，足以支持成员和原则的定制。
- 停止条件：如果仓库上下文不足以安全确定成员或原则，返回 `STOP_AND_ASK`。

### 2. 定制架构团队

- 输入：步骤 1 的项目上下文，加上 [references/member-customization.md](references/member-customization.md) 和 `templates/members-template.yml`。
- 操作：生成定制的 `.architecture/members.yml`。
- 完成：`.architecture/members.yml` 存在，成员集合涵盖当前项目的关键专家角色。
- 停止条件：如果项目上下文不足以进行成员定制，返回 `STOP_AND_ASK`。步骤 2 必须在步骤 3 之前完成。

### 3. 定制架构原则

- 输入：步骤 1 的项目上下文，加上 [references/principles-customization.md](references/principles-customization.md) 和 `templates/principles-template.md`。
- 操作：从模板生成定制的 `.architecture/principles.md`。
- 完成：`.architecture/principles.md` 可以作为后续技术方案编写和架构评审的项目决策基线。
- 停止条件：如果项目上下文不足以进行原则定制，返回 `STOP_AND_ASK`。步骤 3 必须在步骤 4 之前完成。

### 4. 确认模板处理并完成

- 输入：用户关于模板定制的明确答复。
- 操作：
  - 必须询问用户："是否要自定义技术方案模板？"
  - 如果用户明确表示不要自定义：
    - 如有需要创建 `.architecture/templates/` 目录
    - 将默认模板写入 `.architecture/templates/technical-solution-template.md`
  - 如果用户明确表示要自定义：
    - 调用 `manage-technical-solution-template` 技能
    - 用户会提供自定义模板内容
- 完成：模板状态明确声明为"默认模板"或"自定义模板"
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
