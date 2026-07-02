---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 0a3495d31457bedac983287cb94ad373_f784172f75ac11f19641525400d9a7a1
    ReservedCode1: Tbcp6mzVqA3FP1cRiu8Pr8TMvbJnreOsxFMNtOl2OO7Ni/Joxw4SNICH1b+/fH7WPsFvxlhRwxYoNhYbc4Jp5UqMcpghOorfdqry25zUHUAdubBHQqUnDxbirGM5NjlwkEjOieMPXjc/OEBqW4pZKfsTs0681sM/1Crrfe3tibp+WnsJqRZQKqqD46k=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 0a3495d31457bedac983287cb94ad373_f784172f75ac11f19641525400d9a7a1
    ReservedCode2: Tbcp6mzVqA3FP1cRiu8Pr8TMvbJnreOsxFMNtOl2OO7Ni/Joxw4SNICH1b+/fH7WPsFvxlhRwxYoNhYbc4Jp5UqMcpghOorfdqry25zUHUAdubBHQqUnDxbirGM5NjlwkEjOieMPXjc/OEBqW4pZKfsTs0681sM/1Crrfe3tibp+WnsJqRZQKqqD46k=
---

# ARCHITECTURE.md — sci-agent 技术架构设计文档

> 版本：v1.0 | 最后更新：2026-07-02 | 维护者：AI + 1人

---

## 1. 整体架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                      Electron 桌面壳                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                  Next.js (TypeScript) 前端                   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │  │
│  │  │ 文献检索  │ │ AI写作   │ │ 知识库   │ │ 协作空间     │  │  │
│  │  │ 页面      │ │ 页面     │ │ 页面     │ │ 页面         │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP/WS (REST API + JWT)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                   FastAPI (Python 3.11+) 后端                      │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │                    中间件链                                │     │
│  │  CORS → RequestLogger → AuthMiddleware → RateLimiter     │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │
│  │ API路由   │ │ 业务服务层│ │ 数据模型 │ │ 外部集成         │    │
│  │           │ │          │ │          │ │                  │    │
│  │ /auth/*   │ │ AuthServ │ │ User     │ │ 科应API (文献)   │    │
│  │ /papers/* │ │ PaperSvc │ │ Paper    │ │ Docker Engine    │    │
│  │ /lib/*    │ │ Library  │ │ Library  │ │ SMTP 邮件        │    │
│  │ /write/*  │ │ Writing  │ │ Document │ │ 微信开放平台      │    │
│  │ /sandbox/*│ │ Sandbox  │ │ Session  │ │ (预留)           │    │
│  │ /ws/*     │ │ Workspace│ │ Workspace│ │                  │    │
│  │ /audit/*  │ │ AuditLog │ │ ActLog   │ │                  │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘    │
│                                                                    │
└────────────────────────────┬───────────────────────────────────────┘
                             │ asyncpg / SQLAlchemy 2.0
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    PostgreSQL 16 + pgvector                        │
│                                                                    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐     │
│  │ users  │ │ papers │ │library │ │docs    │ │activity_log│     │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────────┘     │
│  ┌────────────┐ ┌────────┐ ┌──────────┐ ┌──────────────────┐    │
│  │workspaces  │ │sandbox │ │annotations│ │paper_embeddings  │    │
│  │ + members  │ │sessions│ │          │ │ (pgvector, 1536d)│    │
│  └────────────┘ └────────┘ └──────────┘ └──────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### 分层说明

| 层 | 职责 | 关键技术 |
|---|---|---|
| 表示层 | Electron 提供原生窗口 / 托盘 / 快捷键；Next.js 负责 UI 渲染 | Electron 28 + Next.js 14 (App Router) |
| 应用层 | REST API 网关，鉴权/限流/日志等横切关注点 | FastAPI + Pydantic v2 |
| 业务层 | 文献检索、AI写作、沙箱调度等核心业务 | 异步 Service 层，依赖注入 |
| 持久层 | 关系数据 + 向量存储 | PostgreSQL 16 + pgvector 0.7 |
| 外部集成 | 第三方API、容器运行时、邮件服务 | httpx + docker-py + aiosmtplib |

---

## 2. 技术选型总览

| 类别 | 选择 | 版本 | 选型理由 | 替代方案（否决原因） |
|------|------|------|---------|---------------------|
| **后端框架** | FastAPI | 0.111+ | 原生异步、自动 OpenAPI 文档、Pydantic 集成 | Django-Ninja（生态重，ORM 耦合深） |
| **前端框架** | Next.js (TS) | 14 | App Router、SSR/SSG 灵活切换、Vercel 生态 | Nuxt3（团队无 Vue 经验） |
| **桌面壳** | Electron | 28 | 跨平台、成熟生态、可复用 Web 代码 | Tauri（Rust 学习曲线，1人项目风险高） |
| **数据库** | PostgreSQL + pgvector | 16 + 0.7 | 向量检索与关系查询一体，避免多库运维 | MongoDB Atlas（非开源、向量方案锁云厂商） |
| **ORM** | SQLAlchemy 2.0 | 2.0+ | 异步支持成熟、与 FastAPI 社区最佳实践一致 | Prisma（Python 端无原生支持） |
| **异步驱动** | asyncpg | 0.29+ | 最快的 PG 异步驱动 | psycopg3（性能稍逊） |
| **数据校验** | Pydantic v2 | 2.x | FastAPI 原生集成、性能较 v1 提升 5-10x | marshmallow（需额外集成） |
| **鉴权** | python-jose + passlib | — | JWT 标准实现、bcrypt 密码哈希 | Auth0/Firebase Auth（不满足私有化部署需求） |
| **文献API** | 科应API (keying) | — | B端高校已签约、中文文献覆盖好 | Semantic Scholar（中文弱）、Crossref（无中文） |
| **AI写作** | 腾讯混元 API | — | Markdown 输出规范、学术风格可控 | OpenAI（数据出境合规风险） |
| **容器调度** | docker-py | 7.x | Python 原生、资源控制精细 | k8s（过度设计，1人运维不可行） |
| **前端UI** | shadcn/ui + Tailwind | — | 组件可定制、Tree-shaking 体积小 | Ant Design（体积大、定制性差） |
| **状态管理** | Zustand | 4.x | 轻量、TS 类型友好、无 boilerplate | Redux Toolkit（模板代码多） |
| **测试** | pytest + Playwright | — | 后端/前端各自领域最佳 | Vitest（前端可用，但 Playwright 覆盖 E2E） |
| **容器化** | Docker Compose | v2 | 单机开发/部署黄金方案 | Podman Compose（兼容性仍有坑） |
| **CI/CD** | GitHub Actions | — | 免费额度够用、生态最全 | GitLab CI（需自托管 runner） |

---

## 3. 项目目录结构

```
sci-agent/
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app 创建 + 中间件注册
│   │   ├── config.py                 # Settings (pydantic-settings)
│   │   ├── dependencies.py           # 依赖注入 (get_db, get_current_user)
│   │   ├── api/                      # API 路由层 (仅声明路由+参数校验)
│   │   │   ├── __init__.py
│   │   │   ├── health.py             # /health
│   │   │   ├── auth.py               # /api/v1/auth/*
│   │   │   ├── papers.py             # /api/v1/papers/*
│   │   │   ├── library.py            # /api/v1/library/*
│   │   │   ├── writing.py            # /api/v1/writing/*
│   │   │   ├── sandbox.py            # /api/v1/sandbox/*
│   │   │   ├── workspaces.py         # /api/v1/workspaces/*
│   │   │   ├── audit.py              # /api/v1/audit/*
│   │   │   └── marketplace.py        # /api/v1/marketplace/* (M9预留)
│   │   ├── core/                     # 核心基础设施
│   │   │   ├── __init__.py
│   │   │   ├── security.py           # JWT 生成/验证、密码哈希
│   │   │   ├── middleware.py          # CORS / Logger / RateLimit
│   │   │   ├── error_handlers.py     # 统一异常处理 → 统一响应格式
│   │   │   └── hash_chain.py         # 防篡改哈希链实现 (M8)
│   │   ├── models/                   # SQLAlchemy ORM 模型
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # DeclarativeBase + 公共 Mixin
│   │   │   ├── user.py
│   │   │   ├── paper.py
│   │   │   ├── library.py
│   │   │   ├── annotation.py
│   │   │   ├── document.py
│   │   │   ├── sandbox.py
│   │   │   ├── workspace.py
│   │   │   └── activity_log.py
│   │   ├── schemas/                  # Pydantic v2 请求/响应模型
│   │   │   ├── __init__.py
│   │   │   ├── common.py             # 统一响应包装、分页基类
│   │   │   ├── auth.py
│   │   │   ├── paper.py
│   │   │   ├── library.py
│   │   │   ├── writing.py
│   │   │   ├── sandbox.py
│   │   │   ├── workspace.py
│   │   │   └── audit.py
│   │   ├── services/                 # 业务逻辑层 (无 HTTP 依赖)
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── paper_service.py
│   │   │   ├── keying_client.py      # 科应API 封装
│   │   │   ├── library_service.py
│   │   │   ├── writing_service.py
│   │   │   ├── sandbox_service.py
│   │   │   ├── workspace_service.py
│   │   │   ├── audit_service.py
│   │   │   └── embedding_service.py  # pgvector 嵌入生成与检索
│   │   └── utils/                    # 工具函数
│   │       ├── __init__.py
│   │       ├── citation_formatter.py # GB/T7714, APA, IEEE, MLA
│   │       └── reference_extractor.py
│   ├── alembic/                      # 数据库迁移
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── conftest.py               # fixture: test_db, async_client
│   │   ├── test_health.py
│   │   ├── test_auth.py
│   │   ├── test_papers.py
│   │   ├── test_library.py
│   │   ├── test_writing.py
│   │   ├── test_sandbox.py
│   │   ├── test_workspaces.py
│   │   └── test_audit.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/                         # Next.js 14 前端
│   ├── app/                          # App Router
│   │   ├── layout.tsx                # 根布局 (Provider wrappers)
│   │   ├── page.tsx                  # 首页 / 登录
│   │   ├── (auth)/                   # 认证路由组
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   └── forgot-password/page.tsx
│   │   ├── (dashboard)/              # 主面板路由组 (需登录)
│   │   │   ├── layout.tsx            # 侧边栏 + 顶栏
│   │   │   ├── page.tsx              # 仪表盘首页
│   │   │   ├── papers/               # 文献检索
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/page.tsx     # 文献详情
│   │   │   ├── library/              # 个人知识库
│   │   │   │   └── page.tsx
│   │   │   ├── writing/              # AI 写作
│   │   │   │   ├── page.tsx
│   │   │   │   └── [docId]/page.tsx
│   │   │   ├── sandbox/              # 仿真沙箱
│   │   │   │   └── page.tsx
│   │   │   ├── workspaces/           # 协作空间
│   │   │   │   ├── page.tsx
│   │   │   │   └── [wsId]/page.tsx
│   │   │   ├── audit/                # 审计面板
│   │   │   │   └── page.tsx
│   │   │   └── settings/             # 个人设置
│   │   │       └── page.tsx
│   │   └── api/                      # Next.js API Route (BFF层)
│   │       └── proxy/[...path]/route.ts  # 反向代理到 FastAPI
│   ├── components/
│   │   ├── ui/                       # shadcn/ui 组件
│   │   ├── auth/                     # 登录/注册表单
│   │   ├── papers/                   # 文献卡片、检索栏
│   │   ├── library/                  # 知识库树、批注面板
│   │   ├── writing/                  # AI写作编辑器
│   │   ├── sandbox/                  # 沙箱终端模拟
│   │   ├── workspace/                # 协作空间组件
│   │   └── layout/                   # 侧边栏、顶栏、面包屑
│   ├── lib/
│   │   ├── api-client.ts             # 统一 API 请求封装 (fetch wrapper)
│   │   ├── auth-store.ts             # Zustand: 用户状态 + Token 管理
│   │   ├── constants.ts
│   │   ├── types/                    # TypeScript 类型定义
│   │   │   ├── user.ts
│   │   │   ├── paper.ts
│   │   │   ├── library.ts
│   │   │   ├── writing.ts
│   │   │   ├── sandbox.ts
│   │   │   ├── workspace.ts
│   │   │   └── common.ts             # ApiResponse<T>, PaginatedResponse<T>
│   │   └── utils/
│   │       ├── citation.ts
│   │       └── format.ts
│   ├── hooks/                        # 自定义 Hooks
│   │   ├── useAuth.ts
│   │   ├── usePapers.ts
│   │   └── useWebSocket.ts
│   ├── public/
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── electron/                         # Electron 桌面壳
│   ├── main.ts                       # 主进程 (窗口管理、托盘)
│   ├── preload.ts                    # 预加载脚本 (安全暴露 API)
│   ├── electron-builder.yml          # 打包配置
│   └── package.json
│
├── docker/                           # Docker 配置
│   ├── docker-compose.yml            # 开发环境：PG16 + pgvector + Redis
│   ├── docker-compose.prod.yml       # 生产环境模板
│   └── postgres/
│       └── init.sql                  # 初始化脚本 (创建扩展)
│
├── docs/                             # 项目管理文档
│   ├── SPEC.md                       # API 契约 (真相源)
│   ├── ARCHITECTURE.md               # 本文档
│   ├── AI_COLLABORATION.md           # AI 协同规范
│   ├── TEST_STRATEGY.md              # 测试策略
│   ├── PROGRESS.md                   # 进度看板
│   └── RISK_MANAGEMENT.md            # 风险管理
│
├── scripts/                          # 工具脚本
│   ├── dev.ps1                       # 一键启动开发环境 (Windows)
│   ├── dev.sh                        # 一键启动开发环境 (Linux/macOS)
│   ├── seed_data.py                  # 测试数据种子脚本
│   └── check_deps.py                 # 依赖检查
│
├── .github/
│   └── workflows/
│       ├── backend-ci.yml            # 后端 CI (lint + test)
│       └── frontend-ci.yml           # 前端 CI (lint + test + build)
│
├── .gitignore
├── .env.example                      # 环境变量模板
└── README.md
```

---

## 4. 后端架构

### 4.1 FastAPI 模块划分

```
app/
├── main.py               # app = FastAPI(); include_router(); add_middleware()
├── config.py             # class Settings(BaseSettings)
├── dependencies.py       # get_db() → AsyncSession; get_current_user() → User
│
├── api/                  # 薄层：参数校验 + 调用 service + 返回响应
│   ├── health.py         # GET /health
│   ├── auth.py           # POST /api/v1/auth/register|login|refresh
│   ├── papers.py         # GET /api/v1/papers/search|{id}
│   ├── library.py        # POST /api/v1/library/add|remove; GET .../list
│   ├── writing.py        # POST /api/v1/writing/generate|polish|paraphrase
│   ├── sandbox.py        # POST /api/v1/sandbox/create|execute; GET .../status
│   ├── workspaces.py     # CRUD /api/v1/workspaces
│   ├── audit.py          # GET /api/v1/audit/logs|report
│   └── marketplace.py    # (M9 预留)
│
├── core/                 # 基础设施，不包含业务逻辑
│   ├── security.py       # create_access_token, verify_token, hash_password
│   ├── middleware.py      # LoggingMiddleware, RateLimitMiddleware
│   ├── error_handlers.py # @app.exception_handler → 统一 JSON 错误响应
│   └── hash_chain.py     # ActivityLog 链式哈希 (M8)
│
├── services/             # 业务逻辑：纯 Python、不 import FastAPI
│   ├── auth_service.py   # register, login, refresh_token
│   ├── paper_service.py  # search, get_by_doi, aggregate_sources
│   ├── keying_client.py  # 科应API: httpx async client + retry + circuit breaker
│   ├── library_service.py
│   ├── writing_service.py # 调用混元API + 溯源标注
│   ├── sandbox_service.py # docker-py 管理容器
│   ├── workspace_service.py
│   ├── audit_service.py  # 日志写入 + 哈希链 + 完整性校验
│   └── embedding_service.py  # OpenAI-compatible embedding API → pgvector
│
├── models/               # SQLAlchemy ORM: 表定义 + 关系
├── schemas/              # Pydantic: 请求体/响应体/查询参数
└── utils/                # 纯工具函数
```

### 4.2 中间件链（按顺序）

| 位置 | 中间件 | 职责 |
|------|--------|------|
| 1 | `CORSMiddleware` | 允许前端跨域（开发: localhost:3000, 生产: electron://） |
| 2 | `RequestLoggingMiddleware` | 请求计时 + 结构化日志 (timestamp, method, path, user_id, duration_ms) |
| 3 | `AuthMiddleware` | 从 Authorization header 提取 Bearer Token → 注入 request.state.user |
| 4 | `RateLimitMiddleware` | 基于 user_id + endpoint 的滑动窗口限流（Redis 可选） |

### 4.3 依赖注入

```python
# app/dependencies.py

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """每个请求获取独立数据库会话，请求结束自动关闭"""
    async with async_session() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """从 JWT 中解析 user_id → 查询数据库 → 返回 User ORM 对象"""
    ...

def require_role(*roles: str):
    """角色权限守卫：在路由上声明 require_role('admin')"""
    ...
```

---

## 5. 前端架构

### 5.1 Next.js App Router 路由设计

| 路由 | 页面 | 布局 | 鉴权 |
|------|------|------|------|
| `/` | 首页/重定向 | 根布局 | 否 |
| `/login` | 登录页 | `(auth)` 布局 | 否 |
| `/register` | 注册页 | `(auth)` 布局 | 否 |
| `/dashboard` | 仪表盘 | `(dashboard)` 布局（侧边栏+顶栏） | JWT 守卫 |
| `/dashboard/papers` | 文献检索 | `(dashboard)` | JWT 守卫 |
| `/dashboard/papers/[id]` | 文献详情 | `(dashboard)` | JWT 守卫 |
| `/dashboard/library` | 知识库 | `(dashboard)` | JWT 守卫 |
| `/dashboard/writing` | AI写作 | `(dashboard)` | JWT 守卫 |
| `/dashboard/writing/[docId]` | 编辑器 | `(dashboard)` | JWT 守卫 |
| `/dashboard/sandbox` | 仿真沙箱 | `(dashboard)` | JWT 守卫 |
| `/dashboard/workspaces` | 协作空间列表 | `(dashboard)` | JWT 守卫 |
| `/dashboard/workspaces/[wsId]` | 空间内部 | `(dashboard)` | JWT 守卫 |
| `/dashboard/audit` | 审计面板 | `(dashboard)` | 管理员 |
| `/dashboard/settings` | 个人设置 | `(dashboard)` | JWT 守卫 |

### 5.2 组件树（核心页面）

```
<RootLayout>
  └─ (dashboard)/layout.tsx
       ├─ <Sidebar>            // 导航菜单
       ├─ <TopBar>             // 用户头像、通知
       └─ <main>
            ├─ PapersPage
            │    ├─ <SearchBar>
            │    ├─ <FilterPanel>     // 年份/期刊/学科
            │    └─ <PaperList>
            │         └─ <PaperCard>  // 标题/作者/摘要/操作按钮
            ├─ WritingPage
            │    ├─ <SourceSelector>  // 选文献作为素材
            │    ├─ <Editor>          // TipTap/Milkdown 富文本
            │    └─ <AITracePanel>    // 溯源标注展示
            └─ SandboxPage
                 ├─ <SessionList>
                 └─ <Terminal>        // xterm.js 模拟终端
```

### 5.3 状态管理方案

| 状态类型 | 方案 | 理由 |
|---------|------|------|
| 服务端状态 | TanStack Query (React Query) | 缓存/重试/乐观更新/自动失效 |
| 客户端全局状态 | Zustand | 轻量、无 Provider 嵌套 |
| 认证状态 | Zustand `auth-store` + localStorage | Token 持久化、登录态全局共享 |
| 表单状态 | React Hook Form + Zod | 类型安全、校验与 Pydantic schema 对齐 |
| URL 状态 | Next.js `useSearchParams` | 检索条件/分页可分享、可回退 |

---

## 6. 数据流设计

### 6.1 文献检索完整链路

```
用户输入 "深度学习 图像分割"
        │
        ▼
[Next.js] SearchBar onChange → debounce 300ms
        │
        ▼
[Next.js] TanStack Query: GET /api/v1/papers/search?q=...&page=1
        │  Authorization: Bearer {access_token}
        ▼
[FastAPI] PaperRouter.search()
        │
        ▼
[FastAPI] PaperService.search()
        ├─→ keying_client.search(q, page, page_size)    # 科应API
        │       │  httpx.AsyncClient → GET 科应 /search
        │       │  响应: { total, items: [...] }
        │       ▼
        │   标准化为内部 Paper schema
        │
        └─→ (预留) source_aggregator.merge()  # 多源去重合并
                │
                ▼
        [返回] { code:0, data: { items:[...], total, page, page_size } }
        │
        ▼
[Next.js] TanStack Query 缓存 → PaperList 渲染
```

### 6.2 AI 写作溯源流程

```
用户选中 3 篇文献 → 点击「生成综述初稿」
        │
        ▼
[FastAPI] WritingService.generate_review()
        │
        ├─→ 从 user_library 读取选中文文献的 title + abstract
        │
        ├─→ 构造 Prompt: "基于以下文献撰写综述，每段末尾标注引用来源"
        │       │
        │       ▼
        │   调用混元 API (markdown 输出)
        │       │
        │       ▼
        │   解析返回内容，提取 AI 生成段落标记
        │
        ├─→ 计算 ai_generated_ratio
        │
        ├─→ 写入 documents 表:
        │       content: "...[AI_GENERATED]段落内容[/AI_GENERATED]..."
        │       source_papers: [{"paper_id": 12, "section": "2.1"}, ...]
        │
        └─→ 写入 activity_log (M8 审计)
        │
        ▼
[返回] { document_id, content, ai_generated_ratio, sources }
```

---

## 7. 部署架构

### 7.1 开发环境 (Docker Compose)

```yaml
# docker/docker-compose.yml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: sciagent
      POSTGRES_USER: sciagent
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports: ["5432:5432"]
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:
    build: ./backend
    environment: { DATABASE_URL: "postgresql+asyncpg://..." }
    ports: ["8000:8000"]
    depends_on: [db, redis]
    volumes:
      - ./backend:/app
      - /var/run/docker.sock:/var/run/docker.sock  # docker-py 需要

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
    volumes:
      - ./frontend:/app

volumes:
  pgdata:
```

### 7.2 生产部署（规划）

- 后端：单个 FastAPI 容器（可横向扩展）+ Nginx 反向代理
- 前端：Next.js `output: 'standalone'` → Node 容器 (或静态导出用于 Electron)
- 数据库：托管 PostgreSQL 16（阿里云 RDS / 自建）
- Electron：`electron-builder` 打包为 .exe / .dmg / .AppImage

---

## 8. 关键技术决策记录 (ADR)

### ADR-001：文献数据入库策略

- **背景**：科应API返回的文献数据应缓存到本地PG还是每次实时查询？
- **选项**：
  - A) 纯代理模式：每次请求实时查科应API，不做本地存储
  - B) 全量导入：提前批量导入文献元数据
  - C) 懒加载缓存：首次查询时写入本地，后续从本地读取
- **结论**：选 **C**。用户查询时先查本地 papers 表，未命中或超过 TTL（7天）时回源查科应API并写入本地。理由：减少API调用频率、支持离线检索历史、降低延迟。

### ADR-002：AI写作输出格式

- **背景**：混元API返回的综述应如何存储和渲染？
- **选项**：
  - A) 纯文本
  - B) Markdown
  - C) 自定义 AST
- **结论**：选 **B**。Markdown 可直接在前端渲染（react-markdown）、可嵌入 AI 溯源标记、可导出为 DOCX/PDF。

### ADR-003：C盘空间不足的应对

- **背景**：开发机 C 盘仅剩不足 10GB，无法容纳 Docker 镜像和 node_modules。
- **选项**：
  - A) 迁移到 D 盘（修改 Docker 数据根目录 + npm/yarn 全局配置）
  - B) 使用云开发机
- **结论**：选 **A**。Docker Desktop 设置 `data-root: D:\docker-data`；`npm config set cache D:\npm-cache`；WSL2 发行版导出到 `D:\wsl`。

### ADR-004：防篡改日志方案

- **背景**：需保证研学行为日志不可篡改，用于学术诚信审查。
- **选项**：
  - A) 区块链上链
  - B) 应用层哈希链
  - C) 数据库触发器 + WAL 审计
- **结论**：选 **B**。应用层 SHA256 哈希链（每条日志含 prev_hash → current_hash = SHA256(data + prev_hash)），定期生成完整性报告。理由：无外部依赖、高校私有化部署可接受、满足审计需求。不选 A 因为引入区块链增加运维复杂度和成本；不选 C 因为 WAL 级别操作对 DBA 仍然可篡改。

### ADR-005：前端与后端API通信方式

- **背景**：Next.js 是否直接调用 FastAPI 还是通过 BFF 代理？
- **选项**：
  - A) 前端直连 FastAPI
  - B) Next.js API Route 代理
  - C) BFF + 直连混合
- **结论**：选 **C**。开发阶段前端 dev server 直连 `localhost:8000`（通过 `next.config.js` rewrites）；生产 Electron 环境也直连本地后端。Next.js API Route 仅用于需要服务端密钥的场景（如 OAuth callback）。

### ADR-006：pgvector 向量维度与模型选择

- **背景**：文献 embedding 用于语义检索和相似文献推荐。
- **选项**：
  - A) OpenAI text-embedding-3-small (1536d)
  - B) 本地 bge-large-zh-v1.5 (1024d)
  - C) 科应API 自带向量
- **结论**：选 **A**，架构预留 **B/C** 切换能力。pgvector 列定义为 `vector(1536)`，EmbeddingService 抽象接口支持多后端，配置切换 `EMBEDDING_BACKEND=openai|local|keying`。

---

*文档结束。本文档与 SPEC.md 共同构成 sci-agent 项目的技术基石。*
*（内容由AI生成，仅供参考）*
