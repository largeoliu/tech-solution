---
name: bootstrap-architecture
description: 用于初始化或修复项目中的 `.architecture/` 目录结构——包括成员、原则和技术方案模板的初始化。
---

# 初始化架构

为当前项目建立或修复 `.architecture/` 目录结构。

## 定位

- 负责 `.architecture/` 初始化。

## 执行循环

1. 读取 `state/current.yaml` 获取当前步骤
2. 读取 `steps/<N>-*.md` 步骤卡片
3. 执行卡片中的操作
4. 更新状态（推进 current_step、追加 completed_steps、写入 checkpoints）
5. 向用户展示步骤摘要
6. 重复直到 step_status: completed

## 状态文件初始化

首次运行时，将 `state/_template.yaml` 复制为 `state/current.yaml`，填写 slug 和 started_at。

## 状态更新规则

- 完成一步：追加 completed_steps，写入 checkpoints.step-<N>，推进 current_step，更新 updated_at
- 遇到 STOP_AND_ASK：设置 blocked: true 并填写 block_reason

## 回退规则

| 触发条件 | 回退到 | 影响范围 |
|----------|--------|----------|
| 项目基础上下文重大变化 | 步骤 1 | 全部产物需重新验证 |
| 成员角色需要调整 | 步骤 2 | members.yml 及后续依赖 |
| 原则需要调整 | 步骤 3 | principles.md 及后续依赖 |
| 模板定制需求变更 | 步骤 4 | 仅模板文件 |

## 完成标准

- `.architecture/members.yml` 存在并反映项目的实际成员组成
- `.architecture/principles.md` 存在并作为项目的决策基线
- `.architecture/templates/technical-solution-template.md` 存在（默认或自定义）
- 最终输出必须明确说明模板是默认的还是自定义的

## 默认模板位置

默认模板位于 `templates/technical-solution-template.md`。

## 行为约定

1. 主路径仅为初始化；不得隐式混合模板替换。
2. 仅在模板状态确认后才输出初始化完成摘要。

## 步骤索引

| 步骤 | 文件 | 说明 |
|------|------|------|
| 1 | `steps/1-analyze-project.md` | 分析项目上下文 |
| 2 | `steps/2-customize-team.md` | 定制架构团队成员 |
| 3 | `steps/3-customize-principles.md` | 定制架构原则 |
| 4 | `steps/4-confirm-template.md` | 确认技术方案模板并完成 |

## 结果格式

```text
Tech Solution 设置完成
技术方案模板：默认模板 / 已替换为用户自定义模板
接下来你可以：
- 编写技术方案文档（使用 create-technical-solution）
- 定制技术方案模板（使用 manage-technical-solution-template）
```

## 完成后清理

Skill 执行完成（step_status: completed）后，删除 `state/current.yaml`。

阻塞状态（blocked: true）时保留状态文件，以便恢复执行。
