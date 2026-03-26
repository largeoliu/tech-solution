import unittest

from tests.skill_validation.helpers import (
    load_create_solution_contract_sources,
    require_snippets_in_order,
    testdata_path,
    top_level_headings,
)


class CreateTechnicalSolutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_create_solution_contract_sources()

    def test_main_skill_requires_current_template_and_redirects_missing_prereqs(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "当前 `.architecture/templates/technical-solution-template.md` 是唯一正文骨架来源；它可能是默认模板，也可能是用户替换后的自定义模板。",
                "必须先读取当前生效模板，再判断方案类型，再选择参与成员。",
                "如果只是初始化 `.architecture/`、补跑安装或替换模板，转到 `setup-architect`。",
            ),
        )
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "- `.architecture/members.yml`",
                "- `.architecture/principles.md`",
                "- `.architecture/templates/technical-solution-template.md`",
                "任一缺失时立即停止，明确说明初始化未完成，并引导用户先使用 `setup-architect`。",
            ),
        )

    def test_main_skill_requires_output_path_and_overwrite_confirmation(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "若三个关键文件齐全但 `.architecture/technical-solutions/` 缺失，则自动创建该目录后继续。",
                "将最终文档写入 `.architecture/technical-solutions/[主题-短横线文件名].md`。",
                "若目标文件已存在且用户未明确要求更新，先确认覆盖还是另存；不要静默覆盖无关文档。",
            ),
        )

    def test_solution_process_defines_slug_rules_and_mandatory_information_blocks(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["solution_process"],
            (
                "如果主题不明确，先澄清，再生成短横线风格文件名。清洗规则如下：",
                "将空格、下划线和常见分隔符折叠为 `-`",
                "如果清洗结果为空，要求用户提供更明确的标题",
                "### 问题与背景",
                "### 目标与非目标",
                "### 约束与依赖",
                "### 推荐方案",
                "### 备选方案与权衡",
                "### 详细设计",
                "### 风险与缓解",
                "### 实施建议",
                "### 评审关注点",
                "### 未决问题",
            ),
        )

    def test_template_adaptation_forbids_new_top_level_sections_and_requires_stop_on_ambiguity(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["template_adaptation"],
            (
                "不允许新增用户模板没有定义的一级章节。",
                "不允许把当前模板重写回默认模板结构。",
                "遇到以下情况时，不要猜测，直接停止并向用户确认：",
                "当前模板缺少承载某个必需信息块的合理位置",
                "模板几乎没有结构，无法安全判断应该在哪里承载关键内容",
            ),
        )

    def test_solution_analysis_guide_requires_architect_and_union_behavior(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["analysis_guide"],
            (
                "系统架构师始终参与",
                "参与成员取并集并去重",
                "必答问题取并集",
                "易漏风险取并集",
                "评审重点按风险高低排序",
            ),
        )

    def test_behavior_fixtures_are_distinct_for_valid_ambiguous_and_fragment_templates(self) -> None:
        custom_headings = top_level_headings(testdata_path("custom-template.md").read_text(encoding="utf-8"))
        ambiguous_headings = top_level_headings(
            testdata_path("ambiguous-template.md").read_text(encoding="utf-8")
        )
        fragment_headings = top_level_headings(testdata_path("template-fragment.md").read_text(encoding="utf-8"))
        code_fence_headings = top_level_headings(
            "# Example\n\n## Real section\n\n```md\n## Ignored inside fence\n```\n\n## Another section\n"
        )

        self.assertEqual(
            custom_headings,
            ["决策摘要", "当前痛点与目标", "候选路径比较", "详细设计", "风险与发布", "未决事项"],
        )
        self.assertEqual(ambiguous_headings, ["主体"])
        self.assertEqual(fragment_headings, ["仅有局部片段"])
        self.assertEqual(code_fence_headings, ["Real section", "Another section"])
        self.assertNotEqual(custom_headings, ambiguous_headings)
        self.assertNotEqual(custom_headings, fragment_headings)
        self.assertNotEqual(ambiguous_headings, fragment_headings)


if __name__ == "__main__":
    unittest.main()
