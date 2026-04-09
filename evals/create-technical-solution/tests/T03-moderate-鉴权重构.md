# T03-鉴权重构

## 用例信息
- **ID**: T03
- **场景**: 全流程完整执行：Session 鉴权重构为 JWT
- **集合**: train

## Query
将现有 Session 鉴权迁移到 JWT，需要保持现有登录接口兼容，用户无需重新登录

## 预期行为 (4 条)
1. 全流程完整执行（步骤 1-12）
2. 生成 WD-TASK 和 WD-SYN
3. WD-SYN 候选方案对比覆盖复用/改造/新建三路径

## Assertions

| ID | 类型 | 描述 | 通过标准 | 失败条件 |
|----|------|------|----------|----------|
| A03.1 | skill-revealing | 产物含 WD-EXP | produced_artifacts 含 WD-EXP-* | 缺少 WD-EXP |
| A03.2 | skill-revealing | 生成 WD-TASK | produced_artifacts 含 WD-TASK | 未生成 |
| A03.3 | skill-revealing | 三路径比较 | 复用/改造/新建都有 | 路径缺失 |
| A03.4 | baseline | 覆盖语义与实现一致 | 默认覆盖目标文件 | 仍要求另存或禁止覆盖 |
