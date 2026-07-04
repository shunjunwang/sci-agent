---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 0a3495d31457bedac983287cb94ad373_f88685c675ac11f19641525400d9a7a1
    ReservedCode1: tKL1yG0uRXhX1lBXOKmWtmMUmjrVYm/Z+m17QgHuB5huNmOIHohIjJZaUjkzoC29PElyZM2q7rAJubVw+ZoU7X1LUlhBRzyEMT3KbnRQY4b2BaQGxdweKypuvLvZe0i0ulsA4dV4VfnNgWE2khE3DsSsuE9M5gZQE5f9Rxzk7UyFrxHwRkzRHoSyorY=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 0a3495d31457bedac983287cb94ad373_f88685c675ac11f19641525400d9a7a1
    ReservedCode2: tKL1yG0uRXhX1lBXOKmWtmMUmjrVYm/Z+m17QgHuB5huNmOIHohIjJZaUjkzoC29PElyZM2q7rAJubVw+ZoU7X1LUlhBRzyEMT3KbnRQY4b2BaQGxdweKypuvLvZe0i0ulsA4dV4VfnNgWE2khE3DsSsuE9M5gZQE5f9Rxzk7UyFrxHwRkzRHoSyorY=
---

# AI_COLLABORATION.md — AI 协同开发规范

> 版本：v1.1 | 最后更新：2026-07-04
> 适用场景：1人 + 多AI Agent 协同开发
> 本文件是**所有AI Agent的协作契约**，违反者将被标记为不可靠Agent

---

## 1. 核心原则（铁律）

### 原则1：SPEC 是唯一真相源

- **任何代码生成前**，必须先读取 `docs/SPEC.md` 中相关模块的 API 契约和数据模型
- 生成的代码**必须**与 SPEC 中声明的端点、请求/响应格式、错误码完全一致
- 如果发现 SPEC 不完善，**先更新 SPEC 再写代码**，不允许"代码先行，文档后补"

### 原则2：不可越界修改

- 修改一个模块的代码**前**，必须声明是否影响其他模块
- **跨模块破坏性变更**（接口签名变动、数据模型字段增删、错误码修改）必须在 task 描述中显式列出影响范围
- 修改 Model 层**必须**同步生成 Alembic 迁移脚本

### 原则3：产物即证据

- 所有 AI 生成的代码**必须可追溯**：每个 PR 描述中标注本模块由哪个 Agent 生成、基于哪个 SPEC 版本
- 测试用例必须与 SPEC 的 API 端点一一对应
- 部署前必须通过本模块的验收 checklist

### 原则4：先跑通再优化

- 新模块开发遵循：**骨架 → 单接口跑通 → 全部接口 → 测试 → 优化**
- 不允许同时修改 3 个以上文件后直接提交，除非是批量重命名
- 每次提交应可独立运行、可独立回滚

### 原则5：类型即文档

- Python 后端：所有函数签名必须有**完整类型注解**，返回值用 `-> Type`
- TypeScript 前端：所有 interface/type 定义在 `lib/types/` 中，禁止 `any`（除非有注释说明原因）
- 类型文件与 SPEC 的数据模型保持一致

---

## 2. AI 开发契约

### 2.1 代码生成前置条件

```
[AI Agent 在生成任何代码前]
1. read_text("SPEC.md") → 定位目标模块
2. read_text("ARCHITECTURE.md") → 确认目录结构和命名规范
3. read_text("AI_COLLABORATION.md") → 本文档
4. 声明：我将实现 SPEC 第 X 章模块 Y 的以下端点：[列表]
5. 开始生成
```

### 2.2 跨模块修改声明

当修改涉及以下情况时，必须在 task 描述中声明：

| 变更类型 | 必须声明的模块 |
|---------|--------------|
| 新增/修改 API 端点 | 对应的前端页面、测试文件 |
| 新增/修改数据模型字段 | Alembic 迁移、Pydantic Schema、前端 types/ |
| 修改错误码 | SPEC.md 错误码表、前端错误处理 |
| 修改中间件 | 所有路由 |
| 新增依赖 (requirements.txt / package.json) | 无（自动列入） |

### 2.3 数据库变更铁律

```
数据库变更三步走：
1. 先修改 models/*.py（SQLAlchemy ORM 定义）
2. 再运行 alembic revision --autogenerate -m "描述"
3. 检查生成的迁移脚本，确认无误后提交
```

- **禁止**手动写 SQL 绕过 Alembic
- **禁止**修改已有 migration 文件（已提交的版本不可变）
- 新增 migration 必须在 PR 中附带前向/回滚测试

### 2.4 类型注解标准

**Python (FastAPI)**：
```python
# ✅ 正确
async def search_papers(
    q: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[PaperOut]:
    ...

# ❌ 错误
async def search_papers(q, page=1, page_size=20, db=None):
    ...
```

**TypeScript (Next.js)**：
```typescript
// ✅ 正确
interface PaperSearchParams {
  q: string;
  page?: number;
  page_size?: number;
}

async function searchPapers(params: PaperSearchParams): Promise<ApiResponse<PaginatedData<Paper>>> {
  ...
}

// ❌ 错误
async function searchPapers(params: any): any { ... }
```

---

## 3. 上下文传递规范

### 3.1 Task 格式标准

每个 AI Agent 接收的 task 必须包含两个字段：

```json
{
  "overall_goal": "项目全局目标（不变，跨轮传递）",
  "current_task": "本轮具体任务（精确到模块+端点+文件路径）"
}
```

**current_task 编写规范**：
```
[动作] + [模块] + [具体范围] + [产出物路径]

示例：
- "实现 M2 文献检索模块的 GET /api/v1/papers/search 端点，写入 backend/app/api/papers.py"
- "为 M1 用户体系的 auth_service.py 编写单元测试，覆盖率 ≥ 80%"
- "修复 M5 AI写作的溯源标注 bug：source_papers 字段为 null 时前端崩溃"
```

### 3.2 memory_ids 使用规则

| 场景 | 是否传 memory_ids | 传哪些 |
|------|------------------|--------|
| 同一模块的连续开发（如分步实现 M2） | ✅ 传 | 上一步的 memory_id |
| 不同模块的独立开发 | ❌ 不传 | 重新开始上下文 |
| 修复 Bug | ✅ 传 | 相关模块的最近 memory_id |
| 代码审查 / 重构 | ✅ 传 | 被审查代码的 memory_id |

### 3.3 inherit_agent_id 使用场景

`inherit_agent_id` 用于跨 Agent 继承工作上下文：

| 场景 | 是否继承 |
|------|---------|
| File Agent 搜索到文件 → 交接给 Coding Agent 写代码 | ✅ 继承 |
| 同一 Agent 连续执行子任务 | ✅ 自继承 |
| 任务完全独立（如同时开发前后端两个模块） | ❌ 不继承 |

### 3.4 会话间握手协议（Session Handshake）

不同 AI 会话之间靠三份文件握手，**新会话启动时必须执行此 Checklist**：

```
┌─────────────────────────────────────────────┐
│  AI Agent 新会话启动 Checklist                │
├─────────────────────────────────────────────┤
│  1. read_text("docs/ISSUE_TRACKER.md")       │
│     → 当前已知缺陷清单，知道"还没修什么"       │
│  2. read_text("SPEC.md")                     │
│     → API 契约真相源，知道"接口应该长什么样"   │
│  3. read_text("PROGRESS.md")                 │
│     → 进度看板，知道"哪些做完了哪些没做"       │
│  4. read_text("docs/adr/README.md")          │
│     → 架构决策记录，知道"为什么这么设计"       │
└─────────────────────────────────────────────┘
```

违反此 Checklist 的代价：重复造轮子、破坏已有接口、引入已修复过的 Bug。

---

## 4. 分支与提交规范

### 4.1 分支命名

```
module/<模块名>       # 新模块开发：module/paper-search
feat/<功能描述>       # 独立功能：feat/pdf-export
fix/<问题描述>        # Bug 修复：fix/token-refresh-loop
refactor/<范围>       # 重构：refactor/auth-service
docs/<内容>           # 文档更新：docs/api-examples
```

### 4.2 提交信息格式

```
<type>(<scope>): <subject>

[可选 body：详细说明变更原因和影响范围]

type: feat | fix | refactor | docs | test | chore
scope: backend | frontend | electron | docker | docs
```

示例：
```
feat(backend): 实现文献检索关键词搜索端点

- GET /api/v1/papers/search 支持 q/page/page_size 参数
- 对接科应API，结果缓存到本地 papers 表
- 新增 keying_client.py 含重试和熔断
```

### 4.3 合并前检查清单

- [ ] 代码通过本模块的单元测试
- [ ] 未引入新的 type errors（`mypy` / `tsc --noEmit`）
- [ ] 相关 SPEC 文档已同步更新
- [ ] 数据库变更附带了 Alembic migration
- [ ] PR 描述中标注了影响范围
- [ ] 无硬编码密钥/密码（统一走环境变量）

### 4.4 三文件闭环修改规则

任何代码变更完成后，必须自动检查以下三份文件是否需要同步更新，**不允许"稍后补"**：

| 变更类型 | 必须检查的文件 | 判断标准 |
|---------|--------------|---------|
| API 签名变更 | SPEC.md | 端点路径/请求参数/响应格式是否与 SPEC 一致 |
| 模块状态变更 | PROGRESS.md | 模块从"进行中"变为"已完成"时更新状态行 |
| Bug 修复 | ISSUE_TRACKER.md | 对应 ID 从 ⬜ 改为 ✅ |
| 架构决策 | docs/adr/ | 新增 ADR 记录决策原因和备选方案 |
| 数据模型字段变更 | SPEC.md + Alembic migration | 两者缺一不可 |

**执行时机**：AI Agent 在 `git commit` 之前，必须自查此表。pre-commit hook 不会帮你检查这个——这是 AI 的行为准则。

---

## 5. 模块开发顺序与依赖声明

```
依赖关系（箭头 = 被依赖方先完成）：

M0 基础设施 ──┬──→ M1 用户体系 ──→ M7 协作空间
              │                              │
              ├──→ M2 文献检索 ──→ M3 知识库 ──→ M5 AI写作
              │         │
              ├──→ M6 沙箱
              │
              └──→ M8 防篡改日志

M9 算法商城 ──→ 依赖 M1 + M6（第3波启动）
```

### 模块完成标准

| 阶段 | 完成标志 |
|------|---------|
| 骨架 | 目录创建、空文件、import 可运行 |
| 单接口 | 至少 1 个端点返回 200 真实响应 |
| 全部 | 模块所有 API 端点可调用、返回正确 |
| 测试 | 覆盖率 ≥ 80%、集成测试通过 |
| 验收 | SPEC checklist 该模块全部打勾 |

---

## 6. 验收标准

### 6.1 每个模块 PR 前必须通过

| 检查项 | 工具/方法 |
|--------|----------|
| Python type check | `mypy backend/app/ --strict` |
| TypeScript type check | `tsc --noEmit` |
| 后端 lint | `ruff check backend/app/` |
| 前端 lint | `eslint frontend/` |
| 单元测试 | `pytest backend/tests/ -x -q` |
| 前端测试 | `npm test -- --passWithNoTests` |
| API 响应格式校验 | 比对 SPEC 中声明的响应 JSON 结构 |

### 6.2 不符合标准时的处理

- type/lint 错误 → **立即修复**，不允许忽略注释
- 测试失败 → **回退到上一稳定版本**，重新分析
- API 格式不一致 → **先更新 SPEC 或修正代码**

---

## 7. AI 开发守则（禁止事项）

以下行为被**严格禁止**，违反即视为 Agent 失控：

| 编号 | 禁止行为 | 后果 |
|------|---------|------|
| ❌ 1 | 不读 SPEC 直接写代码 | 生成代码作废 |
| ❌ 2 | 修改 Model 不生成迁移脚本 | 阻塞其他 Agent |
| ❌ 3 | 使用 `Any` 类型绕过类型检查 | PR 拒绝 |
| ❌ 4 | 硬编码密钥/密码/地址 | 安全漏洞 |
| ❌ 5 | 删除或覆盖其他 Agent 的代码文件（除非声明影响范围并获确认） | 冲突回滚 |
| ❌ 6 | 修改 `common.py` / `base.py` 等公共模块不通知 | 全线报错 |
| ❌ 7 | 绕过 SPEC 声明的错误码，自创错误返回格式 | 前端解析失败 |
| ❌ 8 | 提交包含 `print()` / `console.log()` 的调试代码 | 降低代码质量 |
| ❌ 9 | 单个 PR 包含超过 500 行新增代码（不含测试和迁移） | 审查困难 |
| ❌ 10 | 删除或禁用现有测试以通过 CI | 掩盖问题 |

---

## 8. 日常协作流程

```
┌─────────────────────────────────────────────────────────┐
│  人类开发者（1人）                                        │
│  │                                                       │
│  │ 发布任务 (overall_goal + current_task)                 │
│  ▼                                                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │               AI Agent Pool                       │   │
│  │                                                   │   │
│  │   File Agent    Coding Agent    Test Agent        │   │
│  │   (读SPEC/搜索)  (写代码)        (写测试)          │   │
│  │       │              │              │             │   │
│  │       └──────┬───────┴──────┬───────┘             │   │
│  │              │              │                     │   │
│  │              ▼              ▼                     │   │
│  │          Git Commit + PR                          │   │
│  │              │                                    │   │
│  │              ▼                                    │   │
│  │          CI: lint + test + type check             │   │
│  │              │                                    │   │
│  │         ┌────┴────┐                               │   │
│  │         ▼         ▼                               │   │
│  │      通过       失败 → 回退给对应 Agent 修复      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  每周 Review：                                              │
│  - SPEC 与实际代码一致性检查                                │
│  - PROGRESS.md 更新                                        │
│  - RISK_MANAGEMENT.md 复查                                 │
└─────────────────────────────────────────────────────────┘
```

---

*本文档是 sci-agent 项目多 AI 协作的宪法级文件，所有 Agent 在开始任何开发任务前必须全文阅读。*
*（内容由AI生成，仅供参考）*

---

## 变更记录

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v1.1 | 2026-07-04 | 修正 §2.1 代码生成前置条件的幽灵路径（`docs/` → 根目录）；新增质量门禁协作规范：所有 P0-P3 级变更必须同步更新 ISSUE_TRACKER.md 和 PROGRESS.md；pre-commit + CI 门禁落地后的 Agent 职责明确 |
| v1.0 | 2026-07-02 | 初始版本：三文件闭环修改规则、Task 格式、分支命名、代码规范铁律 |
