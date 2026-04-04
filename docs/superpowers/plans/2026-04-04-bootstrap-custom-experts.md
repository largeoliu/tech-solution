# bootstrap-architecture 模板外专家补齐实现计划

> **给执行 Agent：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐项执行。本计划使用 checkbox（`- [ ]`）跟踪进度。

**目标：** 让全新项目在执行 `bootstrap-architecture` 时，能够稳定补齐 `members-template.yml` 之外但项目实际需要的专家角色。

**方案：** 强化 `bootstrap-architecture` 的 Step 1 -> Step 2 契约。步骤 1 只输出结构化的 `project_signals`，而且这些 signals 只保留会影响后续成员或原则定制的事实；步骤 2 独占专家覆盖判断并生成 `checkpoints.step-2.expert_coverage` 与 `.architecture/members.yml`，必要时把多个未覆盖 signals 合并到更少的新增专家角色里。`INSTALLATION.md` 只描述最终产物，不依赖任何中间状态。

**技术栈：** Markdown 技能文档、YAML 状态约定、git

---

### 任务 1：改造步骤 1，只输出结构化项目信号

**文件：**
- 修改：`skills/bootstrap-architecture/steps/1-analyze-project.md`
- 参考：`docs/superpowers/specs/2026-04-04-bootstrap-custom-experts-design.md`

- [ ] **步骤 1：阅读当前步骤 1 文档与设计稿**

确认当前文档把项目分析和成员角色判断混在一起；同时对齐设计稿中的目标字段：`project_signals`、`platform`、`capability`、`constraint`。

- [ ] **步骤 2：重写“操作”部分**

将 `skills/bootstrap-architecture/steps/1-analyze-project.md` 的“操作”部分改成以下方向：

```md
1. 识别项目的语言/框架/测试 CI/部署方式/目录结构
2. 形成项目上下文清单（带上下文编号）
3. 每项结论标注来源类型（代码结构/目录语义/现有文档）和具体依据
4. 基于项目上下文提取结构化 `project_signals`
5. `project_signals` 只使用固定类别：`platform`、`capability`、`constraint`
6. 每条 signal 记录编号、类别、取值、依据编号，必要时补充简短说明
7. 标注哪些原则章节有依据/无依据
```

- [ ] **步骤 3：重写“完成标准”和“输出”部分**

确保文档明确写出：

```md
- 已生成结构化 `project_signals`
- 每条 signal 都有依据
- `project_signals` 只包含会影响后续成员或原则定制的项目信号，不包含成员角色建议
- `context_items` 和 `project_signals` 写入状态文件
```

- [ ] **步骤 4：人工复查文案边界**

确认步骤 1 只负责“识别并结构化表达项目信号”，不提前判断模板角色要不要生成，也不提前列出模板外专家。

### 任务 2：改造步骤 2，独占专家覆盖判断与成员生成

**文件：**
- 修改：`skills/bootstrap-architecture/steps/2-customize-team.md`
- 依赖：`skills/bootstrap-architecture/steps/1-analyze-project.md`

- [ ] **步骤 1：阅读当前步骤 2 文档并确认缺口**

确认当前文档仍要求从松散上下文中判断模板外专家，缺少对 `project_signals` 和 `expert_coverage` 边界的显式约束。

- [ ] **步骤 2：重写“输入”和“生成流程”部分**

将 `skills/bootstrap-architecture/steps/2-customize-team.md` 改成以下方向：

```md
## 输入
- 步骤 1 的项目上下文（状态文件 `checkpoints.step-1`）
- 步骤 1 的 `project_signals`
- `templates/members-template.yml`

### 生成流程
1. 读取模板角色和 `project_signals`
2. 先判断哪些模板角色已覆盖 `project_signals`，覆盖则生成，不覆盖则跳过并记录原因
3. 检查仍未覆盖的 `project_signals`
4. 将语义相近、可由同一专家承担的未覆盖 signals 合并，尽量减少新增角色数量
5. 为每组未覆盖 signals 新增项目特有专家，填写完整成员字段
6. 将最终成员集合写入 `.architecture/members.yml`
7. 在 `checkpoints.step-2` 记录 `expert_coverage`
8. `expert_coverage` 至少包含 `template_roles`、`custom_roles`、`signal_coverage`，并记录每个角色覆盖的 signals
```

- [ ] **步骤 3：重写“完成标准”和“输出”部分**

确保文档明确写出：

```md
- 已验证 `template_roles` 中所有 `action=generate` 的角色都存在于 `members.yml`
- 已验证 `custom_roles` 中列出的角色都存在于 `members.yml`
- 已验证所有 `project_signals` 都至少有一个角色覆盖
- 如有遗漏，输出缺失角色或未覆盖 signal 及其依据编号
```

- [ ] **步骤 4：人工复查职责边界**

确认步骤 2 只负责“根据 `project_signals` 做专家覆盖判断并落地成员文件”，不把“重新分析项目是什么”的职责拉回步骤 2 之外。

### 任务 3：同步 Step 3 和安装入口的边界文案

**文件：**
- 修改：`skills/bootstrap-architecture/steps/3-customize-principles.md`
- 修改：`INSTALLATION.md`

- [ ] **步骤 1：同步 Step 3 对 Step 1 输出的引用方式**

确认 `skills/bootstrap-architecture/steps/3-customize-principles.md` 继续依赖步骤 1，但只消费项目上下文和 `project_signals`，不接入任何专家覆盖逻辑。

- [ ] **步骤 2：阅读 Stage 3 的完成标准**

确认 `INSTALLATION.md` 当前只要求生成几个文件，尚未明确 `.architecture/members.yml` 必须覆盖项目所需的关键专家角色。

- [ ] **步骤 3：改写 Stage 3 的完成标准**

将 `INSTALLATION.md` 的完成标准改成以下方向：

```md
- 生成 `.architecture/members.yml`，且已覆盖当前项目所需的关键专家角色；当模板不足时，已包含新增的项目特有专家
- 生成 `.architecture/principles.md`
- 生成 `.architecture/templates/technical-solution-template.md`，并在初始化结束前确认该文件最终保留默认模板还是被用户提供的完整 Markdown 整体替换
```

- [ ] **步骤 4：人工复查边界**

确认 `skills/bootstrap-architecture/steps/3-customize-principles.md` 没有接入专家逻辑；确认 `INSTALLATION.md` 没有引入 `checkpoints.step-1`、`project_signals`、`expert_coverage` 或其他中间状态表述，只描述最终产物要求。

### 任务 4：做一次跨文件一致性复查

**文件：**
- 复查：`skills/bootstrap-architecture/steps/1-analyze-project.md`
- 复查：`skills/bootstrap-architecture/steps/2-customize-team.md`
- 复查：`skills/bootstrap-architecture/steps/3-customize-principles.md`
- 复查：`INSTALLATION.md`
- 复查：`docs/superpowers/specs/2026-04-04-bootstrap-custom-experts-design.md`

- [ ] **步骤 1：逐文件核对关键术语**

确认以下术语和职责一致：

```text
skills/bootstrap-architecture/steps/1-analyze-project.md -> project_signals / platform / capability / constraint
skills/bootstrap-architecture/steps/2-customize-team.md -> expert_coverage / template_roles / custom_roles / signal_coverage
skills/bootstrap-architecture/steps/3-customize-principles.md -> 项目上下文 / project_signals
INSTALLATION.md -> 关键专家角色 / 新增的项目特有专家
```

- [ ] **步骤 2：查看最终 diff**

运行：

```bash
git diff -- skills/bootstrap-architecture/steps/1-analyze-project.md skills/bootstrap-architecture/steps/2-customize-team.md skills/bootstrap-architecture/steps/3-customize-principles.md INSTALLATION.md docs/superpowers/specs/2026-04-04-bootstrap-custom-experts-design.md docs/superpowers/plans/2026-04-04-bootstrap-custom-experts.md
```

确认 diff 只包含本次方案需要的文档修改，没有把中间状态泄漏到 `INSTALLATION.md`，也没有让步骤 1 再次承担专家决策。

- [ ] **步骤 3：整理最终工作树状态**

运行：

```bash
git status --short
```

确认工作树只包含本次预期变更；如存在无关变更，不要回退用户已有修改。
