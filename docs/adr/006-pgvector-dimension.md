# ADR-006：pgvector 向量维度与 Embedding 模型选择

> **状态**: 已采纳  
> **日期**: 2026-07-02  
> **来源**: ARCHITECTURE.md 第 8 节 ADR-006

## 背景

文献 embedding 用于语义检索和相似文献推荐。需选定向量维度和 embedding 模型。

## 选项

| 选项 | 方案 | 维度 | 优点 | 缺点 |
|------|------|------|------|------|
| A | OpenAI text-embedding-3-small | 1536d | 质量高、零运维 | 外部 API 依赖、成本 |
| B | 本地 bge-large-zh-v1.5 | 1024d | 无外部依赖、中文优化 | 需 GPU/内存、维度不同 |
| C | 科应 API 自带向量 | — | 无需本地计算 | 绑定单一数据源 |

## 结论

**选 A**，架构预留 **B/C** 切换能力。

- pgvector 列定义为 `vector(1536)`
- `EmbeddingService` 抽象接口支持多后端
- 配置切换：`EMBEDDING_BACKEND=openai|local|keying`

## 影响

- 初始使用 OpenAI（1536 维），后续可切换本地模型时需数据迁移
- 抽象层（`EmbeddingService`）降低切换成本
- 代码中避免硬编码维度值，统一从配置读取
