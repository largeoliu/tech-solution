---
name: manage-technical-solution-template
description: 用于管理技术方案模板的生命周期——在初始化期间应用默认模板，或在初始化完成后替换为自定义模板。
---

# 管理技术方案模板

确定并落地当前有效的技术方案模板到 `.architecture/templates/technical-solution-template.md`。

## 职责边界

- **仅负责：** 模板文件的确定和放置
- **不负责：** `.architecture/members.yml` 初始化、`.architecture/principles.md` 初始化或技术方案文档的创建

## 前置条件

在执行此技能之前，请验证以下文件是否存在：

- `.architecture/members.yml`
- `.architecture/principles.md`

如果任一文件缺失，请停止并先重定向到 `bootstrap-architecture` 进行初始化。

**对于独立替换场景**，还需验证：

- `.architecture/templates/technical-solution-template.md` 已存在

如果模板文件不存在，这是一个初始化场景——请重定向到 `bootstrap-architecture`。

## 完成标准

- `.architecture/templates/technical-solution-template.md` 处于最终状态
- 最终状态明确声明为"默认模板"或"自定义模板"
- 对于自定义模板场景，输出需清楚标识目标文件和输入来源

## 高层工作流

### 1. 识别场景

**输入：** 当前调用上下文——这是初始化结束时的委托还是独立替换

**操作：**
- 如果从 `bootstrap-architecture` 初始化结束时调用，使用用户的明确答复（是否自定义）
- 如果是独立调用，询问用户是保留默认模板还是替换为自定义模板

**完成：** 场景已识别

**停止条件：** 如果用户意图不明确，返回 `STOP_AND_ASK`

### 2. 执行模板放置

**默认模板路径：**
- 输入：来自 `skills/bootstrap-architecture/templates/technical-solution-template.md` 的默认模板源
- 操作：将默认模板复制到 `.architecture/templates/technical-solution-template.md`
- 如有需要，创建 `.architecture/templates/` 目录

**自定义模板路径：**
- 输入：用户提供完整的 Markdown、文件路径或链接
- 操作：
  - 仅接受完整的 Markdown、文件路径或链接
  - 文件路径可以是相对路径（相对于当前工作目录）或绝对路径
  - 直接写入到 `.architecture/templates/technical-solution-template.md`
- 停止条件：如果输入不是完整的 Markdown、文件路径或链接，继续询问；不要自动生成、部分编辑或合并

### 3. 输出结果

**默认模板结果：**
```text
技术方案模板已生成

位置：.architecture/templates/technical-solution-template.md
类型：默认模板
```

**自定义模板结果：**
```text
技术方案模板已更新

位置：.architecture/templates/technical-solution-template.md
来源：用户提供的完整 Markdown / 文件路径 / 链接地址
```

## 行为约定

1. 仅接受完整的 Markdown、文件路径或链接作为自定义模板输入
2. 仅执行完全替换；不进行部分编辑、合并或自动生成
3. 不重新初始化 `.architecture/members.yml` 或 `.architecture/principles.md`
4. 仅在模板状态确认后才输出最终结果

## 相关技能

- `bootstrap-architecture`：用于首先初始化 `.architecture/` 结构
- `create-technical-solution`：用于使用当前模板创建技术方案文档
