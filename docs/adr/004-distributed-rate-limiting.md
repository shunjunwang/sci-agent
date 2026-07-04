# ADR-004: 限流引擎 — 内存 vs Redis 分布式

- **状态**：已决定
- **日期**：2026-07-04
- **决策者**：人 + AI
- **关联 ISSUE**：P1-16

## 上下文

原限流实现使用内存令牌桶，在多 worker 部署下失效（每个 worker 独立计数，实际限流失效）。项目当前是单 worker 开发模式，但 SPEC 要求支持生产级多 worker 部署。

## 选项

| 选项 | 优点 | 缺点 |
|------|------|------|
| A: 保持内存令牌桶 | 零依赖、开发简单 | 多 worker 下完全失效 |
| B: Redis Lua 脚本 | 原子性保证、多 worker 一致 | 需要 Redis 依赖 |
| C: 外部 API 网关限流 | 运维最简单 | 引入外部依赖、成本增加 |

## 决策

选择 **B：Redis Lua 脚本实现分布式令牌桶**。

Lua 脚本保证令牌桶操作的原子性（get + compare + incr 三步合一），解决多 worker 下的竞态问题。

## 后果

- `core/rate_limit.py` 重写，使用 Redis Lua 脚本
- 新增 Redis 依赖（但项目本身已有 Redis 规划用于缓存/会话）
- 单机开发时可用内存令牌桶降级（redis 不可用时自动回退）
- 限流响应格式统一为 SPEC 规定的 `{code: 1004, data: {retry_after: N}}`
