# AGENTS.md - Skill 开发规范指南

## 1. 适用范围

### 1.1 适用场景
- 新建 Skill 目录 `skills/<skill-name>/`
- 重写现有 Skill
- 系统性更新 Skill 内容

### 1.2 不适用场景
- 一次性复盘文档
- 项目背景说明
- 临时协作约定
- Skill 使用说明

### 1.3 设计原则
可脚本化的规则优先下沉到校验器；本文只保留需人工判断的部分。

---

## 2. 核心设计原则

### 2.1 单一职责原则
- 一个 Skill 只承担一个核心职责
- `description` 必须能区分它与相邻 Skill 的边界和触发场景

### 2.2 独立可执行原则
- `SKILL.md` 必须独立可执行
- 阅读后，Agent 应明确知道：该 Skill 做什么、如何进入主路径、何时不能继续
- `SKILL.md` 正文控制在 **500 行以内**

### 2.3 工作流明确原则
- 多步骤 Skill 必须写出工作流和关键串行依赖

### 2.4 一致性原则
- 主文件与支持目录不得互相矛盾
- 下级文档不能引用上级文档，引用链单向

### 2.5 简洁原则
- **上下文窗口是公共资源**，与系统提示、对话历史、其他 Skill 元数据共享
- 默认 Claude 已经很聪明，只添加它不知道的信息
- 每个信息都要自问：Claude 真的需要这段解释吗？这个 token 花得值吗？

### 2.6 设置合适的自由度
根据任务的脆弱性和变化性匹配指令的具体程度：

| 自由度 | 适用场景 | 示例 |
|--------|----------|------|
| **高** (文本指导) | 多种方法有效、依赖上下文决策 | 代码审查、设计评审 |
| **中** (伪代码/模板) | 有偏好模式、可接受一定变化 | 报告生成、数据处理 |
| **低** (精确命令) | 操作脆弱、一致性关键 | 数据库迁移、部署脚本 |

类比：窄桥有悬崖→给精确护栏；开阔场地→给方向并信任 Claude 找最佳路径。

### 2.7 命名规范
- 推荐使用 **gerund 形式** (动名词)：`processing-pdfs`、`analyzing-spreadsheets`、`testing-code`
- 可接受：名词短语 `pdf-processing`、动作导向 `process-pdfs`
- 避免：模糊名称 `helper`/`utils`/`tools`、过于泛化 `documents`/`data`
- `name` 字段规则：最多 64 字符，仅小写字母+数字+连字符，不含保留词 "anthropic"/"claude"

---

## 3. 反模式

| 序号 | 反模式 | 说明 |
|------|--------|------|
| 1 | 职责混杂 | 一个 Skill 同时承担多个核心职责 |
| 2 | 信息隐藏 | 把主路径、必要输入、停止条件藏进 `references/` |
| 3 | 内容矛盾 | 主文件、引用文件、模板说明互相矛盾 |
| 4 | 深层嵌套引用 | 引用链超过一层（SKILL.md → A.md → B.md），Claude 可能只预览不读完 |
| 5 | 太多选项 | 列出多种方法让 Claude 困惑，应给默认方案 + escape hatch |
| 6 | 时间敏感信息 | 包含会过期的日期/版本信息 |
| 7 | Windows 路径 | 使用反斜杠 `\`，应统一用正斜杠 `/` |
| 8 | 假设工具已安装 | 不说明依赖直接写用法 |

---

## 4. Description 字段规范

### 4.1 设计依据
Description 是 Skill 触发的主要机制。Claude 从可能上百个 Skill 中靠它做选择。

### 4.2 结构要求
```
[它做什么] + [何时使用] + [触发关键词]
```

### 4.3 关键规则
- **必须使用第三人称**：✅ "处理 Excel 文件" ❌ "我可以帮你处理"
- **用 imperative 指令**："Use when..." 而非 "This skill does..." — description 是行动指令而非说明文档
- **稍微 pushy**：明确列出触发场景，覆盖用户的多种说法
- **包含具体关键词**：用户可能用的各种同义词都要覆盖
- **最大 1024 字符**
- **注意触发边界**： Agent 只在需要专业领域知识时主动咨询 Skill，简单任务即使描述匹配也可能不触发

### 4.4 示例

**✅ 推荐写法**
```yaml
description: 分析 Figma 设计文件并生成开发者交接文档。当用户上传 .fig 文件、要求"设计规范"、"组件文档"或"设计到代码交接"时使用。
```

**❌ 太模糊 / 无触发条件**
```yaml
description: 帮助处理项目。
description: 实现具有层级关系的 Project 实体模型。
```

**❌ 第一人称**
```yaml
description: 我可以帮你分析数据并生成图表。
```

---

## 5. 渐进式披露

### 5.1 三层加载模型

| 层级 | 何时加载 | Token 消耗 | 内容 |
|------|----------|------------|------|
| **Level 1: 元数据** | 始终 (启动时) | ~100 tokens/Skill | `name` + `description` |
| **Level 2: 指令** | Skill 触发时 | <5k tokens | SKILL.md 正文 |
| **Level 3: 资源** | 按需加载 | 有效无限 | 引用文件、脚本、模板 |

### 5.2 目录结构
```
skill-name/
├── SKILL.md              # 主指令 (触发时加载)
├── FORMS.md              # 专项指南 (按需加载)
├── REFERENCE.md          # API 参考 (按需加载)
├── EXAMPLES.md           # 使用示例 (按需加载)
└── scripts/
    ├── analyze.py        # 工具脚本 (执行，不加载到上下文)
    └── validate.py       # 验证脚本
```

**关键区别**：脚本是**执行**的（输出消耗 token，代码不进入上下文），引用文件是**读取**的（内容进入上下文）。

### 5.3 引用规则
- **只深一层**：SKILL.md → reference.md ✅；SKILL.md → A.md → B.md ❌
- **长引用文件 (>100 行) 加目录**：方便 Claude 预览时看到全貌
- **文件名要有意义**：`form_validation_rules.md` ✅，`doc2.md` ❌
- **按领域组织**：`reference/finance.md`、`reference/sales.md` ✅

---

## 6. 主体指令编写规范

### 6.1 基本结构

```markdown
---
name: skill-name
description: [...]
---

# Skill 名称
## 使用说明（步骤/命令/预期输出）
## 示例（input → output 对）
## 故障排除（错误 → 原因 → 解决）
```

### 6.2 指令最佳实践

**✅ 具体且可执行**
```markdown
运行 `python scripts/validate.py --input {filename}` 检查数据格式。

验证失败常见问题：
- 缺少必填字段
- 日期格式无效（使用 YYYY-MM-DD）
```

**❌ 避免模糊表述**
```markdown
在继续之前验证数据。
```

**清晰引用资源**
```markdown
查阅 `references/api-patterns.md` 了解：
- 速率限制
- 分页模式
- 错误代码
```

### 6.3 解释 why 而非强制
解释原因比 ALWAYS/NEVER 更有效。现代 LLM 有 theory of mind，理解为什么后能超越机械指令。

**❌ 生硬强制**
```markdown
ALWAYS 使用 pdfplumber，NEVER 使用其他库。
```

**✅ 解释原因**
```markdown
使用 pdfplumber 提取文本。它在大多数场景下表现最好，API 简洁，且能处理嵌套表格。
对于需要 OCR 的扫描 PDF，改用 pdf2image + pytesseract。
```

### 6.4 避免太多选项
给一个默认方案，必要时提供 escape hatch。

**❌ 太多选择**
```markdown
你可以用 pypdf、pdfplumber、PyMuPDF、pdf2image...
```

**✅ 默认 + 备选**
```markdown
使用 pdfplumber 提取文本：
```python
import pdfplumber
```

对于需要 OCR 的扫描 PDF，改用 pdf2image + pytesseract。
```

---

## 7. 工作流模式

### 7.1 模板模式
固定格式输出用**严格模板**，需要适配的场景用**灵活模板**（"以下是合理默认格式，根据场景调整"）。

### 7.2 示例模式
提供 input/output 对，比纯描述更清晰：
```markdown
输入：添加 JWT 认证
输出：feat(auth): implement JWT-based authentication
```

### 7.3 条件工作流
在决策点引导 Agent 选择不同分支。

### 7.4 验证循环
"做 → 运行验证器 → 修复 → 重试，直到通过才继续"。

### 7.5 计划-验证-执行
适用于批量操作、破坏性变更：先结构化计划 → 用验证脚本检查 → 通过后执行 → 验证结果。提前捕获错误、错误信息具体可修复。

### 7.6 Checklist 模式
```markdown
任务进度：
- [ ] 步骤 1：分析 (运行 analyze.sh)
- [ ] 步骤 2：创建映射 (编辑 mapping.json)
- [ ] 步骤 3：验证 (运行 validate.sh)
```

---

## 8. 脚本规范

### 8.1 Solve, Don't Punt
脚本应处理错误条件，而不是抛给 Claude。

**✅ 显式处理错误**
```python
def process_file(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        print(f"File {path} not found, creating default")
        with open(path, "w") as f:
            f.write("")
        return ""
```

**❌ 抛给 Claude**
```python
def process_file(path):
    return open(path).read()  # 失败了让 Claude 自己想办法
```

### 8.2 避免 Magic Numbers
所有配置参数都应有理有据、有文档说明。

**✅ 自解释**
```python
REQUEST_TIMEOUT = 30  # HTTP 请求通常 30 秒内完成
MAX_RETRIES = 3       # 3 次重试平衡可靠性与速度，多数间歇故障在第 2 次前解决
```

**❌ 魔法数字**
```python
TIMEOUT = 47  # 为什么是 47？
RETRIES = 5   # 为什么是 5？
```

### 8.3 执行意图清晰
明确告诉 Claude 是**运行**脚本还是**阅读**参考：

```markdown
# ✅ 执行
运行 `python scripts/analyze_form.py input.pdf > fields.json`

# ✅ 阅读参考
参见 `scripts/analyze_form.py` 了解字段提取算法
```

### 8.4 明确依赖
列出所需包，不假设已安装：

```markdown
安装依赖：`pip install pdfplumber`

然后使用：
```python
import pdfplumber
```
```

### 8.5 验证脚本要 verbose
验证脚本应输出具体错误信息，帮助 Claude 修复：

```python
# ✅ 好的错误信息
print(f"字段 'signature_date' 不存在。可用字段: {available_fields}")

# ❌ 差的错误信息
raise KeyError("field not found")
```

---

## 9. 内容指南

### 9.1 避免时间敏感信息
**❌ 会过期的写法**
```markdown
2025 年 8 月之前用旧 API，之后用新 API。
```

**✅ 持久写法**
```markdown
## 当前方法
使用 v2 API：`api.example.com/v2/messages`

## 旧模式
<details>
<summary>旧版 v1 API（2025-08 已废弃）</summary>
使用 `api.example.com/v1/messages`，已不再支持。
</details>
```

### 9.2 术语一致性
全文统一用词：

**✅ 一致**：始终用 "API 端点"、始终用 "字段"、始终用 "提取"
**❌ 不一致**：混用 "API 端点"/"URL"/"API 路由"/"路径"

### 9.3 使用 Unix 路径
始终用正斜杠 `/`，即使在 Windows 上：
- ✅ `scripts/helper.py`、`reference/guide.md`
- ❌ `scripts\helper.py`、`reference\guide.md`

### 9.4 MCP 工具引用
使用 MCP 工具时，用全限定名避免 "tool not found" 错误：

```markdown
使用 BigQuery:bigquery_schema 工具获取表结构
使用 GitHub:create_issue 工具创建 issue
```

格式：`ServerName:tool_name`

---

## 10. Eval 驱动迭代

### 10.1 核心理念
**先建 eval 再写文档**。确保解决真实问题而非想象的需求。

**关键原则：Assertion 应该后定义。**
> "You often don't know what 'good' looks like until the skill has run."

先跑一轮不带 Skill 的基线和带 Skill 的对比，看到实际输出后再定义 assertion。预定义的 assertion 要么太容易（Agent 不带 Skill 也能过），要么太难（要求 Agent 做不到的事）。

**Skill 价值判断的量化标准：**
只有当 `with_skill` 的 pass_rate 提升显著超过额外的时间和 token 成本时，Skill 才有存在价值。如果不用 Skill 也做得一样好，**删掉这个 Skill**。

### 10.2 迭代流程

1. **识别差距**：不用 Skill 跑代表性任务，记录具体失败点
2. **创建 eval**：建 2-3 个场景，不要一开始就过度投入
3. **建立基线**：每个测试用例分别跑两次——**with_skill** 和 **without_skill**
4. **看输出再写 assertion**：对比两次输出，观察差异，定义 assertion
5. **写最小指令**：只写够解决差距、通过 eval 的内容
6. **迭代**：执行 eval → 分析 pattern → 精炼 → 重复

### 10.3 Claude A / Claude B 模式

- **Claude A** (专家)：帮助设计和精炼 Skill 指令
- **Claude B** (使用者)：加载 Skill 后执行真实任务

**流程**：
1. 用 Claude A 完成任务，注意重复提供的上下文
2. 识别可复用模式，让 Claude A 创建 Skill
3. 审查简洁性，去掉不必要的解释
4. 用 Claude B 在相似任务上测试
5. 观察 Claude B 的行为，带回具体问题给 Claude A 改进
6. 重复 observe-refine-test 循环

### 10.4 观察 Claude 如何导航 Skill

关注以下信号：
- **意外探索路径**：Claude 读文件顺序出乎意料 → 结构不够直觉
- **错过连接**：Claude 没跟随引用 → 链接不够明确
- **过度依赖某文件**：反复读同一文件 → 应考虑移入 SKILL.md
- **忽略某文件**：从不访问 → 可能不必要或信号不够

### 10.5 Eval 中的 Pattern 分析（关键）

Aggregate 统计会隐藏重要模式。每次 grading 完成后，逐项分析：

| 模式 | 含义 | 行动 |
|------|------|------|
| **Assertion 在两种配置下都 PASS** | 不区分 Skill 价值 | 删除或替换，Agent 不带 Skill 也做得到 |
| **Assertion 在两种配置下都 FAIL** | Assertion 太难或本身有问题 | 修复 assertion，或承认 Agent 做不到 |
| **有 Skill PASS，无 Skill FAIL** | Skill 真正增加价值的区域 | 理解**哪条指令或脚本**造成了差异，强化它 |
| **同一用例多次运行结果不一致** | 指令不够精确导致 Agent 解读不同 | 加具体示例、更明确的引导 |
| **某个用例耗时/Token 显著偏多** | 执行路径中有瓶颈 | 读 execution transcript 找到具体卡点 |

### 10.6 Assertion 的 Meta-Review

Assertion 本身也需要被审查，不只是看 assertion 的结果：

- **太容易**（always pass regardless of skill quality）→ 虚增 pass rate，删掉
- **太难**（always fail even when output looks humanly good）→ assertion 标准脱离实际
- **不可验证**（无法从输出本身判断是否达到）→ 移到 human review

> **不给 benefit of the doubt**——如果 assertion 说"包含摘要"而输出只有一个 "Summary" 标题 + 一句话 → FAIL。标签在但内容不在不算通过。

### 10.7 Human Review 不可省略

Assertion grading 只能检查你**想到了**的东西。Human reviewer 发现你没想到的问题：输出风格不对、遗漏隐含信息、技术正确但实际没用。

**推荐做法**：blind comparison — 把 with_skill 和 without_skill 的输出都给 LLM judge，**不给标签**，让它对组织性、格式、可用性、打磨度打分。两个输出可能都通过所有 assertion，但整体质量可能有显著差距。

### 10.8 描述优化的 Train/Validation 策略

Description 优化面临 **overfitting 风险**——反复针对同一批 query 调 description，最终只对这批 query 有效。

1. **准备 ~20 条 eval queries**（8-10 条应触发 + 8-10 条不应触发）
2. **Split**：train set ~60% + validation set ~40%，随机打乱，正负比例一致
3. **迭代**：只用 train set 指导改进，validation set 只看最终通过率
4. **选择最好的 validation 版本**，不一定是最后一个
5. **用 5-10 条全新 query 做最终 sanity check**

### 10.9 Eval 结构示例

```json
{
  "skills": ["pdf-processing"],
  "query": "从 PDF 提取所有文本并保存到 output.txt",
  "files": ["test-files/document.pdf"],
  "expected_behavior": [
    "使用合适的 PDF 处理库读取文件",
    "提取所有页面的文本内容，无遗漏",
    "将文本保存到 output.txt，格式清晰可读"
  ]
}
```

---

## 11. 格式规范

### 11.1 语言要求
- 除 `name` 字段外，所有段落使用中文
- 技术术语可保留英文

### 11.2 标题层级
- `#` 文档主标题
- `##` 主要章节
- `###` 子章节
- `####` 具体条目

### 11.3 列表样式
- 无序列表使用 `-`
- 有序列表使用数字
- 嵌套列表缩进 2 空格

### 11.4 代码块
- 使用 fenced code blocks
- 指定语言类型
- 行内代码使用反引号

---

## 12. 补充规范

### 12.1 裁剪原则：最高价值问题

在添加任何内容到 SKILL.md 前，自问：**"没有这段指令，Agent 会做错吗？"**
- 答案"不会" → 删掉
- 不确定 → 实测（跑一次不带 Skill 的基线对比）
- 整个任务不带 Skill 也做得很好 → 这个 Skill 本身不该存在

> Agent 的 context window 是公共资源，每个 token 都在与系统提示、对话历史、其他活跃 Skill 元数据竞争注意力。只添加 Agent **真的不知道**的信息（项目约定、领域陷阱、非直觉边界）。

### 12.2 脚本的 Agentic 行为契约

为 Agent 消费设计的脚本与普通脚本不同，必须满足以下硬要求：

| 要求 | 说明 |
|------|------|
| **禁止交互式提示** | 用 CLI flags、环境变量或 stdin 替代所有交互 |
| **支持 `--help`** | 输出描述 + flag 列表 + 示例，保持简洁 |
| **JSON stdout / 诊断 stderr** | 数据与诊断分离：stdout 输出结构化数据（JSON/CSV/TSV），stderr 输出诊断信息 |
| **幂等性** | 重复执行不产生额外副作用 |
| **有意义的退出码** | 0=成功，非 0=具体失败类型，Agent 可根据退出码决策下一步 |
| **破坏性操作的安全默认** | 默认 dry-run，显式 flag 才执行实际修改 |
| **输入约束枚举** | 对输入值做 enum 校验，返回具体错误如 `"mode 必须是 'preview'/'apply'，收到 'test'"` |

### 12.3 内联依赖声明（自包含脚本）

对于简单脚本推荐内联依赖声明，避免额外 `requirements.txt`：

**Python (PEP 723)**：
```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pdfplumber>=0.9"]
# ///
import pdfplumber
```
配合 `uv run script.py` 使用，自动创建隔离环境。

**Deno**：
```typescript
import { parse } from "jsr:@std/flags@1";
```

**Bun**：
```typescript
import { parse } from "csv-parse"; // 自动安装
```

### 12.4 `allowed-tools` 预授权字段

可选的 `allowed-tools` 字段声明 Skill 需要预批准的工具权限，减少运行时确认弹窗：

```yaml
allowed-tools: "Bash(git:*) Bash(jq:*) Read"
```

仅在工具调用频繁且权限明确需要时使用，大多数 Skill 不需要。

### 12.7 从实际错误积累 Gotchas

Gotchas 是 SKILL.md 中 ROI 最高的内容。不是通用建议（"处理错误"），而是**项目特定的反直觉事实**：

```markdown
## 常见陷阱

- `users` 表使用软删除，查询必须包含 `WHERE deleted_at IS NULL`
- 用户 ID 在数据库中是 `user_id`，认证服务中是 `uid`，计费 API 中是 `accountId`
- `/health` 返回 200 仅表示 Web 服务在运行，不代表数据库连接正常，用 `/ready` 检查完整健康状态
```

**积累方式**：每次 Agent 犯错需要纠正，把修正写进 Gotchas。

### 12.8 近失测试用例（Near-Miss Negatives）

描述优化中有价值的负例是**概念重叠但需求不同**的 query。例如 CSV 分析 Skill 的强负例："用 Python 读 CSV 写入 PostgreSQL"（涉及 CSV 但实际需求是数据库 ETL，不是分析）。

