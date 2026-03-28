## 安装步骤

### Stage 1: 确定目标 skills 目录

先根据当前使用的 AI 助手，确定 `TARGET` 的值：

- Claude：`TARGET=".claude/skills"`
- Qoder：`TARGET=".qoder/skills"`
- Lingma：`TARGET=".lingma/skills"`
- Trae：`TARGET=".trae/skills"`
- 其他助手：`TARGET=".agents/skills"`

### Stage 2: 安装 skills 到目标目录

Stage 2 必须将仓库 `skills/` 目录下当前存在的全部一级 skill 目录完整复制到目标目录。

不要只复制后续将要执行的某一个 skill。

执行以下指令：

```bash
mkdir -p "$TARGET"
git clone https://github.com/largeoliu/tech-solution.git ./tech-solution-tmp
cp -r ./tech-solution-tmp/skills/* "$TARGET"/

for skill_dir in ./tech-solution-tmp/skills/*; do
  [ -d "$skill_dir" ] || continue
  skill_name="$(basename "$skill_dir")"
  [ -f "$TARGET/$skill_name/SKILL.md" ] || (echo "Missing $skill_name/SKILL.md" && exit 1)
done

rm -rf ./tech-solution-tmp
```

### Stage 3: 在同一次流程内完成项目初始化

确认 Stage 2 已将 `skills/` 下当前全部一级 skill 目录安装到目标目录后，继续读取并执行本地 `setup-architect` 的初始化流程，不要等待用户追加输入。

这里指定的是安装完成后的下一步执行入口，不是 Stage 2 的安装范围。

必须基于以下目录下的文件完成当前项目初始化：

- `"$TARGET/setup-architect"`

完成标准：

- 创建 `.architecture/technical-solutions`、`.architecture/templates`
- 生成 `.architecture/members.yml`、`.architecture/principles.md`
- 生成 `.architecture/templates/technical-solution-template.md`，并在初始化结束前确认该文件最终保留默认模板还是被用户提供的完整 Markdown 整体替换
