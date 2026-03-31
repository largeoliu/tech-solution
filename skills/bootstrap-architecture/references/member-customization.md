# 定制架构团队成员

根据你的项目框架和技术栈定制这个名册： `.architecture/members.yml`

## 初始化方式

- 从模板 [../templates/members-template.yml](../templates/members-template.yml) 中识别项目需要的成员。
- 结合你的项目框架和技术栈，添加模板中不存在的成员（如需要）。
- 生成定制后的 `.architecture/members.yml`。

## 编辑成员

完成初始化后，如需新增技术专家，从模板文件末尾的注释模板复制一个成员块并追加到 `members:` 数组中。

**添加成员**：

1. 从 `members-template.yml` 末尾的注释模板复制一个成员块
2. 适当填写所有字段
3. 添加到 `.architecture/members.yml` 的 `members:` 数组中
4. 选择唯一的 `id`（使用小写和下划线）

**移除成员**：

1. 从 `.architecture/members.yml` 删除其条目

**修改成员**：

1. 编辑他们在 `.architecture/members.yml` 中的条目


