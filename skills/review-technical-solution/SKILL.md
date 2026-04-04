---
name: review-technical-solution
description: 在评审技术方案与需求详情、架构原则及现有项目代码时使用，特别是当缺失上下文、未经验证的假设、实现适配风险或代码与实际情况不匹配可能导致提案无效时。
---

# 技术方案评审

## 技能定位
按需求详情、技术方案文档、`.architecture/principles.md` 和项目现有代码做正式评审。只在需要正式评审时使用；创建/补写方案转 `create-technical-solution`。

## 现有资产复用审查原则
- 评审新增、拆分、合并、迁移、平行建设、职责转移或能力增强时，必须主动核验是否已比较现有候选资产，而不只验证方案自述。
- 现有资产不限于接口，也包括 API、service、function、module、component、class、table、schema、model、config、flag、job、script、event、command、workflow、page、form、state、hook 等。
- 若方案未比较现有候选，默认视为 `代码现状对齐` 风险。
- 若代码中存在明确的低风险复用或改造路径，方案仍通过新增、拆分、合并、迁移、平行建设、职责转移或能力增强制造重复能力，直接记为 `blocker`。

## 执行循环
1. **Read state** — 读取 `.architecture/.state/review-technical-solution/` 状态文件，获取 current_step / completed_steps / checkpoints
2. **Read step card** — 读取 `steps/{current_step}` 步骤卡
3. **Execute** — 按步骤卡操作执行
4. **Update state** — 写入 checkpoints.step-N，推进 current_step，标记 step_status
5. **Show summary** — 向用户展示本步摘要
6. **Repeat** — 回到步骤 1，直到 step 8 完成

## 状态文件初始化
首次运行时从 `templates/_template.yaml` 复制为 `.architecture/.state/review-technical-solution/{slug}.yaml`，填充 slug / started_at / updated_at。若目标目录不存在，先创建 `.architecture/.state/review-technical-solution/`。

## 状态更新规则
- 每步完成后追加 completed_steps，写入 checkpoints.step-N
- step_status 取 pending / running / blocked / completed
- blocked=true 时记录 block_reason，不得推进

## 回退规则
用户变更触发回退信号时，将 current_step 回退到对应步骤，清空该步及之后的 checkpoints。

| 变更 | 回退到 |
|------|--------|
| 必要输入被删除或路径变化 | 步骤 1 |
| 方案核心变更意图变化 | 步骤 2 |
| 核心主张发生变化 | 步骤 3 |
| 相关代码发生变更 | 步骤 4 |
| 原则文档变更或分级标准调整 | 步骤 5 |
| 改进前提条件变化 | 步骤 6 |
| 自检发现前序遗漏或错误 | 第一个未完成步骤 |

## 严重级别定义
- `blocker`：主张被证伪、必要依赖不存在、违反核心原则、缺失不可替代落地路径
- `major`：高概率导致返工、风险外溢、关键目标落空
- `minor`：影响范围有限，可在实现前修正
- `note`：提醒/观察/建议项

其中，“未比较现有候选即通过新增、拆分、合并、迁移、平行建设、职责转移或能力增强制造重复能力”默认不低于 `major`；“已有低风险复用/改造路径却仍制造重复能力”直接按 `blocker` 处理。

## 最终结论规则
- 任一 blocker → `阻断`
- 缺少必要输入 → `无法开展正式评审`
- 无 blocker 但有 major → `需修改`
- 仅有 minor/note 且核心主张已充分证实 → `通过`
- 关键待核验主张风险足以影响方向 → `需修改` 或 `阻断`

## 固定输出与字段要求
六区块顺序：评审结论 / 阻断项 / 主要问题 / 改进方案 / 待补充信息 / 建议验证。任一区块为空写 `- 无`。
- 评审结论：conclusion（四选一）、summary
- 问题项：severity、category、problem、evidence、impact、recommendation、validation、targets
- 改进项：category、recommendation、validation、targets
- 待补充：missing_information、reason、targets
- 建议验证：validation、targets

## 步骤索引
| # | 步骤 | 文件 |
|---|------|------|
| 1 | 校验输入完整性 | `steps/01-validate-inputs.md` |
| 2 | 判断方案类型 | `steps/02-classify-solution.md` |
| 3 | 提取核心主张 | `steps/03-extract-claims.md` |
| 4 | 代码取证 | `steps/04-code-evidence.md` |
| 5 | 归因与分级 | `steps/05-attribution.md` |
| 6 | 生成改进方案 | `steps/06-improvement-plan.md` |
| 7 | 输出前自检 | `steps/07-pre-output-check.md` |
| 8 | 正式输出 | `steps/08-formal-output.md` |

## 相关技能
- `create-technical-solution`：创建、补写或更新技术方案正文
