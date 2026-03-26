# 技术方案模板定制与替换

此文档是 `setup-architect` 中模板替换分支的补充说明，用来展开输入细节、场景差异和摘要文案。

主 skill 已定义模板替换的硬规则：

- 替换前必须完成前置校验。
- 若 setup 不完整，则必须停止，并要求用户先完成完整初始化。
- 只接受完整 Markdown、文件路径或链接地址。
- 只允许整体替换 `.architecture/templates/technical-solution-template.md`。
- 不允许自动生成模板、局部编辑或内容合并。

这里不再重复充当唯一硬规则来源，而是补充说明两类场景：

- 初始化收尾时确认模板是否定制
- 项目已完成 setup 后，单独替换技术方案模板

当前生效模板可能是默认模板，也可能是用户替换后的自定义模板。

## 通用前置校验

先确认 setup 所需文件完整：

```bash
test -d .architecture/templates && echo "✅ Templates 目录存在"
test -f .architecture/templates/technical-solution-template.md && echo "✅ technical solution 模板存在"
test -f .architecture/members.yml && echo "✅ members.yml 存在"
test -f .architecture/principles.md && echo "✅ principles.md 存在"
```

若任一校验失败，则视为 setup 不完整，应停止并要求用户先执行完整初始化；不要静默补文件。

## 通用输入与替换规则

- 接受用户直接提供的完整 Markdown 模板内容、文件路径或者链接地址。
- 收到后整体替换 `.architecture/templates/technical-solution-template.md`。
- 若用户尚未提供完整 Markdown，则继续索要。
- 不支持恢复默认模板。
- 不支持自动生成模板、局部编辑或内容合并。

## 通用输出约定

- 输出中必须明确模板最终状态。
- 输出中必须明确目标文件为 `.architecture/templates/technical-solution-template.md`。
- 各场景只保留自己的摘要文案，不重复定义主 skill 已明确的硬规则。

## 场景 A：初始化收尾时确认模板是否定制

先执行“通用前置校验”。

该场景特有逻辑：

- 若回答“不需要”，保留当前 `.architecture/templates/technical-solution-template.md`。首次安装通常保留默认模板；重跑初始化时保留现有项目模板。
- 若回答“需要”，按“通用输入与替换规则”处理。

初始化场景摘要：

```text
Tech Solution 设置完成

技术方案模板：默认模板 / 已替换为用户自定义模板

接下来你可以：
- 编写技术方案文档
```

## 场景 B：安装后单独替换技术方案模板

先执行“通用前置校验”。

该场景特有逻辑：

- 直接要求用户提供完整 Markdown 模板内容，不存在“保留当前模板”的分支。
- 收到后按“通用输入与替换规则”处理。

安装后替换场景摘要：

```text
技术方案模板已更新

位置：.architecture/templates/technical-solution-template.md
来源：用户提供的完整 Markdown 模板
```
