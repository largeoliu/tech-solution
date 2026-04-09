---
name: bootstrap-architecture
description: 用于初始化或修复项目中的 `.architecture/` 目录结构——包括成员、原则和默认技术方案模板的初始化。
---

# 初始化架构

为当前项目建立或修复 `.architecture/` 目录结构。

## 定位

- 负责 `.architecture/` 初始化。

## 执行循环

1. 读取 `.architecture/.state/bootstrap-architecture/current.yaml` 获取当前步骤
2. 读取 `steps/<N>-*.md` 步骤卡片
3. 执行卡片中的操作
4. 更新状态（写入 `checkpoints.step-<N>.yaml`、同步 `current.yaml`、推进 `current_step`）
5. 向用户展示步骤摘要
6. 重复直到 step_status: completed

## 状态文件初始化

首次运行时，将 `templates/_template.yaml` 复制为 `.architecture/.state/bootstrap-architecture/current.yaml`，填写 slug 和 started_at。若目标目录不存在，先创建 `.architecture/.state/bootstrap-architecture/`。

状态模板必须初始化 `required_artifacts`、`produced_artifacts`、`template_mode` 和 `cleanup_allowed`，避免出现“步骤已完成但产物未落盘”的伪完成状态。

## 状态更新规则

- 完成一步时，必须同时：
  - 写入 `checkpoints.step-<N>.yaml`
  - 在 `current.yaml` 中同步 `completed_steps`、`current_step`、`updated_at`
  - 将本步实际落盘的文件追加到 `produced_artifacts`
- `current.yaml` 只保存运行中的最新状态；步骤摘要和验证结果必须保留在对应的 `checkpoints.step-<N>.yaml`
- 遇到 STOP_AND_ASK：设置 `blocked: true` 并填写 `block_reason`
- 步骤 4 负责自动创建 `.architecture/templates/` 并写入默认模板，不在初始化流程中询问用户是否自定义模板

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
- `template_mode` 已明确记录为 `default` 或 `customized`
- 只有在全部 required_artifacts 已落盘后，才能将 `step_status` 标记为 `completed`
- `current_step 必须等于最终步骤`
- 只有在 `cleanup_allowed: true` 时，才能删除 `.architecture/.state/bootstrap-architecture/`

## 默认模板位置

默认模板位于 `templates/technical-solution-template.md`。

## 行为约定

1. 初始化主路径必须无交互完成，默认模板由步骤 4 自动落盘。
2. 如需替换模板，在初始化完成后显式调用 `manage-technical-solution-template`。
3. 仅在模板状态明确且全部 required_artifacts 落盘后，才输出初始化完成摘要。

## 步骤索引

| 步骤 | 文件 | 说明 |
|------|------|------|
| 1 | `steps/1-analyze-project.md` | 分析项目上下文 |
| 2 | `steps/2-customize-team.md` | 定制架构团队成员 |
| 3 | `steps/3-customize-principles.md` | 定制架构原则 |
| 4 | `steps/4-confirm-template.md` | 写入默认技术方案模板并完成初始化 |

## 结果格式

```text
Tech Solution 设置完成
技术方案模板：默认模板 / 已替换为用户自定义模板
接下来你可以：
- 编写技术方案文档（使用 create-technical-solution）
- 定制技术方案模板（使用 manage-technical-solution-template）
```

## 完成后清理

仅当 `step_status: completed`、`cleanup_allowed: true` 且全部 required_artifacts 存在时，删除整个 `.architecture/.state/bootstrap-architecture/` 目录。

阻塞状态（blocked: true）时保留该目录，以便恢复执行。
