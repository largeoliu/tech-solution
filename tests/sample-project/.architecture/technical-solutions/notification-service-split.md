# 通知服务拆分方案

## 概述

将单体通知服务拆分为消息网关和推送服务两个独立服务。消息网关负责消息路由和队列管理，推送服务负责实际发送（短信、邮件、App推送）。拆分后两个服务独立部署、独立扩展，通过消息队列解耦。

## 服务拆分方案

### 拆分策略选择

**结论：采用职责分离拆分方案，拆分为消息网关 + 推送服务**

| 方案 | 可行性 | 理由 |
|------|--------|------|
| 职责分离（推荐） | 可行 | 消息网关聚焦路由和队列，推送服务聚焦通道发送，职责单一清晰 |
| 通道分离 | 不可行 | 按短信/邮件/推送通道拆分会导致推送服务过于碎片化 |
| 保留单体 | 不推荐 | 无法独立扩展，路由和发送耦合维护成本高 |

**不可复用原因：**
- 现有服务耦合路由和推送逻辑，无法通过改造实现解耦
- 需要新增消息队列基础设施，复用价值低

**不可改造原因：**
- 改造风险高，影响现有通知链路稳定性
- 拆分后架构更清晰，长期维护成本更低

### 兼容性设计

- 消息网关提供与现有通知服务相同的 API 接口
- 存量业务代码无需修改，仅变更服务发现地址
- 双写期间两个服务同时运行，逐步切流

## 职责边界

### 服务职责定义

| 服务 | 职责范围 | 核心能力 |
|------|----------|----------|
| 消息网关 | 消息接入、路由、队列、死信处理 | Kafka 消息持久化、优先级队列、死信队列管理 |
| 推送服务 | 通道适配、发送、重试、模板管理 | 短信通道（阿里云）、邮件通道（SMTP）、App推送（极光/华为） |

### 接口边界

**消息网关 API（对外接口）：**
- `POST /api/v1/notifications/send` - 发送通知请求
- `GET /api/v1/notifications/{id}/status` - 查询发送状态
- `POST /api/v1/notifications/batch` - 批量发送

**消息网关 -> 推送服务（内部接口）：**
- 通过 Kafka Topic `notification.push.sms` 传输短信任务
- 通过 Kafka Topic `notification.push.email` 传输邮件任务
- 通过 Kafka Topic `notification.push.app` 传输App推送任务

### 部署边界

| 服务 | 部署规格 | 扩展策略 |
|------|----------|----------|
| 消息网关 | 2核4G * 2副本 | CPU密集型，独立扩缩容 |
| 推送服务 | 4核8G * 3副本 | IO密集型，根据发送量弹性扩展 |

## 数据模型

### 消息网关数据模型

```
Topic: notification.inbox
├── notification_id      (string, 主键)
├── source_service        (string, 来源服务)
├── target_user          (string, 目标用户)
├── channel              (enum: sms/email/app/push)
├── priority             (enum: high/normal/low)
├── payload              (json, 消息内容)
├── scheduled_at         (timestamp, 计划发送时间)
├── created_at           (timestamp, 创建时间)
└── status               (enum: pending/routed/failed)

Topic: notification.dlq (死信队列)
├── notification_id
├── original_topic
├── error_reason
├── retry_count
└── failed_at
```

### 推送服务数据模型

```
Table: push_task
├── id                    (bigint, 主键)
├── notification_id      (string, 关联消息网关)
├── channel               (enum: sms/email/app)
├── recipient             (string, 手机号/邮箱/device_token)
├── template_id           (string, 模板标识)
├── template_params       (json, 模板参数)
├── status                (enum: pending/sending/success/failed)
├── retry_count           (int, 重试次数)
├── sent_at               (timestamp, 发送时间)
└── created_at            (timestamp, 创建时间)

Table: push_template
├── id                    (bigint, 主键)
├── template_code         (string, 模板编码)
├── channel               (enum: sms/email/app)
├── content_template      (text, 内容模板)
├── variables             (json, 变量定义)
└── status                (enum: active/inactive)
```

## 实现方案

### 第一阶段：消息网关
1. 搭建 Kafka 集群
2. 实现消息接入 API（统一入口）
3. 实现消息路由逻辑（按渠道、优先级）
4. 实现消息队列（Kafka Topic 划分）
5. 实现死信队列处理

### 第二阶段：推送服务
1. 引入 RabbitMQ 消费消息
2. 实现短信通道适配（阿里云短信）
3. 实现邮件通道适配（SMTP）
4. 实现 App 推送通道（极光/华为推送）
5. 实现模板管理和渲染

### 第三阶段：对接与切换
1. 消息网关与上游业务对接
2. 推送服务与外部通道对接
3. 存量通知服务双写
4. 逐步切流，观察监控
5. 下线存量通知服务

### 任务分解

| 任务 | 负责人 | 依赖 |
|------|--------|------|
| Kafka 集群搭建 | backend-dev | 运维 |
| 消息网关核心开发 | backend-dev | Kafka |
| RabbitMQ 部署 | backend-dev | 运维 |
| 推送服务核心开发 | backend-dev | RabbitMQ |
| 短信通道对接 | backend-dev | 阿里云 |
| 邮件通道对接 | backend-dev | SMTP |
| 推送通道对接 | frontend-dev | 极光/华为 |
| 监控告警 | backend-dev | 全流程 |