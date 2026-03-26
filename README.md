# Tech Solution

一个通过 AI skills 定制技术方案模板、编写技术方案文档的协作框架，可在任何项目中与 AI 助手协同使用。

## 如何安装

把下面这句话发给 AI 助手：

```bash
获取并执行指示 https://raw.githubusercontent.com/largeoliu/tech-solution/refs/heads/main/INSTALLATION.md
```

## 如何使用

### 定制技术方案模板（setup-architect）

你可以让 AI 协助确认、替换或定制当前项目的技术方案模板。

```text
使用 setup-architect skill，帮我定制当前项目的技术方案模板。
```

模板文件位置：`.architecture/templates/technical-solution-template.md`

### 编写技术方案文档（create-technical-solution）

你可以基于主题、需求描述、已有文档路径或相关上下文，让 AI 创建、补全或更新正式技术方案文档。

在写入最终方案前，AI 会先在对话中逐一展示参与成员各 1 份结构化 `专家产物`，再展示 1 份 `协作收敛纪要`，覆盖共同结论、争议点、候选方案对比、选定方向和未决问题。这些中间产物默认只在对话中展示，不额外生成侧车文档；如果中途修正约束，AI 会说明哪些中间产物失效，并从相应阶段继续。

```text
使用 create-technical-solution skill，帮我编写当前项目的技术方案文档。
```

方案文档位置：`.architecture/technical-solutions/`
