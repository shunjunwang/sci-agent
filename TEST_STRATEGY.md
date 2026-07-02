---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 0a3495d31457bedac983287cb94ad373_f93bad1975ac11f19641525400d9a7a1
    ReservedCode1: /69SNuf7UOF95uQhVFeMoFPtPEA+g5q1F71BPF0ZCJ+oq4AiA8otgBPCFRRe3IBxeUQOWYKT4gEsM9/EuBWfb0NJvoxaec0RRBG0wu3iEgfIuS/vvyXUliMYjCjWKBWZFhugkwvDWiHyfILU7Vojzmri/xo09GqihM9KzSXEO5gyJNsvkjBTFGrXrMU=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 0a3495d31457bedac983287cb94ad373_f93bad1975ac11f19641525400d9a7a1
    ReservedCode2: /69SNuf7UOF95uQhVFeMoFPtPEA+g5q1F71BPF0ZCJ+oq4AiA8otgBPCFRRe3IBxeUQOWYKT4gEsM9/EuBWfb0NJvoxaec0RRBG0wu3iEgfIuS/vvyXUliMYjCjWKBWZFhugkwvDWiHyfILU7Vojzmri/xo09GqihM9KzSXEO5gyJNsvkjBTFGrXrMU=
---

# TEST_STRATEGY.md — sci-agent 测试策略

> 版本：v1.0 | 最后更新：2026-07-02

---

## 1. 测试金字塔与比例分配

```
         ╱  E2E  ╲          5%   关键用户流程（端到端）
        ╱──────────╲
       ╱  集成测试   ╲       25%   API集成 + 页面集成
      ╱──────────────╲
     ╱   单元测试      ╲     70%   函数级 + 组件级
    ╱──────────────────╲
```

| 层级 | 占比 | 工具 | 目标 |
|------|------|------|------|
| 单元测试 | 70% | pytest (后端) / Vitest (前端) | 覆盖率 ≥ 80% |
| 集成测试 | 25% | pytest + httpx (后端) / Playwright (前端) | 每个端点 ≥ 1正1异 |
| E2E | 5% | Playwright | 核心用户路径（注册→检索→写作→导出） |

---

## 2. 后端测试策略

### 2.1 测试目录结构

```
backend/tests/
├── conftest.py                  # 全局 fixture
│   ├── async_client             # httpx.AsyncClient(app)
│   ├── test_db                  # 隔离测试数据库 session
│   ├── test_user                # 预创建的测试用户
│   └── auth_headers             # 带有效 Token 的 Header
├── test_health.py               # M0 健康检查
├── test_auth.py                 # M1 用户体系
├── test_papers.py               # M2 文献检索
├── test_library.py              # M3 知识库
├── test_writing.py              # M5 AI写作
├── test_sandbox.py              # M6 沙箱
├── test_workspaces.py           # M7 协作空间
└── test_audit.py                # M8 防篡改日志
```

### 2.2 单元测试 (pytest)

**覆盖目标**：
- `services/*.py`：所有 public 方法
- `core/security.py`：JWT 生成/验证、密码哈希
- `core/hash_chain.py`：哈希链计算与校验
- `utils/*.py`：引用格式化、提取器

**命名规范**：
```python
# test_<文件名>.py 中
def test_<函数名>_<场景>_<期望结果>():
    """
    示例：
    def test_create_access_token_valid_user_returns_jwt():
    def test_search_papers_empty_query_raises_validation_error():
    def test_hash_chain_append_log_creates_correct_chain():
    """
```

**Mock 策略**：
- 外部API调用（科应、混元、邮件）→ 必须 mock（`unittest.mock` 或 `pytest-mock`）
- Docker 操作 → 必须 mock（使用 `docker-py` 的 mock client）
- 数据库操作 → 使用真实测试数据库（见 2.3）
- 时间相关 → 使用 `freezegun` 固定时间

### 2.3 API 集成测试

**每个模块的最小测试矩阵**：

| 端点数量 | 正常用例 | 异常用例 | 合计 |
|---------|---------|---------|------|
| N 个端点 | N 个 (200/201) | ≥ N 个 (4xx/5xx) | ≥ 2N |

**异常用例覆盖**（每个端点至少包含）：

| 错误场景 | 错误码 |
|---------|--------|
| 缺少必填参数 | 1001 |
| 未登录 | 1002 |
| Token 过期 | 1003 |
| 权限不足 | 1004 |
| 资源不存在 | 2001 |
| （模块特定错误） | 3001/4001 等 |

**测试数据库约定**：
```python
# conftest.py
@pytest.fixture(scope="function")  # 每个测试函数独立
async def test_db():
    # 1. 创建临时数据库或使用固定测试库
    # 2. 运行 Alembic migration 到最新
    # 3. yield session
    # 4. 回滚所有变更（或 DROP 重建）
```

- 测试数据库名称：`sciagent_test`
- 每次测试前运行 `alembic upgrade head`
- 每次测试后回滚（使用事务回滚，非 DROP 重建，保证速度）

### 2.4 Mock 外部服务 Factory

```python
# tests/conftest.py

@pytest.fixture
def mock_keying_api(httpx_mock):
    """Mock 科应API，返回标准文献搜索响应"""
    httpx_mock.add_response(
        url="https://api.keying.cn/v1/search",
        json={
            "total": 100,
            "items": [
                {
                    "title": "深度学习在医学图像分割中的应用",
                    "authors": ["张三", "李四"],
                    "doi": "10.1234/example.2024",
                    "journal": "计算机学报",
                    "year": 2024,
                    "abstract": "..."
                }
            ]
        }
    )
    return httpx_mock

@pytest.fixture
def mock_hunyuan_api(httpx_mock):
    """Mock 混元API，返回AI写作结果"""
    httpx_mock.add_response(
        url="https://api.hunyuan.cloud.tencent.com/v1/chat/completions",
        json={
            "choices": [{
                "message": {
                    "content": "## 研究综述\n\n... [AI_GENERATED]..."
                }
            }]
        }
    )
```

---

## 3. 前端测试策略

### 3.1 组件测试 (Vitest + Testing Library)

**测试范围**：关键交互组件

| 组件 | 测试重点 |
|------|---------|
| `SearchBar` | 输入防抖、回车触发、清空按钮 |
| `PaperCard` | 渲染完整信息、操作按钮点击 |
| `LoginForm` | 表单校验、错误提示、提交 loading 态 |
| `Editor` (AI写作) | AI 生成内容渲染、溯源标记展示 |
| `Sidebar` | 导航高亮、折叠/展开 |

**组件测试模板**：
```typescript
// frontend/__tests__/components/SearchBar.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SearchBar } from '@/components/papers/SearchBar';

describe('SearchBar', () => {
  it('renders input field', () => {
    render(<SearchBar onSearch={vi.fn()} />);
    expect(screen.getByPlaceholderText(/搜索文献/)).toBeInTheDocument();
  });

  it('calls onSearch after debounce', async () => {
    const onSearch = vi.fn();
    render(<SearchBar onSearch={onSearch} />);
    await userEvent.type(screen.getByRole('textbox'), '深度学习');
    // 等待 debounce 300ms
    await new Promise(r => setTimeout(r, 350));
    expect(onSearch).toHaveBeenCalledWith('深度学习');
  });
});
```

### 3.2 页面集成测试 (Playwright)

**测试范围**：关键用户路径

```typescript
// e2e/critical-path.spec.ts
test('注册 → 检索 → 添加到知识库 → 导出', async ({ page }) => {
  // 1. 注册
  await page.goto('/register');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'Test1234!');
  await page.click('button[type="submit"]');

  // 2. 检索
  await page.goto('/dashboard/papers');
  await page.fill('[placeholder="搜索文献"]', '机器学习');
  await page.waitForResponse('/api/v1/papers/search');

  // 3. 添加到知识库
  await page.click('[data-testid="add-to-library"]:first-child');
  await page.waitForResponse('/api/v1/library/add');

  // 4. 导出
  await page.goto('/dashboard/library');
  await page.click('[data-testid="export-bibtex"]');
  // 验证下载
});
```

---

## 4. AI 辅助测试

### 4.1 AI 自动生成测试用例流程

```
1. AI 读取 SPEC.md → 提取模块 API 契约
2. AI 为每个端点生成测试骨架：
   - 正常用例（基于 SPEC 中的请求/响应示例）
   - 异常用例（基于错误码表）
3. AI 向人类开发者展示测试计划 → 确认
4. AI 写入测试文件到 tests/ 目录
5. 运行 pytest → 修正失败用例 → 提交
```

### 4.2 AI 生成测试报告的格式

```markdown
## 测试报告 — M2 文献检索模块

**日期**：2026-07-02
**Agent**：Test Agent #3
**基于 SPEC 版本**：v1.0

### 测试统计
| 指标 | 数值 |
|------|------|
| 总用例数 | 24 |
| 通过 | 22 |
| 失败 | 1 |
| 跳过 | 1 |
| 覆盖率 | 87% |

### 失败用例
| 用例 | 期望 | 实际 | 原因 |
|------|------|------|------|
| test_search_papers_no_results_returns_empty | 200 | 500 | keying API mock 未处理空结果 |

### 修复建议
- 在 `keying_client.py` 中增加空结果处理分支
```

---

## 5. 测试环境配置

### 5.1 本地开发测试

```bash
# 后端
cd backend
pip install -r requirements-dev.txt
pytest tests/ -v --cov=app --cov-report=term-missing

# 前端
cd frontend
npm test                    # Vitest 单元测试
npx playwright test         # E2E 测试

# 一键运行全部
cd scripts && ./test_all.sh
```

### 5.2 CI 环境 (GitHub Actions)

```yaml
# .github/workflows/backend-ci.yml
name: Backend CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: sciagent_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements-dev.txt
      - run: ruff check backend/app/
      - run: mypy backend/app/ --strict
      - run: pytest backend/tests/ -v --cov
```

---

## 6. 持续测试约定

| 时机 | 运行内容 | 超时 | 失败处理 |
|------|---------|------|---------|
| 每次 `git push` | lint + type check | 2min | 阻止推送 |
| PR 创建 | 单元测试 + 集成测试 | 10min | 阻止合并 |
| PR 合并到 main | 全量测试 + E2E | 15min | 回滚并通知 |
| 每日凌晨 2:00 | 全量测试 (含 slow) | 30min | 通知人类开发者 |

### 快速开发例外

> 开发中频繁提交（WIP）可在 commit message 中包含 `[skip ci]` 跳过 CI。但 PR 创建时**不允许**跳过。

---

*本文档定义了 sci-agent 项目的测试标准。所有 AI Agent 生成的测试代码必须符合上述规范。*
*（内容由AI生成，仅供参考）*
