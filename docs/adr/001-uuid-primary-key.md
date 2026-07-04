# ADR-001: 主键策略 — UUID vs BIGSERIAL

- **状态**：已决定
- **日期**：2026-07-04
- **决策者**：人 + AI
- **关联 ISSUE**：P1-21

## 上下文

SPEC 最初要求使用 PostgreSQL BIGSERIAL 自增主键（性能更好、索引更小），但实际实现中全部使用了 UUID（UniversalUUID 类型）。在代码审查中暴露了这个分歧。

## 选项

| 选项 | 优点 | 缺点 |
|------|------|------|
| A: 迁移到 BIGSERIAL | 索引更小、查询更快、与 SPEC 一致 | 需要改全部模型 + 外键 + 迁移脚本，风险极高 |
| B: 保留 UUID | 分布式友好、防 ID 枚举、无需改代码 | 索引体积大、查询略慢 |

## 决策

选择 **B：保留 UUID**，并更新 SPEC.md 以反映这一决策。

理由：
1. UUID 天然防 ID 枚举攻击，更适合 SaaS 多租户场景
2. UniversalUUID 兼容层已在 SQLite 和 PostgreSQL 双环境下验证通过
3. BIGSERIAL 迁移的成本（修改 14+ 模型、所有外键、API 响应格式）远超收益

## 后果

- SPEC.md 主键类型字段已更新为 UUID
- 未来切换 PostgreSQL 时，UUID 类型可直接映射，无需迁移
- 需关注 UUID 索引性能，必要时添加 `uuid_generate_v4()` 辅助索引
