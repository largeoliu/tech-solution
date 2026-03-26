## 安装步骤

### Stage 1: 确定目标 skills 目录

先根据当前使用的 AI 助手，确定 `TARGET` 的值：

- Claude：`TARGET=".claude/skills"`
- Qoder：`TARGET=".qoder/skills"`
- Lingma：`TARGET=".lingma/skills"`
- 其他助手：`TARGET=".agents/skills"`

### Stage 2: 安装 skills 到目标目录

执行以下指令：

```bash
mkdir -p "$TARGET"
git clone https://github.com/largeoliu/tech-solution.git ./tech-solution-tmp
cp -r ./tech-solution-tmp/skills/* "$TARGET"/
rm -rf ./tech-solution-tmp
```

### Stage 3: 在同一次流程内完成项目初始化

Stage 2 完成后，继续读取并执行本地 `setup-architect` 的初始化流程，不要等待用户追加输入。

必须基于以下目录下的文件完成当前项目初始化：

- `"$TARGET/setup-architect"`

完成标准：

- 创建 `.architecture/technical-solutions`、`.architecture/templates`
- 生成 `.architecture/members.yml`、`.architecture/principles.md`
- 生成 `.architecture/templates/technical-solution-template.md`，并在初始化结束前确认该文件最终保留默认模板还是被用户提供的完整 Markdown 整体替换
