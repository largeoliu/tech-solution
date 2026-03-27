# Skill Drift Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成 `setup-architect` 与 `create-technical-solution` 的三场景漂移检查，并产出带证据路径的中文报告。

**Architecture:** 先建立两份 skill 的规范矩阵，把顶层流程、引用约束、停机点、确认点、交接产物收敛到同一处；再按场景 A/B/C 推演并写出逐场景结论、横向对比与最小修正建议。

**Tech Stack:** Markdown, 仓库内 skill 文档, `rg`, `python3`

---

## File Structure

- Create: `docs/superpowers/reports/2026-03-26-skill-drift-check-matrix.md` - 汇总两个 skill 的顶层流程、引用约束、停机点、确认点、交接产物与候选漂移风险。
- Create: `docs/superpowers/reports/2026-03-26-skill-drift-check-report.md` - 输出三场景检查结论、横向对比、问题分级与最小修正建议。
- Read: `docs/superpowers/specs/2026-03-26-skill-drift-check-design.md` - 已批准的检查设计，作为计划覆盖范围与判定口径的唯一规格来源。
- Read: `skills/setup-architect/SKILL.md` - 上游安装 skill 的主流程与完成标准。
- Read: `skills/setup-architect/references/installation-procedures.md` - 安装目录与文件产物来源。
- Read: `skills/setup-architect/references/member-customization.md` - 成员定制约束。
- Read: `skills/setup-architect/references/principles-customization.md` - 原则定制约束。
- Read: `skills/setup-architect/references/technical-solution-template-customization.md` - 模板替换规则与停止条件。
- Read: `skills/create-technical-solution/SKILL.md` - 技术方案生成 skill 的主流程、前置检查与完成标准。
- Read: `skills/create-technical-solution/references/solution-process.md` - 独立输入、信息块、质量门禁。
- Read: `skills/create-technical-solution/references/template-adaptation.md` - 模板映射与无法安全放置时的停止条件。
- Read: `skills/create-technical-solution/references/solution-analysis-guide.md` - 方案类型分析、成员集与风险清单来源。

### Task 1: Prepare Report Files

**Files:**
- Create: `docs/superpowers/reports/2026-03-26-skill-drift-check-matrix.md`
- Create: `docs/superpowers/reports/2026-03-26-skill-drift-check-report.md`
- Read: `docs/superpowers/specs/2026-03-26-skill-drift-check-design.md`

- [ ] **Step 1: Create the report directory**

Run: `mkdir -p docs/superpowers/reports`
Expected: command succeeds with no output

- [ ] **Step 2: Write the matrix document skeleton**

```markdown
# Skill 漂移规范矩阵

## setup-architect
| 顶层步骤 | 约束文档 | 必停节点 | 必确认节点 | 下游产物或假设 | 候选漂移风险 |
| --- | --- | --- | --- | --- | --- |

## create-technical-solution
| 顶层步骤 | 约束文档 | 必停节点 | 必确认节点 | 下游产物或假设 | 候选漂移风险 |
| --- | --- | --- | --- | --- | --- |
```

- [ ] **Step 3: Write the report document skeleton**

```markdown
# Skill 漂移检查报告

## 检查范围
- 检查对象：`setup-architect` 与 `create-technical-solution`
- 检查方法：规范矩阵 + 场景推演
- 检查场景：A 串联主路径，B 单独执行且前置不满足，C 单独执行且前置满足

## 判定口径
- `确认漂移`
- `高风险漂移`
- `无明显漂移`

## 场景 A：串联主路径
### 预期交接契约
### 检查发现
### 结论

## 场景 B：单独执行且前置不满足
### 预期停机行为
### 检查发现
### 结论

## 场景 C：单独执行且前置满足
### 预期独立执行路径
### 检查发现
### 结论

## 横向对比
## 最小修正建议
```

- [ ] **Step 4: Verify both report files have the expected headings**

Run: `rg -n "^## " docs/superpowers/reports/2026-03-26-skill-drift-check-*.md`
Expected: output includes `## setup-architect`, `## create-technical-solution`, `## 场景 A：串联主路径`, `## 场景 B：单独执行且前置不满足`, `## 场景 C：单独执行且前置满足`, `## 横向对比`, and `## 最小修正建议`

### Task 2: Build the `setup-architect` Matrix and Scenario A Contract

**Files:**
- Modify: `docs/superpowers/reports/2026-03-26-skill-drift-check-matrix.md`
- Modify: `docs/superpowers/reports/2026-03-26-skill-drift-check-report.md`
- Read: `skills/setup-architect/SKILL.md`
- Read: `skills/setup-architect/references/installation-procedures.md`
- Read: `skills/setup-architect/references/member-customization.md`
- Read: `skills/setup-architect/references/principles-customization.md`
- Read: `skills/setup-architect/references/technical-solution-template-customization.md`

- [ ] **Step 1: Extract the top-level workflow and reference constraints**

Run: `rg -n "完成标准|工作流程|只替换模板|技术方案模板|成员定制|原则定制" skills/setup-architect/SKILL.md skills/setup-architect/references/*.md`
Expected: matches from `skills/setup-architect/SKILL.md` plus all four reference documents

- [ ] **Step 2: Insert these exact `setup-architect` matrix rows**

```markdown
## setup-architect
| 顶层步骤 | 约束文档 | 必停节点 | 必确认节点 | 下游产物或假设 | 候选漂移风险 |
| --- | --- | --- | --- | --- | --- |
| 分析项目 | `skills/setup-architect/SKILL.md` | 无显式停机 | 无显式确认 | 识别语言、框架、测试、CI、部署、目录结构，作为后续定制依据 | 分析结果没有定义明确的交接格式，后续步骤容易各自解释 |
| 安装架构框架 | `skills/setup-architect/SKILL.md`；`skills/setup-architect/references/installation-procedures.md` | 结构错误时回到安装步骤 | 无显式确认 | 创建 `.architecture/technical-solutions/`、`.architecture/templates/`，并在目标不存在时复制模板、成员、原则文件 | 完成标准里的“配置种子”术语没有在安装说明里被单独定义 |
| 定制成员 | `skills/setup-architect/SKILL.md`；`skills/setup-architect/references/member-customization.md`；`skills/setup-architect/templates/members-template.yml` | 无显式停机 | 需要保留核心成员 | 生成可供下游选择参与者的 `.architecture/members.yml` | 模板中的建议性说明和强制性约束混在一起，容易被误读 |
| 定制原则 | `skills/setup-architect/SKILL.md`；`skills/setup-architect/references/principles-customization.md`；`skills/setup-architect/templates/principles-template.md` | 无显式停机 | 需要覆盖边界、API/事件/数据边界、测试、安全合规、决策标准 | 生成供下游共享上下文使用的 `.architecture/principles.md` | 最低覆盖范围写在引用文档里，但主流程没有单独复核点 |
| 复核结构并安全清理 | `skills/setup-architect/SKILL.md`；`skills/setup-architect/references/installation-procedures.md` | 结构不正确时返回安装步骤 | 无显式确认 | 确认 `.architecture/` 结构完整，可交给下游 skill 使用 | “安全清理”没有定义具体动作，容易让执行者自行脑补 |
| 询问模板定制并总结 | `skills/setup-architect/SKILL.md`；`skills/setup-architect/references/technical-solution-template-customization.md` | 仅替换模板但前置未完成时应停止 | 需要确认是否定制模板 | 生成最终可供下游读取的 `.architecture/templates/technical-solution-template.md` | 严格的整文件替换规则和停止条件主要在引用文档里，主流程里不够显式 |
```

- [ ] **Step 3: Write the Scenario A contract and review bullets into the report**

```markdown
## 场景 A：串联主路径
### 预期交接契约
- `setup-architect` 需要稳定产出 `.architecture/technical-solutions/`
- `setup-architect` 需要稳定产出 `.architecture/members.yml`
- `setup-architect` 需要稳定产出 `.architecture/principles.md`
- `setup-architect` 需要稳定产出 `.architecture/templates/technical-solution-template.md`

### 检查发现
- 先核对安装步骤是否显式创建目录和文件。
- 再核对成员定制、原则定制、模板定制是否会破坏下游契约。
- 重点验证“配置种子”“安全清理”“只替换模板”这 3 个容易漂移的点。

### 结论
- 只有在 4 个交接产物、模板替换规则、原则最小覆盖范围都闭合时，才能写成“无明显漂移”。
```

- [ ] **Step 4: Verify Scenario A findings reference source paths**

Run: `rg -n "skills/setup-architect|\\.architecture" docs/superpowers/reports/2026-03-26-skill-drift-check-report.md`
Expected: output shows path references near every contract bullet and finding block in the Scenario A section

### Task 3: Build the `create-technical-solution` Matrix and Scenarios B/C

**Files:**
- Modify: `docs/superpowers/reports/2026-03-26-skill-drift-check-matrix.md`
- Modify: `docs/superpowers/reports/2026-03-26-skill-drift-check-report.md`
- Read: `skills/create-technical-solution/SKILL.md`
- Read: `skills/create-technical-solution/references/solution-process.md`
- Read: `skills/create-technical-solution/references/template-adaptation.md`
- Read: `skills/create-technical-solution/references/solution-analysis-guide.md`

- [ ] **Step 1: Extract the workflow, stop rules, and reference-only constraints**

Run: `rg -n "前置|工作流程|模板|类型|质量门禁|system architect|覆盖写入|overwrite|信息块" skills/create-technical-solution/SKILL.md skills/create-technical-solution/references/*.md`
Expected: matches from `skills/create-technical-solution/SKILL.md`, `references/solution-process.md`, `references/template-adaptation.md`, and `references/solution-analysis-guide.md`

- [ ] **Step 2: Insert these exact `create-technical-solution` matrix rows**

```markdown
## create-technical-solution
| 顶层步骤 | 约束文档 | 必停节点 | 必确认节点 | 下游产物或假设 | 候选漂移风险 |
| --- | --- | --- | --- | --- | --- |
| 明确主题与范围 | `skills/create-technical-solution/SKILL.md` | 主题不清时继续澄清，不进入生成 | 无显式确认 | 形成主题、目标、非目标、约束、影响范围、文件名基础 | 如果范围澄清不充分，后续成员选择和模板映射都会漂移 |
| 校验前置 | `skills/create-technical-solution/SKILL.md` | 缺少 `.architecture/members.yml`、`.architecture/principles.md`、`.architecture/templates/technical-solution-template.md` 时立即停止并回指 `setup-architect` | 无显式确认 | 只有前置成立时才允许继续执行 | 输出目录 `.architecture/technical-solutions/` 缺失时是“创建”还是“停止”没有写清 |
| 加载成员并选择参与者 | `skills/create-technical-solution/SKILL.md`；`skills/create-technical-solution/references/solution-analysis-guide.md` | 无显式停机 | 参与者选择需要可解释，且应包含 system architect | 形成参与协作的成员集合 | 主流程把成员选择放在类型分析之前，和分析指南的顺序不一致 |
| 构建共享上下文并读取模板 | `skills/create-technical-solution/SKILL.md`；`skills/create-technical-solution/references/template-adaptation.md` | 模板结构无法安全承载信息块时应停止并询问用户 | 无显式确认 | 形成原则、现状、实现、外部约束、模板结构的共享语境 | 顶层又要求“总是先读当前模板”，但流程里把模板读取放在第 4 步，顺序容易漂移 |
| 组织独立成员输入 | `skills/create-technical-solution/SKILL.md`；`skills/create-technical-solution/references/solution-process.md` | 无显式停机 | 输入格式需要统一 | 形成可收敛的成员观点材料 | 如果只看主流程，容易漏掉引用文档中的统一输入契约 |
| 收敛结论并映射模板 | `skills/create-technical-solution/SKILL.md`；`skills/create-technical-solution/references/solution-process.md`；`skills/create-technical-solution/references/template-adaptation.md`；`skills/create-technical-solution/references/solution-analysis-guide.md` | 无法安全映射模板时必须停下询问用户 | 需要明确争议、选项、决策、权衡和开放问题 | 形成标准信息块并放入现有模板结构 | 质量门禁和强制信息块主要在引用文档里，顶层流程容易漏掉 |
| 生成、保存并报告结果 | `skills/create-technical-solution/SKILL.md`；`skills/create-technical-solution/references/solution-process.md` | 目标文件已存在但用户未确认更新时停止覆盖 | 需要确认是否覆盖已有文件 | 在 `.architecture/technical-solutions/` 下产出最终方案文档 | 完成标准弱于引用文档里的必备信息块，容易过早判定完成 |
```

- [ ] **Step 3: Write the Scenario B section with the explicit stop checks**

```markdown
## 场景 B：单独执行且前置不满足
### 预期停机行为
- 明确列出缺失的前置项
- 明确回指 `setup-architect`
- 不伪造 `.architecture/*`
- 不继续做成员选择、模板映射、文档生成

### 检查发现
- 重点核对前置检查是否写在顶层流程里。
- 重点核对输出目录缺失时是否有明确处理规则。
- 重点核对停机后是否还留下“半继续执行”的空间。

### 结论
- 只有显式前置检查、显式回指、显式停止都成立时，才能写成“无明显漂移”。
```

- [ ] **Step 4: Write the Scenario C section with the independent-execution checks**

```markdown
## 场景 C：单独执行且前置满足
### 预期独立执行路径
- 读取当前模板
- 判断方案类型
- 选择参与成员
- 构建共享上下文
- 组织独立输入
- 收敛并映射到模板
- 经过质量门禁后保存落盘

### 检查发现
- 重点核对“先读模板”与“第 4 步读模板”是否冲突。
- 重点核对“先做类型分析”与“先选成员”是否冲突。
- 重点核对质量门禁和强制信息块是否只藏在引用文档里。
- 重点核对保存时的覆盖确认是否足够显式。

### 结论
- 只有顺序一致、信息块完整、模板约束闭合时，才能写成“无明显漂移”。
```

### Task 4: Classify Findings and Finish the Report

**Files:**
- Modify: `docs/superpowers/reports/2026-03-26-skill-drift-check-report.md`
- Modify: `docs/superpowers/reports/2026-03-26-skill-drift-check-matrix.md`
- Read: `docs/superpowers/specs/2026-03-26-skill-drift-check-design.md`

- [ ] **Step 1: Add the cross-scenario comparison table**

```markdown
## 横向对比

| 维度 | 场景 A | 场景 B | 场景 C |
| --- | --- | --- | --- |
| 交接契约 | 检查 `setup-architect` 是否稳定产出 4 个下游依赖 | 不适用 | 依赖既有 4 个前置物是否足够独立运行 |
| 停机行为 | 检查模板替换专用分支是否有明确停止条件 | 检查前置失败时是否立刻停机 | 检查模板无法安全映射或覆盖未确认时是否停机 |
| 顺序一致性 | 检查上游定制顺序是否破坏下游假设 | 检查失败后是否还会继续后续步骤 | 检查模板读取、类型分析、成员选择、质量门禁顺序是否一致 |
| 引用依赖程度 | 检查关键规则是否散落在多个引用文档 | 检查停机规则是否只藏在引用文档 | 检查强制信息块和质量门禁是否只藏在引用文档 |
```

- [ ] **Step 2: Validate and classify the known candidate issues using fixed finding blocks**

For each issue below, add one finding block with `现象`、`原因`、`影响场景`、`证据路径`、`判定`、`最小修正建议` 这 6 项，先按默认分级写入，再在核对证据后微调：

```markdown
- `setup-architect` 中“配置种子”术语未在安装说明中落地，默认判定：`高风险漂移`
- `setup-architect` 中“安全清理”未定义具体动作，默认判定：`高风险漂移`
- `setup-architect` 的模板替换严格规则主要在引用文档里，默认判定：`高风险漂移`
- `create-technical-solution` 同时要求“总是先读当前模板”又把模板读取放在第 4 步，默认判定：`确认漂移`
- `create-technical-solution` 主流程先选成员、分析指南先定类型，默认判定：`确认漂移`
- `create-technical-solution` 对输出目录缺失时的处理不明确，默认判定：`高风险漂移`
- `create-technical-solution` 的质量门禁和强制信息块主要藏在引用文档里，默认判定：`高风险漂移`
- `create-technical-solution` 的完成标准弱于引用文档里的信息块要求，默认判定：`高风险漂移`
```

- [ ] **Step 3: Add the minimal remediation list verbatim**

```markdown
## 最小修正建议
- 将 `setup-architect` 中“配置种子”的具体含义收敛到安装步骤或完成标准中，避免术语漂移。
- 将 `setup-architect` 中“安全清理”的动作写明，避免执行者自行解释。
- 将 `setup-architect` 的模板替换停止条件前移到主流程，减少只看顶层 skill 时的漏读风险。
- 将 `create-technical-solution` 的“先读模板”和“第 4 步读模板”合并成一个明确顺序。
- 将 `create-technical-solution` 的类型分析和成员选择顺序统一，避免先选人再定分析类型。
- 将 `create-technical-solution` 对输出目录缺失时的行为写成显式规则。
- 将 `create-technical-solution` 的质量门禁和强制信息块提升到主 skill 或在主流程中显式回指。
```

- [ ] **Step 4: Run the final document checks**

Run: `rg -n "TODO|TBD|待补|稍后|之后处理" docs/superpowers/reports/2026-03-26-skill-drift-check-*.md`
Expected: no output

Run: `rg -n "现象|原因|影响场景|证据路径|判定|最小修正建议" docs/superpowers/reports/2026-03-26-skill-drift-check-report.md`
Expected: repeated matches showing every finding block contains all six required fields

Run: `python3 - <<'PY'
from pathlib import Path
report = Path('docs/superpowers/reports/2026-03-26-skill-drift-check-report.md').read_text()
required = [
    '## 检查范围',
    '## 判定口径',
    '## 场景 A：串联主路径',
    '## 场景 B：单独执行且前置不满足',
    '## 场景 C：单独执行且前置满足',
    '## 横向对比',
    '## 最小修正建议',
]
missing = [item for item in required if item not in report]
if missing:
    raise SystemExit('MISSING: ' + ', '.join(missing))
print('OK: all required sections present')
PY`
Expected: `OK: all required sections present`
