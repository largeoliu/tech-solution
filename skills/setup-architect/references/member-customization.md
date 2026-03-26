# 定制架构团队成员

根据你的项目框架和技术栈定制这个名册： `.architecture/members.yml`

## 编辑成员

初始化 `.architecture/members.yml` 时，先复制 [../templates/members-template.yml](../templates/members-template.yml) 作为起点。完成初始化后，如需新增技术专家，再从同一文件末尾的注释模板复制一个成员块并追加到 `members:` 数组中。

**添加成员**：
1. 从 `members-template.yml` 末尾的注释模板复制一个成员块
2. 适当填写所有字段
3. 添加到 `.architecture/members.yml` 的 `members:` 数组中
4. 选择唯一的 `id`（使用小写和下划线）

**移除成员**：
1. 从 `.architecture/members.yml` 删除其条目

**修改成员**：
1. 编辑他们在 `.architecture/members.yml` 中的条目


## 核心成员（保留这些）

这些核心成员应该为所有项目保留：
- **系统架构师**：整体架构一致性
- **领域专家**：业务领域表示
- **安全专家**：安全分析
- **性能专家**：性能和可扩展性
- **可维护性专家**：代码质量和技术债务

这些核心成员已内置在 [../templates/members-template.yml](../templates/members-template.yml) 中，可直接用来初始化 `.architecture/members.yml`。

**添加技术专家，不要替换核心成员。**
