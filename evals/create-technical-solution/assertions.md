# create-technical-solution Skill Assertions

## Assertion 类型

| 类型 | 定义 |
|------|------|
| **skill-revealing** | 有 skill PASS，无 skill FAIL |
| **baseline** | 有无 skill 都能通过 |

## 核心 Skill-Revealing Assertions (39 条)

### 1. 成员与专家管理 (6 条)
- A01.7: 所有 selected_members 来自 `.architecture/members.yml` 实际条目，不虚构
- A01.8: WD-EXP-* 的 expert-slug 与步骤 5 选定成员一一映射
- A01.13: `决策类型=新建` 必须在关键证据引用中回答"为什么不能复用"和"为什么不能改造"
- A04.1: repowiki 检测并记录
- A04.2: repowiki 不替代 CTX
- A06.2: 新建路径双重否定（不可复用+不可改造）

### 2. Flow Tier 判定 (4 条)
- A01.6: full/moderate/light 三级判定正确
- A02.1: light 判定正确
- A03.1: moderate 判定正确
- A01.4: required_artifacts 与 tier 匹配

### 3. 中间产物完整性 (8 条)
- A01.19: 全流程仅维护 1 份 working draft
- A01.20: checkpoint 只保留流程摘要（区块名、数量、gate），不承载正文
- A02.2: light 不生成 WD-TASK
- A02.3: light 不执行步骤 8/9
- A03.2: moderate 不生成 WD-EXP
- A03.4: moderate 不执行步骤 9
- A03.5: moderate 生成 WD-SYN（非 WD-SYN-LIGHT）
- A04.3: WD-EXP 数量匹配成员数

### 3.1 State / Draft 边界 (4 条)
- A07.1: state.yaml 仅保留最小流程控制字段
- A07.2: 共享上下文、专家判断、收敛正文不得写入 state
- A07.3: step-7~12 summary 必须为单行短摘要
- A07.4: 正文证据仅存在于 working draft / final document

### 4. Validation Gate 执行 (6 条)
- A01.11: validate-state.py 门禁被执行
- A02.6: light 门禁正确处理（不因 step 8 缺失报错）
- A04.5: 按槽位增量收敛
- A05.1: repowiki 不存在正确报告
- A05.2: moderate 产物正确
- A06.3: completed_steps 无跳号

### 5. 模板约束 (3 条)
- A01.5: 模板槽位编号正确
- A01.15: 最终文档一级章节与模板完全一致
- A04.7: 成稿无新增章节

### 6. 描述边界 (8 条)
- A03.6: 三路径比较（复用/改造/新建）
- A03.7: 不覆盖已有同名文档
- A04.4: 专家逐槽位分析
- A04.6: 模板承载缺口记录
- A06.1: 职责迁移证据充分
- D01-D04: 描述边界验证
- N01-N06: 负向用例不触发

## Assertion 有效性评估

按 AGENTS.md §10.5 pattern 分析：

| Pattern | 适用场景 |
|---------|----------|
| 阈值守恒 | flow_tier 判定、产物数量 |
| 增量收敛 | checkpoint 数据量增长 |
| 因果链 | 前置文件→步骤2→步骤3 |
| 反面验证 | 负向用例不触发 |
| 边界守卫 | validate-state.py gate |
