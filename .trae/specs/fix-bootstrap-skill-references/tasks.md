# Tasks

- [x] Task 1: 修复步骤 2 步骤卡片引用断裂
  - [x] SubTask 1.1: 移除 `steps/2-customize-team.md` 中对 `references/member-customization.md` 的引用
  - [x] SubTask 1.2: 在步骤卡片中内联必要的定制规则（从已删除的 references 文件中提取关键规则）
  - [x] SubTask 1.3: 添加输出边界约束，明确 members.yml 只包含模板定义的字段

- [x] Task 2: 修复步骤 3 步骤卡片引用断裂
  - [x] SubTask 2.1: 移除 `steps/3-customize-principles.md` 中对 `references/principles-customization.md` 的引用
  - [x] SubTask 2.2: 在步骤卡片中内联必要的定制规则（从已删除的 references 文件中提取关键规则）
  - [x] SubTask 2.3: 添加输出边界约束，明确 principles.md 只包含模板定义的七个章节

- [x] Task 3: 添加临时状态文件清理逻辑
  - [x] SubTask 3.1: 在 `SKILL.md` 中添加"完成后清理"章节
  - [x] SubTask 3.2: 明确执行完成后删除 `state/current.yaml`
  - [x] SubTask 3.3: 明确阻塞状态时保留状态文件

# Task Dependencies

- Task 1 和 Task 2 可以并行执行
- Task 3 独立执行，无依赖
