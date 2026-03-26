# Technical Solution Progress Transparency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `create-technical-solution` 增加“阶段性播报协议”，在正式技术方案落盘前，按阶段向用户展示结构化专家产物和协作收敛纪要，减少等待黑盒感，并允许用户在中途纠偏。

**Architecture:** 保持现有主流程 `专家独立输入 -> 协作收敛 -> 最终成稿` 不变，只增加一层“对话内可见性协议”。详细展示契约放在独立参考文档中，`SKILL.md` 只负责接入和高层约束，`solution-process.md` 继续作为标准 schema 的事实来源并补充展示/回退规则。

**Tech Stack:** Markdown skill docs, repo conventions, `rg`, `git diff --check`, manual scenario walkthroughs, git commits

---

### Task 1: 新增阶段性播报协议参考文档

**Files:**
- Create: `skills/create-technical-solution/references/progress-transparency.md`
- Test: `skills/create-technical-solution/references/progress-transparency.md`

- [ ] **Step 1: 先做缺口检查**

Run: `rg -n "阶段性播报协议|专家产物：|协作收敛纪要|变更影响说明" "skills/create-technical-solution/references" || true`
Expected: no output

- [ ] **Step 2: 新建协议文档，写入最小可用版本**

Create `skills/create-technical-solution/references/progress-transparency.md` with the protocol for stage boundaries, expert cards, convergence memo, display boundary rules, and invalidation/re-entry behavior.

- [ ] **Step 3: 验证新文档已包含关键结构**

Run: `rg -n "阶段边界|专家产物：|协作收敛纪要|展示边界规则|变更影响说明" "skills/create-technical-solution/references/progress-transparency.md"`
Expected: matches for all five headings/patterns in the new file

- [ ] **Step 4: Commit**

```bash
git add skills/create-technical-solution/references/progress-transparency.md
git commit -m "feat(skill): 新增技术方案阶段性播报协议"
```

### Task 2: 将阶段性播报协议接入主技能合同

**Files:**
- Modify: `skills/create-technical-solution/SKILL.md`
- Test: `skills/create-technical-solution/SKILL.md`

- [ ] **Step 1: 先确认主技能还未接入该协议**

Run: `rg -n "progress-transparency|阶段性播报|过程可见产物|协作收敛纪要" "skills/create-technical-solution/SKILL.md" || true`
Expected: no output

- [ ] **Step 2: 修改完成标准、高层工作流、详细说明、行为契约、结果汇报格式**

Update `skills/create-technical-solution/SKILL.md` so it references the new transparency contract in completion criteria, member-input workflow, convergence workflow, detailed references, behavior contract, and result reporting.

- [ ] **Step 3: 验证主技能接入点都已出现**

Run: `rg -n "阶段性播报协议|专家产物|协作收敛纪要|过程可见产物|稳定、可解释、可归因" "skills/create-technical-solution/SKILL.md"`
Expected: matches in completion standard, workflow, docs list, behavior contract, and result report format

- [ ] **Step 4: Commit**

```bash
git add skills/create-technical-solution/SKILL.md
git commit -m "feat(skill): 为技术方案技能接入阶段性播报流程"
```

### Task 3: 扩展标准产出流程文档，连接 schema 与用户可见产物

**Files:**
- Modify: `skills/create-technical-solution/references/solution-process.md`
- Test: `skills/create-technical-solution/references/solution-process.md`

- [ ] **Step 1: 先确认流程文档还没有展示/回退规则**

Run: `rg -n "专家产物：|协作收敛纪要|阶段回退|变更影响说明|scratchpad" "skills/create-technical-solution/references/solution-process.md" || true`
Expected: no output

- [ ] **Step 2: 在独立输入和协作收敛章节后补充对话内展示格式，并新增回退规则章节**

Extend `skills/create-technical-solution/references/solution-process.md` with user-visible expert artifact formatting, user-visible convergence memo formatting, and stage rollback/invalidation rules.

- [ ] **Step 3: 扩展质量门槛，覆盖展示安全和回退安全**

Add quality checks for complete expert cards, rejected alternatives, invalidation announcements, scratchpad safety, and summary-first rendering.

- [ ] **Step 4: 验证流程文档已经覆盖展示和回退契约**

Run: `rg -n "对话内专家产物展示格式|对话内协作纪要展示格式|阶段回退与失效规则|变更影响说明|摘要优先" "skills/create-technical-solution/references/solution-process.md"`
Expected: matches for all five contracts

- [ ] **Step 5: Commit**

```bash
git add skills/create-technical-solution/references/solution-process.md
git commit -m "feat(skill): 补充中间产物展示与回退规则"
```

### Task 4: 更新 README 并做仓库级验收

**Files:**
- Modify: `README.md`
- Test: `README.md`
- Test: `skills/create-technical-solution/SKILL.md`
- Test: `skills/create-technical-solution/references/progress-transparency.md`
- Test: `skills/create-technical-solution/references/solution-process.md`

- [ ] **Step 1: 先确认 README 还没有说明中间产物可见性**

Run: `rg -n "专家产物|协作收敛纪要|默认只在对话中展示" "README.md" || true`
Expected: no output

- [ ] **Step 2: 补充用户可见行为说明**

Update the `create-technical-solution` usage section so it explains the expert artifacts, convergence memo, and in-conversation-only behavior.

- [ ] **Step 3: 运行仓库级契约检查**

Run: `rg -n "阶段性播报协议|专家产物|协作收敛纪要|默认只在对话中展示|过程可见产物" "README.md" "skills/create-technical-solution"`
Expected: matches spread across the updated files

Run: `git diff --check`
Expected: no output

- [ ] **Step 4: 做 3 个手工验收场景走查**

Walk through normal flow, strong-disagreement flow, and user-interruption flow using the new documentation contracts.

- [ ] **Step 5: Commit**

```bash
git add README.md skills/create-technical-solution/SKILL.md skills/create-technical-solution/references/progress-transparency.md skills/create-technical-solution/references/solution-process.md
git commit -m "feat(readme): 补充技术方案阶段性产物说明"
```
