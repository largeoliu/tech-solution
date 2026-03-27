# Skill Drift Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 `setup-architect` 与 `create-technical-solution` 的 6 个流程漂移问题，让主 skill 本身就能表达正确顺序、停机规则、模板约束和完成标准。

**Architecture:** 先把 `setup-architect` 改成带显式分支的权威入口，让模板替换硬规则直接出现在主 skill 中；再把 `create-technical-solution` 重排为唯一主路径，并把最小信息块、最小质量门槛和更严格的完成标准提升到主 skill。最后统一 4 份引用文档的职责边界与措辞，确保“当前生效模板”可以是默认模板也可以是用户替换后的自定义模板，且所有规则都围绕当前生效模板执行。

**Tech Stack:** Markdown, Python 3 standard library (`pathlib`), repository skill documents

---

## File Structure

- Modify: `skills/setup-architect/SKILL.md` - 将主 skill 改成完整初始化 / 模板替换两条明确分支，并把模板替换硬规则前移。
- Modify: `skills/setup-architect/references/technical-solution-template-customization.md` - 把模板替换引用文档改成“补充说明”角色，与主 skill 对齐。
- Modify: `skills/create-technical-solution/SKILL.md` - 重排唯一主路径，显式区分语义前置和输出目录，提升最小信息块、最小质量门槛和更严格的完成标准。
- Modify: `skills/create-technical-solution/references/solution-analysis-guide.md` - 收敛为类型分析依据、推荐成员、风险和评审重点来源，不再竞争顶层顺序。
- Modify: `skills/create-technical-solution/references/solution-process.md` - 保留独立输入、收敛、10 类信息块和完整质量门槛，同时与主 skill 的摘要闭环对齐。
- Modify: `skills/create-technical-solution/references/template-adaptation.md` - 统一“当前生效模板”措辞，强调模板可能是默认模板或用户替换后的自定义模板。
- Read: `docs/superpowers/specs/2026-03-26-skill-drift-fix-design.md` - 经用户确认的设计规格。
- Read: `skills/create-technical-solution/references/progress-transparency.md` - 保持中间产物展示约定不被主 skill 重排破坏。

### Task 1: Surface `setup-architect` Branches and Hard Rules

**Files:**
- Modify: `skills/setup-architect/SKILL.md`
- Read: `docs/superpowers/specs/2026-03-26-skill-drift-fix-design.md`
- Read: `skills/setup-architect/references/technical-solution-template-customization.md`

- [ ] **Step 1: Write the failing contract check for the main `setup-architect` skill**

```python
from pathlib import Path

text = Path("skills/setup-architect/SKILL.md").read_text()

required_snippets = [
    "## 使用路径",
    "### 路径 A：完整初始化",
    "### 路径 B：仅替换技术方案模板",
    "若 setup 不完整，则必须停止，并要求用户先完成完整初始化。",
    "只允许整体替换 `.architecture/templates/technical-solution-template.md`。",
    "不允许自动生成模板、局部编辑或内容合并。",
    "当前生效模板可以是默认模板，也可以是用户替换后的自定义模板。",
]

for snippet in required_snippets:
    assert snippet in text, f"missing snippet: {snippet}"
```

- [ ] **Step 2: Run the contract check and verify it fails**

Run: `python3 - <<'PY'
from pathlib import Path

text = Path("skills/setup-architect/SKILL.md").read_text()

required_snippets = [
    "## 使用路径",
    "### 路径 A：完整初始化",
    "### 路径 B：仅替换技术方案模板",
    "若 setup 不完整，则必须停止，并要求用户先完成完整初始化。",
    "只允许整体替换 `.architecture/templates/technical-solution-template.md`。",
    "不允许自动生成模板、局部编辑或内容合并。",
    "当前生效模板可以是默认模板，也可以是用户替换后的自定义模板。",
]

for snippet in required_snippets:
    assert snippet in text, f"missing snippet: {snippet}"
PY`
Expected: FAIL with `AssertionError` for the missing branch/rule snippets

- [ ] **Step 3: Replace the completion and workflow blocks in `skills/setup-architect/SKILL.md`**

```markdown
## 完成标准

- 创建最小 `.architecture/` 目录结构。
- 安装 `.architecture/members.yml`、`.architecture/principles.md` 和 `.architecture/templates/technical-solution-template.md`。
- 按项目现实定制成员与原则，并保证原则可直接用于技术方案与架构评审。
- `.architecture/templates/technical-solution-template.md` 已明确为当前生效模板。
- 当前生效模板可以是默认模板，也可以是用户替换后的自定义模板。

## 使用路径

### 路径 A：完整初始化

适用于首次安装、补跑初始化，或需要重新建立 `.architecture/` 基础结构的情况。

### 路径 B：仅替换技术方案模板

适用于 setup 已完成，且用户只想替换 `.architecture/templates/technical-solution-template.md` 的情况。

## 路径 A：完整初始化

### 1. 分析项目

识别语言、框架、测试/CI、部署方式和目录结构。

### 2. 安装架构框架

按 [references/installation-procedures.md](references/installation-procedures.md) 创建目录，并安装模板和基础文件。

### 3. 定制架构团队

按 [references/member-customization.md](references/member-customization.md) 设置专家成员。

### 4. 定制架构原则

按 [references/principles-customization.md](references/principles-customization.md) 补充与项目现实一致的原则；后续技术方案和架构评审会将这些原则作为必需输入。

### 5. 复核正式项目结构

按安装文档验证最终结构，若结构不符，返回第 2 步重新安装。

### 6. 确认当前生效模板并收尾

- 先询问用户是否需要定制技术方案模板。
- 若回答“不需要”，保留当前 `.architecture/templates/technical-solution-template.md`；首次安装通常保留默认模板，重跑初始化时也可能保留项目现有模板。
- 若回答“需要”，先校验 `.architecture/templates/technical-solution-template.md`、`.architecture/members.yml`、`.architecture/principles.md` 已存在；若 setup 不完整，则必须停止，并要求用户先完成完整初始化。
- 只接受完整 Markdown、文件路径或链接地址。
- 只允许整体替换 `.architecture/templates/technical-solution-template.md`。
- 不允许自动生成模板、局部编辑或内容合并。
- 详细输入处理和场景摘要见 [references/technical-solution-template-customization.md](references/technical-solution-template-customization.md)。

初始化摘要：

```text
Tech Solution 设置完成

技术方案模板：默认模板 / 已替换为用户自定义模板

接下来你可以：
- 编写技术方案文档
```

## 路径 B：仅替换技术方案模板

- 不重跑初始化流程。
- 先校验 `.architecture/templates/technical-solution-template.md`、`.architecture/members.yml`、`.architecture/principles.md` 已存在；若任一缺失，则必须停止，并要求用户先完成完整初始化。
- 直接要求用户提供完整 Markdown、文件路径或链接地址。
- 收到后整体替换 `.architecture/templates/technical-solution-template.md`。
- 不允许自动生成模板、局部编辑或内容合并。
- 详细输入处理和场景摘要见 [references/technical-solution-template-customization.md](references/technical-solution-template-customization.md)。
```

- [ ] **Step 4: Run the same contract check and verify it passes**

Run: `python3 - <<'PY'
from pathlib import Path

text = Path("skills/setup-architect/SKILL.md").read_text()

required_snippets = [
    "## 使用路径",
    "### 路径 A：完整初始化",
    "### 路径 B：仅替换技术方案模板",
    "若 setup 不完整，则必须停止，并要求用户先完成完整初始化。",
    "只允许整体替换 `.architecture/templates/technical-solution-template.md`。",
    "不允许自动生成模板、局部编辑或内容合并。",
    "当前生效模板可以是默认模板，也可以是用户替换后的自定义模板。",
]

for snippet in required_snippets:
    assert snippet in text, f"missing snippet: {snippet}"

print("OK: setup-architect main skill now exposes both branches and hard rules")
PY`
Expected: `OK: setup-architect main skill now exposes both branches and hard rules`

### Task 2: Align the Template-Replacement Reference With the Main Skill

**Files:**
- Modify: `skills/setup-architect/references/technical-solution-template-customization.md`
- Read: `skills/setup-architect/SKILL.md`

- [ ] **Step 1: Write the failing reference-alignment check**

```python
from pathlib import Path

text = Path("skills/setup-architect/references/technical-solution-template-customization.md").read_text()

assert "补充说明" in text
assert "主 skill 已定义模板替换的硬规则" in text
assert "唯一操作规范" not in text
assert "当前生效模板可能是默认模板，也可能是用户替换后的自定义模板。" in text
```

- [ ] **Step 2: Run the reference-alignment check and verify it fails**

Run: `python3 - <<'PY'
from pathlib import Path

text = Path("skills/setup-architect/references/technical-solution-template-customization.md").read_text()

assert "补充说明" in text
assert "主 skill 已定义模板替换的硬规则" in text
assert "唯一操作规范" not in text
assert "当前生效模板可能是默认模板，也可能是用户替换后的自定义模板。" in text
PY`
Expected: FAIL because the current file still describes itself as the unique operation spec and lacks the new alignment language

- [ ] **Step 3: Replace the reference intro and shared-rule sections with the aligned wording**

```markdown
# 技术方案模板定制与替换

此文档是 `setup-architect` 中模板替换分支的补充说明，用来展开输入细节、场景差异和摘要文案。

主 skill 已定义模板替换的硬规则：

- 替换前必须完成前置校验。
- 若 setup 不完整，则必须停止，并要求用户先完成完整初始化。
- 只接受完整 Markdown、文件路径或链接地址。
- 只允许整体替换 `.architecture/templates/technical-solution-template.md`。
- 不允许自动生成模板、局部编辑或内容合并。

这里不再重复充当唯一硬规则来源，而是补充说明两类场景：

- 初始化收尾时确认模板是否定制
- 项目已完成 setup 后，单独替换技术方案模板

当前生效模板可能是默认模板，也可能是用户替换后的自定义模板。

## 通用前置校验

先确认 setup 所需文件完整：

```bash
test -d .architecture/templates && echo "✅ Templates 目录存在"
test -f .architecture/templates/technical-solution-template.md && echo "✅ technical solution 模板存在"
test -f .architecture/members.yml && echo "✅ members.yml 存在"
test -f .architecture/principles.md && echo "✅ principles.md 存在"
```

若任一校验失败，则视为 setup 不完整，应停止并要求用户先执行完整初始化；不要静默补文件。

## 通用输入与替换规则

- 接受用户直接提供的完整 Markdown 模板内容、文件路径或者链接地址。
- 收到后整体替换 `.architecture/templates/technical-solution-template.md`。
- 若用户尚未提供完整 Markdown，则继续索要。
- 不支持恢复默认模板。
- 不支持自动生成模板、局部编辑或内容合并。

## 通用输出约定

- 输出中必须明确模板最终状态。
- 输出中必须明确目标文件为 `.architecture/templates/technical-solution-template.md`。
- 各场景只保留自己的摘要文案，不重复定义主 skill 已明确的硬规则。
```

- [ ] **Step 4: Run the same reference-alignment check and verify it passes**

Run: `python3 - <<'PY'
from pathlib import Path

text = Path("skills/setup-architect/references/technical-solution-template-customization.md").read_text()

assert "补充说明" in text
assert "主 skill 已定义模板替换的硬规则" in text
assert "唯一操作规范" not in text
assert "当前生效模板可能是默认模板，也可能是用户替换后的自定义模板。" in text

print("OK: template replacement reference is now aligned with the main skill")
PY`
Expected: `OK: template replacement reference is now aligned with the main skill`

### Task 3: Rebuild the `create-technical-solution` Main Path

**Files:**
- Modify: `skills/create-technical-solution/SKILL.md`
- Read: `docs/superpowers/specs/2026-03-26-skill-drift-fix-design.md`
- Read: `skills/create-technical-solution/references/solution-process.md`
- Read: `skills/create-technical-solution/references/solution-analysis-guide.md`
- Read: `skills/create-technical-solution/references/template-adaptation.md`
- Read: `skills/create-technical-solution/references/progress-transparency.md`

- [ ] **Step 1: Write the failing contract check for the main `create-technical-solution` skill**

```python
from pathlib import Path

text = Path("skills/create-technical-solution/SKILL.md").read_text()

order = [
    "### 2. 检查语义前置文件",
    "### 3. 读取当前生效模板",
    "### 4. 判断方案类型",
    "### 5. 加载成员名册并选择参与者",
]

positions = [text.index(item) for item in order]
assert positions == sorted(positions), positions

required_snippets = [
    "若三个关键文件齐全但 `.architecture/technical-solutions/` 缺失，则自动创建该目录后继续。",
    "## 主文档可见的最小信息块",
    "## 主文档可见的最小质量门槛",
    "至少存在一个被认真比较过的备选方案，并写明未选原因。",
    "已体现边界与职责、依赖关系、实施建议和评审关注点。",
    "最终内容已按当前生效模板完成落位，且保存行为符合覆盖确认规则。",
]

for snippet in required_snippets:
    assert snippet in text, f"missing snippet: {snippet}"
```

- [ ] **Step 2: Run the contract check and verify it fails**

Run: `python3 - <<'PY'
from pathlib import Path

text = Path("skills/create-technical-solution/SKILL.md").read_text()

order = [
    "### 2. 检查语义前置文件",
    "### 3. 读取当前生效模板",
    "### 4. 判断方案类型",
    "### 5. 加载成员名册并选择参与者",
]

positions = [text.index(item) for item in order]
assert positions == sorted(positions), positions

required_snippets = [
    "若三个关键文件齐全但 `.architecture/technical-solutions/` 缺失，则自动创建该目录后继续。",
    "## 主文档可见的最小信息块",
    "## 主文档可见的最小质量门槛",
    "至少存在一个被认真比较过的备选方案，并写明未选原因。",
    "已体现边界与职责、依赖关系、实施建议和评审关注点。",
    "最终内容已按当前生效模板完成落位，且保存行为符合覆盖确认规则。",
]

for snippet in required_snippets:
    assert snippet in text, f"missing snippet: {snippet}"
PY`
Expected: FAIL because the current file still has the old order and lacks the new summary sections/rules

- [ ] **Step 3: Replace the positioning, summary, completion, workflow, and contract blocks in `skills/create-technical-solution/SKILL.md`**

```markdown
## 技能定位

- 负责把主题、约束、架构成员观点和阶段性中间产物收敛为可评审的正式技术方案文档。
- 依赖项目约定文件，而不是临时口头约定：
  - `.architecture/members.yml`
  - `.architecture/principles.md`
  - `.architecture/templates/technical-solution-template.md`
- 当前 `.architecture/templates/technical-solution-template.md` 是唯一正文骨架来源；它可能是默认模板，也可能是用户替换后的自定义模板。
- 必须先读取当前生效模板，再判断方案类型，再选择参与成员。
- 主 skill 负责唯一主路径、关键停机规则、最小信息块摘要、最小质量门槛和完成标准；引用文档负责完整细则。
- 只在需要正式技术方案文档时使用；如果只是初始化 `.architecture/`、补跑安装或替换模板，转到 `setup-architect`。

## 主文档可见的最小信息块

- 问题与背景
- 目标与非目标
- 约束与依赖
- 推荐方案
- 备选方案与权衡
- 详细设计
- 风险与缓解
- 实施建议
- 评审关注点
- 未决问题

这些是最小必须覆盖的语义内容，而不是固定章节名。

如果当前生效模板没有与这些信息块一一对应的显式章节，也不能跳过它们；必须按模板语义把内容落到现有章节、小节、表格或列表中。

如果某个必需信息块无法在不破坏模板意图、且不新增新的一级章节的前提下安全落位，立即停止并向用户确认。

## 主文档可见的最小质量门槛

- 每个标准信息块都已生成。
- 分阶段中间产物已按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示。
- 至少存在一个被认真比较过的备选方案，并写明未选原因。
- 每个主要风险都包含影响、概率判断和缓解方向。
- 已体现边界与职责、依赖关系、实施建议和评审关注点。
- 未决问题写明缺什么信息、由谁补齐。
- 最终内容已按当前生效模板完成落位，而不是退回默认模板章节。

## 完成标准

- 主题、目标、非目标、约束、影响范围已经明确。
- 参与成员选择与方案类型一致，且至少包含系统架构师。
- 共享上下文已覆盖原则、现状、已有实现、关键约束和当前生效模板结构。
- 成员独立输入与协作收敛结果完整，并已抽象为标准信息块。
- 分阶段中间产物已按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示：每位参与成员各 1 份结构化 `专家产物`，以及 1 份结构化 `协作收敛纪要`；这些中间产物默认不作为侧车文档落盘。
- 文档已覆盖关键标准信息块，并体现备选方案、未选原因、风险判断与缓解方向。
- 已体现边界与职责、依赖关系、实施建议、评审关注点和未决问题。
- 最终内容已按当前生效模板完成落位，且保存行为符合覆盖确认规则。

## 高层工作流

### 1. 定题与范围判断

输入可以是方案主题、需求描述、已有文档路径，或用户给出的上下文片段。

先明确：问题、目标与非目标、约束与依赖、影响范围、相关需求。主题模糊时先澄清，再生成安全的短横线风格文件名。

### 2. 检查语义前置文件

确认以下文件全部存在：

- `.architecture/members.yml`
- `.architecture/principles.md`
- `.architecture/templates/technical-solution-template.md`

任一缺失时立即停止，明确说明初始化未完成，并引导用户先使用 `setup-architect`。

### 3. 读取当前生效模板

读取当前 `.architecture/templates/technical-solution-template.md` 的标题、章节层级、说明文字和现有结构。它可能是默认模板，也可能是用户替换后的自定义模板；后续正文必须服从它的实际结构。

### 4. 判断方案类型

先按 [references/solution-analysis-guide.md](references/solution-analysis-guide.md) 判断主题命中哪一类方案，再据此确定必答问题、易漏风险、评审重点和推荐参与成员。

### 5. 加载成员名册并选择参与者

读取 `.architecture/members.yml`。默认至少包含系统架构师；再根据上一步的方案类型与名册中的自定义专家决定最终参与成员集合。

### 6. 构建共享上下文

整合 `.architecture/principles.md`、代码与配置、Repo Wiki、现有实现、相关文档和外部约束。原则文档是判断标准，不是可选背景。

### 7. 组织成员独立输入

要求每个参与成员基于共享上下文，按统一字段独立产出自己的判断，不要直接重复别人的结论。

每个成员完成独立输入后，立即按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示该成员的结构化 `专家产物`。

详细格式见 [references/solution-process.md](references/solution-process.md)。

### 8. 收敛为标准信息块

把成员输入收敛成共同结论、争议点、候选方案对比、选定方向、原则冲突与取舍、未决问题，再整理成标准信息块。

完成收敛后、生成最终文档前，必须先按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示 1 份结构化 `协作收敛纪要`。如果用户在 `专家产物` 或 `协作收敛纪要` 展示后新增约束、修正目标或调整范围，先说明失效范围，再从最近受影响的阶段边界重进。

### 9. 将信息块落位到当前模板并通过质量门槛

把标准信息块无侵入落到当前生效模板；若模板没有同名章节，则按现有结构语义落位。若无法安全落位则停止并向用户确认。生成最终文档前，逐项检查主文档可见的最小质量门槛和 [references/solution-process.md](references/solution-process.md) 的完整质量门槛。

### 10. 保存并汇报结果

若三个关键文件齐全但 `.architecture/technical-solutions/` 缺失，则自动创建该目录后继续。

将最终文档写入 `.architecture/technical-solutions/[主题-短横线文件名].md`。

若目标文件已存在且用户未明确要求更新，先确认覆盖还是另存；不要静默覆盖无关文档。

## 行为契约

执行此技能时，始终遵守以下契约：

1. 先读取当前生效模板。
2. 再判断方案类型。
3. 再选择参与成员。
4. 分阶段在对话中展示 `专家产物` 与 `协作收敛纪要`。
5. 先生成标准信息块，再把它们无侵入落到当前生效模板。
6. 缺少语义前置、无法展示稳定中间产物或无法安全落位时停止并确认。
```

- [ ] **Step 4: Run the same contract check and verify it passes**

Run: `python3 - <<'PY'
from pathlib import Path

text = Path("skills/create-technical-solution/SKILL.md").read_text()

order = [
    "### 2. 检查语义前置文件",
    "### 3. 读取当前生效模板",
    "### 4. 判断方案类型",
    "### 5. 加载成员名册并选择参与者",
]

positions = [text.index(item) for item in order]
assert positions == sorted(positions), positions

required_snippets = [
    "若三个关键文件齐全但 `.architecture/technical-solutions/` 缺失，则自动创建该目录后继续。",
    "## 主文档可见的最小信息块",
    "## 主文档可见的最小质量门槛",
    "至少存在一个被认真比较过的备选方案，并写明未选原因。",
    "已体现边界与职责、依赖关系、实施建议和评审关注点。",
    "最终内容已按当前生效模板完成落位，且保存行为符合覆盖确认规则。",
]

for snippet in required_snippets:
    assert snippet in text, f"missing snippet: {snippet}"

print("OK: create-technical-solution main skill now has one path and explicit acceptance closure")
PY`
Expected: `OK: create-technical-solution main skill now has one path and explicit acceptance closure`

### Task 4: Realign the Detailed Reference Documents

**Files:**
- Modify: `skills/create-technical-solution/references/solution-analysis-guide.md`
- Modify: `skills/create-technical-solution/references/solution-process.md`
- Modify: `skills/create-technical-solution/references/template-adaptation.md`
- Read: `skills/create-technical-solution/SKILL.md`

- [ ] **Step 1: Write the failing reference-role regression check**

```python
from pathlib import Path

analysis = Path("skills/create-technical-solution/references/solution-analysis-guide.md").read_text()
process = Path("skills/create-technical-solution/references/solution-process.md").read_text()
adapt = Path("skills/create-technical-solution/references/template-adaptation.md").read_text()

assert "顶层执行顺序以 `skills/create-technical-solution/SKILL.md` 为准" in analysis
assert "主 skill 提供摘要式闭环；本文件提供完整版细则。" in process
assert "当前生效模板可能是默认模板，也可能是用户替换后的自定义模板。" in adapt
assert "如果当前模板无法安全承载某个必需信息块，应停止并向用户确认，而不是回退到默认模板章节。" in adapt
```

- [ ] **Step 2: Run the reference-role regression check and verify it fails**

Run: `python3 - <<'PY'
from pathlib import Path

analysis = Path("skills/create-technical-solution/references/solution-analysis-guide.md").read_text()
process = Path("skills/create-technical-solution/references/solution-process.md").read_text()
adapt = Path("skills/create-technical-solution/references/template-adaptation.md").read_text()

assert "顶层执行顺序以 `skills/create-technical-solution/SKILL.md` 为准" in analysis
assert "主 skill 提供摘要式闭环；本文件提供完整版细则。" in process
assert "当前生效模板可能是默认模板，也可能是用户替换后的自定义模板。" in adapt
assert "如果当前模板无法安全承载某个必需信息块，应停止并向用户确认，而不是回退到默认模板章节。" in adapt
PY`
Expected: FAIL because the current reference docs still use the older responsibility wording

- [ ] **Step 3: Replace the intro/responsibility paragraphs in the three reference docs**

```markdown
# 技术方案分析指引

这个文档只定义“看什么”。它负责提供方案类型识别依据、推荐参与成员、必答问题、易漏风险和评审重点，不负责最终文档结构，也不负责顶层执行顺序。无论当前生效模板是默认模板还是用户替换后的自定义模板，这份分析指引都可直接复用。

## 使用方式

顶层执行顺序以 `skills/create-technical-solution/SKILL.md` 为准：先读取当前生效模板，再判断方案类型，再选择参与成员。本文只负责在“判断方案类型”这一步提供分析依据。

先判断当前主题最像哪一类方案，再决定是否同时命中多类。
```

```markdown
# 技术方案标准产出流程

这个文档只定义“怎么产出”。它负责成员独立输入格式、协作收敛格式、标准信息块和完整质量门槛，不负责方案类型差异判断，也不负责顶层执行顺序。主 skill 提供摘要式闭环；本文件提供完整版细则。
```

```markdown
## 6. 标准信息块

协作收敛完成后，必须整理出一组模板无关的标准信息块。它们是内容契约，不等同于当前模板中的章节名。当前生效模板可能是默认模板，也可能是用户替换后的自定义模板；一个信息块可以独占一个章节，也可以和其他信息块共享同一个现有章节。
```

```markdown
## 7. 质量门槛

生成最终文档前，先满足主 skill 可见的最小质量门槛，再逐项自检本节的完整质量门槛：
```

```markdown
# 技术方案模板适配规则

这个文档只定义“如何把标准信息块落到当前生效模板”。它不定义信息块本身，不负责成员分析，也不修改用户自定义模板的定制流程。这里的“当前生效模板”可能是默认模板，也可能是用户替换后的自定义模板。

## 基本原则

- 当前 `.architecture/templates/technical-solution-template.md` 是唯一正文骨架来源。
- 当前生效模板可能是默认模板，也可能是用户替换后的自定义模板。
- 先理解当前模板的语义和层级，再决定信息块落位。
- 允许在现有章节内部增加更细的小节、列表标题或表格行。
- 不允许新增用户模板没有定义的一级章节。
- 不允许把当前模板重写回默认模板结构。
- 不允许要求用户补标记、占位符、前置元数据或额外契约文件。
- 如果当前模板无法安全承载某个必需信息块，应停止并向用户确认，而不是回退到默认模板章节。
```

- [ ] **Step 4: Run the same reference-role regression check and verify it passes**

Run: `python3 - <<'PY'
from pathlib import Path

analysis = Path("skills/create-technical-solution/references/solution-analysis-guide.md").read_text()
process = Path("skills/create-technical-solution/references/solution-process.md").read_text()
adapt = Path("skills/create-technical-solution/references/template-adaptation.md").read_text()

assert "顶层执行顺序以 `skills/create-technical-solution/SKILL.md` 为准" in analysis
assert "主 skill 提供摘要式闭环；本文件提供完整版细则。" in process
assert "当前生效模板可能是默认模板，也可能是用户替换后的自定义模板。" in adapt
assert "如果当前模板无法安全承载某个必需信息块，应停止并向用户确认，而不是回退到默认模板章节。" in adapt

print("OK: create-technical-solution reference docs now match the main-skill contract")
PY`
Expected: `OK: create-technical-solution reference docs now match the main-skill contract`

### Task 5: Run End-to-End Contract Verification

**Files:**
- Read: `skills/setup-architect/SKILL.md`
- Read: `skills/setup-architect/references/technical-solution-template-customization.md`
- Read: `skills/create-technical-solution/SKILL.md`
- Read: `skills/create-technical-solution/references/solution-analysis-guide.md`
- Read: `skills/create-technical-solution/references/solution-process.md`
- Read: `skills/create-technical-solution/references/template-adaptation.md`
- Read: `docs/superpowers/specs/2026-03-26-skill-drift-fix-design.md`

- [ ] **Step 1: Run the consolidated spec-coverage verification script**

Run: `python3 - <<'PY'
from pathlib import Path

setup_main = Path('skills/setup-architect/SKILL.md').read_text()
setup_ref = Path('skills/setup-architect/references/technical-solution-template-customization.md').read_text()
cts_main = Path('skills/create-technical-solution/SKILL.md').read_text()
analysis = Path('skills/create-technical-solution/references/solution-analysis-guide.md').read_text()
process = Path('skills/create-technical-solution/references/solution-process.md').read_text()
adapt = Path('skills/create-technical-solution/references/template-adaptation.md').read_text()

assert '### 路径 A：完整初始化' in setup_main
assert '### 路径 B：仅替换技术方案模板' in setup_main
assert '只允许整体替换 `.architecture/templates/technical-solution-template.md`。' in setup_main
assert '主 skill 已定义模板替换的硬规则' in setup_ref

order = [
    '### 2. 检查语义前置文件',
    '### 3. 读取当前生效模板',
    '### 4. 判断方案类型',
    '### 5. 加载成员名册并选择参与者',
]
positions = [cts_main.index(item) for item in order]
assert positions == sorted(positions), positions

assert '若三个关键文件齐全但 `.architecture/technical-solutions/` 缺失，则自动创建该目录后继续。' in cts_main
assert '## 主文档可见的最小信息块' in cts_main
assert '## 主文档可见的最小质量门槛' in cts_main
assert '最终内容已按当前生效模板完成落位，且保存行为符合覆盖确认规则。' in cts_main

assert '顶层执行顺序以 `skills/create-technical-solution/SKILL.md` 为准' in analysis
assert '主 skill 提供摘要式闭环；本文件提供完整版细则。' in process
assert '当前生效模板可能是默认模板，也可能是用户替换后的自定义模板。' in adapt
assert '停止并向用户确认' in adapt

print('OK: all six documents reflect the approved drift-fix contract')
PY`
Expected: `OK: all six documents reflect the approved drift-fix contract`

- [ ] **Step 2: Run the placeholder scan across all modified skill docs**

Run: `python3 - <<'PY'
from pathlib import Path

targets = [
    Path('skills/setup-architect/SKILL.md'),
    Path('skills/setup-architect/references/technical-solution-template-customization.md'),
    Path('skills/create-technical-solution/SKILL.md'),
    Path('skills/create-technical-solution/references/solution-analysis-guide.md'),
    Path('skills/create-technical-solution/references/solution-process.md'),
    Path('skills/create-technical-solution/references/template-adaptation.md'),
]
needles = ('TODO', 'TBD', '待补', '稍后', '之后处理')

matches = []
for path in targets:
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        for needle in needles:
            if needle in line:
                matches.append(f'{path}:{lineno}:{needle}:{line}')

if matches:
    raise SystemExit('\n'.join(matches))

print('OK: no placeholder terms in modified skill docs')
PY`
Expected: `OK: no placeholder terms in modified skill docs`

- [ ] **Step 3: Run the diff sanity check on the edited skill files**

Run: `git diff --check -- skills/setup-architect/SKILL.md skills/setup-architect/references/technical-solution-template-customization.md skills/create-technical-solution/SKILL.md skills/create-technical-solution/references/solution-analysis-guide.md skills/create-technical-solution/references/solution-process.md skills/create-technical-solution/references/template-adaptation.md`
Expected: no output
