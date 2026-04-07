# 步骤 6：检测 repowiki 目录

## 输入
- 项目仓库
- 状态文件

## 操作
1. **【强制】前置条件自检**：
   - 运行 `python scripts/validate-state.py --state <状态文件路径> --step 6 --flow-tier <flow_tier> --format json`
   - 确认步骤 5 已完成（selected_members 已写入且非空）
   - 若验证失败，按 `repair_plan[]` 修复后重试
   - 展示自检结果（通过/不通过 + 具体原因）
2. 执行 `find . -type d -name "repowiki"`
3. 存在则记录路径并标记下一步必须纳入
   - **记录格式**：`repowiki_path: ".qoder/repowiki/zh/content"`
   - **标记格式**：`repowiki_exists: true`
4. 不存在则报告跳过
   - **记录格式**：`repowiki_exists: false`
5. 将 `repowiki_checked: true` 和检测结果写入状态文件 `checkpoints.step-6`
6. 检测结果向用户展示

**checkpoint模板**：
```yaml
checkpoints:
  step-6: |
    repowiki检测完成
    - repowiki_exists: true/false
    - repowiki_path: ".qoder/repowiki/zh/content" (如存在)
    - 下一步必须纳入: 是/否
```

## 完成标准
- 已明确报告 repowiki 是否存在
- 如存在已确定完整路径
- 检测结果已向用户展示

## 输出
- 更新状态文件 checkpoints.step-6

## 门控
未完成检测不得进入第 7 步。

## 回退信号
repowiki 目录检测结果变化或需要重新检测。
