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
- **必须使用第三人称**：✅ "处理 Excel 文件并生成报告" ❌ "我可以帮你处理 Excel 文件"
- **稍微 pushy**：Claude 倾向于 undertrigger，需要明确列出触发场景
- **包含具体关键词**：用户可能用的各种说法都要覆盖
- **最大 1024 字符**

### 4.4 优秀示例

**✅ 具体且可执行**
```yaml
description: 分析 Figma 设计文件并生成开发者交接文档。当用户上传 .fig 文件、要求"设计规范"、"组件文档"或"设计到代码交接"时使用。
```

**✅ 包含触发短语 (pushy 版)**
```yaml
description: 构建简单快速的数据可视化仪表板。当用户提到仪表板、数据可视化、内部指标、或想展示任何公司数据时使用，即使用户没有明确说"仪表板"。
```

**✅ 清晰的价值主张**
```yaml
description: PayFlow 的端到端客户入职工作流。处理账户创建、支付设置和订阅管理。当用户说"入职新客户"、"设置订阅"或"创建 PayFlow 账户"时使用。
```

### 4.5 糟糕示例

**❌ 太模糊**
```yaml
description: 帮助处理项目。
```

**❌ 缺少触发条件**
```yaml
description: 创建复杂的多页文档系统。
```

**❌ 过于技术性，无用户触发词**
```yaml
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

## 使用说明

### 步骤 1：[步骤名称]
步骤说明。

```bash
命令示例
```

**预期输出：** 成功结果描述

## 示例

### 示例 1：场景名称

**用户说：**"用户输入"

**执行动作：**
1. 动作一
2. 动作二

**结果：** 执行结果

## 故障排除

### 错误：错误信息

**原因：** 原因说明

**解决方案：** 解决方法
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

**严格模板** (API 响应、数据格式等)：
```markdown
## 报告结构
ALWAYS 使用此模板：
```markdown
# [标题]
## 执行摘要
## 关键发现
## 建议
```
```

**灵活模板** (需要适配的场景)：
```markdown
## 报告结构
以下是合理的默认格式，根据具体分析类型调整：
```markdown
# [标题]
## 执行摘要
## 关键发现
[根据发现调整章节]
```
```

### 7.2 示例模式
提供 input/output 对，比纯描述更清晰：

```markdown
## Commit 消息格式

**示例 1：**
输入：添加了基于 JWT 的用户认证
输出：
```
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
```

**示例 2：**
输入：修复了报告中日期显示不正确的 bug
输出：
```
fix(reports): correct date formatting in timezone conversion
```

遵循此风格：type(scope): 简短描述，然后详细解释。
```

### 7.3 条件工作流模式
在决策点引导 Claude：

```markdown
## 文档修改工作流

1. 确定修改类型：

   **创建新内容？** → 跟随下方"创建工作流"
   **编辑现有内容？** → 跟随下方"编辑工作流"

2. 创建工作流：使用 docx-js 库，从零构建
3. 编辑工作流：解包文档 → 修改 XML → 每次修改后验证 → 重新打包
```

### 7.4 验证循环模式
运行验证器 → 修复错误 → 重复：

```markdown
## 内容审核流程

1. 按照 STYLE_GUIDE.md 起草内容
2. 对照清单审核：
   - 检查术语一致性
   - 验证示例格式
   - 确认必填章节
3. 如发现问题：记录问题 → 修改 → 重新审核
4. 全部通过后才继续
5. 保存最终文档
```

### 7.5 计划-验证-执行模式
适用于批量操作、破坏性变更、高风险操作：

```markdown
## 批量更新流程

1. 分析：运行 `python scripts/analyze.py input.pdf` 生成 `fields.json`
2. 创建计划：编辑 `changes.json` 列出所有变更
3. 验证计划：运行 `python scripts/validate.py changes.json`
   - 如验证失败：修复 → 重新验证
4. 执行：运行 `python scripts/apply.py changes.json`
5. 验证结果：运行 `python scripts/verify.py output.pdf`
```

**为什么有效**：提前捕获错误、机器可验证、可逆规划、错误信息具体可修复。

### 7.6 Checklist 模式
复杂流程提供检查清单，让 Claude 跟踪进度：

```markdown
任务进度：
- [ ] 步骤 1：分析表单 (运行 analyze_form.py)
- [ ] 步骤 2：创建字段映射 (编辑 fields.json)
- [ ] 步骤 3：验证映射 (运行 validate_fields.py)
- [ ] 步骤 4：填充表单 (运行 fill_form.py)
- [ ] 步骤 5：验证输出 (运行 verify_output.py)
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

### 10.2 迭代流程

1. **识别差距**：不用 Skill 跑代表性任务，记录具体失败点
2. **创建 eval**：建 3 个场景测试这些差距
3. **建立基线**：测量无 Skill 时的表现
4. **写最小指令**：只写够解决差距、通过 eval 的内容
5. **迭代**：执行 eval、对比基线、精炼

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

### 10.5 Eval 结构示例

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

## 12. 总结

本文档定义 Skill 开发规范：

1. **适用范围** - 明确适用和不适用场景
2. **核心设计原则** - 单一职责、独立可执行、工作流明确、一致性、简洁、自由度、命名规范
3. **反模式** - 需避免的设计陷阱
4. **Description 规范** - 第三人称、具体、pushy、包含触发关键词
5. **渐进式披露** - 三层加载、只深一层、按领域组织
6. **指令编写规范** - 解释 why、避免多选项、具体可执行
7. **工作流模式** - 模板、示例、条件、验证循环、计划-验证-执行、checklist
8. **脚本规范** - solve don't punt、无 magic numbers、执行意图清晰、明确依赖
9. **内容指南** - 无时间敏感信息、术语一致、Unix 路径、MCP 全限定名
10. **Eval 驱动迭代** - Claude A/B 模式、观察真实行为
11. **格式规范** - 语言和排版要求
