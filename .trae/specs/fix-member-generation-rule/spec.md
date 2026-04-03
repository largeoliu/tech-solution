# 修复成员生成遗漏新增专家规则 Spec

## Why

在修复引用断裂问题时，遗漏了原始 `references/member-customization.md` 中的关键规则："结合你的项目框架和技术栈，添加模板中不存在的成员（如需要）"。导致现在只生成模板中存在的专家，无法根据项目实际需要添加新的专家角色。

## What Changes

- 在 `steps/2-customize-team.md` 中添加"新增项目特有专家"规则
- 补充团队成员定制的核心原则

## Impact

- Affected specs: `skills/bootstrap-architecture/steps/2-customize-team.md`
- Affected code: members.yml 生成逻辑

## ADDED Requirements

### Requirement: 支持新增项目特有专家

步骤 2 SHALL 支持根据项目上下文新增模板中不存在的专家角色。

#### Scenario: 项目需要模板之外的专家
- **WHEN** 步骤 1 的项目上下文中发现需要某个专家角色，但该角色不在模板中
- **THEN** 应新增该专家角色到 members.yml
- **THEN** 新增的专家必须有依据引用步骤 1 上下文编号

#### Scenario: 新增专家的字段完整性
- **WHEN** 新增模板中不存在的专家角色
- **THEN** 必须填写所有必要字段：id, name, title, specialties, disciplines, skillsets, domains, perspective, 依据

### Requirement: 遵循团队定制核心原则

步骤 2 SHALL 遵循团队成员定制的核心原则：

1. **技术栈匹配原则**：团队成员的技术能力与项目技术栈保持一致
2. **团队规模控制原则**：核心团队由 5-7 名专家组成
3. **视角多样性原则**：成员具备不同的专业背景和技术专长
4. **能力结构平衡原则**：合理配置领域深度专家与技术通才

## MODIFIED Requirements

### Requirement: 步骤 2 生成流程

`steps/2-customize-team.md` 的生成流程 SHALL 包含新增专家的步骤：

修改前：
```markdown
### 生成流程
1. 从模板 `templates/members-template.yml` 中识别项目需要的成员
2. 遍历模板中每个成员角色
3. 检查步骤 1 上下文中是否存在相关依据
4. 有依据则生成并引用上下文编号；无依据则跳过
5. 每位成员生成时必须标注"依据"字段引用步骤 1 上下文编号
6. 记录汇总：模板 N 个角色中 M 个有依据生成/X 个跳过
```

修改后：
```markdown
### 生成流程
1. 从模板 `templates/members-template.yml` 中识别项目需要的成员
2. 遍历模板中每个成员角色
3. 检查步骤 1 上下文中是否存在相关依据
4. 有依据则生成并引用上下文编号；无依据则跳过
5. 检查步骤 1 上下文中是否存在模板未覆盖的项目特有专家需求
6. 如有，新增这些专家角色，填写完整字段并标注依据
7. 每位成员生成时必须标注"依据"字段引用步骤 1 上下文编号
8. 记录汇总：模板 N 个角色中 M 个有依据生成/X 个跳过，新增 Y 个项目特有专家

### 核心原则
- 技术栈匹配：成员技术能力与项目技术栈保持一致
- 规模控制：核心团队 5-7 名专家
- 视角多样：成员具备不同专业背景和技术专长
- 能力平衡：合理配置领域深度专家与技术通才
```
