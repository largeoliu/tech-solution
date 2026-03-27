---
name: setup-architect
description: 在项目中安装并初始化 Tech Solution，或在已完成 setup 的项目中替换/更新/自定义技术方案模板。当用户请求“安装 tech-solution”、重跑初始化、替换技术方案模板或类似表达时使用。
---

# 设置 Tech Solution

为当前项目初始化 Tech Solution。

## 定位

`setup-architect` 是项目初始化的权威流程来源：

- 首次安装时，skills 复制完成后应继续依据本目录文件完成项目初始化
- 后续如需补跑或重跑初始化，可显式调用本 skill

## 完成标准

- 创建最小 `.architecture/` 目录结构。
- 安装 `.architecture/members.yml`、`.architecture/principles.md` 和 `.architecture/templates/technical-solution-template.md`。
- 按项目现实定制成员与原则，并保证原则可直接用于技术方案与架构评审。
- `.architecture/templates/technical-solution-template.md` 已明确为当前生效模板。
- 当前生效模板可以是默认模板，也可以是用户替换后的自定义模板。

## 使用路径

### 路径 A：完整初始化

适用于首次安装、补跑初始化，或需要重新建立 `.architecture/` 基础结构的情况。

### 路径 B：仅替换技术方案模板

适用于 setup 已完成，且用户只想替换 `.architecture/templates/technical-solution-template.md` 的情况。

## 路径 A：完整初始化

### 1. 安装架构框架

按 [references/installation-procedures.md](references/installation-procedures.md) 创建目录，并安装模板和基础文件。

### 2. 分析项目

识别语言、框架、测试/CI、部署方式和目录结构。

### 3. 定制架构团队

按 [references/member-customization.md](references/member-customization.md) 设置专家成员。

### 4. 定制架构原则

按 [references/principles-customization.md](references/principles-customization.md) 把 `.architecture/principles.md` 定制成宿主项目的上下文和判断基线；后续技术方案编写与架构评审会将这些原则作为必需输入。

### 5. 复核正式项目结构

按安装文档验证最终结构，若结构不符，返回第 1 步重新安装。

### 6. 确认当前生效模板并收尾

- 必须先询问用户是否需要定制技术方案模板。
- 若用户尚未明确回答，则返回 `STOP_AND_ASK`，继续等待；此时不允许输出最终“Tech Solution 设置完成”摘要。
- 若回答“不需要”或明确表示保留当前模板，才可保留当前 `.architecture/templates/technical-solution-template.md`；首次安装通常保留默认模板，重跑初始化时也可能保留项目现有模板。
- 若回答“需要”，先校验 `.architecture/templates/technical-solution-template.md`、`.architecture/members.yml`、`.architecture/principles.md` 已存在；若 setup 不完整，则必须停止，并要求用户先完成完整初始化。
- 定制分支只接受完整 Markdown、文件路径或链接地址。
- 只允许整体替换 `.architecture/templates/technical-solution-template.md`；不允许自动生成模板、局部编辑或内容合并。
- 只有在用户明确选择保留当前模板，或已提供有效完整输入并完成整体替换后，才允许输出最终“Tech Solution 设置完成”摘要。
- 详细输入处理和场景摘要见 [references/technical-solution-template-customization.md](references/technical-solution-template-customization.md)。

初始化摘要：

```text
Tech Solution 设置完成

技术方案模板：默认模板 / 已替换为用户自定义模板

接下来你可以：
- 编写技术方案文档
```

## 路径 B：仅替换技术方案模板

- 不重跑初始化流程。
- 先校验 `.architecture/templates/technical-solution-template.md`、`.architecture/members.yml`、`.architecture/principles.md` 已存在；若任一缺失，则必须停止，并要求用户先完成完整初始化。
- 直接要求用户提供完整 Markdown、文件路径或链接地址。
- 收到后整体替换 `.architecture/templates/technical-solution-template.md`。
- 不允许自动生成模板、局部编辑或内容合并。
- 详细输入处理和场景摘要见 [references/technical-solution-template-customization.md](references/technical-solution-template-customization.md)。
