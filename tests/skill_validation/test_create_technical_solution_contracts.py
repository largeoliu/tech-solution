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
                "若 `.architecture/technical-solutions/working-drafts/` 缺失，则自动创建该目录后继续，以便承载唯一 working draft。",
                "若三个关键文件齐全但 `.architecture/technical-solutions/` 缺失，则自动创建该目录后继续。",
                "将最终文档写入 `.architecture/technical-solutions/[主题-短横线文件名].md`。",
                "若目标文件已存在且用户未明确要求更新，先确认覆盖还是另存；不要静默覆盖无关文档。",
            ),
        )

    def test_main_skill_enforces_template_locked_workflow(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "必须先读取当前生效模板，再判断方案类型，再选择参与成员。",
                "### 7. 生成模板任务单",
                "明确每个模板槽位的语义、负责参与成员、专家必答问题、禁止越界输出的事项，以及会阻止安全落位的阻塞条件。",
                "### 8. 组织专家按模板逐槽位分析",
                "按模板槽位逐项独立分析，不要直接重复别人的结论，也不要输出模板外可见结构。",
                "### 9. 按模板逐槽位协作收敛",
                "只保留能够稳定落回当前模板已有位置的内容。",
                "### 10. 严格模板成稿并保存结果",
                "保持当前生效模板的现有结构，不新增任何模板外可见结构；若模板没有同名章节，则按现有结构语义落位。",
            ),
        )

    def test_shared_context_must_flow_through_all_artifacts(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "### 6. 构建共享上下文",
                "先形成一份 `共享上下文清单`",
                "`上下文编号`",
                "`来源`",
                "`结论或约束`",
                "`适用槽位`",
                "`可信度或缺口`",
                "### 7. 生成模板任务单",
                "`本槽位必须消费的共享上下文`",
                "`缺失即停止的上下文`",
                "### 8. 组织专家按模板逐槽位分析",
                "`已使用的共享上下文编号`",
                "`未使用原因`",
                "`结论是否超出上下文支持`",
                "### 9. 按模板逐槽位协作收敛",
                "`本槽位已核销的共享上下文`",
                "`上下文冲突如何处理`",
                "`仍缺哪条共享上下文`",
                "### 10. 严格模板成稿并保存结果",
                "任一槽位若无法回溯到已核销的共享上下文编号，停止成稿并确认。",
            ),
        )

    def test_behavior_contract_orders_shared_context_before_task_sheet(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "3. 再选择参与成员。",
                "4. 第 6 步必须先产出 `共享上下文清单`。",
                "5. 再生成 `模板任务单`。",
                "6. `共享上下文清单`、`模板任务单`、各份 `专家产物`、`协作收敛纪要` 和 `变更影响说明` 必须先写入同一份 working draft，再按阶段对外展示摘要。",
            ),
        )

    def test_reference_docs_require_context_traceability_and_stop_rules(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["solution_process"],
            (
                "`共享上下文清单`",
                "`上下文编号`",
                "`来源`",
                "`结论或约束`",
                "`适用槽位`",
                "`可信度或缺口`",
                "`本槽位必须消费的共享上下文`",
                "`缺失即停止的上下文`",
                "`已使用的共享上下文编号`",
                "`未使用原因`",
                "`结论是否超出上下文支持`",
                "`本槽位已核销的共享上下文`",
                "`上下文冲突如何处理`",
                "`仍缺哪条共享上下文`",
                "任一槽位若缺少必须消费的共享上下文，必须标记为阻塞并停止后续自动成稿。",
            ),
        )
        require_snippets_in_order(
            self,
            self.sources["progress_transparency"],
            (
                "### 共享上下文清单：展示契约",
                "`共享上下文清单` 是第 6 步共享证据的对话内展示包装",
                "必须先展示 `共享上下文清单`，再展示 `模板任务单`，才允许进入 `专家按模板逐槽位分析阶段`。",
                "`模板任务单` 是对 `references/solution-process.md` 中 `模板任务单` 的对话内展示包装",
                "`本槽位必须消费的共享上下文`",
                "`缺失即停止的上下文`",
                "`专家产物` 是对 `references/solution-process.md` 中 `专家按模板逐槽位分析` 的对话内展示包装",
                "`已使用的共享上下文编号`",
                "`未使用原因`",
                "`结论是否超出上下文支持`",
                "`协作收敛纪要` 是 `references/solution-process.md` 中 canonical `按模板逐槽位协作收敛` 结构的对话内展示形态。",
                "`本槽位已核销的共享上下文`",
                "`上下文冲突如何处理`",
                "`仍缺哪条共享上下文`",
                "若任一槽位缺少已核销的共享上下文，不进入 `严格模板成稿阶段`。",
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

    def test_solution_process_requires_template_slot_artifacts(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["solution_process"],
            (
                "## 3. 模板任务单",
                "`槽位标识`",
                "`每位专家必答问题`",
                "## 4. 专家按模板逐槽位分析",
                "`是否参与该槽位`",
                "`建议写法或建议内容`",
                "## 5. 按模板逐槽位协作收敛",
                "`共同结论`",
                "`未采纳理由`",
            ),
        )

    def test_solution_process_forbids_generic_expert_shells(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["solution_process"],
            (
                "专家不能再以 `设计目标`、`关键约束`、`主要风险`、`关键权衡` 等通用标题组织自己的主结构。",
                "只能围绕模板已有槽位回答。",
                "如果某个槽位与该专家无关，应明确标记无贡献，而不是自由发挥到别的结构里。",
            ),
        )

    def test_solution_process_treats_semantic_obligations_as_checklist_not_parallel_structure(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["solution_process"],
            (
                "最终文档仍必须覆盖下面这组最低语义义务。",
                "它们只是最终成稿前的检查清单。",
                "不是模板外的中间层，也不是要求另起一套通用章节名。",
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

    def test_template_chain_is_locked_in_adaptation_and_progress_docs(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["template_adaptation"],
            (
                "当前 `.architecture/templates/technical-solution-template.md` 是唯一正文骨架来源。",
                "当前模板不仅是最终正文骨架，也是整条分析链唯一的信息架构。",
                "不允许在任何阶段引入模板外的章节层级。",
                "如果某个必要信息在当前模板内没有合法落点，应停止并向用户确认。",
            ),
        )
        require_snippets_in_order(
            self,
            self.sources["progress_transparency"],
            (
                "模板任务单阶段",
                "专家按模板逐槽位分析阶段",
                "`专家按模板逐槽位分析` 的对话内展示包装",
                "按 `references/solution-process.md` 的模板逐槽位字段顺序展示",
                "按模板逐槽位协作收敛阶段",
                "canonical `按模板逐槽位协作收敛` 结构的对话内展示形态",
                "模板发生变化时，至少回退到 `模板任务单`。",
            ),
        )
        self.assertNotIn("成员独立输入格式", self.sources["progress_transparency"])
        self.assertNotIn("canonical `协作收敛`", self.sources["progress_transparency"])
        self.assertIn("严格模板成稿阶段", self.sources["solution_process"])

    def test_template_task_sheet_is_visible_before_expert_analysis(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["progress_transparency"],
            (
                "## 3. 模板任务单",
                "`模板任务单` 是对 `references/solution-process.md` 中 `模板任务单` 的对话内展示包装",
                "模板槽位、参与专家、必答问题和阻塞条件稳定后，必须先展示 `模板任务单`，再进入 `专家按模板逐槽位分析阶段`。",
                "最小展示外壳如下：",
                "## 模板任务单",
                "[按 references/solution-process.md 的模板任务单格式渲染正文]",
                "按 `references/solution-process.md` 的 canonical `模板任务单` schema 与当前模板槽位顺序稳定展示，不得自行换序或删减必填字段。",
            ),
        )
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "### 7. 生成模板任务单",
                "先基于当前生效模板生成一份 `模板任务单`",
                "完成后，必须先按 [references/working-draft-protocol.md](references/working-draft-protocol.md) 将这份 `模板任务单` 写入 `WD-TASK`，再在对话中展示摘要。",
                "### 8. 组织专家按模板逐槽位分析",
            ),
        )
        self.assertIn(
            "过程可见产物：已写入 1 份 working draft，并摘要展示 1 份共享上下文清单、1 份模板任务单、[成员数] 份专家产物与 1 份协作收敛纪要",
            self.sources["main"],
        )

    def test_contracts_require_zero_new_visible_content_and_safe_stop(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "最终只把已收敛内容写回当前模板已有位置。",
                "缺少语义前置、无法展示稳定中间产物或无法安全落位时停止并确认。",
            ),
        )
        require_snippets_in_order(
            self,
            self.sources["solution_process"],
            (
                "任何槽位如果没有足够语义支撑，必须标记为阻塞并停止后续自动成稿。",
                "`选定写法` 只能落回当前模板已有槽位，不得外溢为模板外可见结构。",
            ),
        )
        require_snippets_in_order(
            self,
            self.sources["progress_transparency"],
            (
                "`严格模板成稿阶段` 只负责把已稳定的结论映射回当前模板，不发明模板外可见结构。",
                "若模板无法安全承载必需信息，应停止并向用户确认，而不是绕过模板约束继续写。",
            ),
        )
        require_snippets_in_order(
            self,
            self.sources["template_adaptation"],
            (
                "不允许在任何阶段引入模板外的章节层级。",
                "不允许新增用户模板没有定义的一级章节。",
                "如果某个必要信息在当前模板内没有合法落点，应停止并向用户确认。",
            ),
        )

    def test_progress_transparency_change_impact_mentions_invalidated_template_task_sheet_content(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["progress_transparency"],
            (
                "## 变更影响说明",
                "- 受影响内容：[哪些模板任务单槽位、哪些专家槽位分析、哪些协作收敛结论、哪些模板映射内容失效]",
                "- 最近受影响的阶段边界：[模板任务单阶段 / 专家按模板逐槽位分析阶段 / 按模板逐槽位协作收敛阶段 / 严格模板成稿阶段]",
            ),
        )
        require_snippets_in_order(
            self,
            self.sources["progress_transparency"],
            (
                "要求：",
                "- 如果已展示的 `模板任务单` 内容受影响，必须明确说明其哪些槽位已作废或失效，不得继续视为当前有效版本。",
            ),
        )

    def test_solution_process_requires_working_draft_before_user_display(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["solution_process"],
            (
                "适用于全部用户可见产物的共享规则如下：",
                "`共享上下文清单`、`模板任务单`、`专家按模板逐槽位分析`、`按模板逐槽位协作收敛`、`变更影响说明` 都必须先补齐本文件要求的必填字段，再写入 working draft，再对用户展示。",
                "对外展示时，默认只展示稳定摘要，并使用 `详见 working draft：WD-CTX（共享上下文清单）` 这类稳定引用指向完整内容。",
                "阶段回退或重算时，先更新 working draft 中对应区块，再对外展示 `变更影响说明`。",
                "最终文档生成后，先执行吸收检查，再删除 working draft。",
            ),
        )

    def test_progress_transparency_switches_to_summary_plus_working_draft_references(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["progress_transparency"],
            (
                "中间产物必须先写入 working draft，再对用户展示摘要。",
                "`详见 working draft：WD-CTX（共享上下文清单）`",
                "`详见 working draft：WD-TASK（模板任务单）`",
                "`详见 working draft：WD-EXP-system-architect（系统架构师专家产物）`",
                "`详见 working draft：WD-SYN（协作收敛纪要）`",
                "`详见 working draft：WD-IMPACT-[n]（变更影响说明）`",
            ),
        )
        self.assertNotIn(
            "中间产物默认只在当前对话中展示，不新增正式文档或侧车文件。",
            self.sources["progress_transparency"],
        )

    def test_working_draft_protocol_defines_single_draft_path_blocks_and_lifecycle(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["working_draft_protocol"],
            (
                "`.architecture/technical-solutions/working-drafts/[slug].working.md`",
                "整个一次技术方案生成过程只维护一份 working draft。",
                "## WD-CTX 共享上下文清单",
                "## WD-TASK 模板任务单",
                "## WD-EXP-[expert-slug] 专家产物",
                "## WD-SYN 协作收敛纪要",
                "## WD-IMPACT-[n] 变更影响说明",
                "每个阶段完成后，必须先把完整 canonical schema 写入 working draft，再对用户展示摘要。",
                "working draft 不保存 scratchpad、原始推理链路或聊天记录。",
                "吸收检查通过后，删除 working draft。",
            ),
        )

    def test_working_draft_protocol_requires_restart_on_slug_change(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["working_draft_protocol"],
            (
                "`slug` 必须与最终技术方案目标文件使用同一份短横线文件名。",
                "若用户改变主题并导致 `slug` 改变，应停止当前流程并基于新 `slug` 重新开始，而不是并行保留多份 working draft。",
            ),
        )

    def test_working_draft_protocol_defers_block_content_to_canonical_schemas(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["working_draft_protocol"],
            (
                "下列 `WD-*` 区块只定义稳定区块身份、working draft 落位与最小索引字段。",
                "每个区块的完整正文仍必须遵循 `references/solution-process.md` 中对应阶段的 canonical schema。",
                "这些字段只是帮助定位、引用与回退的最小索引字段，不构成第二套更弱的替代 schema。",
                "## WD-TASK 模板任务单",
                "## WD-EXP-[expert-slug] 专家产物",
                "## WD-SYN 协作收敛纪要",
            ),
        )

    def test_main_skill_requires_working_draft_round_trip(self) -> None:
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "## 完成标准",
                "分阶段中间产物先写入 `.architecture/technical-solutions/working-drafts/[主题-短横线文件名].working.md`，再按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示摘要；过程中不新增除最终技术方案文档外的正式交付物。",
                "生成最终文档后，先执行吸收检查；通过后删除 working draft。",
                "## 高层工作流",
            ),
        )
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "`.architecture/technical-solutions/working-drafts/[主题-短横线文件名].working.md`",
                "完成后，必须先按 [references/working-draft-protocol.md](references/working-draft-protocol.md) 将 `共享上下文清单` 写入 `WD-CTX`，再按 [references/progress-transparency.md](references/progress-transparency.md) 在对话中展示摘要。",
                "完成后，必须先按 [references/working-draft-protocol.md](references/working-draft-protocol.md) 将这份 `模板任务单` 写入 `WD-TASK`，再在对话中展示摘要。",
                "每个成员完成独立输入后，先写入对应 `WD-EXP-[expert-slug]` 区块，再展示摘要。",
                "完成收敛后、生成最终文档前，必须先将 `协作收敛纪要` 写入 `WD-SYN`，再在对话中展示摘要。",
                "过程可见产物：已写入 1 份 working draft，并摘要展示 1 份共享上下文清单、1 份模板任务单、[成员数] 份专家产物与 1 份协作收敛纪要",
                "生成最终文档后，先执行吸收检查；通过后删除 working draft。",
            ),
        )
        require_snippets_in_order(
            self,
            self.sources["main"],
            (
                "## 行为契约",
                "`共享上下文清单`、`模板任务单`、各份 `专家产物`、`协作收敛纪要` 和 `变更影响说明` 必须先写入同一份 working draft，再按阶段对外展示摘要。",
                "最终文档生成后，先执行吸收检查；通过后删除 working draft。",
                "最终保持当前模板现有结构，不新增任何模板外可见结构；最终只把已收敛内容写回当前模板已有位置。",
                "缺少语义前置、无法展示稳定中间产物、无法安全落位，或任一槽位缺少可回溯的共享上下文编号时停止并确认。",
            ),
        )
        self.assertNotIn("这些中间产物默认不作为侧车文档落盘", self.sources["main"])

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
