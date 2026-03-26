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

- 创建最小 `.architecture/` 目录结构
- 安装模板、配置种子、`members.yml`、`principles.md`
- 按项目现实定制成员与原则，并保证原则可直接用于技术方案与架构评审
- 确认 `.architecture/templates/technical-solution-template.md` 最终采用默认模板或用户提供的自定义模板

## 工作流

### 1. 分析项目

识别语言、框架、测试/CI、部署方式和目录结构。

### 2. 安装架构框架

按 [references/installation-procedures.md](references/installation-procedures.md) 创建目录，并安装模板、配置种子和基础文件。

### 3. 定制架构团队

按 [references/member-customization.md](references/member-customization.md) 设置专家成员。

### 4. 定制架构原则

按 [references/principles-customization.md](references/principles-customization.md) 补充与项目现实一致的原则；后续技术方案和架构评审会将这些原则作为必需输入。

### 5. 复核正式项目结构并安全清理

按安装文档验证最终结构，若结构不符，返回第 2 步重新安装。

### 6. 最后确认技术方案模板并收尾

按 [references/technical-solution-template-customization.md](references/technical-solution-template-customization.md) 完成技术方案模板确认，并在此步骤中一并提供初始化摘要：

```text
Tech Solution 设置完成

技术方案模板：默认模板 / 已替换为用户自定义模板

接下来你可以：
- 编写技术方案文档
```

## 安装后定制技术方案模板

如果项目已完成 setup 且用户只需替换技术方案模板，不要重跑上述初始安装流程，直接读取 [references/technical-solution-template-customization.md](references/technical-solution-template-customization.md)。
