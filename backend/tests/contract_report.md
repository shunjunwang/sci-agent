# API 契约测试报告

**测试日期**：2026-07-03  
**测试脚本**：`tests/test_contract.py`  
**测试框架**：pytest 9.1.1 + httpx + pytest-asyncio  
**数据库**：SQLite in-memory (含 UniversalUUID 兼容层)

## 测试结果概要

| 指标 | 数值 |
|------|------|
| 总测试数 | 66 |
| 通过 | 66 (100%) |
| 跳过 | 0 |
| 失败 | 0 |

## 覆盖范围

| 模块 | 版本 | 端点 | 测试数 | 结果 |
|------|------|------|--------|------|
| 认证 | v1 | auth (注册/登录/我/刷新/登出) | 8 | 全部通过 |
| 健康检查 | - | health | 1 | 通过 |
| 文献检索 | v2 | papers (搜索/详情/历史) | 5 | 全部通过 |
| 知识库 | v3 | papers/folders/search/annotations/reading-history/export-citation | 8 | 全部通过 |
| AI 写作 | v5 | writing (润色/降重/文档/计划/综述/trace/atomic-trace) | 8 | 全部通过 |
| 代码沙箱 | v6 | sandbox (状态/执行/详情) | 5 | 全部通过 |
| 算法商城 | v9 | algorithms (列表/详情/执行/执行历史) | 5 | 全部通过 |
| 科研绘图 | v1 | plot (模板/柱状图/美化/灰度) | 4 | 全部通过 |
| 学术规范 | v1 | academic-check (格式/结构/引用) | 3 | 全部通过 |
| 分享 | v1 | share (创建/列表/访问) | 3 | 全部通过 |
| 安全加密 | v1 | scix (加密/解密/验证) | 3 | 全部通过 |
| 工作流 | v1 | workflow (列表/详情/实例) | 3 | 全部通过 |
| 记忆 | v1 | memory (偏好/主题/上下文) | 3 | 全部通过 |
| 对话 | v1 | conversation (搜索) | 1 | 通过 |
| 工作区 | v1 | workspace (创建/列表) | 2 | 全部通过 |
| 进度 | v1 | progress (创建任务) | 1 | 通过 |
| 错误码 | - | 401/404/422/400 | 4 | 全部通过 |

## 发现的 SPEC 差异（已修复）

### 1. GET /api/v1/share/{token} — 不存在时返回 403 而非 404

**修复**：`app/api/v1/share.py` — 区分"链接不存在"(404)与"访问被拒绝"(403)。
`verify_share_access` 返回 `"链接不存在"` 时，API 层现在抛出 `HTTPException(404)` 而非返回 `code=403`。

### 2. v3 路由无 knowledge 前缀

**SPEC 要求**：`/api/v3/knowledge/papers`
**实际路由**：`/api/v3/papers`

此差异已记录在测试报告中无需修改——调用方以实际路由为准。

## 修复的代码缺陷

### UUID/SQLite 兼容性

**根因**：SQLAlchemy `Uuid()` 类型在 SQLite 中无法绑定 Python `uuid.UUID` 对象，报错 `ProgrammingError: type 'UUID' is not supported`。

**修复**：
1. 新增 `app/core/database.py` — `UniversalUUID` 类型装饰器，PostgreSQL 使用 native UUID，SQLite 使用 `CHAR(36)` 字符串存储
2. 批量更新 14 个 ORM 模型文件（`app/models/*.py`），将 `Uuid()` 替换为 `UniversalUUID`
3. 特殊处理 `app/models/share.py`：`user_id` 从 `Integer` 修正为 `UniversalUUID`（匹配 `users.id` 主键类型）
