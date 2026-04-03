# 修复 members.yml 严格遵循模板 Spec

## Why

用户要求生成的 members.yml 严格遵循模板格式，但步骤卡片要求添加"依据"字段，而模板中没有这个字段。应将"依据"信息记录到状态文件中，而不是 members.yml 中。

## What Changes

- 从步骤卡片中移除在 members.yml 中添加"依据"字段的要求
- 改为在状态文件 checkpoints.step-2 中记录依据映射
- 更新输出边界约束，移除"依据"字段

## Impact

- Affected specs: `skills/bootstrap-architecture/steps/2-customize-team.md`
- Affected code: members.yml 生成逻辑

## ADDED Requirements

### Requirement: 依据信息记录在状态文件中

步骤 2 SHALL 将成员与依据的映射关系记录到状态文件 `checkpoints.step-2` 中，而不是 members.yml 中。

#### Scenario: 依据记录到状态文件
- **WHEN** 生成成员配置
- **THEN** members.yml 严格遵循模板格式，不包含"依据"字段
- **THEN** 状态文件 checkpoints.step-2 中包含成员 ID 与依据的映射

#### Scenario: 状态文件依据映射格式
- **WHEN** 记录依据映射
- **THEN** 格式为 `{成员ID: 依据编号列表}`

## MODIFIED Requirements

### Requirement: 步骤 2 生成流程

`steps/2-customize-team.md` 的生成流程 SHALL 修改为：

修改前：
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
```

修改后：
```markdown
### 生成流程
1. 从模板 `templates/members-template.yml` 中识别项目需要的成员
2. 遍历模板中每个成员角色
3. 检查步骤 1 上下文中是否存在相关依据
4. 有依据则生成；无依据则跳过
5. 检查步骤 1 上下文中是否存在模板未覆盖的项目特有专家需求
6. 如有，新增这些专家角色，填写完整字段
7. 将成员 ID 与依据编号的映射记录到状态文件 checkpoints.step-2
8. 记录汇总：模板 N 个角色中 M 个有依据生成/X 个跳过，新增 Y 个项目特有专家

### 输出边界约束
- members.yml 严格遵循模板格式，只包含模板定义的字段：id, name, title, specialties, disciplines, skillsets, domains, perspective
- 不包含"依据"、"sources"等模板之外的字段
- 依据信息记录在状态文件中，不写入 members.yml
```

### Requirement: 完成标准

完成标准 SHALL 移除"每位成员都有依据引用"（指写入 members.yml），改为在状态文件中记录：

修改前：
```markdown
## 完成标准
- .architecture/members.yml 存在
- 成员集合涵盖当前项目关键专家角色
- 每位成员都有依据引用
- ...
```

修改后：
```markdown
## 完成标准
- .architecture/members.yml 存在
- 成员集合涵盖当前项目关键专家角色
- members.yml 严格遵循模板格式
- 依据映射已记录到状态文件 checkpoints.step-2
- ...
```
