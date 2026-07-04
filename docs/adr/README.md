# ADR — 架构决策记录

> 目录索引。每个决策一个文件，记录上下文 + 选项 + 决策 + 后果。
> 新 AI 会话启动时先读本目录，理解"为什么这么设计"。

## ADR 索引 (docs/adr/)

| 编号 | 标题 | 日期 | 状态 |
|------|------|------|------|
| [001](001-uuid-primary-key.md) | 主键策略：UUID vs BIGSERIAL | 2026-07-04 | 已决定 |
| [002](002-encryption-dual-backend.md) | 加密算法：Fernet + AES-256-GCM 双后端 | 2026-07-04 | 已决定 |
| [003](003-sandbox-isolation.md) | 代码沙箱：subprocess vs Docker | 2026-07-04 | 已决定 |
| [004](004-distributed-rate-limiting.md) | 限流引擎：内存 vs Redis 分布式 | 2026-07-04 | 已决定 |
| [005](005-frontend-api-communication.md) | 前端 API 通信方式 | 2026-07-04 | 已决定 |
| [006](006-pgvector-dimension.md) | pgvector 向量维度与模型选择 | 2026-07-04 | 已决定 |

## ARCHITECTURE.md 第 8 节 ADR 与 docs/adr/ 交叉引用

> **注意**：当前项目存在两套 ADR 编号体系共存。ARCHITECTURE.md 第 8 节使用业务决策编号，docs/adr/ 文件使用技术实现编号。以下为交叉引用表。

| ARCHITECTURE.md §8 ADR | 业务决策 | docs/adr/ 文件 | 技术实现 |
|------------------------|---------|---------------|---------|
| ADR-001 | 文献数据入库策略（懒加载缓存） | 001-uuid-primary-key.md | 主键策略：UUID vs BIGSERIAL |
| ADR-002 | AI 写作输出格式（Markdown） | 002-encryption-dual-backend.md | 加密算法：Fernet + AES-256-GCM |
| ADR-003 | C 盘空间不足应对（迁移到 D 盘） | 003-sandbox-isolation.md | 代码沙箱：subprocess vs Docker |
| ADR-004 | 防篡改日志方案（应用层哈希链） | 004-distributed-rate-limiting.md | 限流引擎：内存 vs Redis |
| ADR-005 | 前端 API 通信方式（BFF + 直连混合） | 005-frontend-api-communication.md | 前端 API 通信方式 |
| ADR-006 | pgvector 向量维度与模型选择（OpenAI 1536d） | 006-pgvector-dimension.md | pgvector 向量维度与模型选择 |

**编号含义**：
- ARCHITECTURE.md §8 的编号按决策时间顺序（1-6），描述**业务层面**的架构决策
- docs/adr/ 文件编号按创建顺序（1-6），描述**技术实现层面**的架构决策
- ADR-005 和 ADR-006 两套编号描述同一决策，因此保持一致
- 引用时建议优先使用 `ARCHITECTURE.md 第 8 节 ADR-N` 的表述以避免歧义

## 模板

新建 ADR 时复制以下结构：

```markdown
# ADR-XXX: 标题

- **状态**：提议 / 已决定 / 已废弃
- **日期**：YYYY-MM-DD
- **决策者**：人 + AI

## 上下文

（为什么要做这个决策？技术约束、业务需求、之前的问题）

## 选项

| 选项 | 优点 | 缺点 |
|------|------|------|
| A | ... | ... |
| B | ... | ... |

## 决策

选择了 X，因为...

## 后果

（正面和负面后果，以及需要跟进的事项）
```

## 模板

新建 ADR 时复制以下结构：

```markdown
# ADR-XXX: 标题

- **状态**：提议 / 已决定 / 已废弃
- **日期**：YYYY-MM-DD
- **决策者**：人 + AI

## 上下文

（为什么要做这个决策？技术约束、业务需求、之前的问题）

## 选项

| 选项 | 优点 | 缺点 |
|------|------|------|
| A | ... | ... |
| B | ... | ... |

## 决策

选择了 X，因为...

## 后果

（正面和负面后果，以及需要跟进的事项）
```
