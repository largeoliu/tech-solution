# create-technical-solution Eval Tests INDEX

## 正向用例 (T01-T06)

| ID | 文件 | 描述 | flow_tier |
|----|------|------|-----------|
| T01 | T01-full-新增订单支付模块.md | 完整流程：新增订单支付模块 | full |
| T02 | T02-light-单模块小改动.md | 单模块小改动：用户模块加邮箱字段 | light |
| T03 | T03-moderate-鉴权重构.md | 多模块协调：Session 鉴权重构为 JWT | moderate |
| T04 | T04-full-repowiki-多租户数据隔离.md | full + repowiki 存在：多租户数据隔离 | full |
| T05 | T05-moderate-repowiki-不存在-缓存层.md | moderate + repowiki 不存在：新增缓存层 | moderate |
| T06 | T06-full-服务拆分.md | 拆分服务：通知服务拆为消息网关+推送 | full |

## 边缘用例 (E01-E06)

| ID | 文件 | 描述 |
|----|------|------|
| E01 | E01-边缘-单成员.md | 名册仅 1 名成员 |
| E02 | E02-边缘-主题模糊.md | 主题模糊需步骤 1 澄清 |
| E03 | E03-边缘-前置文件缺失.md | principles.md 缺失引导 bootstrap |
| E04 | E04-边缘-slug-冲突.md | slug 冲突需终止重启 |
| E05 | E05-边缘-WD-EXP-字段缺失.md | WD-EXP 缺必填字段门禁拒绝 |
| E06 | E06-边缘-两模块边界判定.md | 两模块无新建核心能力边界判定 |

## 描述边界用例 (D01-D04)

| ID | 文件 | 描述 |
|----|------|------|
| D01 | D01-描述边界-补写口头约定.md | 补写技术方案 |
| D02 | D02-描述边界-更新已有方案.md | 更新已有方案 |
| D03 | D03-描述边界-查询现有架构.md | 查询现有架构描述 |
| D04 | D04-描述边界-规划任务分解.md | 规划任务分解（非方案文档） |

## 负向用例 (N01-N06)

| ID | 文件 | 描述 |
|----|------|------|
| N01 | N01-负向用例-分析CSV数据.md | 分析 CSV 销售数据 |
| N02 | N02-负向用例-写Python脚本.md | 写 Python 脚本批量处理日志 |
| N03 | N03-负向用例-画架构图.md | 画现有系统架构图 |
| N04 | N04-负向用例-REST改gRPC.md | 纯代码改写 |
| N05 | N05-负向用例-ReviewPR.md | Review PR 代码质量问题 |
| N06 | N06-负向用例-写API文档.md | 写 API 使用文档 |

## 统计

- 正向用例：6 条 (train: 4, validation: 2)
- 边缘用例：6 条 (train: 3, validation: 3)
- 描述边界：4 条 (train: 2, validation: 2)
- 负向用例：6 条 (train: 3, validation: 3)
- **总计：22 条**
