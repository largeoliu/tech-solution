# 安装流程改进 Spec

## Why
当前安装流程存在两个问题：1) 会覆盖项目原有的 skill 目录，导致用户自定义的 skill 丢失；2) 在项目上下文分析后应该添加专家但未添加专家，导致成员配置不完整。

## What Changes
- 修改 INSTALLATION.md 中 Stage 2 的安装逻辑，改为增量安装而非覆盖安装
- 修改 bootstrap-architecture skill 的步骤 2 (steps/2-customize-team.md)，增加验证机制确保有依据的专家角色被正确添加

## Impact
- Affected specs: INSTALLATION.md, skills/bootstrap-architecture/steps/2-customize-team.md
- Affected code: 安装脚本、成员初始化流程

## ADDED Requirements

### Requirement: 增量安装 Skill 目录
安装流程 SHALL 采用增量安装策略，保留目标目录中已存在的 skill 目录。

#### Scenario: 目标目录已存在同名 skill
- **WHEN** 目标目录中已存在与待安装 skill 同名的目录
- **THEN** 跳过该 skill 的安装，保留原有内容，并输出提示信息

#### Scenario: 目标目录不存在某 skill
- **WHEN** 目标目录中不存在待安装的某个 skill
- **THEN** 将该 skill 完整复制到目标目录

#### Scenario: 目标目录为空
- **WHEN** 目标目录不存在或为空
- **THEN** 将所有 skill 完整复制到目标目录

### Requirement: 确保专家角色正确添加
bootstrap-architecture 步骤 2 SHALL 确保在项目上下文中找到依据的专家角色被正确添加到成员配置中。

#### Scenario: 项目上下文有依据但未添加专家
- **WHEN** 步骤 1 的项目上下文分析中找到了某个专家角色的依据
- **THEN** 该专家角色必须被添加到 `.architecture/members.yml` 中

#### Scenario: 专家添加失败时的处理
- **WHEN** 某个有依据的专家角色未能成功添加
- **THEN** 输出明确的错误信息，说明哪个专家角色添加失败及原因

#### Scenario: 成员配置生成后的验证
- **WHEN** 步骤 2 完成成员配置生成
- **THEN** 必须验证所有有依据的专家角色都已存在于 members.yml 中

## MODIFIED Requirements

### Requirement: Stage 2 安装命令
Stage 2 的安装命令 SHALL 改为增量复制，使用条件判断避免覆盖已存在的 skill 目录。

原命令：
```bash
cp -r ./tech-solution-tmp/skills/* "$TARGET"/
```

修改为增量安装逻辑：
```bash
for skill_dir in ./tech-solution-tmp/skills/*; do
  [ -d "$skill_dir" ] || continue
  skill_name="$(basename "$skill_dir")"
  if [ -d "$TARGET/$skill_name" ]; then
    echo "跳过已存在的 skill: $skill_name"
  else
    cp -r "$skill_dir" "$TARGET/"
    echo "已安装 skill: $skill_name"
  fi
done
```

### Requirement: 步骤 2 完成标准增加验证
bootstrap-architecture 的步骤 2 完成标准 SHALL 增加验证环节：

在 `steps/2-customize-team.md` 的完成标准中增加：
- 验证所有在项目上下文中有依据的专家角色都已存在于 members.yml
- 如有遗漏，输出具体遗漏的专家角色及其依据编号
- 验证结果记录到状态文件 checkpoints.step-2
