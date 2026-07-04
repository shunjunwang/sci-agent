# ADR-005：前端与后端 API 通信方式

> **状态**: 已采纳  
> **日期**: 2026-07-02  
> **来源**: ARCHITECTURE.md 第 8 节 ADR-005

## 背景

Next.js 前端需要与 FastAPI 后端通信。需决定是直接调用还是通过中间层代理。

## 选项

| 选项 | 方案 | 优点 | 缺点 |
|------|------|------|------|
| A | 前端直连 FastAPI | 简单、零额外开销 | 无服务端密钥保护 |
| B | Next.js API Route 代理 | 密钥安全、可添加 BFF 逻辑 | 增加延迟、维护成本 |
| C | BFF + 直连混合 | 兼顾性能与安全 | 需明确分工规则 |

## 结论

**选 C（BFF + 直连混合）**。

- **开发阶段**：前端 dev server 通过 `next.config.js` rewrites 直连 `localhost:8000`
- **生产 Electron 环境**：直连本地后端（`localhost:8000`）
- **Next.js API Route**：仅用于需要服务端密钥的场景（如 OAuth callback）

## 影响

- 前端无需 CORS 复杂配置（开发 rewrites 解决）
- OAuth 等敏感流程通过 Next.js API Route 保护密钥
- 常规 API 调用走直连，保持低延迟
