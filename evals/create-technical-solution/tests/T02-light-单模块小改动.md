# T02-单模块小改动

## 用例信息
- **ID**: T02
- **场景**: 全流程完整执行：用户模块加邮箱字段
- **集合**: train

## Query
在用户模块加一个邮箱字段用来发通知

## 预期行为 (4 条)
1. 全流程完整执行（步骤 1-12），required_artifacts 含 WD-CTX, WD-TASK, WD-EXP, WD-SYN
2. 生成 WD-CTX, WD-TASK, WD-EXP-* 和 WD-SYN
3. 最终文档写入 .architecture/technical-solutions/[slug].md

## Assertions

| ID | 类型 | 描述 | 通过标准 | 失败条件 |
|----|------|------|----------|----------|
| A02.1 | skill-revealing | 产物含完整 WD-EXP | produced_artifacts 含 WD-EXP-* | 缺少 WD-EXP |
| A02.2 | skill-revealing | 生成 WD-TASK | produced_artifacts 含 WD-TASK | 未生成 |
| A02.3 | baseline | 最终文件输出 | 文档存在于正确路径 | 文件不存在 |
