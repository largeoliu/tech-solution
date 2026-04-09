# T01-full-新增订单支付模块

## 用例信息
- **ID**: T01
- **场景**: 完整流程：新增订单支付模块
- **集合**: train

## Query
为电商平台新增微信和支付宝双通道支付模块，需要支持退款、对账、异步回调，不影响现有订单流程

## 预期行为 (12 条)
1. 状态文件初始化，slug 为 ASCII kebab-case
2. 步骤 2 确认三前置文件存在
3. 步骤 3 提取模板一级章节并编号 SLOT-01, SLOT-02, ...
4. 步骤 4 required_artifacts 含 WD-CTX, WD-TASK, WD-EXP, WD-SYN
5. 步骤 5 selected_members 全部来自 .architecture/members.yml 实际条目
6. 步骤 6 检测 repowiki（存在或不存在均报告）
7. 步骤 7 WD-CTX 写入 working draft，每条来源可追溯至少 2 个文件
8. 步骤 8 运行 validate-state.py 门禁通过，WD-TASK 写入，必答问题具体
9. 步骤 9 每位专家仅对参与槽位写 WD-EXP-*，新建结论含不可复用/不可改造证据
10. 步骤 10 按槽位增量写入 WD-SYN，三路径比较完整
11. 步骤 11 最终文档一级章节与模板完全一致
12. 步骤 12 absorption_check_passed 为 true 后才清理中间产物

## Assertions

| ID | 类型 | 描述 | 通过标准 | 失败条件 |
|----|------|------|----------|----------|
| A01.1 | skill-revealing | 状态文件正确初始化 | slug 为 ASCII kebab-case | slug 包含空格或特殊字符 |
| A01.2 | skill-revealing | slug 格式正确 | 小写字母、数字、连字符 | 包含大写、下划线 |
| A01.3 | skill-revealing | 主题摘要写入 | checkpoint.step-1 包含主题 | 主题缺失 |
| A01.4 | skill-revealing | 前置文件门禁 | 步骤 2 三文件检查 | 缺失文件未报错 |
| A01.5 | skill-revealing | 模板槽位编号正确 | SLOT-01, 02, 03, 04 | 编号缺失或错误 |
| A01.6 | **关键** | 成员来自名册 | selected_members ⊆ members.yml | 包含虚构成员 |
| A01.7 | **关键** | 无虚构专家名称 | WD-EXP-* slug 来自名册 | 包含不存在专家 |
| A01.8 | skill-revealing | WD-CTX 来源可追溯 | 每条 ctx 引用 ≥2 文件 | 引用缺失 |
| A01.9 | skill-revealing | 现有资产候选逐条建立 | 复用/改造/新建三路径 | 路径缺失 |
| A01.9 | skill-revealing | validate-state.py 门禁被执行 | exit code 0 | 未调用 |
| A01.9 | skill-revealing | WD-TASK 必答问题具体 | 问题与槽位对应 | 问题模糊 |
| A01.9 | **关键** | 新建结论有证据 | 回答不可复用+不可改造 | 证据缺失 |
| A01.9 | skill-revealing | 三路径覆盖 | 复用/改造/新建都有 | 路径缺失 |
| A01.9 | skill-revealing | 最终文档对齐模板 | 一级章节一致 | 章节缺失/新增 |
| A01.9 | skill-revealing | absorption_check 通过才清理 | cleanup_allowed=true | 未检查 |
| A01.9 | baseline | repowiki 被纳入 | 存在则引用 | 不适用 |
| A01.9 | skill-revealing | 全流程自动推进 | completed_steps 连续 | 跳号 |
| A01.9 | skill-revealing | 仅一份 working draft | slug 一致 | 多份草稿 |
| A01.9 | skill-revealing | checkpoint 含具体数据 | 含条目数/区块名 | 仅"已完成" |
