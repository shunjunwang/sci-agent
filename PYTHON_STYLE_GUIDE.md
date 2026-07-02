---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 0a3495d31457bedac983287cb94ad373_825c82d675b911f19641525400d9a7a1
    ReservedCode1: BSD/+hyinTq9ZygXv9pg3cYMBjagfhVGe7fcjliWos94k4rcyRTZ49/M+eiAanWTv74mOc3ncxdbZWpzELLiM8l+j5FOrAu0gpL4U0bFsoGYyK8rn74p0Jd5EDaZXhEpYRBHQO8oGgccguiCVcm/FpAev2JRiKXN3IZ6B97AzScv0FSSVkYpOV55/lk=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 0a3495d31457bedac983287cb94ad373_825c82d675b911f19641525400d9a7a1
    ReservedCode2: BSD/+hyinTq9ZygXv9pg3cYMBjagfhVGe7fcjliWos94k4rcyRTZ49/M+eiAanWTv74mOc3ncxdbZWpzELLiM8l+j5FOrAu0gpL4U0bFsoGYyK8rn74p0Jd5EDaZXhEpYRBHQO8oGgccguiCVcm/FpAev2JRiKXN3IZ6B97AzScv0FSSVkYpOV55/lk=
---

# Python 代码规范 — sci-agent 项目

> 版本：v1.0 | 最后更新：2026-07-02
> 适用范围：所有 AI Agent 生成的 Python 代码
> 约束力：AI_COLLABORATION.md 第 5 条铁律引用本文档

---

## 1. 目录结构

```
D:\projects\sci-agent\
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI 入口
│   │   ├── config.py           # 配置管理（pydantic-settings）
│   │   ├── api/                # 路由层（按模块分）
│   │   │   ├── __init__.py
│   │   │   ├── v1/             # API v1
│   │   │   │   ├── __init__.py
│   │   │   │   ├── users.py
│   │   │   │   ├── papers.py
│   │   │   │   └── ...
│   │   │   └── deps.py         # 依赖注入（get_db, get_current_user 等）
│   │   ├── models/             # SQLAlchemy ORM 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── paper.py
│   │   │   └── ...
│   │   ├── schemas/            # Pydantic 请求/响应 Schema
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── ...
│   │   ├── services/           # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── ...
│   │   └── core/               # 核心基础设施
│   │       ├── __init__.py
│   │       ├── database.py     # 数据库连接与会话管理
│   │       ├── security.py     # JWT / 密码哈希
│   │       └── exceptions.py   # 自定义异常
│   ├── migrations/             # Alembic 数据库迁移
│   ├── tests/                  # 测试
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/                   # Next.js 前端
├── electron/                   # Electron 桌面壳
├── docs/                       # 项目文档
├── scripts/                    # 工具脚本
├── .ai-memory/                 # AI 执行日志
├── docker-compose.yml
└── AI_CONTEXT.md
```

## 2. 命名约定

| 对象 | 规则 | 示例 |
|------|------|------|
| 模块/文件 | `snake_case` | `paper_service.py`, `user_model.py` |
| 类 | `PascalCase` | `PaperService`, `UserCreateSchema` |
| 函数/方法 | `snake_case` | `get_paper_by_id()`, `create_user()` |
| 变量 | `snake_case` | `paper_count`, `access_token` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_PAGE_SIZE`, `DEFAULT_TIMEOUT` |
| 私有成员 | 前缀 `_` | `_validate_email()`, `self._db` |
| 数据库表 | `snake_case` 复数 | `users`, `papers`, `user_libraries` |
| API 端点 | `kebab-case` | `/api/v1/papers/search`, `/api/v1/user-libraries` |

## 3. 代码风格

### 3.1 类型注解

所有公开函数必须有完整类型注解：

```python
# ✅ 正确
from typing import Optional
from uuid import UUID

async def get_paper_by_id(
    paper_id: UUID,
    user_id: Optional[UUID] = None,
    include_abstract: bool = True,
) -> dict[str, object]:
    ...

# ❌ 错误 — 无类型注解
def get_paper_by_id(paper_id, user_id=None, include_abstract=True):
    ...
```

### 3.2 导入顺序

遵循 isort 规则，分三组，空行分隔：

```python
# 1. 标准库
import asyncio
from datetime import datetime

# 2. 第三方库
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# 3. 本地模块
from app.core.database import get_db
from app.models.paper import Paper
```

### 3.3 字符串

- 默认使用双引号 `"..."`，与 Black 格式化器一致
- f-string 优先于 `.format()` 和 `%` 格式化
- 多行字符串用三引号 `"""..."""`

```python
# ✅
message = f"用户 {user.name} 创建了论文 {paper.title}"
# ❌
message = "用户 {} 创建了论文 {}".format(user.name, paper.title)
```

### 3.4 文档字符串

所有公开函数使用 Google 风格 docstring：

```python
async def search_papers(
    query: str,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, object]:
    """检索论文。

    Args:
        query: 搜索关键词。
        page: 页码，从 1 开始。
        page_size: 每页条数，最大 100。

    Returns:
        包含 papers 列表和 total_count 的字典。

    Raises:
        ValueError: page_size 超过 100 时抛出。
    """
    ...
```

### 3.5 异步优先

数据库操作和外部 API 调用一律使用 async/await：

```python
# ✅
async def get_user(user_id: UUID) -> User | None:
    async with get_db() as db:
        return await db.get(User, user_id)

# ❌ 禁止同步阻塞调用
def get_user(user_id):
    with get_db() as db:
        return db.query(User).filter(User.id == user_id).first()
```

### 3.6 异常处理

```python
# ✅ 抛出自定义异常，附带上下文
from app.core.exceptions import NotFoundError

async def get_paper_or_404(paper_id: UUID) -> Paper:
    paper = await get_paper_by_id(paper_id)
    if not paper:
        raise NotFoundError(
            message="论文不存在",
            detail={"paper_id": str(paper_id)}
        )
    return paper

# ❌ 禁止裸 Exception 或笼统消息
raise Exception("not found")
```

## 4. FastAPI 专属规范

### 4.1 路由定义

```python
from fastapi import APIRouter, Depends, Query
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/papers", tags=["papers"])

@router.get("/search", response_model=PaperListResponse)
async def search_papers(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
) -> PaperListResponse:
    ...
```

### 4.2 Schema 定义

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class PaperCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    abstract: str | None = Field(None, max_length=5000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "A Novel Approach to CRISPR",
                "abstract": "We present..."
            }
        }
    }

class PaperResponse(BaseModel):
    id: UUID
    title: str
    abstract: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
```

### 4.3 依赖注入

```python
# app/api/v1/deps.py
from fastapi import Depends, Header
from app.core.security import decode_access_token

async def get_current_user(
    authorization: str = Header(...),
) -> User:
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    return await get_user_by_id(payload["sub"])
```

## 5. 数据库规范

### 5.1 模型定义

```python
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class Paper(Base):
    __tablename__ = "papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    abstract = Column(String(5000))
    created_at = Column(DateTime, nullable=False, server_default="now()")

    annotations = relationship("Annotation", back_populates="paper")
```

### 5.2 查询规范

- 禁止在路由层直接写 SQL 或 ORM 查询，必须封装在 services 层
- 分页查询统一使用 `LIMIT + OFFSET`
- 禁止 `SELECT *`，ORM 层面用 `defer()` 排除大字段

## 6. 工具链

```bash
# 格式化
black --line-length 100 backend/

# 导入排序
isort --profile black backend/

# 类型检查
mypy backend/ --strict

# 代码检查
ruff check backend/ --fix

# 测试（覆盖率目标 80%）
pytest backend/tests/ --cov=backend/app --cov-report=term
```

## 7. Git 提交规范

```
<type>: <简短描述>

类型：
  feat     新功能
  fix      修复
  docs     文档
  refactor 重构
  test     测试
  chore    工程配置

示例：
  feat: 添加论文检索 API
  fix: 修复 JWT token 过期判断
  docs: 更新 API 契约文档
```

**禁止事项：**
- 禁止 `console.log` / `print()` 提交到仓库
- 禁止提交含硬编码密钥（API Key、密码）的代码
- 禁止单次提交超过 500 行变更

---

*本文档由 Git 管理。违反上述规范的代码将在 Code Review 中拒绝合并。*
*（内容由AI生成，仅供参考）*
