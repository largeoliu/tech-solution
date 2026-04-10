# 步骤 1：分析项目

## 输入
- 当前仓库的目录结构、代码文件、现有文档
- `templates/principles-template.md`（仅读取主章节结构，用于操作 8 的覆盖标注）

## 操作
1. 识别项目的语言/框架/测试CI/部署方式/目录结构
2. 形成项目上下文清单（带上下文编号）
3. 每项结论标注来源类型（代码结构/目录语义/现有文档）和具体依据
4. 基于项目上下文提取结构化 `project_signals`，只表达会影响后续成员或原则定制的项目事实和关键信号，不提前下成员角色结论
5. `project_signals` 仅使用固定类别：`platform`（如 `web` / `mobile` / `backend` / `cli`）、`capability`（如 `frontend` / `data` / `ai` / `infra` / `security` / `performance` / `compliance`）、`domain`（如 `payments` / `ugc` / `workflow` / `multi_tenant`）、`constraint`（如 `real_time` / `high_scale` / `complex_integration`）
6. 每条 signal 必须包含 signal 编号、类别、取值、依据编号；必要时补充简短说明，解释该 signal 为什么会影响后续成员或原则定制
7. 如果某个业务事实会影响后续成员或原则，但还停留在 `context_items`，必须先在本步骤将其提升为 `project_signals`，不能把 `context_items` 编号直接带到后续步骤中充当 signal
8. 标注哪些原则章节有依据/无依据

## 完成标准
- 项目上下文清单完整
- 每项结论都有来源类型和具体依据
- `project_signals` 已形成且每条 signal 都有依据
- `project_signals` 只包含会影响后续成员或原则定制的项目事实和关键信号，不包含成员角色或专家建议
- 原则章节覆盖检查完成（标注有依据和无依据的章节）

## 输出
- 更新状态文件 checkpoints.step-1.yaml
- 将 `context_items` 和 `project_signals` 写入状态文件

## 门控
仓库上下文不足以安全确定项目事实、关键信号或原则时返回 STOP_AND_ASK

