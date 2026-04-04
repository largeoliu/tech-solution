# bootstrap-architecture 模板外专家补齐设计

## 背景

全新项目执行安装后，会继续进入 `bootstrap-architecture` 生成 `.architecture/members.yml`。
当前流程虽然在步骤 2 明确写了“如果模板未覆盖项目特有专家则新增”，但步骤 1 只输出松散的项目上下文，步骤 2 又要一边理解项目、一边决定专家覆盖，边界发虚，导致它很容易只生成模板内的默认专家，而漏掉项目真正需要的模板外专家。

## 问题定义

当前问题不是安装阶段遗漏了某个文件，而是 `bootstrap-architecture` 内部的步骤契约不完整：

- 步骤 1 现在混合了项目分析和成员角色判断，职责边界不清。
- 步骤 2 缺少稳定的结构化输入，只能从松散上下文中自行推断模板外专家，执行稳定性差。
- `INSTALLATION.md` 应只关心最终产物，不应依赖或校验中间状态。

## 目标

- 让步骤 1 明确产出结构化 `project_signals`，沉淀可复用的项目事实和关键信号。
- 让步骤 2 独占专家覆盖判断，基于 `project_signals` 稳定生成模板内与模板外专家。
- 保持 `.architecture/members.yml` 只包含模板允许的最终字段。
- 保持 `INSTALLATION.md` 只描述最终产物标准，不检查临时状态。

## 非目标

- 不扩充 `members-template.yml` 的默认专家集合。
- 不在本次修改中新增回归样例、验收脚本或额外测试框架。
- 不改变 `.architecture/members.yml` 的字段边界。

## 方案概述

核心思路是把“项目是什么样”的分析职责固定在步骤 1，把“这些信号需要哪些专家覆盖”的决策职责固定在步骤 2。

### 步骤 1：输出结构化 `project_signals`

`skills/bootstrap-architecture/steps/1-analyze-project.md` 将从当前“上下文清单 + 角色/章节有无依据标注”升级为“上下文清单 + 结构化项目信号”。

步骤 1 除了识别项目语言、框架、部署、目录结构等上下文，还必须输出一个结构化对象，例如挂在 `checkpoints.step-1.project_signals` 下，只表达会影响后续成员或原则定制的项目事实，不直接下专家结论。

- `platform`：项目运行形态，如 `web` / `mobile` / `backend` / `cli`。
- `capability`：项目需要重点覆盖的能力面，如 `frontend` / `data` / `ai` / `infra` / `security` / `performance` / `compliance`。
- `constraint`：会影响原则或团队配置的关键约束，如 `real_time` / `high_scale` / `complex_integration`。

每条 signal 都要带上：

- `id`
- `type`
- `value`
- `evidence`
- 必要时的 `note`

这样步骤 1 回答的是“这是什么项目、有哪些关键能力和约束”，而不是“应该配哪些人”。同一份 `project_signals` 既能服务步骤 2 的团队定制，也能服务步骤 3 的原则定制。

### 步骤 2：基于 `project_signals` 做专家覆盖

`skills/bootstrap-architecture/steps/2-customize-team.md` 的输入将从“步骤 1 的项目上下文”收紧为“步骤 1 的项目上下文 + `project_signals`”。

步骤 2 的生成逻辑改为确定性执行：

1. 读取模板角色和 `project_signals`。
2. 先判断哪些模板角色已经覆盖 `project_signals`，覆盖则生成，不覆盖则跳过并记录原因。
3. 检查仍未覆盖的 `project_signals`。
4. 将语义相近、可由同一专家承担的未覆盖 signals 合并，尽量用最少的新增角色完成覆盖，而不是机械地一条 signal 对应一个新增角色。
5. 为每组未覆盖 signals 新增项目特有专家，并按模板字段边界写入 `.architecture/members.yml`。
6. 将专家覆盖结果记录到 `checkpoints.step-2.expert_coverage`，至少包含 `template_roles`、`custom_roles`、`signal_coverage`；每个角色条目记录其覆盖的 signals 和依据。

步骤 2 不再承担“重新分析项目是什么”的职责，但它必须独占“哪些 signal 需要哪些专家覆盖”的判断逻辑。这样模板角色与模板外专家的映射规则只维护一处，不会在步骤 1 和步骤 2 之间漂移。

### 步骤 2：验证规则同步收紧

步骤 2 的完成标准与验证摘要需要改成针对覆盖结果进行精确校验：

- `template_roles` 中所有 `action=generate` 的角色必须出现在 `.architecture/members.yml`。
- `custom_roles` 中列出的每个角色都必须出现在 `.architecture/members.yml`。
- 所有 `project_signals` 都至少有一个角色覆盖。
- 如有缺失，步骤 2 直接未完成，并输出缺失角色或未覆盖 signal 及其依据编号。

这里的验证仍然属于 `bootstrap-architecture` 内部过程约束，不暴露给 `INSTALLATION.md`。

### 步骤 3：继续复用步骤 1 结果

`skills/bootstrap-architecture/steps/3-customize-principles.md` 继续消费步骤 1 的项目上下文，但现在可以明确复用 `project_signals` 来支持原则章节生成。

这一步不引入新的专家逻辑，只让步骤 1 的分析结果被步骤 3 更直接地复用。

### 安装入口的边界保持简洁

`INSTALLATION.md` 只保留安装入口和最终产物标准，不检查 `checkpoints.step-1`、`project_signals`、`expert_coverage` 等中间状态。

但最终产物标准需要更精确地表达结果要求：

- `.architecture/members.yml` 已生成。
- `.architecture/members.yml` 已覆盖当前项目所需的关键专家角色；当模板不足时，已包含新增的项目特有专家。
- `.architecture/principles.md` 已生成。
- `.architecture/templates/technical-solution-template.md` 已生成并完成模板确认。

这样可以保持安装入口只关心结果，同时把“如何识别并补齐模板外专家”的复杂性封装在 `bootstrap-architecture` 内部。

## 涉及文件

- 修改 `skills/bootstrap-architecture/steps/1-analyze-project.md`
- 修改 `skills/bootstrap-architecture/steps/2-customize-team.md`
- 视情况微调 `skills/bootstrap-architecture/steps/3-customize-principles.md`
- 修改 `INSTALLATION.md`

## 预期结果

修改完成后，全新项目在执行安装并进入 `bootstrap-architecture` 时，步骤 1 会先沉淀结构化 `project_signals`，步骤 2 再按这些 signals 稳定完成专家覆盖和 `.architecture/members.yml` 生成。这样即使模板只有默认 4 个专家，也能根据项目上下文可靠补齐前端、移动端、数据、AI 或其他项目特有专家，同时保持步骤边界清晰。
