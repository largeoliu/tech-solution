# 步骤 2：定制架构团队

## 输入
- 步骤 1 的项目上下文（状态文件 checkpoints.step-1）
- references/member-customization.md
- templates/members-template.yml

## 操作
1. 遍历模板中每个成员角色
2. 检查步骤 1 上下文中是否存在相关依据
3. 有依据则生成并引用上下文编号；无依据则跳过
4. 每位成员生成时必须标注"依据"字段引用步骤 1 上下文编号
5. 记录汇总：模板 N 个角色中 M 个有依据生成/X 个跳过

## 完成标准
- .architecture/members.yml 存在
- 成员集合涵盖当前项目关键专家角色
- 每位成员都有依据引用
- 来源汇总已记录

## 输出
- 更新状态文件 checkpoints.step-2
- 写入 .architecture/members.yml

## 门控
项目上下文不足以进行成员定制时返回 STOP_AND_ASK；步骤 2 必须在步骤 3 之前完成

## 回退信号
项目上下文变化导致成员角色需要调整
