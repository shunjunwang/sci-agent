# ADR-003: 代码沙箱 — subprocess vs Docker

- **状态**：已决定
- **日期**：2026-07-04
- **决策者**：人 + AI
- **关联 ISSUE**：P0-01

## 上下文

M6 沙箱模块最初使用 `subprocess.run` 裸执行任意代码，存在严重安全风险（可读取环境变量、访问文件系统、网络调用）。这是一个典型的"快速原型变成生产代码"的问题。

## 选项

| 选项 | 优点 | 缺点 |
|------|------|------|
| A: subprocess + 白名单 | 零依赖、启动快 | 安全边界不可靠、易绕过 |
| B: Docker 隔离 | 真正的进程级隔离、资源限制 | 需要 Docker 环境、启动慢 |
| C: Firecracker microVM | 最强隔离、AWS 生产验证 | 依赖复杂、Windows 不支持 |

## 决策

选择 **B：Docker 隔离执行**，不可用时拒绝请求返回 InternalServerError。

理由：
1. 项目已依赖 Docker（docker-compose.yml），不引入新依赖
2. 进程级隔离是代码执行的最低安全基线
3. 可在 Dockerfile 中预装 Python/R/Julia 运行时

## 后果

- `api/v6/sandbox.py` 从 subprocess 改为 Docker SDK 调用
- 用户环境需要 Docker Desktop 运行中
- 每个执行请求启动新容器，有 ~2s 冷启动开销
- 后续可研究容器预热池优化
