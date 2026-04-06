# Session 鉴权迁移到 JWT 方案

## 概述

将现有 Session 鉴权迁移到 JWT，实现无状态认证。需要保持现有登录接口兼容，用户无需重新登录。

## Session vs JWT 对比

| 维度 | Session | JWT |
|------|---------|-----|
| 存储方式 | 服务端 Session 存储 | 客户端 Token 自包含 |
| 扩展性 | 需共享 Session 存储（如 Redis） | 无状态，可水平扩展 |
| 失效机制 | 服务端主动失效 | 过期自动失效 |
| 性能 | 每次请求需验证 Session ID | 无需服务端存储验证 |
| 适用场景 | 有状态服务、单体应用 | 微服务、分布式系统 |

## 迁移方案

### 阶段一：双轨制并行
1. 登录接口同时返回 Session 和 JWT
2. 验证中间件支持双模式识别
3. 存量 Session 用户静默续签为 JWT

### 阶段二：逐步切换
1. 前端切换存储从 Session 到 JWT
2. 旧版 Session 逐步过期
3. 下线 Session 相关代码

### 阶段三：完全迁移
1. 移除 Session 验证逻辑
2. 清理 Redis Session 存储
3. 仅保留 JWT 验证

## 兼容性设计

### 接口兼容
- 登录接口保持现有返回格式，增加 token 字段
- 请求头区分：Authorization: Bearer \<token\>
- 双模式自动降级，优先使用 JWT

### 存量用户处理
- 首次访问时静默颁发 JWT
- Session 与 JWT 并行期设置 30 天
- 迁移窗口期后强制下线 Session

## 风险控制

| 风险项 | 影响 | 缓解措施 |
|--------|------|----------|
| Token 泄露 | 高 | HTTPS 传输，short-lived accessToken + refreshToken |
| 无法主动失效 | 中 | 黑名单机制或短过期时间 |
| 迁移期间双模式复杂度 | 低 | 设定明确迁移窗口期 |