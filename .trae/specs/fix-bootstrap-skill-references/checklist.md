# Checklist

## 步骤卡片引用修复

- [x] `steps/2-customize-team.md` 不再引用 `references/member-customization.md`
- [x] `steps/3-customize-principles.md` 不再引用 `references/principles-customization.md`
- [x] 步骤卡片包含必要的定制规则，可独立执行

## 输出边界约束

- [x] `steps/2-customize-team.md` 明确 members.yml 只包含模板定义的字段
- [x] `steps/3-customize-principles.md` 明确 principles.md 只包含模板定义的七个章节

## 临时文件清理

- [x] `SKILL.md` 包含"完成后清理"章节
- [x] 明确执行完成后删除 `state/current.yaml`
- [x] 明确阻塞状态时保留状态文件

## 整体验证

- [x] 所有步骤卡片引用的文件都存在
- [x] Skill 可以正常执行，不会因找不到引用文件而产生错误输出
