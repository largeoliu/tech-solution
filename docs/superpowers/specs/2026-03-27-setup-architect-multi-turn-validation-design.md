---
# setup-architect 多轮验证建模设计

**日期**：2026-03-27

**目标**：在不引入真实模型调用和 CLI 端到端执行的前提下，为 `setup-architect` 的 skill validation 体系补上可复用的多轮对话建模能力，重点锁定“初始化尾声必须先询问是否定制技术方案模板，并在收到回答前停止”的流程契约。

## 问题与目标

当前 `tests/skill_validation/` 已经具备三类基础能力：

- 基于 `SKILL.md` 和 reference 文档的静态契约断言。
- 基于 `case_catalog.py` 的统一 case 元数据管理。
- 基于固定 fixture 和临时项目 bootstrap 的稳定测试前置。

这套体系足以覆盖单轮输入对应单个结果分类的场景，但不足以稳定表达如下流程：

1. 用户请求完整执行 `setup-architect`
2. skill 完成初始化前置后，必须先询问“是否需要定制技术方案模板”
3. 在用户尚未回答时，本轮必须停在 `STOP_AND_ASK`
4. 用户第二轮回答“不需要”或提供完整模板后，skill 才能进入最终成功分支

当前问题不是仓库里完全没有这条规则，而是它只以“先询问用户”这种单句形式存在于文档中，缺少正式的多轮建模和回合间验证方式。因此：

- 文档层容易遗漏“问完就停”的硬边界。
- case catalog 只能表达单轮 prompt，无法把“第一轮停住、第二轮继续”当成正式回归对象。
- 新增多轮流程时，测试逻辑只能散落在测试代码里，难以形成统一约定。

本设计的目标不是引入真实 agent E2E，而是把“多轮状态机”纳入现有 validation 体系，先为 `setup-architect` 建立第一批正式多轮 case，并保持与现有单轮 case 兼容。

## 设计原则

- 多轮验证优先复用现有 `ValidationCase` 体系，而不是另起一套平行数据结构。
- 现有单轮 case 必须保持兼容，不能为了支持多轮而强制迁移全部 catalog。
- 多轮 schema 先服务 `setup-architect`，不一次性重构全部 skill 的验证模型。
- 验证目标仍然是结果分类和行为不变量，而不是自然语言回复全文匹配。
- 不引入真实模型调用，不引入外部服务依赖，不把测试稳定性建立在生成式输出波动上。
- 文档契约和多轮 case 必须互相印证：流程文档给出硬规则，多轮 case 锁定回合边界。

## 非目标

- 不引入真实 CLI 会话 harness。
- 不为这次改动补一个通用的 agent 运行时模拟器。
- 不把全部现有 `setup-architect` case 迁移为多轮结构。
- 不改变现有 `STOP_AND_REDIRECT`、`STOP_AND_ASK`、`SUCCESS_INIT` 等结果分类含义。
- 不把回复文案做成 golden transcript 测试。

## 总体方案

### 1. 扩展 `ValidationCase`，增加可选多轮结构

在 `tests/skill_validation/case_catalog.py` 中新增一个回合级数据结构，例如：

```python
@dataclass(frozen=True)
class ConversationTurn:
    user_input: str
    expected_result: str
    assert_paths: Tuple[str, ...] = ()
    assert_structure: Tuple[str, ...] = ()
    assert_semantics: Tuple[str, ...] = ()
    assert_safety: Tuple[str, ...] = ()
    forbidden_behavior: Tuple[str, ...] = ()
```

然后给现有 `ValidationCase` 增加一个可选字段：

```python
turns: Tuple[ConversationTurn, ...] = ()
```

这样做的含义是：

- 旧 case 仍然只使用 `prompt` + 顶层断言字段。
- 新的多轮 case 使用 `turns` 明确声明每一轮输入和期望结果。
- catalog 依然只有一个统一入口，不会出现“单轮 case 在一处、多轮 case 在另一处”的分裂。

### 2. 保持单轮 schema 与多轮 schema 的兼容共存

兼容策略如下：

- `prompt` 字段继续保留，作为单轮 case 的正式输入描述。
- `turns` 为空时，case 按现有单轮模型处理。
- `turns` 非空时，case 由新的多轮测试模块消费；此时 `prompt` 可以作为摘要描述或总场景说明，而不是唯一输入源。
- 现有断言字段继续保留在 `ValidationCase` 顶层，用于描述整个 case 的总体性质；逐轮差异断言放在 `ConversationTurn` 内，并沿用相同的不变量分类（路径、结构、语义、安全、禁止行为）。

这保证了这次改动只是在 catalog 上做增量扩展，而不是 schema 级重写。

### 3. 用新的多轮测试模块消费 `turns`

新增 `tests/skill_validation/test_setup_architect_conversation_simulation.py`，职责限定为：

- 读取 `case_catalog.py` 中带 `turns` 的 `setup-architect` case。
- 校验每个 case 至少有两轮，并且第一轮、第二轮的结果分类符合设计预期。
- 锁定回合边界上的关键不变量，例如“第一轮未回答前不得输出 `Tech Solution 设置完成`”。

这个模块不是执行真实模型，也不是解析真实 transcript，而是把多轮 case 当作正式验证输入，检查其状态迁移定义是否完整、是否与 skill contract 一致。

### 4. 文档契约继续作为多轮验证的正式上游

多轮 schema 不是为了替代文档硬规则，而是为了让文档硬规则变成可回归验证的结构化场景。

因此，本设计要求同时收紧两处正式契约：

- `skills/setup-architect/SKILL.md`
- `skills/setup-architect/references/technical-solution-template-customization.md`

需要明确写出：

- 先询问用户是否需要定制技术方案模板。
- 若用户尚未回答，本轮结果为 `STOP_AND_ASK`。
- 未收到回答前，不得输出 `Tech Solution 设置完成` 初始化摘要。
- 只有在用户明确回答“不需要”，或已完成合法模板整体替换后，才能输出初始化摘要。

## 首批多轮 case 设计

本次只给 `setup-architect` 增加两条多轮 case，避免一次性改动太大。

### `SA-13` 初始化尾声未回答时必须停下

- Layer：`流程场景层`
- Fixture：`complete-architecture-default-template`
- 目的：将“先询问模板是否定制”从文档语义提升为正式回合边界

回合设计：

1. Turn 1
   - User Input：请求完整执行 `setup-architect`
   - Expected Result：`STOP_AND_ASK`
   - Assert Semantics：明确询问是否需要定制技术方案模板
   - Assert Safety：未收到回答前不输出初始化完成摘要
   - Forbidden Behavior：直接输出 `Tech Solution 设置完成`
2. Turn 2
   - User Input：`不需要，保留当前模板`
   - Expected Result：`SUCCESS_INIT`
   - Assert Semantics：模板最终状态明确为保留当前模板

### `SA-14` 初始化尾声在第二轮接受完整模板替换

- Layer：`行为回归层`
- Fixture：`template-replacement-inputs`
- 目的：验证多轮等待后进入合法模板替换成功路径

回合设计：

1. Turn 1
   - User Input：请求完整执行 `setup-architect`
   - Expected Result：`STOP_AND_ASK`
   - Assert Semantics：明确询问是否需要定制技术方案模板
   - Forbidden Behavior：跳过确认直接收尾
2. Turn 2
   - User Input：提供完整 Markdown 模板内容或合法路径/链接
   - Expected Result：`SUCCESS_REPLACE_TEMPLATE`
   - Assert Paths：`.architecture/templates/technical-solution-template.md`
   - Assert Safety：整体替换，不做局部 merge

## 与现有 case 的关系

- `SA-04` 保留：继续表达“用户明确回答保留当前模板时，结果应为 `SUCCESS_INIT`”的单轮终态。
- `SA-05` 保留：继续表达“初始化尾声已进入模板替换分支时，完整模板输入可成功替换”的单轮终态。
- `SA-08` 保留：继续表达“模板片段 / patch / 口头描述”这种非法输入必须 `STOP_AND_ASK` 的边界规则。

也就是说，多轮 case 不是替代这些单轮 case，而是补上它们之间缺失的“回合过渡”验证层。

## 代码与文档变更范围

### `tests/skill_validation/case_catalog.py`

- 新增 `ConversationTurn` 数据结构。
- 给 `ValidationCase` 增加可选 `turns` 字段。
- 保持 `vcase(...)` 调用方式兼容单轮 case。
- 新增 `SA-13`、`SA-14`。
- 将新 case 编入合适的 phase 列表。

### `tests/skill_validation/test_case_catalog.py`

- 增加对 `turns` 元数据的基础校验。
- 校验带 `turns` 的 case 至少两轮。
- 校验单轮与多轮 case 的 catalog 计数和 phase 顺序保持一致。

### `tests/skill_validation/test_setup_architect_contracts.py`

- 增加顺序断言，锁定“先问 -> 停止等待 -> 未回答前不得总结 -> 回答后才允许成功收尾”。
- 补充 reference 文档中的场景 A 断言，防止再次漏掉 `STOP_AND_ASK` 语义。

### `tests/skill_validation/test_setup_architect_conversation_simulation.py`

- 新建多轮 case 消费器。
- 断言 `SA-13`、`SA-14` 的 turn-by-turn 结构完整。
- 断言第一轮为 `STOP_AND_ASK`，第二轮才进入成功分支。

### `docs/superpowers/testing/skill-validation.md`

- 把新增多轮 case 写入对应 phase 列表。
- 在 runbook 中补一句说明：部分 case 会使用 catalog 内的多轮 `turns` 定义来表达回合边界。

### `docs/superpowers/specs/2026-03-26-skill-validation-design.md`

- 更新 `夹具策略` 或 `Case 模板`，说明 catalog 允许可选的多轮 `turns`。
- 在 `setup-architect` 用例矩阵中补入 `SA-13`、`SA-14`。

### `.github/workflows/skills-integration-tests.yml`

- 保持 `python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v` 不变。
- 建议补一条资源存在性校验：`setup-architect/references/technical-solution-template-customization.md` 已被安装到 assistant 目标目录。

## 分层与 phase 放置建议

- `SA-13` 推荐放入 `Phase 1`，因为它锁定的是“未回答前不得继续”的硬停机规则。
- `SA-14` 推荐放入 `Phase 2`，因为它是在硬停机规则之上，继续验证合法成功分支是否稳定。

这样分层的目的，是先把危险的“越过用户确认直接收尾”问题锁死，再补齐合法分支的稳定覆盖。

## 风险与权衡

- `schema 复杂度上升`：`ValidationCase` 不再是纯单轮结构，但兼容保留单轮路径可以把复杂度限制在最小范围。
- `测试仍非真实 E2E`：本设计不会证明真实模型一定按规则执行，只能证明仓库已经把多轮契约正式化并纳入回归体系。
- `case catalog 职责扩张`：catalog 从“单轮场景登记表”扩为“单轮 + 多轮统一登记表”，因此必须补最小元数据校验，避免坏数据进入测试。
- `首批只覆盖 setup-architect`：这是有意的范围控制；先证明 schema 可用，再考虑是否让 `create-technical-solution` 或 `review-technical-solution` 复用。

## 实施顺序

1. 先收紧 `skills/setup-architect/SKILL.md` 与 `skills/setup-architect/references/technical-solution-template-customization.md` 的正式规则。
2. 再扩展 `tests/skill_validation/case_catalog.py` 的 schema，并新增 `SA-13`、`SA-14`。
3. 更新 `tests/skill_validation/test_case_catalog.py`，锁住多轮元数据质量。
4. 新增 `tests/skill_validation/test_setup_architect_conversation_simulation.py`，消费多轮 case。
5. 同步 `docs/superpowers/testing/skill-validation.md` 与 `docs/superpowers/specs/2026-03-26-skill-validation-design.md`。
6. 最后跑全量 `tests/skill_validation/`，确认单轮与多轮路径一起通过。

这个顺序的目的，是先固定正式 contract，再扩 schema，再补执行器，最后让文档、catalog 和测试一起收口，避免先写执行器却没有稳定规则基线。

## 预期结果

完成本设计后，仓库会从“只有单轮 case 的 validation 体系”升级为“单轮与多轮兼容的 validation 体系”。对 `setup-architect` 而言，最关键的收益是：

- “询问模板定制”不再只是文档里的软描述，而会成为正式的多轮回归场景。
- “未回答前不得输出 `Tech Solution 设置完成`”会同时受到文档契约和多轮 case 的双重保护。
- 后续若还要为其他 skill 增加多轮状态机验证，可以直接复用 `turns` schema，而不必重新发明测试建模方式。
---
