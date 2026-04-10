# 步骤 4：确认技术方案模板并完成初始化

## 输入
- 前三步已生成的成员、原则与状态文件
- `templates/technical-solution-template.md`

## 操作
1. 创建 `.architecture/templates/` 目录
2. 向用户展示默认模板的结构概要，并询问是否使用默认模板或提供自定义模板
3. 根据用户选择执行：
   - **使用默认模板**：将 `templates/technical-solution-template.md` 写入 `.architecture/templates/technical-solution-template.md`，在状态中记录 `template_mode: default`
   - **使用自定义模板**：获取用户提供的自定义模板内容（完整的 Markdown、文件路径或链接），将其写入 `.architecture/templates/technical-solution-template.md`，在状态中记录 `template_mode: customized`。不接受部分内容、片段编辑或自动生成——必须是用户明确提供的完整模板
4. 将模板文件追加到 `produced_artifacts`
5. 写入 `checkpoints.step-4.yaml`
6. 只有在全部 required_artifacts 已存在时，才将 `step_status` 标记为 `completed` 并设置 `cleanup_allowed: true`
7. 展示初始化摘要

## 完成标准
- 技术方案模板已写入 `.architecture/templates/technical-solution-template.md`
- `template_mode` 已明确记录为 `default` 或 `customized`
- 用户已对模板选择做出明确决定
- 上下文依据汇总已展示

## 输出
- 更新状态文件 `checkpoints.step-4.yaml`
- 仅在 required_artifacts 全部落盘后标记 `step_status: completed`

## 门控
模板文件无法写入时返回 STOP_AND_ASK；用户未提供完整的自定义模板内容时继续询问，不要自动生成或部分填充

<HARD-GATE>
步骤 4 完成判定门控：将 `step_status` 标记为 `completed` 或设置 `cleanup_allowed: true` 之前，必须确认以下全部条件：
1. `.architecture/members.yml` 存在
2. `.architecture/principles.md` 存在
3. `.architecture/templates/technical-solution-template.md` 存在
4. `template_mode` 已明确记录为 `default` 或 `customized`
违反任一条即不得标记完成或允许清理。
</HARD-GATE>

