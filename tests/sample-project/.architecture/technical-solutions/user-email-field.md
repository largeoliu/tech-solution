# 用户模块邮箱字段技术方案

## 概述

在用户模块中新增 `email` 字段，用于支持通知服务发送邮件通知。该字段为可选字段，默认值为空字符串，支持通知服务通过该字段获取用户邮箱地址并发送邮件。

- **目标**: 为用户模块新增 email 字段，支持通知服务发送邮件通知
- **非目标**: 不涉及其他用户字段修改、不涉及用户认证流程变更、不涉及新建核心能力
- **影响范围**: 用户表、用户注册/更新API、通知服务集成
- **约束**: 邮箱格式需符合 RFC 5322 规范；需考虑向后兼容

## 架构设计

### 数据层设计

在用户表新增 `email` 字段：

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| email | VARCHAR(255) | NOT NULL DEFAULT '' | 用户邮箱地址，用于通知服务发送邮件 |

### 接口设计

用户服务提供邮箱查询接口供通知服务调用：

```python
# 用户服务客户端
def get_user_email(user_id: str) -> str:
    """获取用户邮箱地址"""
    user = user_service.get(user_id)
    return user.email
```

### 关键约束

- 邮箱格式需符合 RFC 5322 规范
- 向后兼容：现有业务不受影响
- 默认值为空字符串，不强制用户填写

## 实现方案

### 步骤 1: 数据库迁移

执行 DDL 添加 email 字段：

```sql
ALTER TABLE users ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT '';
```

### 步骤 2: API 扩展

在用户注册和更新接口中增加 email 参数支持：

- `POST /api/v1/users` (注册)
- `PUT /api/v1/users/{id}` (更新)

### 步骤 3: 通知服务集成

通知服务在发送邮件前调用用户服务获取邮箱地址：

```python
# 通知服务发送邮件流程
def send_notification_email(user_id: str, content: str):
    email = user_service.get_user_email(user_id)
    if email:
        smtp_client.send(email, content)
```

## 风险评估

| 风险类型 | 风险等级 | 应对措施 |
|----------|----------|----------|
| 数据迁移风险 | 低 | 采用非阻塞式 ALTER TABLE 加字段 |
| 兼容性风险 | 低 | 向后兼容的变更，不影响现有功能 |
| 邮箱格式风险 | 中 | 实施时进行格式校验，符合 RFC 5322 规范 |
