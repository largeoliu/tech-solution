# Create Technical Solution Context Enforcement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `create-technical-solution` require explicit downstream consumption of step-6 shared context, and validate that contract in both static docs and behavior case coverage.

**Architecture:** Tighten the skill through a single evidence chain: step 6 produces a shared-context inventory, `模板任务单` binds each slot to required context, expert artifacts must cite consumed context, convergence must reconcile context usage, and final drafting must stop if any slot lacks context support. Back the wording with validation updates so weak models cannot satisfy the flow through vague compliance.

**Tech Stack:** Markdown skill docs, Python `unittest` validation suite

---

### Task 1: Add failing contract tests for shared-context propagation

**Files:**
- Modify: `tests/skill_validation/test_create_technical_solution_contracts.py`
- Test: `tests/skill_validation/test_create_technical_solution_contracts.py`

- [x] **Step 1: Write the failing test**

```python
    def test_shared_context_must_flow_through_all_artifacts(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "### 6. 构建共享上下文",
                "共享上下文清单",
                "### 7. 生成模板任务单",
                "本槽位必须消费的共享上下文",
                "### 8. 组织专家按模板逐槽位分析",
                "已使用的共享上下文编号",
                "### 9. 按模板逐槽位协作收敛",
                "本槽位已核销的共享上下文",
                "### 10. 严格模板成稿并保存结果",
                "每个槽位都能回溯到已核销的共享上下文编号",
            ),
        )
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_shared_context_must_flow_through_all_artifacts -v`
Expected: FAIL because the current skill docs do not yet require context inventory propagation or slot-level traceability.

- [x] **Step 3: Write minimal implementation**

```markdown
### 6. 构建共享上下文

先形成一份 `共享上下文清单`，至少包含 `上下文编号`、`来源`、`结论或约束`、`适用槽位`、`可信度或缺口`。

### 7. 生成模板任务单

- `本槽位必须消费的共享上下文`

### 8. 组织专家按模板逐槽位分析

- `已使用的共享上下文编号`

### 9. 按模板逐槽位协作收敛

- `本槽位已核销的共享上下文`

### 10. 严格模板成稿并保存结果

生成最终文档前，确认每个槽位都能回溯到已核销的共享上下文编号。
```

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts.CreateTechnicalSolutionContractTests.test_shared_context_must_flow_through_all_artifacts -v`
Expected: PASS

### Task 2: Add failing case-catalog coverage for missing context consumption

**Files:**
- Modify: `tests/skill_validation/case_catalog.py`
- Modify: `tests/skill_validation/test_case_catalog.py`
- Test: `tests/skill_validation/test_case_catalog.py`

- [x] **Step 1: Write the failing test**

```python
EXPECTED_PHASE_3 = {
    "SA-09",
    "SA-10",
    "SA-11",
    "SA-12",
    "CTS-10",
    "CTS-11",
    "CTS-12",
    "CTS-13",
    "RTS-07",
    "RTS-08",
    "RTS-09",
}
```

```python
    def test_cts_13_tracks_missing_shared_context_consumption(self) -> None:
        self.assertEqual(CASE_INDEX["CTS-13"].expected_result, "STOP_AND_ASK")
        self.assertIn("共享上下文", CASE_INDEX["CTS-13"].assert_semantics[0])
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.skill_validation.test_case_catalog.CaseCatalogTests -v`
Expected: FAIL because `CTS-13` and its phase membership do not exist yet.

- [x] **Step 3: Write minimal implementation**

```python
    vcase(
        "CTS-13",
        "create-technical-solution",
        "对抗边界层",
        "complete-architecture-default-template",
        "第六步已收集上下文，但专家分析和协作收敛没有显式引用任何共享上下文编号，仍试图继续成稿。",
        "缺少共享上下文消费链时必须停机并回退到受影响阶段",
        "STOP_AND_ASK",
        assert_semantics=("明确指出缺失的共享上下文消费链",),
        assert_safety=("不允许无证据继续成稿",),
        forbidden_behavior=("跳过上下文引用继续生成最终方案",),
    )
```

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.skill_validation.test_case_catalog.CaseCatalogTests -v`
Expected: PASS

### Task 3: Implement the shared-context evidence chain in the skill docs

**Files:**
- Modify: `skills/create-technical-solution/SKILL.md`
- Modify: `skills/create-technical-solution/references/solution-process.md`
- Modify: `skills/create-technical-solution/references/progress-transparency.md`
- Test: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts -v`

- [x] **Step 1: Write the minimal doc changes to satisfy the failing tests**

```markdown
## 共享上下文清单
- `上下文编号`
- `来源`
- `结论或约束`
- `适用槽位`
- `可信度或缺口`

## 模板任务单新增字段
- `本槽位必须消费的共享上下文`
- `缺失即停止的上下文`

## 专家按模板逐槽位分析新增字段
- `已使用的共享上下文编号`
- `未使用原因`
- `结论是否超出上下文支持`

## 按模板逐槽位协作收敛新增字段
- `本槽位已核销的共享上下文`
- `上下文冲突如何处理`
- `仍缺哪条共享上下文`
```

- [x] **Step 2: Run targeted contract tests**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts -v`
Expected: PASS with the new contract tests and existing create-solution contract tests all green.

- [x] **Step 3: Tighten stop conditions and quality gates**

```markdown
- 任一槽位若缺少必须消费的共享上下文，必须标记阻塞并停止后续成稿。
- 专家结论若无法给出共享上下文编号或说明超出支持范围，必须回退，不得继续收敛。
- 协作收敛若无法核销上下文消费链，必须停止，不得输出看似完整的最终文档。
- 最终成稿前，逐槽位检查上下文编号、核销结果和缺口是否一致。
```

- [x] **Step 4: Run tests to verify the tightened docs still pass**

Run: `python3 -m unittest tests.skill_validation.test_create_technical_solution_contracts -v`
Expected: PASS

### Task 4: Run the full validation suite and inspect for regressions

**Files:**
- Test: `tests/skill_validation/test_*.py`

- [x] **Step 1: Run the full suite**

Run: `python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v`
Expected: PASS with all existing suites plus the new create-solution coverage.

- [x] **Step 2: If failures appear, fix only the failing contracts or phase expectations**

```python
# Example fix shape
EXPECTED_PHASE_3_ORDER = (
    "SA-09",
    "SA-10",
    "SA-11",
    "SA-12",
    "CTS-10",
    "CTS-11",
    "CTS-12",
    "CTS-13",
    "RTS-07",
    "RTS-08",
    "RTS-09",
)
```

- [x] **Step 3: Re-run the full suite**

Run: `python3 -m unittest discover -s tests/skill_validation -p "test_*.py" -v`
Expected: PASS
