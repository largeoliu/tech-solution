## 安装步骤

### Stage 1: 识别当前助手并解析目标目录

Stage 1 必须先识别当前 AI 助手运行时，再将结果标准化为 `assistant_id`，然后按 `TARGETS[assistant_id][scope]` 解析目标目录。

`assistant_id` 只能来自当前 AI 助手宿主或运行时环境。

不能根据项目里是否存在 `.qoder/`、`.trae/`、`.claude/` 等目录推断当前助手。

这些项目目录只描述仓库历史或已有安装结果，不代表当前执行安装流程的助手。

默认安装范围是项目级安装；若用户请求全局安装，仍必须使用同一个 `assistant_id` 和显式映射解析目标目录。若全局目标未定义，必须停止，不能猜测。

当 `scope=project` 时，映射必须严格为：

- `claude -> .claude/skills`
- `qoder -> .qoder/skills`
- `lingma -> .lingma/skills`
- `trae -> .trae/skills`
- `generic -> .agents/skills`

判定顺序必须是：先读取宿主显式信号，再读取宿主进程、启动器、路径、元数据等宿主特征信号，然后标准化为 `assistant_id`，最后解析 `TARGETS[assistant_id][scope]`。

低优先级信号不能覆盖高优先级显式身份；如果宿主显式信号与宿主特征识别结果冲突，也必须停止安装。

若无法唯一识别当前助手，则停止安装并输出诊断。

诊断必须说明已观察到的信号、这些信号分别指向哪些助手、为什么当前结果属于缺失/冲突/未知，以及本次安装没有执行。

禁止回退到项目目录扫描，也禁止因为项目里已经存在某个目录就覆盖运行时识别结果。

验收示例：

- `Trae runtime + existing .qoder/ -> .trae/skills`
- `Qoder runtime + existing .trae/ -> .qoder/skills`
- `unrecognized runtime + multiple assistant directories -> fail without guessing`

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

- 生成 `.architecture/members.yml`、`.architecture/principles.md`
- 生成 `.architecture/templates/technical-solution-template.md`，在初始化结束前确认该文件最终保留默认模板还是被用户提供的完整 Markdown 整体替换

