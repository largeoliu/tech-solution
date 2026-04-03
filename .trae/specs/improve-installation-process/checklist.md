# Checklist

## 安装流程改进

- [x] INSTALLATION.md Stage 2 使用增量安装逻辑，不再覆盖已存在的 skill 目录
- [x] 已存在的 skill 被跳过时输出明确的提示信息
- [x] 新安装的 skill 输出成功提示信息

## 专家角色添加验证

- [x] steps/2-customize-team.md 完成标准包含验证环节
- [x] 验证环节检查所有有依据的专家角色是否已存在于 members.yml
- [x] 专家角色遗漏时输出明确的错误信息，包含遗漏的角色名称及依据编号
- [x] 验证结果记录到状态文件 checkpoints.step-2
