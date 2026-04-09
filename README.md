# Tech Solution

一个通过 AI skills 定制技术方案模板、编写技术方案文档的协作框架，可在任何项目中与 AI 助手协同使用。

## 如何安装

优先把下面这句话发给 AI 助手，让它直接读取当前仓库中的 `INSTALLATION.md`：

```bash
读取当前仓库中的 `INSTALLATION.md`，并按文档完成安装和初始化。
```

如果当前助手不能直接读取仓库文件，再退回到 raw URL 方式：

```bash
获取并执行指示 https://raw.githubusercontent.com/largeoliu/tech-solution/refs/heads/main/INSTALLATION.md
```

## 如何使用

### 定制技术方案模板（manage-technical-solution-template）

你可以让 AI 协助替换或定制当前项目的技术方案模板。

```text
使用 manage-technical-solution-template skill，帮我定制当前项目的技术方案模板。
```

模板文件位置：`.architecture/templates/technical-solution-template.md`

### 编写技术方案文档（create-technical-solution）

你可以基于主题、需求描述、已有文档路径或相关上下文，让 AI 创建、补全或更新正式技术方案文档。

```text
使用 create-technical-solution skill，帮我编写当前项目的技术方案文档。
```

方案文档位置：`.architecture/technical-solutions/`
