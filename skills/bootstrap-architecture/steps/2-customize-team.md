# 步骤 2：定制架构团队

## 输入
- 步骤 1 的项目上下文（状态文件 checkpoints.step-1）
- templates/members-template.yml

## 操作

### 生成流程
1. 从模板 `templates/members-template.yml` 中识别项目需要的成员
2. 遍历模板中每个成员角色
3. 检查步骤 1 上下文中是否存在相关依据
4. 有依据则生成；无依据则跳过
5. 检查步骤 1 上下文中是否存在模板未覆盖的项目特有专家需求
6. 如有，新增这些专家角色，填写完整字段
7. 将成员 ID 与依据编号的映射记录到状态文件 checkpoints.step-2
8. 记录汇总：模板 N 个角色中 M 个有依据生成/X 个跳过，新增 Y 个项目特有专家

### 核心原则
- 技术栈匹配：成员技术能力与项目技术栈保持一致
- 规模控制：核心团队 5-7 名专家
- 视角多样：成员具备不同专业背景和技术专长
- 能力平衡：合理配置领域深度专家与技术通才

### 输出边界约束
- members.yml 严格遵循模板格式，只包含模板定义的字段：id, name, title, specialties, disciplines, skillsets, domains, perspective
- 不包含"依据"、"sources"等模板之外的字段
- 依据信息记录在状态文件中，不写入 members.yml

## 完成标准
- .architecture/members.yml 存在
- 成员集合涵盖当前项目关键专家角色
- members.yml 严格遵循模板格式
- 依据映射已记录到状态文件 checkpoints.step-2
- 来源汇总已记录（模板 N 个角色中 M 个有依据生成/X 个跳过，新增 Y 个项目特有专家）
- 验证所有在项目上下文中有依据的专家角色都已存在于 members.yml
- 如有遗漏，输出具体遗漏的专家角色及其依据编号
- 验证结果记录到状态文件 checkpoints.step-2

## 输出
- 更新状态文件 checkpoints.step-2
- 写入 .architecture/members.yml
- 验证结果摘要（包含已验证角色数、遗漏角色列表）

## 门控
项目上下文不足以进行成员定制时返回 STOP_AND_ASK；步骤 2 必须在步骤 3 之前完成

## 回退信号
项目上下文变化导致成员角色需要调整
