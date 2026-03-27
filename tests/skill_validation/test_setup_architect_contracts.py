import unittest

from tests.skill_validation.helpers import (
    load_setup_contract_sources,
    require_all_snippets,
    require_snippets_in_order,
    top_level_headings,
)


class SetupArchitectContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_setup_contract_sources()

    def test_main_skill_exposes_install_and_template_only_paths(self) -> None:
        require_all_snippets(
            self,
            self.sources["main"],
            (
                "### 1. 安装架构框架",
                "### 6. 确认当前生效模板并收尾",
                "## 路径 B：仅替换技术方案模板",
                "- 不重跑初始化流程。",
            ),
        )

    def test_main_skill_lists_install_before_project_analysis(self) -> None:
        main = self.sources["main"]
        install_heading = "### 1. 安装架构框架"
        analysis_heading = "### 2. 分析项目"

        self.assertIn(install_heading, main)
        self.assertIn(analysis_heading, main)
        self.assertLess(main.index(install_heading), main.index(analysis_heading))

    def test_main_skill_keeps_install_and_analysis_contract_in_order(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "### 1. 安装架构框架",
                "按 [references/installation-procedures.md](references/installation-procedures.md) 创建目录，并安装模板和基础文件。",
                "### 2. 分析项目",
                "识别语言、框架、测试/CI、部署方式和目录结构。",
            ),
        )

    def test_main_skill_waits_for_template_answer_before_init_summary(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "必须先询问用户是否需要定制技术方案模板。",
                "若用户尚未明确回答，则返回 `STOP_AND_ASK`，继续等待；此时不允许输出最终“Tech Solution 设置完成”摘要。",
                "只有在用户明确选择保留当前模板，或已提供有效完整输入并完成整体替换后，才允许输出最终“Tech Solution 设置完成”摘要。",
                "初始化摘要：",
            ),
        )

    def test_installation_reference_creates_minimum_structure(self) -> None:
        require_all_snippets(
            self,
            self.sources["installation"],
            (
                "mkdir -p .architecture/technical-solutions",
                "mkdir -p .architecture/templates",
                ".architecture/templates/technical-solution-template.md",
                ".architecture/members.yml",
                ".architecture/principles.md",
            ),
        )

    def test_template_customization_requires_complete_setup_and_full_input(self) -> None:
        require_all_snippets(
            self,
            self.sources["template_customization"],
            (
                "若任一校验失败，则视为 setup 不完整，应停止并要求用户先执行完整初始化；不要静默补文件。",
                "接受用户直接提供的完整 Markdown 模板内容、文件路径或者链接地址。",
                "收到后整体替换 `.architecture/templates/technical-solution-template.md`。",
                "不支持恢复默认模板。",
                "不支持自动生成模板、局部编辑或内容合并。",
            ),
        )

    def test_template_customization_scene_a_keeps_retain_current_template_branch(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["template_customization"],
            (
                "## 场景 A：初始化收尾时确认模板是否定制",
                "若回答“不需要”，保留当前 `.architecture/templates/technical-solution-template.md`。",
                "初始化场景摘要：",
            ),
        )

    def test_template_customization_scene_b_keeps_replace_only_branch(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["template_customization"],
            (
                "## 场景 B：安装后单独替换技术方案模板",
                "直接要求用户提供完整 Markdown 模板内容，不存在“保留当前模板”的分支。",
                "安装后替换场景摘要：",
            ),
        )

    def test_template_customization_scene_a_waits_before_init_summary(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["template_customization"],
            (
                "必须先询问用户是否需要定制技术方案模板。",
                "若用户尚未明确回答，则返回 `STOP_AND_ASK`，继续等待；此时不允许输出最终 `Tech Solution 设置完成` 摘要。",
                "只有在用户明确选择保留当前模板，或已提供有效完整输入并完成整体替换后，才允许输出最终 `Tech Solution 设置完成` 摘要。",
                "初始化场景摘要：",
            ),
        )

    def test_member_customization_preserves_core_members(self) -> None:
        require_all_snippets(
            self,
            self.sources["member_customization"],
            (
                "系统架构师",
                "领域专家",
                "安全专家",
                "性能专家",
                "可维护性专家",
                "添加技术专家，不要替换核心成员。",
            ),
        )

    def test_principles_customization_preserves_core_principles_and_coverage(self) -> None:
        require_all_snippets(
            self,
            self.sources["principles_customization"],
            (
                "不要删除下方“核心原则（保留这些）”中的基础原则",
                "至少覆盖模块边界与依赖方向、API / 事件 / 数据边界、测试和验证基线、安全与合规底线，以及技术方案和实施计划的决策标准",
                "宜居代码",
                "清晰优于炫技",
                "关注点分离",
                "可演化性",
                "可观测性",
                "设计即安全",
                "领域中心设计",
                "务实的简洁性",
                "变更影响意识",
            ),
        )

    def test_principles_customization_requires_host_project_baseline_rules(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["principles_customization"],
            (
                "`.architecture/principles.md` 的主要作用，是为宿主项目后续的技术方案编写与架构评审提供项目上下文和判断基线。",
                "按七个主章节填写宿主项目事实、边界、底线和当前现实。",
                "核心原则必须保留，但必须翻译成宿主项目语境下的判断规则。",
                "只保留会影响技术方案和评审判断的内容。",
                "不要写成 README、系统清单、接口总表或运维手册。",
            ),
        )

    def test_main_skill_positions_principles_as_required_judgment_baseline(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "### 4. 定制架构原则",
                "按 [references/principles-customization.md](references/principles-customization.md) 把 `.architecture/principles.md` 定制成宿主项目的上下文和判断基线；",
                "后续技术方案编写与架构评审会将这些原则作为必需输入。",
            ),
        )

    def test_principles_template_uses_host_project_baseline_sections(self) -> None:
        self.assertEqual(
            top_level_headings(self.sources["principles_template"]),
            [
                "文档目的与使用方式",
                "业务域与项目语义",
                "模块边界与依赖方向",
                "数据、接口与事件边界",
                "质量属性与治理底线",
                "当前必须尊重的项目现实",
                "方案编写与评审准绳",
                "原则映射表",
            ],
        )

    def test_principles_template_embeds_inline_host_project_guidance_and_mapping(self) -> None:
        principles_template = self.sources["principles_template"]

        require_all_snippets(
            self,
            principles_template,
            (
                "本文档用于为后续技术方案编写与评审提供项目上下文和判断基线。",
                "### 本项目事实",
                "### 为什么重要",
                "### 对方案与评审的要求",
                "核心原则必须保留，但要翻译成当前项目里的具体判断规则。",
                "| 核心原则 | 主要落点章节 | 本项目中的约束含义 |",
            ),
        )
        self.assertNotIn(
            "复制下方模板，在上方合适位置新增项目特定原则",
            principles_template,
        )


if __name__ == "__main__":
    unittest.main()
