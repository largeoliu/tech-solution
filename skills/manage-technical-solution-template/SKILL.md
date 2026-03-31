---
name: manage-technical-solution-template
description: 处理技术方案模板的自定义替换——用户确定要使用自定义模板时调用。
---

# 管理技术方案模板

将用户提供的自定义模板写入 `.architecture/templates/technical-solution-template.md`。

## 职责边界

- **仅负责：** 技术方案模板文件的自定义替换

## 完成标准

## 完成标准

- `.architecture/templates/technical-solution-template.md` 存在并包含用户提供的内容
- 输出明确标识目标文件和输入来源

## 工作流

### 步骤 1：获取用户模板

用户需提供以下之一：
- 完整的 Markdown 内容
- 文件路径（相对或绝对路径）
- 链接地址

### 步骤 2：写入模板

将用户提供的内容写入 `.architecture/templates/technical-solution-template.md`。

如需创建目录，先执行：
```bash
mkdir -p .architecture/templates
```

**停止条件：** 如果输入不是完整的 Markdown、文件路径或链接，继续询问；不要自动生成、部分编辑或合并

### 步骤 3：输出结果

```text
技术方案模板已更新

位置：.architecture/templates/technical-solution-template.md
来源：用户提供的完整 Markdown / 文件路径 / 链接地址
```

## 行为约定

1. 仅接受完整的 Markdown、文件路径或链接作为输入
2. 仅执行完全替换；不进行部分编辑、合并或自动生成
3. 仅在模板写入后才输出最终结果

## 相关技能

- `create-technical-solution`：使用当前模板创建技术方案文档
