import unittest

from tests.skill_validation.helpers import (
    load_review_solution_contract_sources,
    require_snippets_in_order,
)


class ReviewTechnicalSolutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_review_solution_contract_sources()

    def test_frontmatter_uses_searchable_name_and_description(self) -> None:
        main = self.sources['main']
        self.assertIn('name: review-technical-solution', main)
        self.assertIn(
            'description: Use when reviewing a technical solution against requirement details, architecture principles, and existing project code',
            main,
        )

    def test_main_skill_requires_four_inputs_and_blocks_missing_context(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['main'],
            (
                '- `需求详情`',
                '- `技术方案文档`',
                '- `.architecture/principles.md`',
                '- `相关项目代码`',
                '任一缺失时，不做正式结论，直接输出 `无法开展正式评审`。',
            ),
        )

    def test_main_skill_requires_code_evidence_and_fixed_output_order(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['main'],
            (
                '不能因为用户催促、方案写得完整，或“看起来合理”就跳过代码核验。',
                '`待核验风险`',
                '1. `评审结论`',
                '2. `阻断项`',
                '3. `主要问题`',
                '4. `改进方案`',
                '5. `待补充信息`',
                '6. `建议验证`',
            ),
        )

    def test_main_skill_references_task2_docs_instead_of_task1_only_wording(self) -> None:
        main = self.sources['main']
        self.assertIn('`references/review-process.md`', main)
        self.assertIn('`references/review-analysis-guide.md`', main)
        self.assertIn('`references/review-output-contract.md`', main)
        self.assertNotIn('当前 Task 1 仅锁定主入口契约，不依赖额外说明文档。', main)
        self.assertNotIn(
            '后续若补充细分流程或分类指引，应在对应任务落地时再新增文档并回填引用；当前不得假定这些说明已存在。',
            main,
        )

    def test_main_skill_locks_review_step_chain(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "### 2. 判断方案类型",
                "未完成第 2 步，不得进入第 3 步。",
                "### 3. 提取核心主张",
                "未完成第 3 步，不得进入第 4 步。",
                "### 4. 代码取证",
                "未完成第 4 步，不得进入第 5 步。",
                "### 5. 归因与分级",
                "未完成第 5 步，不得进入第 6 步。",
                "### 6. 生成改进方案",
                "未完成第 6 步，不得进入第 7 步。",
                "### 7. 输出前自检",
                "未完成第 7 步，不得进入第 8 步。",
                "### 8. 正式输出",
                "不得引入任何新的推理或判断，只能基于前 1 到 7 步已闭合的结果进行整理和呈现。",
            ),
        )

    def test_review_process_defines_claim_extraction_and_evidence_states(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['review_process'],
            (
                '## 4. 主张提取',
                '至少提取以下信息：',
                '`claim_id`',
                '`statement`',
                '`expected_evidence`',
                '## 5. 代码取证',
                '`已证实`',
                '`已证伪`',
                '`待核验`',
            ),
        )

    def test_review_process_defines_severity_and_conclusion_rules(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['review_process'],
            (
                '## 7. 问题分级规则',
                '`blocker`',
                '`major`',
                '`minor`',
                '`note`',
                '## 8. 最终结论规则',
                '任何 `blocker` -> `阻断`',
                '缺少必要输入 -> `无法开展正式评审`',
            ),
        )

    def test_review_process_promotes_self_check_to_release_gate(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["review_process"],
            (
                "## 10. 输出前自检",
                "未完成第 7 步，不得进入第 8 步。",
                "本轮结果为 `STOP_AND_ASK`。",
                "只允许回到第一个未完成步骤修正。",
            ),
        )

    def test_analysis_guide_covers_all_solution_types_and_union_behavior(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['analysis_guide'],
            (
                '1. 新功能方案',
                '2. 重构或替换方案',
                '3. 跨系统或平台能力方案',
                '4. 安全 / 合规 / 数据保护方案',
                '5. 性能 / 容量 / 成本优化方案',
                '评审问题取并集',
                '必查证据取并集',
                '最终结论按最高严重级别判定',
                '## 4. 各类重点',
                '### 1. 新功能方案',
                '必查问题：',
                '必查代码证据：',
                '常见阻断项：',
                '### 2. 重构或替换方案',
                '必查问题：',
                '必查代码证据：',
                '常见阻断项：',
                '### 3. 跨系统或平台能力方案',
                '必查问题：',
                '必查代码证据：',
                '常见阻断项：',
                '### 4. 安全 / 合规 / 数据保护方案',
                '必查问题：',
                '必查代码证据：',
                '常见阻断项：',
                '### 5. 性能 / 容量 / 成本优化方案',
                '必查问题：',
                '必查代码证据：',
                '常见阻断项：',
            ),
        )

    def test_output_contract_requires_fixed_sections_and_issue_fields(self) -> None:
        require_snippets_in_order(
            self,
            self.sources['output_contract'],
            (
                '1. `评审结论`',
                '2. `阻断项`',
                '3. `主要问题`',
                '4. `改进方案`',
                '5. `待补充信息`',
                '6. `建议验证`',
                '`通过`',
                '`需修改`',
                '`阻断`',
                '`无法开展正式评审`',
                '`severity`',
                '`category`',
                '`problem`',
                '`evidence`',
                '`impact`',
                '`recommendation`',
                '`validation`',
                '`targets`',
                '所有区块都必须出现',
            ),
        )

    def test_output_contract_forbids_new_reasoning_in_final_output(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["output_contract"],
            (
                "正式输出只能消费前七步已经闭合的结果。",
                "不得引入任何新的推理或判断，只能基于前 1 到 7 步已闭合的结果进行整理和呈现。",
                "不得在正式输出阶段新增主类型 / 附加类型判断。",
                "不得在正式输出阶段补做主张提取、证据状态判定、问题分级或改进动作。",
            ),
        )


if __name__ == '__main__':
    unittest.main()
