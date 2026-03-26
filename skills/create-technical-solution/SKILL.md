---
name: create-technical-solution
description: 使用相关架构团队成员协作创建技术方案文档，支持项目自定义模板。当用户请求 "创建技术方案" 或类似表达时使用。
---

# 创建技术方案

按项目模板组织内容，由相关架构成员协作形成技术方案。

## 流程

### 1. 解析输入与定题

输入可能是方案主题、需求描述，或已有上下文文档路径。

明确：问题、目标与非目标、约束与依赖、影响范围、相关需求。

如果主题不明确，先澄清。生成 kebab-case 文件名：移除 `..` `/` `\` 控制字符和首尾空白 → 折叠空格/下划线/分隔符为 `-` → 小写，只保留 `[a-z0-9-]` → 去掉首尾 `-`，限制长度；清洗为空则要求用户提供更明确的标题。

### 2. 准备前置条件

确保 `.architecture/technical-solutions/` 存在：

```bash
mkdir -p .architecture/technical-solutions
ls .architecture/technical-solutions
```

确认 `.architecture/members.yml`、`.architecture/principles.md`、`.architecture/templates/technical-solution-template.md` 均存在。任一缺失则停止并说明 setup 不完整。

### 3. 加载成员并选择参与者

读取 `.architecture/members.yml`。

默认必选系统架构师；非 trivial 方案通常加入可维护性专家和实施策略师。按主题补充：涉及业务语义加入领域专家，涉及认证/数据保护/合规加入安全专家，涉及延迟/吞吐/成本效率加入性能专家。跨系统、高风险或平台级主题升级为全员参与。

### 4. 构建共享上下文

整合 `.architecture/principles.md`、repowiki文档、代码/配置/架构说明、已有实现。原则文档是方案判断标准，不是可选背景；所有成员基于同一上下文设计。

### 5. 独立设计输入并协作收敛

各成员先独立产出：视角说明、设计目标、关键约束、方案贡献、风险与权衡、原则对齐与冲突、必要保护措施、未决问题。独立输入基于共享上下文，避免泛泛评论或重复。

然后收敛出：设计共识、争议点、候选方案对比、选定方向、选择理由、原则冲突的取舍、未决问题与后续决策点。

按项目模板生成最终方案，涵盖：问题与目标、背景与约束（包含原则约束）、设计共识、方案摘要、备选方案与权衡（包含原则驱动的取舍）、详细设计、风险与缓解、实施建议、评审关注点、未决问题 / 后续决策点。

### 6. 生成、保存并报告

写入 `.architecture/technical-solutions/[topic-kebab-case].md`。若文件已存在且用户未明确要求更新，先确认覆盖还是另存；不要静默覆盖无关文档。

```text
技术方案已创建或更新：[Title]

位置：.architecture/technical-solutions/[filename].md
参与成员：[Members]

关键点：
- 选定方向：[Approach]
- 主要权衡：[Trade-off]
- 未决问题：[Open Questions]
```
