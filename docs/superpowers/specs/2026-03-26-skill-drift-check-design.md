# Skill 漂移检查设计

## 概述

本说明定义了一套只读检查方法，用来判断 `setup-architect` 和 `create-technical-solution` 是否存在执行流程漂移。

这次检查不把“.architecture/* 尚未生成”默认判定为漂移，而是分 3 种运行场景来判断：两个 skill 串联时是否能稳定衔接、单独执行编写技术方案 skill 且前置不满足时能否正确停机、单独执行编写技术方案 skill 且前置满足时能否独立按规范完成。

## 范围

纳入检查：
- `skills/setup-architect/SKILL.md`
- `skills/setup-architect/references/installation-procedures.md`
- `skills/setup-architect/references/member-customization.md`
- `skills/setup-architect/references/principles-customization.md`
- `skills/setup-architect/references/technical-solution-template-customization.md`
- `skills/create-technical-solution/SKILL.md`
- `skills/create-technical-solution/references/solution-process.md`
- `skills/create-technical-solution/references/template-adaptation.md`
- `skills/create-technical-solution/references/solution-analysis-guide.md`

不纳入检查：
- 直接修改 skill 内容
- 运行真实子代理模拟
- 仅因为安装前缺少 `.architecture/*` 就判定为漂移

## 场景

### 场景 A：串联主路径

检查预期主路径：先执行 `setup-architect`，再执行 `create-technical-solution`。

需要回答的问题：
- `setup-architect` 的完成态，是否会产出 `create-technical-solution` 所需的前置物？
- 这些交接产物以及它们的语义是否足够清晰，能让后一个 skill 直接依赖，而不需要回头猜安装过程中的上下文？
- `setup-architect` 中与成员定制、原则定制、模板定制相关的分支，是否会破坏下游契约？

通过标准：
- `setup-architect` 的完成态可以直接满足 `create-technical-solution` 的前置检查和运行假设。

漂移迹象：
- 交接产物定义不完整或彼此不一致。
- 某个关键交接规则只写在侧边引用文档里，主流程容易漏掉。
- 某个定制分支可能产出一种下游 skill 没有明确接受的状态。

### 场景 B：单独执行编写技术方案 skill，且前置不满足

检查直接触发 `create-technical-solution`，但前置文件或目录缺失的情况。

需要回答的问题：
- 这个 skill 是否显式校验必需前置？
- 当前置不满足时，它是否会在成员选择、模板适配、文档生成之前停止？
- 它是否会明确把用户导回 `setup-architect`，而不是自行补造 `.architecture/*`？

通过标准：
- skill 会明确报告缺失前置、明确指向 `setup-architect`，并在不伪造项目产物、不生成半成品技术方案的前提下停止。

漂移迹象：
- 停机条件只是隐含的，不是显式规则。
- 缺少输出目录或关键文件时，行为不清晰。
- 文档允许在前置失败后“半继续”执行。

### 场景 C：单独执行编写技术方案 skill，且前置满足

检查直接触发 `create-technical-solution`，且所需前置文件和目录已经存在的情况。

需要回答的问题：
- 这个 skill 是否能仅基于既有 `.architecture/*` 契约独立运行？
- 模板读取、方案类型分析、成员选择、共享上下文构建、信息收敛、质量门禁、保存落盘这些步骤，在各文档中的顺序是否一致？
- 完成标准是否足以覆盖引用文档中要求的关键信息块和模板约束？

通过标准：
- skill 文档能够拼成一条清晰、唯一、且不依赖 `setup-architect` 继续参与的执行路径。

漂移迹象：
- 主 skill 和引用文档对关键步骤顺序要求不同。
- 完成标准弱于引用文档里的强制要求。
- 关键运行规则只出现在引用文档里，顶层流程很容易漏读。

## 检查方法

本次检查分为两层。

### 1. 规范矩阵

对每个 skill 建一张矩阵，映射：
- 顶层流程步骤
- 约束该步骤的引用文档
- 必须停机的节点
- 必须确认的节点
- 该步骤产出的下游依赖或运行假设

这张矩阵会作为判断“主 skill 流程”和“引用文档约束”是否一致的依据。

### 2. 场景推演

将矩阵分别放入场景 A、B、C 中推演，根据各场景下流程是否稳定来归类问题。

## 判定规则

每条发现按以下 3 类判定：

- `确认漂移`：两个规范来源直接冲突，或者流程无法被解释成一条稳定的执行路径。
- `高风险漂移`：文档没有直接冲突，但关键约束分散、表述不完整、或顺序安排容易导致跳步、误判分支、漏掉强约束。
- `无明显漂移`：顶层流程、引用约束、分支规则、停机行为、交接假设整体一致，没有明显流程漂移。

以下情况本身不算漂移：
- 安装前缺少 `.architecture/*`
- 已清楚定义、并带有显式门禁的可选用户分支

## 结果输出结构

最终报告将包含：
- 检查范围和判定口径
- 场景 A、B、C 的逐场景结论
- 横向对比：交接契约、停机行为、独立执行能力
- 每条发现对应的证据路径
- 最小修正建议，优先补顺序、补停机点、补交接契约，而不是大改整个 skill 结构

## 证据记录格式

每条发现统一按以下结构记录：
- 现象
- 原因
- 影响场景
- 证据路径
- 判定
- 最小修正建议

## 风险与限制

- 这是一份基于文档的检查设计，因此可以识别“执行流程漂移风险”，但不能直接证明真实运行时一定会这样表现。
- 如果后续需要做实测，可以把这 3 个场景继续展开成压力测试或子代理模拟。
