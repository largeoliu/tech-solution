# T03-moderate-鉴权重构

## 用例信息
- **ID**: T03
- **场景**: 多模块协调：Session 鉴权重构为 JWT
- **flow_tier**: moderate
- **集合**: train

## Query
将现有 Session 鉴权迁移到 JWT，需要保持现有登录接口兼容，用户无需重新登录

## 预期行为 (6 条)
1. flow_tier 判定为 moderate
2. required_artifacts 含 WD-CTX, WD-TASK, WD-SYN，不含 WD-EXP
3. 生成 WD-TASK 和 WD-SYN（非 WD-SYN-LIGHT）
4. 不执行步骤 9，不生成 WD-EXP-*
5. WD-SYN 候选方案对比覆盖复用/改造/新建三路径
6. 若已有同名文件，默认覆盖目标文件

## Assertions

| ID | 类型 | 描述 | 通过标准 | 失败条件 |
|----|------|------|----------|----------|
| A03.1 | **关键** | flow_tier 判定为 moderate | flow_tier=moderate | 判定为 light/full |
| A03.2 | skill-revealing | 产物不含 WD-EXP | produced_artifacts 不含 WD-EXP-* | 包含了 WD-EXP |
| A03.3 | skill-revealing | 生成 WD-TASK | produced_artifacts 含 WD-TASK | 未生成 |
| A03.4 | skill-revealing | 不生成 WD-EXP-* | produced_artifacts 不含 WD-EXP | 生成了 |
| A03.5 | skill-revealing | 生成完整 WD-SYN | produced_artifacts 含 WD-SYN | 生成了 WD-SYN-LIGHT |
| A03.6 | skill-revealing | 三路径比较 | 复用/改造/新建都有 | 路径缺失 |
| A03.7 | baseline | 覆盖语义与实现一致 | 默认覆盖目标文件 | 仍要求另存或禁止覆盖 |
