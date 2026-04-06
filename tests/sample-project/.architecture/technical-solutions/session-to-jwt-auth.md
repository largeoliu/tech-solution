# Session 鉴权迁移到 JWT 方案

## 概述

将现有 Session 鉴权迁移到 JWT，实现无状态认证。需要保持现有登录接口兼容，用户无需重新登录。迁移期间支持 Session 和 JWT 双模式，逐步切流确保平滑过渡。

## 架构设计

### 认证方式对比
| 维度 | Session | JWT |
|------|---------|-----|
| 存储 | 服务端 Session | 客户端 Token |
| 扩展性 | 需共享 Session 存储 | 无状态，可水平扩展 |
| 失效机制 | 服务端主动失效 | 过期自动失效 |
| 适用场景 | 有状态服务 | 微服务、分布式系统 |

### 迁移路径选择：改造现有系统
**结论：采用 JWT 改造方案，理由如下：**
- 现有系统为微服务架构，Session 共享需要引入 Redis，增加运维复杂度
- JWT 可实现真正的无状态认证，横向扩展更简单
- 现有登录接口保持不变，仅变更 token 生成和验证逻辑

### 新旧系统兼容性
- 登录接口同时支持返回 Session 和 JWT
- 验证中间件支持双模式识别，自动降级
- 存量 Session 用户静默续签为 JWT

## 实现方案

### 第一阶段：JWT 生成与验证
1. 引入 JJWT 库，配置签名密钥（HS256）
2. 登录成功后生成 JWT，Claims 包含 userId, roles, exp
3. 新增 JWT 验证中间件，拦截受保护路由
4. 保留 Session 验证逻辑，双模式并行

### 第二阶段：接口兼容
1. 现有登录接口返回格式增加 token 字段
2. 前端逐步切换存储从 Session 到 JWT
3. 迁移期间通过请求头区分：Authorization: Bearer <token>

### 第三阶段：存量用户迁移
1. 存量 Session 用户首次访问时静默颁发 JWT
2. Session 逐步过期，最终全部切换到 JWT
3. 下线 Session 相关代码和 Redis 存储

### 任务分解
| 任务 | 负责人 | 依赖 |
|------|--------|------|
| JWT 工具类开发 | backend-dev | 无 |
| 登录接口改造 | backend-dev | JWT 工具类 |
| 验证中间件 | backend-dev | JWT 工具类 |
| 前端 token 存储 | frontend-dev | 登录接口 |
| 存量迁移脚本 | backend-dev | 验证中间件 |
| 监控指标埋点 | backend-dev | 全流程 |

## 风险评估

| 风险项 | 影响 | 缓解措施 |
|--------|------|----------|
| Token 泄露 | 高 | HTTPS 传输，refreshToken 定期轮换 |
| 无法主动失效 | 中 | short-lived accessToken + refreshToken 机制 |
| 密码修改后 Token 仍有效 | 中 | 黑名单机制或短过期时间 |
| 迁移期间双模式复杂度 | 低 | 设定迁移窗口期，过期后下线 Session |
