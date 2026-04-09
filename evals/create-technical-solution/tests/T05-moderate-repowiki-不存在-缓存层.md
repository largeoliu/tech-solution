# T05-repowiki-不存在-缓存层

## 用例信息
- **ID**: T05
- **场景**: 全流程 + repowiki 不存在：新增缓存层
- **集合**: validation

## Query
在现有 API 层前面加一层 Redis 缓存，优化读取性能，缓存需要设置合理的过期策略

## 预期行为 (4 条)
1. 全流程完整执行（步骤 1-12）
2. repowiki 不存在时步骤 6 报告未找到并跳过
3. 生成 WD-CTX, WD-TASK, WD-EXP, WD-SYN

## Assertions

| ID | 类型 | 描述 | 通过标准 | 失败条件 |
|----|------|------|----------|----------|
| A05.1 | skill-revealing | repowiki 不存在正确报告 | checkpoint 记录"未找到" | 未报告 |
| A05.2 | skill-revealing | 全流程产物完整 | 含 WD-EXP, WD-TASK, WD-SYN | 产物缺失 |
