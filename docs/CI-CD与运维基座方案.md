# CI/CD 与运维基座方案

> **适用范围**：sci-agent 全栈项目（Python 后端 + Next.js 前端）
> **版本**：v1.0
> **最后更新**：2026-07-02

---

## 1. CI/CD 管线（GitHub Actions）

### 1.1 触发策略

| 事件                          | 工作流          | 说明                              |
| ----------------------------- | --------------- | --------------------------------- |
| push 到 `feature/*` 分支      | lint + test     | 快速反馈，阻止低质量代码进入评审  |
| PR 合并到 `main`              | 完整 test + build | 构建 Docker 镜像并推送至镜像仓库 |
| 打 tag `v*`                   | build + deploy  | 触发生产部署（见第 5 节）         |
| schedule（每周一 09:00 UTC）  | security-scan   | Dependabot + pip-audit + npm audit |

### 1.2 Workflow 文件设计

#### 1.2.1 lint.yml

```yaml
name: Lint

on:
  push:
    branches: [feature/*]
  pull_request:
    branches: [main]

jobs:
  lint-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: pip install ruff mypy

      - name: Ruff check
        run: ruff check backend/

      - name: Mypy type check
        run: mypy backend/ --ignore-missing-imports

  lint-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install & Lint
        run: |
          cd frontend
          npm ci
          npm run lint
```

#### 1.2.2 test.yml

```yaml
name: Test

on:
  push:
    branches: [feature/*]
  pull_request:
    branches: [main]

jobs:
  test-python:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: sciagent
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: sciagent_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install & Test
        env:
          DATABASE_URL: postgresql://sciagent:testpass@localhost:5432/sciagent_test
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov
          pytest backend/tests/ --cov=backend --cov-report=xml --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install & Test
        run: |
          cd frontend
          npm ci
          npm test -- --coverage
```

#### 1.2.3 build.yml

```yaml
name: Build & Push

on:
  pull_request:
    branches: [main]
    types: [closed]

jobs:
  build:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        run: |
          echo "sha=$(git rev-parse --short HEAD)" >> $GITHUB_OUTPUT
          echo "version=$(node -p "require('./package.json').version")" >> $GITHUB_OUTPUT

      - name: Build & Push Backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/backend:latest
            ghcr.io/${{ github.repository }}/backend:${{ steps.meta.outputs.version }}
            ghcr.io/${{ github.repository }}/backend:${{ steps.meta.outputs.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build & Push Frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/frontend:latest
            ghcr.io/${{ github.repository }}/frontend:${{ steps.meta.outputs.version }}
            ghcr.io/${{ github.repository }}/frontend:${{ steps.meta.outputs.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 1.3 依赖缓存策略

| 语言/生态 | 缓存键                          | 缓存路径                          | 触发条件               |
| --------- | ------------------------------- | --------------------------------- | ---------------------- |
| Python    | `${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}` | `~/.cache/pip`                    | `requirements.txt` 变更 |
| pip       | 由 `setup-python` 的 `cache: pip` 自动管理 | —                                 | `requirements.txt` 变更 |
| npm       | `${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}` | `~/.npm`                          | `package-lock.json` 变更 |
| Docker    | `type=gha`（GitHub Actions Cache）       | BuildKit 缓存层                   | Dockerfile / 依赖文件变更 |

---

## 2. 环境分离

### 2.1 环境矩阵

| 环境       | 用途               | 基础设施                                      | 数据策略                     |
| ---------- | ------------------ | --------------------------------------------- | ---------------------------- |
| **dev**    | 本地开发           | Docker Compose（仅依赖服务） + 本地 Python/Node | 本地 PostgreSQL 16，数据可重置 |
| **staging**| 预发布验证         | Docker Compose 全栈模拟生产                    | 独立 PostgreSQL 实例，匿名化生产数据 |
| **production** | 线上服务       | 云服务器（ECS / 自建）                         | 托管 PostgreSQL（如 Supabase / RDS） |

### 2.2 环境变量管理

```
sci-agent/
├── .env.dev              # 开发环境变量（提交到仓库，不含密钥）
├── .env.staging          # staging 环境变量模板
├── .env.prod             # 生产环境变量模板
└── .github/
    └── workflows/
        └── ...
```

**关键原则**：

| 变量类型     | 存放位置            | 示例                                  |
| ------------ | ------------------- | ------------------------------------- |
| 非敏感配置   | `.env.*` 文件       | `LOG_LEVEL=DEBUG`、`API_TIMEOUT=30`   |
| 敏感密钥     | GitHub Secrets      | `DATABASE_URL`、`OPENAI_API_KEY`、`JWT_SECRET` |
| 部署注入     | 服务器 `/etc/environment` 或 Docker secrets | `SENTRY_DSN`、`PROD_DB_PASSWORD`     |

**CI 中注入 Secrets 示例**：

```yaml
- name: Run migrations
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    JWT_SECRET: ${{ secrets.JWT_SECRET }}
  run: alembic upgrade head
```

### 2.3 数据库隔离

| 环境   | 数据库              | 隔离方式                             |
| ------ | ------------------- | ------------------------------------ |
| dev    | 本地 PostgreSQL 16  | Docker Compose 容器，端口 5432       |
| staging| 独立 PostgreSQL     | Docker Compose 内 `db-staging` 服务，端口 5433 |
| prod   | 托管 PostgreSQL     | 云提供商托管，连接池 `pgbouncer` 前置 |

**dev 环境 docker-compose.yml 数据库片段**：

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: sciagent
      POSTGRES_PASSWORD: devonly
      POSTGRES_DB: sciagent_dev
    ports:
      - "5432:5432"
    volumes:
      - pgdata_dev:/var/lib/postgresql/data

volumes:
  pgdata_dev:
```

---

## 3. 监控与可观测性

### 3.1 架构总览

```
App (Python / Next.js)
  │
  ├─→ Sentry SDK ───────────→ Sentry (错误追踪)
  ├─→ structlog → stdout ──→ Loki / ELK (日志聚合)
  └─→ Prometheus metrics ──→ Grafana (指标可视化 + 告警)
```

### 3.2 错误追踪：Sentry

#### Python 后端集成

```python
# backend/app/core/sentry.py
import sentry_sdk
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration

def init_sentry(dsn: str, environment: str):
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=0.1 if environment == "production" else 1.0,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
        ],
    )
```

#### Next.js 前端集成

```javascript
// frontend/sentry.client.config.js
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_ENV,
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.05,
  replaysOnErrorSampleRate: 1.0,
});
```

### 3.3 日志：structlog → Loki

#### Python 端配置

```python
# backend/app/core/logging.py
import structlog
import logging

def setup_logging(level: str = "INFO"):
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),  # 输出 JSON，便于 Loki 解析
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    logging.basicConfig(level=level, format="%(message)s")

logger = structlog.get_logger()
```

#### Docker Compose 集成 Loki + Promtail

```yaml
# docker-compose.observability.yml
services:
  loki:
    image: grafana/loki:2.9
    ports:
      - "3100:3100"

  promtail:
    image: grafana/promtail:2.9
    volumes:
      - /var/log:/var/log:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
```

### 3.4 指标：Prometheus + Grafana

#### Python 端暴露指标

```python
# backend/app/core/metrics.py
from prometheus_fastapi_instrumentator import Instrumentator

def setup_metrics(app):
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
```

#### 核心监控指标

| 指标名称                      | 类型      | 说明                        |
| ----------------------------- | --------- | --------------------------- |
| `http_requests_total`         | Counter   | API 总请求数                |
| `http_request_duration_seconds` | Histogram | API 延迟分布（P50/P95/P99） |
| `http_errors_total`           | Counter   | 5xx / 4xx 错误数            |
| `db_pool_size`                | Gauge     | 数据库连接池当前使用数      |
| `db_pool_overflow`            | Counter   | 连接池溢出次数              |
| `paper_search_duration_seconds` | Histogram | 论文检索耗时分布            |

#### Grafana Dashboard Key Panels

```
Row 1: 概览
  - 请求 QPS（Stat）
  - 平均延迟（Stat）
  - 错误率（Stat）

Row 2: 延迟分析
  - P50 / P95 / P99 延迟折线图

Row 3: 错误分析
  - 按 endpoint 分组的错误率热力图
  - 5xx vs 4xx 堆叠柱状图

Row 4: 数据库
  - DB 连接池使用率（Gauge）
  - 慢查询数（Counter）
```

### 3.5 告警规则

| 告警名称                    | 条件                            | 严重级别 | 通知渠道        |
| --------------------------- | ------------------------------- | -------- | --------------- |
| High Error Rate             | 5xx 错误率 > 5%（5 分钟内）     | Critical | PagerDuty + 企微 |
| API Latency Spike           | P95 延迟 > 2s（5 分钟内）       | Warning  | 企业微信        |
| DB Connection Pool Exhausted | 连接池利用率 > 90%             | Critical | PagerDuty + 企微 |
| Service Down                | `up` == 0                      | Critical | PagerDuty + 企微 |

**Prometheus 告警规则示例**：

```yaml
# prometheus-alerts.yml
groups:
  - name: sci-agent
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate: {{ $value | humanizePercentage }}"

      - alert: APILatencyHigh
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency > 2s"
```

---

## 4. 依赖安全扫描

### 4.1 Dependabot 配置

文件路径：`.github/dependabot.yml`

```yaml
version: 2
updates:
  # Python 依赖
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Asia/Shanghai"
    allow:
      - dependency-type: "all"
    labels:
      - "dependencies"
      - "python"
    open-pull-requests-limit: 5
    versioning-strategy: increase

  # npm 依赖
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Asia/Shanghai"
    labels:
      - "dependencies"
      - "javascript"
    open-pull-requests-limit: 5

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Asia/Shanghai"
```

### 4.2 pip-audit 集成到 CI

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  schedule:
    - cron: "0 9 * * 1"   # 每周一 09:00 UTC
  workflow_dispatch:       # 允许手动触发

jobs:
  pip-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install pip-audit
        run: pip install pip-audit

      - name: Audit Python dependencies
        run: pip-audit -r backend/requirements.txt --require-hashes

  npm-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Audit npm dependencies
        run: |
          cd frontend
          npm ci
          npm audit --audit-level=high
```

### 4.3 npm audit 策略

| 严重级别 | 行为                                   |
| -------- | -------------------------------------- |
| low      | 记录警告，不阻塞 CI                    |
| moderate | 记录警告，不阻塞 CI                    |
| high     | CI 失败，强制修复（`--audit-level=high`） |
| critical | CI 失败，强制修复                      |

对于短期无法修复的漏洞，使用 `.nsprc` 文件管理例外：

```json
{
  "1099999": {
    "active": true,
    "notes": "等待上游修复，暂无可用补丁",
    "expiry": "2026-09-01"
  }
}
```

---

## 5. 发布与回滚策略

### 5.1 Semantic Versioning

```
MAJOR.MINOR.PATCH

MAJOR：不兼容的 API 变更
MINOR：向后兼容的功能新增
PATCH：向后兼容的 Bug 修复
```

| 分支      | 版本号来源             | 示例  |
| --------- | ---------------------- | ----- |
| main      | `package.json` 中 `version` 字段 | 1.2.0 |
| PR 预览   | `v{version}-pre.{PR_NUMBER}` | 1.2.0-pre.42 |

### 5.2 Changelog 自动生成

使用 **release-please**（Google 出品）自动管理版本与 Changelog：

```yaml
# .github/workflows/release-please.yml
name: Release Please

on:
  push:
    branches: [main]

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          release-type: node
          package-name: sci-agent
          changelog-types: |
            [
              { "type": "feat", "section": "Features" },
              { "type": "fix", "section": "Bug Fixes" },
              { "type": "perf", "section": "Performance Improvements" },
              { "type": "docs", "section": "Documentation" },
              { "type": "refactor", "section": "Code Refactoring" }
            ]
```

**Commit 规范（Conventional Commits）**：

```
feat: add literature review module     → MINOR
fix: resolve paper parsing timeout     → PATCH
feat!: drop support for Python 3.10   → MAJOR（注意 `!`）
docs: update API reference             → 不触发版本变更
```

### 5.3 Docker 镜像标签策略

| 标签       | 含义                    | 何时推送           | 是否可回滚 |
| ---------- | ----------------------- | ------------------ | ---------- |
| `latest`   | 当前最新 stable         | 每次合入 main      | 否         |
| `{version}`| semver 版本号（如 `1.2.0`） | release-please 创建 release | 是 |
| `{git-sha}`| 短 commit hash（如 `a3f2b1c`） | 每次 build        | 是（精确回滚） |

**拉取指定版本用于回滚**：

```bash
# 回滚到 v1.1.0
docker pull ghcr.io/sci-agent/backend:1.1.0
docker pull ghcr.io/sci-agent/frontend:1.1.0
```

### 5.4 回滚流程

#### 自动回滚（CI 部署失败）

```yaml
# .github/workflows/deploy.yml
- name: Deploy
  run: |
    docker compose -f docker-compose.prod.yml pull
    docker compose -f docker-compose.prod.yml up -d

- name: Health Check
  run: |
    for i in $(seq 1 30); do
      STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.sci-agent.com/health)
      if [ "$STATUS" = "200" ]; then
        echo "Healthy"
        exit 0
      fi
      sleep 2
    done
    echo "Health check failed"

- name: Rollback on failure
  if: failure()
  run: |
    echo "Rolling back to previous version..."
    docker compose -f docker-compose.prod.yml down
    docker compose -f docker-compose.prod.yml up -d
```

#### 手动回滚步骤

| 步骤 | 命令                                                         | 说明                     |
| ---- | ------------------------------------------------------------ | ------------------------ |
| 1    | `git log --oneline -5`                                       | 确认回滚目标 commit      |
| 2    | `docker pull ghcr.io/sci-agent/backend:<TARGET_VERSION>`     | 拉取目标版本镜像         |
| 3    | `docker pull ghcr.io/sci-agent/frontend:<TARGET_VERSION>`    | 同上                     |
| 4    | `export TAG=<TARGET_VERSION> && docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml up -d` | 停机 + 替换镜像 + 启动   |
| 5    | `curl https://api.sci-agent.com/health`                      | 验证健康检查通过         |
| 6    | `docker logs sci-agent-backend --tail 50`                    | 观察日志确认无异常       |

#### 数据回滚（PostgreSQL）

> 镜像回滚不包含数据回滚。如需回滚数据库 schema：

```bash
# 回滚最近一次 migration
alembic downgrade -1

# 回滚到指定 revision
alembic downgrade {revision_id}
```

| 场景           | 策略                                          |
| -------------- | --------------------------------------------- |
| schema 兼容    | 向后兼容的 migration，只回滚镜像不回滚数据    |
| schema 不兼容  | 回滚镜像 + `alembic downgrade` 到匹配版本     |
| 数据损坏       | 从最近一次 `pg_dump` 备份恢复（见备份方案文档） |

---

## 附录 A：目录结构概览

```
sci-agent/
├── .github/
│   ├── workflows/
│   │   ├── lint.yml
│   │   ├── test.yml
│   │   ├── build.yml
│   │   ├── deploy.yml
│   │   ├── security-scan.yml
│   │   └── release-please.yml
│   └── dependabot.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       └── core/
│           ├── sentry.py
│           ├── logging.py
│           └── metrics.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── sentry.client.config.js
├── .env.dev
├── .env.staging
├── docker-compose.yml              # dev
├── docker-compose.staging.yml
├── docker-compose.prod.yml
├── docker-compose.observability.yml
├── prometheus-alerts.yml
└── promtail-config.yml
```

## 附录 B：快速检查清单

- [ ] `lint.yml`、`test.yml`、`build.yml` 已创建并在 CI 中通过
- [ ] `dependabot.yml` 已配置 pip + npm + GitHub Actions 三类 ecosystem
- [ ] Sentry DSN 已配置到 GitHub Secrets，`sentry_sdk.init()` 仅在 prod 启用低采样
- [ ] structlog 输出 JSON 格式日志，stdout 方式对接 Loki/Promtail
- [ ] `/metrics` 端点已暴露，Prometheus 可抓取
- [ ] Grafana Dashboard 已导入（ID 或 JSON 模型）
- [ ] PagerDuty 与企业微信 webhook 告警通道已配置
- [ ] release-please workflow 已基于 main 分支触发
- [ ] Docker 镜像标签同时包含 `latest`、`{version}`、`{git-sha}`
- [ ] 回滚脚本已测试通过（手动执行 `docker compose down && up`）
