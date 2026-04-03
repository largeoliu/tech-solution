# 步骤 3：定制架构原则

## 输入
- 步骤 1 的项目上下文（状态文件 checkpoints.step-1）
- references/principles-customization.md
- templates/principles-template.md

## 操作
1. 遍历模板七个章节
2. 检查步骤 1 上下文中是否存在相关依据
3. 有依据则生成并引用依据编号；无依据则跳过
4. 每个"本项目事实"条目必须包含"依据"字段
5. 记录汇总：模板 7 个章节中 M 个有依据生成/X 个跳过

## 完成标准
- .architecture/principles.md 存在
- 可作为后续技术方案编写和架构评审的项目决策基线
- 来源汇总已记录

## 输出
- 更新状态文件 checkpoints.step-3
- 写入 .architecture/principles.md

## 门控
项目上下文不足以进行原则定制时返回 STOP_AND_ASK；步骤 3 必须在步骤 4 之前完成

## 回退信号
项目上下文变化导致原则需要调整
