# 安装流程

## 执行步骤

### 1. 创建 `.architecture/`

```bash
mkdir -p .architecture/technical-solutions
mkdir -p .architecture/templates
```

只创建运行所需的最小目录。

### 2. 安装模板与基础文件

```bash
SKILL_ROOT="[setup-architect skill directory]"


test -f .architecture/templates/technical-solution-template.md || cp "$SKILL_ROOT/templates/technical-solution-template.md" .architecture/templates/technical-solution-template.md
test -f .architecture/members.yml || cp "$SKILL_ROOT/templates/members-template.yml" .architecture/members.yml
test -f .architecture/principles.md || cp "$SKILL_ROOT/templates/principles-template.md" .architecture/principles.md
```

`SKILL_ROOT` 应指向当前 `setup-architect` skill 目录。


## 验证与清理

- 这里的验证结果用于完成第 5 步“复核正式项目结构”。
- 若结构复核尚未完成，则返回 `STOP_AND_ASK`，继续等待；未完成第 5 步，不得进入第 6 步模板确认。
- 若结构复核已完成但结构不符，则返回第 1 步重新安装。

```bash
test -d .architecture/technical-solutions && echo "✅ Solutions 目录存在"
test -d .architecture/templates && echo "✅ Templates 目录存在"
test -f .architecture/templates/technical-solution-template.md && echo "✅ technical solution 模板存在"
test -f .architecture/members.yml && echo "✅ members.yml 存在"
test -f .architecture/principles.md && echo "✅ principles.md 存在（技术方案 / 架构评审必需）"
```
