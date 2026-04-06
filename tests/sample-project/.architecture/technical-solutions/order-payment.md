# 电商平台双通道支付模块技术方案

## 概述

### 项目背景

为电商平台新增微信和支付宝双通道支付模块，需要支持退款、对账、异步回调，同时不影响现有订单流程。本方案将支付模块设计为独立微服务，通过消息队列与订单服务解耦，确保支付功能的高可用性和可扩展性。

### 核心需求

| 需求类型 | 具体描述 | 优先级 |
|----------|----------|--------|
| 支付通道 | 支持微信支付（Native/JSAPI/APP）和支付宝（当面付/手机支付） | P0 |
| 退款功能 | 支持部分退款和全额退款，退款原路返回 | P0 |
| 对账功能 | T+1 日终对账，支持差异检测和告警 | P1 |
| 异步回调 | 支付结果通过异步回调通知，确保最终一致性 | P0 |
| 订单解耦 | 不修改现有订单流程，通过事件驱动更新 | P0 |

### 设计目标

- **高可用**：支付服务独立部署，支持通道降级
- **可扩展**：通道路由可配置，新增通道易于扩展
- **安全性**：签名验签、密钥隔离、完整的审计日志
- **一致性**：支付幂等性设计，消息队列确保最终一致

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端应用                               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   订单服务      │  │   支付服务      │  │   通知服务      │
│  (Order Svc)   │  │ (Payment Svc)   │  │ (Notify Svc)    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         │    ┌───────────────┼───────────────┐    │
         │    │               │               │    │
         ▼    ▼               ▼               ▼    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Kafka 消息队列                              │
└──────────────┬──────────────────┬──────────────────┬───────────┘
               │                  │                  │
               ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    微信支付      │  │    支付宝        │  │    对账服务      │
│   (WeChat Pay)  │  │   (Alipay)      │  │ (Reconciliation) │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 模块定位

支付模块为独立微服务，承载以下四大职责：

| 职责 | 说明 |
|------|------|
| 统一收银台 | 聚合微信/支付宝两大通道，提供一致的支付体验 |
| 通道路由 | 根据用户选择的通道或系统策略路由到对应渠道 |
| 退款处理 | 处理退款请求，支持部分退款和全额退款 |
| 对账清算 | 每日对账，生成差异报告并告警 |

### 核心组件设计

#### 1. Payment Gateway（统一收银台）

- **职责**：聚合多个支付通道，提供统一的支付接口
- **位置**：支付服务内部
- **接口**：`POST /api/payment/create`

#### 2. Channel Router（通道路由器）

- **职责**：根据通道标识或系统策略选择支付渠道
- **策略**：权重路由、通道可用性检查、降级策略

#### 3. Refund Service（退款服务）

- **职责**：处理退款请求，校验退款条件，执行退款操作
- **约束**：仅支持原通道退款，需校验支付状态

#### 4. Reconciliation Service（对账服务）

- **职责**：T+1 日终拉取对账文件，比对系统记录与通道记录
- **输出**：对账差异报告、告警通知

### 数据模型

#### PaymentOrder（支付订单）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| order_id | VARCHAR(64) | 电商订单号（唯一索引） |
| payment_id | VARCHAR(64) | 支付单号（通道侧） |
| channel | ENUM | 支付通道：WECHAT/ALIPAY |
| channel_type | VARCHAR(32) | 通道类型：NATIVE/JSAPI/APP/AP |
| amount | DECIMAL(12,2) | 支付金额 |
| currency | VARCHAR(8) | 币种，默认 CNY |
| status | ENUM | 支付状态：PENDING/SUCCESS/FAILED/CLOSED |
| callback_url | VARCHAR(256) | 异步回调地址 |
| extra | JSON | 扩展字段（平台自定义数据） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### RefundRecord（退款记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| payment_id | VARCHAR(64) | 关联支付单号 |
| refund_id | VARCHAR(64) | 退款单号 |
| refund_amount | DECIMAL(12,2) | 退款金额 |
| refund_reason | VARCHAR(256) | 退款原因 |
| refund_type | ENUM | 退款类型：FULL/PARTIAL |
| status | ENUM | 退款状态：PENDING/SUCCESS/FAILED |
| operator | VARCHAR(64) | 操作员 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### ReconciliationLog（对账日志）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| check_date | DATE | 对账日期 |
| channel | ENUM | 支付通道 |
| total_amount | DECIMAL(14,2) | 通道总金额 |
| total_count | INT | 交易笔数 |
| sys_amount | DECIMAL(14,2) | 系统总金额 |
| sys_count | INT | 系统笔数 |
| diff_amount | DECIMAL(14,2) | 差异金额 |
| diff_count | INT | 差异笔数 |
| status | ENUM | 对账状态：PENDING/CHECKED/DIFF_FOUND |
| report_url | VARCHAR(256) | 对账报告文件地址 |
| created_at | DATETIME | 创建时间 |

### 集成方式

| 集成点 | 方式 | 说明 |
|--------|------|------|
| 订单服务 | Kafka 消息队列 | 支付状态变更事件异步通知 |
| 支付通道 | HTTP API | 微信/支付宝开放平台 API |
| 对账文件 | SFTP/API | 定时拉取通道侧对账文件 |
| 监控告警 | 消息通知 | 对账差异、支付异常告警 |

---

## 实现方案

### 技术选型

| 组件 | 技术栈 | 版本 |
|------|--------|------|
| 服务框架 | Spring Boot | 2.7.x |
| 消息队列 | Apache Kafka | 3.x |
| 数据库 | MySQL 8.0 | 8.0 |
| 连接池 | Druid | 1.2.x |
| 微信 SDK | wechatpay-apache-httpclient | 1.4.x |
| 支付宝 SDK | alipay-sdk-java | 4.35.x |
| 定时任务 | XXL-Job | 2.3.x |

### 项目结构

```
payment-service/
├── src/main/java/com/ecommerce/payment/
│   ├── PaymentApplication.java
│   ├── config/
│   │   ├── WeChatPayConfig.java
│   │   ├── AlipayConfig.java
│   │   └── KafkaConfig.java
│   ├── controller/
│   │   ├── PaymentController.java
│   │   └── RefundController.java
│   ├── service/
│   │   ├── PaymentService.java
│   │   ├── ChannelRouter.java
│   │   ├── WeChatPayService.java
│   │   ├── AlipayService.java
│   │   ├── RefundService.java
│   │   └── ReconciliationService.java
│   ├── repository/
│   │   ├── PaymentOrderRepository.java
│   │   ├── RefundRecordRepository.java
│   │   └── ReconciliationLogRepository.java
│   ├── entity/
│   │   ├── PaymentOrder.java
│   │   ├── RefundRecord.java
│   │   └── ReconciliationLog.java
│   ├── dto/
│   │   ├── PaymentRequest.java
│   │   ├── PaymentResponse.java
│   │   ├── RefundRequest.java
│   │   └── RefundResponse.java
│   ├── event/
│   │   ├── PaymentSuccessEvent.java
│   │   └── PaymentFailedEvent.java
│   ├── listener/
│   │   └── PaymentCallbackListener.java
│   ├── job/
│   │   └── ReconciliationJob.java
│   └── util/
│       ├── SignatureUtil.java
│       └── JsonUtil.java
├── src/main/resources/
│   ├── application.yml
│   ├── mapper/
│   │   └── *.xml
│   └── sql/
│       └── init.sql
└── pom.xml
```

### 核心接口设计

#### 1. 创建支付订单

```
POST /api/payment/create
Content-Type: application/json

请求体：
{
  "orderId": "E202604060001",
  "channel": "WECHAT",
  "channelType": "NATIVE",
  "amount": 99.50,
  "currency": "CNY",
  "callbackUrl": "https://api.ecommerce.com/payment/callback",
  "subject": "商品订单支付",
  "extra": {}
}

响应体：
{
  "code": 0,
  "message": "success",
  "data": {
    "paymentId": "P2026040600001",
    "orderId": "E202604060001",
    "channel": "WECHAT",
    "payUrl": "weixin://wxpay/bizpayurl?pr=xxxxx",
    "qrCode": "https://api.qrserver.com/v1/create-qr-code?...",
    "expireTime": "2026-04-06T15:00:00+08:00"
  }
}
```

#### 2. 支付回调

```
POST /api/payment/callback/{channel}
Content-Type: application/x-www-form-urlencoded

微信回调参数：
- return_code: SUCCESS/FAIL
- return_msg: 返回信息
- result_code: SUCCESS/FAIL
- mch_id: 商户号
- out_trade_no: 商户订单号
- transaction_id: 微信订单号
- total_fee: 订单金额（分）
- cash_fee: 现金支付金额
- time_end: 支付时间

支付宝回调参数：
- trade_status: TRADE_SUCCESS/TRADE_FINISHED
- out_trade_no: 商户订单号
- trade_no: 支付宝交易号
- total_amount: 订单金额
- gmt_payment: 支付时间
```

#### 3. 退款申请

```
POST /api/payment/refund
Content-Type: application/json

请求体：
{
  "paymentId": "P2026040600001",
  "refundAmount": 50.00,
  "refundReason": "用户申请取消订单",
  "operator": "admin001"
}

响应体：
{
  "code": 0,
  "message": "success",
  "data": {
    "refundId": "R2026040600001",
    "paymentId": "P2026040600001",
    "refundAmount": 50.00,
    "status": "PENDING",
    "createdAt": "2026-04-06T14:30:00+08:00"
  }
}
```

### 业务流程

#### 支付流程

```
1. 用户选择支付方式，提交支付请求
2. 支付服务创建 PaymentOrder，状态为 PENDING
3. ChannelRouter 根据 channel 选择对应支付渠道
4. 调用通道预下单接口，获取支付链接/二维码
5. 返回支付信息给客户端
6. 用户完成支付
7. 支付通道发起异步回调
8. 支付服务验证签名，更新 PaymentOrder 状态为 SUCCESS
9. 发送 PaymentSuccessEvent 到 Kafka
10. 订单服务消费事件，更新订单状态
```

#### 退款流程

```
1. 用户/管理员发起退款请求
2. 退款服务校验：
   - 支付状态是否为 SUCCESS
   - 退款金额是否超过可退金额
   - 是否存在进行中的退款
3. 创建 RefundRecord，状态为 PENDING
4. 调用通道退款接口
5. 等待通道返回退款结果
6. 更新 RefundRecord 状态
7. 发送退款结果通知
```

#### 对账流程

```
1. XXL-Job 定时任务每日凌晨执行
2. 拉取前一日（T+1）对账文件
   - 微信：下载微信支付对账文件
   - 支付宝：下载支付宝对账文件
3. 解析对账文件，与系统记录比对
4. 生成 ReconciliationLog
5. 如有差异，生成差异报告并告警
6. 差异数据进入人工处理流程
```

### 兼容性设计

| 设计点 | 方案 |
|--------|------|
| 订单解耦 | 支付结果通过 Kafka 消息通知订单服务，订单服务无需同步等待 |
| 现有流程 | 现有订单流程无需修改，通过事件驱动更新订单状态 |
| 服务部署 | 支付服务独立部署，不影响主业务可用性 |
| 通道降级 | 当某个通道不可用时，自动切换到备用通道 |

---

## 风险评估

### 风险矩阵

| 风险项 | 概率 | 影响 | 风险等级 | 缓解措施 |
|--------|------|------|----------|----------|
| 支付通道不可用 | 中 | 高 | 高 | 通道降级策略，支付宝/微信互为备份 |
| 重复支付 | 低 | 高 | 高 | 支付幂等性设计，订单号唯一约束 |
| 回调超时/丢失 | 中 | 中 | 中 | 回调重试机制（最大3次）+ 主动查询补偿 |
| 对账差异 | 中 | 中 | 中 | T+1 差异告警，人工介入处理流程 |
| 资金安全风险 | 低 | 极高 | 极高 | 签名验签、密钥隔离、完整审计日志 |
| 数据库单点 | 低 | 高 | 高 | 主从复制 + 读写分离架构 |
| 消息丢失 | 低 | 中 | 中 | Kafka 消息持久化 + 消费确认机制 |

### 资金安全保障措施

1. **签名验签机制**
   - 微信支付：使用 RSA256 签名验证回调请求
   - 支付宝：使用 RSA2 签名验证回调请求
   - 所有接口请求必须携带签名

2. **密钥管理**
   - 微信/支付宝密钥存储在配置中心（HashiCorp Vault）
   - 生产环境密钥不硬编码
   - 密钥轮换机制（每90天）

3. **审计日志**
   - 记录所有支付、退款操作
   - 日志保留期限：2年
   - 敏感字段脱敏存储

4. **风控规则**
   - 单笔支付限额：单账号单笔最高 50000 CNY
   - 日累计限额：单账号日累计最高 100000 CNY
   - 异常交易监控：短时间多笔小额交易告警

### 应急响应预案

| 场景 | 响应措施 |
|------|----------|
| 微信支付通道不可用 | 立即切换到支付宝通道，通过配置中心开关控制 |
| 大量回调超时 | 触发主动查询补偿任务，批量查询支付状态 |
| 对账差异超过阈值 | 暂停当日结算，通知财务人员人工处理 |
| 数据库故障 | 切换到从库，继续提供查询服务，降级写操作 |

### 监控指标

| 指标 | 阈值 | 告警方式 |
|------|------|----------|
| 支付成功率 | < 95% | 短信+邮件 |
| 回调失败率 | > 1% | 短信+邮件 |
| 对账差异率 | > 0.1% | 邮件 |
| 接口响应时间 | P99 > 500ms | 钉钉机器人 |
| 队列积压 | > 1000 | 短信 |