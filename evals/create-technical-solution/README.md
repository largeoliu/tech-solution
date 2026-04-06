# create-technical-solution Eval

eval 驱动迭代开发 Skill 的测试框架。

## 目录结构

```
evals/create-technical-solution/
├── eval_runner.py          # 测试运行器
├── test_validate_state.py  # pytest 单元测试
├── cases/T01.json          # 22 条用例定义
├── tests/                  # 人读的 markdown 测试用例
├── assertions.md           # assertion 规格说明
├── pattern-analysis.md     # pattern 分析指南
├── fixtures/               # 测试 fixture
└── reports/                # 评判报告
```

## 快速开始

```bash
# 初始化测试项目
uv run evals/create-technical-solution/eval_runner.py setup-project

# 列出现有用例
uv run evals/create-technical-solution/eval_runner.py list

# 在测试项目中运行 skill 后评判
uv run evals/create-technical-solution/eval_runner.py grade T01 --target tests/sample-project

# 生成报告
uv run evals/create-technical-solution/eval_runner.py report
```

## 用例分类

- **T01-T06**: 正向用例 (train/validation)
- **E01-E06**: 边缘用例
- **D01-D04**: 描述边界
- **N01-N06**: 负向用例

## 核心 assertion

见 `assertions.md`
