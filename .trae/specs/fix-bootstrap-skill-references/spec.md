# 修复 bootstrap-architecture Skill 引用断裂和输出污染 Spec

## Why

提交 `f8b021e04aaf0401f3c8d0f1778950df83e2aa15` 重构 skill 时删除了 references 目录，但步骤卡片仍引用这些已删除的文件，导致 AI 执行时找不到参考文档，产生了错误的输出内容（members.yml 多了 sources 字段，principles.md 多了文档维护等不该有的内容），同时临时状态文件也没有清理。

## What Changes

- 修复步骤卡片中对已删除 references 文件的引用，将必要规则内联到步骤卡片
- 添加临时状态文件清理逻辑
- 明确输出边界，防止生成多余内容

## Impact

- Affected specs: `skills/bootstrap-architecture/steps/2-customize-team.md`, `skills/bootstrap-architecture/steps/3-customize-principles.md`, `skills/bootstrap-architecture/SKILL.md`
- Affected code: bootstrap-architecture skill 执行流程

## ADDED Requirements

### Requirement: 步骤卡片必须自包含必要规则

步骤卡片 SHALL 包含执行该步骤所需的全部必要规则，不得引用不存在的文件。

#### Scenario: 步骤卡片包含完整规则
- **WHEN** AI 读取步骤卡片执行操作
- **THEN** 步骤卡片中包含所有必要的定制规则，无需查找外部引用文件

#### Scenario: 步骤卡片引用文件存在
- **WHEN** 步骤卡片引用某个文件
- **THEN** 该文件必须存在且可访问

### Requirement: 临时状态文件必须清理

Skill 执行完成后 SHALL 清理临时状态文件 `state/current.yaml`。

#### Scenario: Skill 执行完成
- **WHEN** bootstrap-architecture skill 执行完成（step_status: completed）
- **THEN** `state/current.yaml` 文件应被删除

#### Scenario: Skill 执行中断
- **WHEN** Skill 执行被阻塞（blocked: true）
- **THEN** `state/current.yaml` 文件应保留，以便恢复执行

### Requirement: 输出内容边界明确

生成的 `members.yml` 和 `principles.md` SHALL 只包含模板中定义的字段和章节，不得添加模板之外的内容。

#### Scenario: members.yml 输出正确
- **WHEN** 生成 `.architecture/members.yml`
- **THEN** 只包含模板 `templates/members-template.yml` 中定义的字段（id, name, title, specialties, disciplines, skillsets, domains, perspective, 依据）
- **THEN** 不包含 sources 等模板之外的字段

#### Scenario: principles.md 输出正确
- **WHEN** 生成 `.architecture/principles.md`
- **THEN** 只包含模板 `templates/principles-template.md` 中定义的七个章节
- **THEN** 不包含"文档维护"等模板之外的章节

## MODIFIED Requirements

### Requirement: 步骤 2 输入列表

`steps/2-customize-team.md` 的输入列表 SHALL 移除对已删除文件的引用：

原输入：
```markdown
## 输入
- 步骤 1 的项目上下文（状态文件 checkpoints.step-1）
- references/member-customization.md
- templates/members-template.yml
```

修改为：
```markdown
## 输入
- 步骤 1 的项目上下文（状态文件 checkpoints.step-1）
- templates/members-template.yml
```

### Requirement: 步骤 3 输入列表

`steps/3-customize-principles.md` 的输入列表 SHALL 移除对已删除文件的引用：

原输入：
```markdown
## 输入
- 步骤 1 的项目上下文（状态文件 checkpoints.step-1）
- references/principles-customization.md
- templates/principles-template.md
```

修改为：
```markdown
## 输入
- 步骤 1 的项目上下文（状态文件 checkpoints.step-1）
- templates/principles-template.md
```

### Requirement: SKILL.md 完成标准

`SKILL.md` 的完成标准 SHALL 添加临时文件清理说明：

新增：
```markdown
## 完成后清理

Skill 执行完成（step_status: completed）后，删除 `state/current.yaml`。

阻塞状态（blocked: true）时保留状态文件，以便恢复执行。
```
