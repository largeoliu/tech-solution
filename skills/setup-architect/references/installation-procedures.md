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

```bash
test -d .architecture/technical-solutions && echo "✅ Solutions 目录存在"
test -d .architecture/templates && echo "✅ Templates 目录存在"
test -f .architecture/templates/technical-solution-template.md && echo "✅ technical solution 模板存在"
test -f .architecture/members.yml && echo "✅ members.yml 存在"
test -f .architecture/principles.md && echo "✅ principles.md 存在（技术方案 / 架构评审必需）"
```
