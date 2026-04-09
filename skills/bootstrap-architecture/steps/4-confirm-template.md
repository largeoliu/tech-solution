# 步骤 4：写入默认技术方案模板并完成初始化

## 输入
- 前三步已生成的成员、原则与状态文件
- `templates/technical-solution-template.md`

## 操作
1. 创建 `.architecture/templates/` 目录
2. 写入默认模板到 `.architecture/templates/technical-solution-template.md`
3. 在状态中记录 `template_mode: default`，并将模板文件追加到 `produced_artifacts`
4. 写入 `checkpoints.step-4.yaml`
5. 只有在全部 required_artifacts 已存在时，才将 `step_status` 标记为 `completed` 并设置 `cleanup_allowed: true`
6. 展示初始化摘要，并说明如需替换默认模板，请在初始化完成后显式调用 `manage-technical-solution-template`

## 完成标准
- 默认模板已写入 `.architecture/templates/technical-solution-template.md`
- 模板状态明确声明为 `default`
- 上下文依据汇总已展示
- 不要求在初始化流程中额外询问用户

## 输出
- 更新状态文件 `checkpoints.step-4.yaml`
- 仅在 required_artifacts 全部落盘后标记 `step_status: completed`

## 门控
默认模板文件无法写入时返回 STOP_AND_ASK

## 回退信号
无（最终步骤）
