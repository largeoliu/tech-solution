# Pattern 分析指南

## 评估 Assertion 有效性

### 1. 阈值守恒 Pattern
**原理**: 有序集合的成员数量在转换中守恒。

```
WD-CTX 条目数 × 2 ≤ 追溯文件数
selected_members 数量 = WD-EXP-* 数量
```

### 2. 增量收敛 Pattern
**原理**: 后期 checkpoint 的数据量 ≥ 早期 checkpoint。

```
len(checkpoint_step_10) > len(checkpoint_step_7)
```

### 3. 因果链 Pattern
**原理**: B 发生则 A 必须已发生。

```
state.can_enter_step_10 == True  ⇒  步骤 7 已完成
```

### 4. 反面验证 Pattern
**原理**: 负向用例的行为是"零生成"。

```
N01-N06: 不创建 .architecture/.state/ 下的任何文件
```

### 5. 边界守卫 Pattern
**原理**: gate 检查在步骤间强制停止。

```
validate-state.py exit code = 0  ⇒  进入下一步
validate-state.py exit code = 2  ⇒  阻塞在当前步骤
```

## Assertion 评分

| 分数 | 标准 |
|------|------|
| 5 | 覆盖核心行为，可重复验证 |
| 4 | 覆盖主要路径 |
| 3 | 部分覆盖 |
| 2 | 间接验证 |
| 1 | 难以自动化 |
