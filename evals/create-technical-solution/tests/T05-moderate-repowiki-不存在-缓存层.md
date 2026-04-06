# T05-moderate-repowiki-不存在-缓存层

## 用例信息
- **ID**: T05
- **场景**: moderate + repowiki 不存在：新增缓存层
- **flow_tier**: moderate
- **集合**: validation

## Query
在现有 API 层前面加一层 Redis 缓存，优化读取性能，缓存需要设置合理的过期策略

## 预期行为 (4 条)
1. flow_tier 判定为 moderate
2. repowiki 不存在时步骤 6 报告未找到并跳过
3. 生成 WD-CTX, WD-TASK, WD-SYN，不生成 WD-EXP
4. required_artifacts 与 tier 匹配

## Assertions

| ID | 类型 | 描述 | 通过标准 | 失败条件 |
|----|------|------|----------|----------|
| A05.1 | skill-revealing | repowiki 不存在正确报告 | checkpoint 记录"未找到" | 未报告 |
| A05.2 | **关键** | moderate 产物正确 | 正确组合 | 产物错误 |
