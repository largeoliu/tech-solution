---
name: review-technical-solution
description: Use when reviewing a technical solution against requirement details, architecture principles, and existing project code, especially when missing context, unverified assumptions, implementation-fit risks, or code-reality mismatches could invalidate the proposal.
---

# 技术方案评审

按需求详情、技术方案文档、`.architecture/principles.md` 和项目现有代码做正式评审。主技能文件定义职责边界、停机规则、固定输出和红旗信号；`references/review-process.md` 提供正式评审流程细则，`references/review-analysis-guide.md` 提供方案分类与评审焦点指引，`references/review-output-contract.md` 提供固定区块、允许结论值、字段名和空区块写法约束。

## 技能定位

- 只在需要正式评审技术方案时使用；如果用户要创建、补写或更新方案正文，转到 `create-technical-solution`。
- 正式评审依赖四类证据源：
  - `需求详情`
  - `技术方案文档`
  - `.architecture/principles.md`
  - `相关项目代码`
- 必须先看需求、再看方案、再看原则、再看代码；不能只读文档表面后直接下结论。
- 主 skill 负责唯一主路径、硬性阻断、固定输出、红旗信号和完成标准；引用文档负责完整细则。

## 必要上下文

正式评审前必须确认以下输入齐全且可读：
- `需求详情`
- `技术方案文档`
- `.architecture/principles.md`
- `相关项目代码`

任一缺失时，不做正式结论，直接输出 `无法开展正式评审`。

并明确：
- 缺了什么
- 为什么这会阻断正式评审
- 需要补什么后再继续

## 高层工作流

### 1. 校验输入完整性

缺少必要上下文时立即停止，不输出 `通过`、`需修改` 或 `阻断`。

### 2. 判断方案类型

先判断方案属于哪一类主要变更，再识别是否同时涉及跨模块、数据、接口、部署或治理等附加影响范围。

### 3. 提取核心主张

从需求与方案中提取目标、非目标、约束、复用能力、变更边界、接口、数据结构、测试与发布策略。

### 4. 代码取证

在相关项目代码中核验核心主张是否成立、边界是否匹配、依赖是否存在。不能因为用户催促、方案写得完整，或“看起来合理”就跳过代码核验。

### 5. 归因与分级

按需求对齐、架构对齐、代码现状对齐、完整性、可落地性归因问题，并基于证据与影响分级。

### 6. 生成改进方案

每个重要问题都要给出可执行的改进方向与验证动作。

## 硬性规则

- 任一必要输入缺失时，不做正式结论，直接输出 `无法开展正式评审`。
- 所有已确认问题都必须给出证据，证据只能来自需求详情、技术方案文档、`.architecture/principles.md`、项目代码 / 配置 / schema / 接口 / 测试。
- 证据不足时只能标记为 `待核验风险`，不能把猜测写成事实。
- 找不到方案声称复用的现有能力时，必须显式指出代码证据缺失或主张被代码证伪。
- 不能因为用户催促、时间紧、方案写得完整，或“先评再补代码”就降低评审标准。

## 固定输出

正式输出必须按以下顺序展开：
1. `评审结论`
2. `阻断项`
3. `主要问题`
4. `改进方案`
5. `待补充信息`
6. `建议验证`

## 红旗信号

出现以下说法时，停下来重新核验证据：
- ‘这个方案看起来合理，不用看代码了。’
- ‘用户赶时间，我先给个结论。’
- ‘先按经验评，代码之后再补。’
- ‘现有能力大概率有，先默认它存在。’
- ‘摘要差不多够了，不用看完整方案正文。’

## 说明

- 本文件是 `review-technical-solution` 的主入口契约，重点是输入门槛、停机规则、证据要求和固定输出顺序。
- `references/review-process.md` 负责展开正式评审流程、主张提取、代码取证、问题分级和输出前自检。
- `references/review-analysis-guide.md` 负责展开方案分类判定，以及各类方案的必查问题、必查代码证据和常见阻断项。
- `references/review-output-contract.md` 负责展开固定输出区块、允许的结论值、字段要求，以及空区块必须写 `- 无` 的规则。
