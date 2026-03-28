# create-technical-solution 工作草稿机制设计

**日期**：2026-03-28

**目标**：为 `create-technical-solution` 增加统一的 working draft 机制，把各阶段完整结构化中间产物写入单一临时载体，提升弱模型在长链路技术方案生成中的稳定性与质量下限，同时不限制强模型的输出上限。

## 问题与目标

当前 `create-technical-solution` 已经有比较完整的阶段化 contract，但阶段性中间产物默认只在对话中展示，不落盘为稳定载体。这对强模型通常还能工作，但对弱模型或上下文较小的模型存在明显风险：

- 早期阶段的结构化产物容易被后续长对话挤出上下文窗口。
- 下游阶段会凭不完整记忆重建 `共享上下文清单`、`模板任务单`、`专家产物` 或 `协作收敛纪要`。
- 即使 schema 设计正确，只要中间产物没有稳定外部记忆，最终文档质量仍然高度依赖模型本身的上下文保持能力。

本设计要解决的不是“是否把所有草稿都保存下来”，而是建立一条更窄、更稳定、更容易被弱模型遵守的统一主链路：每个阶段都把完整、可复用的结构化结果写进单一 working draft，再让后续阶段显式消费它。

## 设计原则

- **统一流，不分模式**：所有场景都走同一条 working draft 主链路，不再区分“仅对话模式”和“临时落盘模式”。
- **working draft 是质量下限保障，不是质量上限约束**：弱模型依赖 draft 获取稳定外部记忆；强模型仍然必须写 draft，但可以在对话中展开更多高质量解释。
- **单一临时载体**：不为每个阶段创建独立临时文件，只维护一份随阶段更新的 working draft。
- **结构化结果落盘，非结构化推理不落盘**：只保存 canonical schema 产物，不保存 scratchpad、原始推理链路、聊天争论记录或未成形草稿。
- **正式模板仍然唯一**：`.architecture/templates/technical-solution-template.md` 仍然是最终文档唯一正文骨架；working draft 不是第二套正式模板。
- **对话默认摘要优先**：用户在对话中看到的是稳定摘要和关键引用，不是完整长文倾倒。
- **最终只有一个正式交付物**：`.architecture/technical-solutions/[slug].md` 仍是唯一正式技术方案文档；working draft 只是过程中的临时持久化载体。

## 非目标

- 不改变最终正式文档的输出位置或角色。
- 不放宽现有的模板优先、无合法落位即停机、缺少关键上下文即停机等硬规则。
- 不引入多份阶段侧车文件、独立过程归档系统或长期保留的过程文档。
- 不要求强模型只能输出摘要；强模型可以在展示边界内补充更多说明。
- 不保存原始推理过程或把内部思考过程伪装成中间产物。

## 统一新流程

`create-technical-solution` 的主链路仍然保持现有阶段顺序，但每个阶段完成后必须多执行一个固定动作：**把该阶段完整结构化产物写入 working draft**。

统一流程如下：

1. `共享上下文清单阶段`
2. `模板任务单阶段`
3. `专家按模板逐槽位分析阶段`
4. `按模板逐槽位协作收敛阶段`
5. `严格模板成稿阶段`
6. `吸收检查与 working draft 删除阶段`

关键变化不是新增一个并行流程，而是把既有阶段性产物全部从“仅对话可见”升级为“先写入 working draft，再在对话中展示摘要”。

## Working Draft 协议

### 位置

working draft 固定放在：

`.architecture/technical-solutions/working-drafts/[slug].working.md`

其中 `[slug]` 与最终技术方案文档保持同一主题 slug，便于一一对应。

若 `.architecture/technical-solutions/working-drafts/` 不存在，可在正式生成流程中按需创建；这不改变正式方案文档仍写入 `.architecture/technical-solutions/[slug].md` 的规则。

### 单一文件原则

- 整个一次技术方案生成过程只维护一份 working draft。
- 新阶段结果写入同一文件，不为 `共享上下文清单`、`模板任务单`、`专家产物`、`协作收敛纪要` 分拆成多个临时文件。
- 同类阶段如果因回退或重算生成新版本，应覆盖或标记替换旧稳定版本，而不是无限追加历史垃圾内容。

### 必写内容

working draft 中必须保存这些稳定中间产物的**完整 canonical schema 版本**：

- `共享上下文清单`
- `模板任务单`
- 每位参与专家各一份 `专家产物`
- `协作收敛纪要`
- 发生回退、重算或失效时的 `变更影响说明`

这里的“完整”指：字段和顺序必须满足 `skills/create-technical-solution/references/solution-process.md` 中定义的必填 schema，而不是只写摘要。

### 不写内容

working draft 明确不保存以下内容：

- scratchpad
- 原始推理链路
- 内部自检痕迹
- 原始争论聊天记录
- 只为模型临时过脑子而存在的非结构化草稿

这样做的目标是让 working draft 成为稳定、可追溯、可消费的中间产物仓，而不是把全部思维噪音都外置化。

## Working Draft 内部结构

建议新增独立参考文档 `references/working-draft-protocol.md`，统一定义 working draft 的结构、生命周期和引用规则。设计上，单份 draft 至少应包含以下稳定区块：

```markdown
# Working Draft: [方案标题]

**关联主题**： [主题]
**关联 slug**： [slug]
**当前阶段**： [共享上下文清单阶段 / 模板任务单阶段 / 专家按模板逐槽位分析阶段 / 按模板逐槽位协作收敛阶段 / 严格模板成稿阶段 / 吸收检查阶段]
**状态**： [进行中 / 已完成待吸收 / 已吸收待删除]

---

## WD-CTX 共享上下文清单
[按 canonical 共享上下文清单 schema 的完整内容]

---

## WD-TASK 模板任务单
[按 canonical 模板任务单 schema 的完整内容]

---

## WD-EXP-[expert-slug] 专家产物
[按 canonical 专家按模板逐槽位分析 schema 的完整内容]

---

## WD-SYN 协作收敛纪要
[按 canonical 按模板逐槽位协作收敛 schema 的完整内容]

---

## WD-IMPACT-[n] 变更影响说明
[按 canonical 变更影响说明 schema 的完整内容]
```

这里的 `WD-CTX`、`WD-TASK`、`WD-EXP-[expert-slug]`、`WD-SYN`、`WD-IMPACT-[n]` 是稳定区块标识，目的是让对话摘要和后续阶段引用时有明确锚点，降低弱模型在长链路中引用错位的概率。

## 对话展示策略

working draft 成为完整中间产物的权威载体后，对话展示策略调整为：**完整内容写 draft，用户展示看摘要，必要时带稳定引用。**

### 展示原则

- 默认对话只展示稳定摘要，不直接倾倒 canonical 全量长文。
- 摘要必须保留本阶段最重要的稳定结论、关键缺口、主要争议和下一步动作。
- 若需要引用完整产物，使用稳定区块标识，而不是模糊说“见上文”或“见前面的产物”。

### 引用格式

本设计采用统一引用格式：

`详见 working draft：<区块标识>（<区块名称>）`

例如：

- `详见 working draft：WD-CTX（共享上下文清单）`
- `详见 working draft：WD-TASK（模板任务单）`
- `详见 working draft：WD-EXP-system-architect（系统架构师专家产物）`
- `详见 working draft：WD-SYN（协作收敛纪要）`

这样既保留可读性，又提供稳定、低歧义的引用锚点。

### 强模型自由度

对强模型，不要求只能输出极短摘要。只要不违反 `progress-transparency.md` 的展示边界规则，强模型可以在摘要后补充更多解释、权衡或细节。换句话说：

- working draft 写入是**硬约束**；
- 对话展开深度是**软约束**。

因此 working draft 只提高质量下限，不限制质量上限。

## 下游消费规则

引入 working draft 后，后续阶段的消费规则必须明确收紧：

- 后续阶段消费前置产物时，应以 working draft 中的稳定内容为准，不依赖“模型还记得前文”。
- 凡是被下游阶段消费的中间产物，必须已经写入 working draft；否则视为不存在。
- 对话摘要不是下游阶段的唯一依据；它只是给用户看的压缩视图。
- 如果 working draft 中的某个区块尚未完成、缺字段或存在阻塞，下游阶段不得跳过它继续推进。

这条规则的本质是：**把 schema 级中间产物从对话记忆对象，改为显式可引用对象。**

## 生命周期与删除规则

working draft 的生命周期遵循：

1. 技术方案主题确定后创建对应 working draft。
2. 每个阶段完成后立即更新相应区块。
3. 用户中途新增约束、修正目标或调整范围时，先写入 `变更影响说明`，再从最近受影响阶段重进。
4. 最终技术方案成稿后，执行吸收检查。
5. 吸收检查通过后，删除 working draft。

### 吸收检查

吸收检查至少验证以下事项：

- working draft 中已稳定的关键结论是否都已被最终文档吸收。
- `共享上下文清单` 到最终文档的证据链是否仍然可追溯。
- `协作收敛纪要` 中被否决方案、未采纳理由、未决问题等关键内容是否已按模板语义正确落位。
- 不存在“只留在 working draft、却没有进入最终文档也没有被显式舍弃”的关键结论。

如果吸收检查不通过，先修正最终文档，再删除 working draft。不得生成正式文档后直接忘记 draft 的存在。

### 删除后的唯一正式产物

删除 working draft 后，唯一正式交付物仍然是：

`.architecture/technical-solutions/[slug].md`

若某些决策理由确有评审价值，也只能通过当前模板已有合法位置吸收进正式文档；不能把 working draft 当作长期保留的第二份交付物。

## 回退与重进

working draft 机制必须与现有的失效/重进机制兼容，而不是替代它。

- 当用户新增约束、修正目标、调整范围或补充关键事实时，先判断最近受影响的阶段边界。
- 在重进前，先把 `变更影响说明` 写入 working draft，并明确哪些区块失效、哪些区块仍然有效。
- 失效的专家产物或收敛结论不得继续被表述为当前有效版本。
- 重进完成后，用新稳定区块替换旧版本，再继续推进。

这样，working draft 承担的是“稳定过程状态存储”，而不是“绕过失效机制的缓存”。

## 文件级影响

### `skills/create-technical-solution/SKILL.md`

- 在高层工作流和完成标准中加入 working draft 的创建、阶段写入、下游消费、吸收检查和删除语义。
- 把“这些中间产物默认不作为侧车文档落盘”的旧表述改为“这些中间产物必须写入单一 working draft；对用户默认仅展示摘要”。
- 在行为契约中加入“每个阶段完成后先写 working draft，再展示摘要并进入下一阶段”的硬规则。

### `skills/create-technical-solution/references/progress-transparency.md`

- 保留现有阶段边界与展示边界思想。
- 将用户可见产物从“直接渲染完整中间产物”调整为“摘要优先 + working draft 稳定引用”。
- 明确引用格式和展示措辞，避免对话里出现模糊的“见前文”式引用。

### `skills/create-technical-solution/references/solution-process.md`

- 保留现有 canonical schema 定义。
- 新增规则：canonical 产物在对用户展示前必须先写入 working draft。
- 质量门槛中增加对 draft 写入完整性、下游消费合法性、吸收检查完整性的检查项。

### `skills/create-technical-solution/references/working-draft-protocol.md`

- 新增独立参考文档，专门定义 working draft 的结构、区块标识、生命周期、引用格式、回退时的失效表示和删除规则。
- 让 `SKILL.md` 继续负责主链路编排，避免把过多协议细节塞进主技能文件。

## 验证重点

完成实现后，至少应验证以下行为：

- 每个阶段完成后，都先形成符合 canonical schema 的完整产物并写入 working draft。
- 对话展示默认是摘要，而不是把完整长文直接倾倒出来。
- 后续阶段引用前置产物时，使用 working draft 中的稳定区块，而不是依赖隐式记忆。
- 模板变更、约束变更或范围变更时，能先写 `变更影响说明` 再从最近受影响阶段重进。
- 最终成稿后执行吸收检查，并在通过后删除 working draft。
- 最终正式技术方案仍然严格服从当前模板，不因 working draft 存在而引入模板外可见结构。

## 主要风险与缓解

- **写入负担上升**：每个阶段都写 draft，流程会更重。缓解方式是只写 canonical schema 的稳定结果，不写噪音内容，并维持单一文件而不是多文件体系。
- **draft 与对话摘要漂移**：摘要可能与 draft 不一致。缓解方式是把 draft 视为权威来源，摘要从 draft 派生，并使用稳定区块引用。
- **draft 成为第二模板**：如果规则不清，模型可能把 draft 当正式文档骨架。缓解方式是在协议中明确：draft 只存中间产物，最终仍严格写回当前模板。
- **忘记删除 draft**：流程结束后遗留临时文件。缓解方式是在完成标准和质量门槛中加入强制吸收检查与删除步骤。

## 实施顺序

1. 先新增 `skills/create-technical-solution/references/working-draft-protocol.md`，固定协议细节与区块标识。
2. 再修改 `skills/create-technical-solution/references/solution-process.md`，把 working draft 写入/消费要求接入 canonical schema 规则。
3. 再修改 `skills/create-technical-solution/references/progress-transparency.md`，把用户可见展示切换为摘要 + working draft 引用。
4. 最后修改 `skills/create-technical-solution/SKILL.md`，让主技能只负责编排、停机规则、质量门槛和完成标准。
5. 用验证场景锁定“每阶段写 draft、下游显式消费、最终吸收删除、模板仍是唯一正式骨架”这四类关键行为。

## 预期结果

完成本设计后，`create-technical-solution` 会从“阶段产物主要存在于对话记忆中”的流程，收敛为“阶段产物始终有单一稳定外部记忆”的流程。这样一来：

- 弱模型即使上下文能力有限，也能沿着 working draft 稳定推进，最终质量下限显著提高。
- 强模型仍然可以输出更完整、更高质量的解释与权衡，不会因为新机制而被压缩到只有摘要。
- 用户看到的对话会更短、更清晰，但系统内部的结构化证据链会更稳定、更可追溯。
