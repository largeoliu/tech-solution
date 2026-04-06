# T02-light-单模块小改动

## 用例信息
- **ID**: T02
- **场景**: 单模块小改动：用户模块加邮箱字段
- **flow_tier**: light
- **集合**: train

## Query
在用户模块加一个邮箱字段用来发通知

## 预期行为 (6 条)
1. flow_tier 判定为 light
2. required_artifacts 仅含 WD-CTX, WD-SYN-LIGHT
3. 不生成 WD-TASK 和 WD-EXP-*
4. 生成 WD-CTX 和 WD-SYN-LIGHT
5. 步骤 8/9 显式跳过并记录原因
6. 最终文档写入 .architecture/technical-solutions/[slug].md

## Assertions

| ID | 类型 | 描述 | 通过标准 | 失败条件 |
|----|------|------|----------|----------|
| A02.1 | **关键** | flow_tier 判定为 light | flow_tier=light | 判定为 moderate/full |
| A02.2 | skill-revealing | 不生成 WD-TASK | produced_artifacts 不含 WD-TASK | 生成了 WD-TASK |
| A02.3 | skill-revealing | 不执行步骤 8/9 | checkpoint 记录跳过 | 执行了步骤 8/9 |
| A02.4 | skill-revealing | 步骤 8/9 显式记录跳过 | checkpoint 含跳过原因 | 无跳过记录 |
| A02.5 | skill-revealing | WD-SYN-LIGHT 字段完整 | 含 4 个一级章节 | 章节缺失 |
| A02.6 | skill-revealing | light 门禁正确处理 | 不因 step8 缺失报错 | 报错 |
| A02.7 | baseline | 最终文件输出 | 文档存在于正确路径 | 文件不存在 |
