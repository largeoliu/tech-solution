# T04-full-repowiki-多租户数据隔离

## 用例信息
- **ID**: T04
- **场景**: full 流程 + repowiki 存在：多租户数据隔离
- **集合**: train

## Query
实现多租户数据隔离方案，采用行级租户标识方案，需要隔离用户数据，现有 API 需要增加租户过滤

## 预期行为 (7 条)
1. 步骤 6 检测并记录 repowiki 路径，后续分析引用其中内容但正文仍只写入 draft
2. 专家分析的关键结论仍绑定 CTX 编号，repowiki 仅作补充
3. 每个需要专家判断的槽位均有对应的 WD-EXP-* 区块
4. 每位专家仅对参与槽位写判断，参与槽位字段非全部
5. WD-SYN 按槽位逐个写入，checkpoint 展示逐槽位收敛过程
6. 若结论无法在现有模板承载，记录模板承载缺口并阻止进入下一步
7. 最终文档一级章节与模板完全一致

## Assertions

| ID | 类型 | 描述 | 通过标准 | 失败条件 |
|----|------|------|----------|----------|
| A04.1 | **关键** | repowiki 检测记录 | checkpoint.step-6 提及 repowiki | 未检测 |
| A04.2 | skill-revealing | repowiki 不替代 CTX | CTX 仍为主要依据 | repowiki 替代了 CTX |
| A04.3 | skill-revealing | WD-EXP 数量匹配 | WD-EXP-* 数量 = 专家数 | 数量不匹配 |
| A04.4 | skill-revealing | 专家逐槽位分析 | 每个槽位有对应分析 | 分析缺失 |
| A04.5 | skill-revealing | 按槽位增量收敛 | checkpoint 展示收敛 | 无收敛记录 |
| A04.6 | skill-revealing | 模板承载缺口记录 | 缺失时明确记录缺口并阻止进入下一步 | 未记录 |
| A04.7 | skill-revealing | 成稿无新增章节 | 一级章节数=4 | 新增了章节 |
