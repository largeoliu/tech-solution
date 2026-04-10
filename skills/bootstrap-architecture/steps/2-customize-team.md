# 步骤 2：定制架构团队

## 输入
- 步骤 1 的项目上下文与 `project_signals`（状态文件 checkpoints.step-1）
- templates/members-template.yml

## 操作

### 生成流程
1. 读取 `templates/members-template.yml` 中的模板角色，以及步骤 1 输出的 `project_signals`
2. 先遍历模板中每个成员角色，判断它是否覆盖一个或多个 `project_signals`
3. 能覆盖则生成该模板角色；不能覆盖则跳过并记录原因
4. 完成模板遍历后，检查仍未覆盖的 `project_signals`
5. 将语义相近、可由同一专家承担的未覆盖 signals 合并，尽量用最少的新增角色完成覆盖；默认目标 5-7 名专家，若所有 `project_signals` 已被覆盖且模板角色全部适配，则不少于模板 generate 数即可
6. 为每组未覆盖 signals 新增项目特有专家角色，填写完整成员字段；允许一个新增角色覆盖多个 signals
7. 将最终成员集合写入 `.architecture/members.yml`，严格遵循模板字段边界
8. 将 `expert_coverage` 记录到状态文件 `checkpoints.step-2.yaml`，至少包含 `template_roles`、`custom_roles`、`signal_coverage`；每个角色条目记录其覆盖的 signals 和依据
9. 记录汇总：模板 N 个角色中 M 个生成/X 个跳过，新增 Y 个项目特有专家，覆盖 K 个 `project_signals`；若最终人数少于 5 名，需说明所有 `project_signals` 已被覆盖
10. `signal_coverage` 只能引用 signal 编号（如 `S1`），不能引用 `context_items` 编号（如 `C1`）；如果某个角色只能由原始上下文支撑而没有对应 signal，先回到步骤 1 补齐 signal，再继续步骤 2

### 核心原则
- 信号驱动：成员选择必须显式响应步骤 1 的 `project_signals`
- 技术栈匹配：成员技术能力与项目技术栈保持一致
- 规模控制：默认目标 5-7 名专家；所有 `project_signals` 已覆盖时允许少于 5 名，但不超过 7 名；超过 7 名时需合并相近角色，上限 9 名
- 视角多样：成员具备不同专业背景和技术专长
- 能力平衡：合理配置领域深度专家与技术通才

### 输出边界约束
- members.yml 严格遵循模板格式，只包含模板定义的字段：id, name, title, specialties, disciplines, skillsets, domains, perspective
- 不包含"依据"、"sources"等模板之外的字段
- 依据信息记录在状态文件中，不写入 members.yml
- `signal_coverage` 只允许使用 signal 编号，不允许混入 `context_items` 编号

## 完成标准
- .architecture/members.yml 存在
- 成员集合涵盖当前项目关键专家角色
- members.yml 严格遵循模板格式
- `expert_coverage` 已记录到状态文件 `checkpoints.step-2.yaml`
- 来源汇总已记录（模板 N 个角色中 M 个生成/X 个跳过，新增 Y 个项目特有专家，覆盖 K 个 `project_signals`）
- 已验证 `template_roles` 中 `action=generate` 的角色都存在于 `members.yml`
- 已验证 `custom_roles` 中列出的角色都存在于 `members.yml`
- 已验证所有 `project_signals` 都至少有一个角色覆盖
- 如有遗漏，输出缺失角色或未覆盖 signal 及其依据编号
- 若最终成员少于 5 名，已确认所有 `project_signals` 均已覆盖
- 验证结果记录到状态文件 checkpoints.step-2.yaml

## 输出
- 更新状态文件 checkpoints.step-2
- 写入 .architecture/members.yml
- 验证结果摘要（包含已覆盖 signal 数、未覆盖 signal 列表、生成/跳过/新增角色统计，以及 signal 到角色的覆盖关系）

## 门控
项目上下文或 `project_signals` 不足以进行成员定制时返回 STOP_AND_ASK；步骤 2 必须在步骤 3 之前完成

