---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 0a3495d31457bedac983287cb94ad373_faa11b6d75ac11f1a7da5254006c9bbf
    ReservedCode1: 0vwwcnNthHURxzj6uW6d3dpHQcMLTUMYg+RTebrnIlA1sByjvjXbPVazf8ENgA2qEiqvMMvDFsnLV1FY5KXaEmILW3lNMsDOgDlWP5/vl1NSet0GajwsRA7evC3TxNKfs1T/mmjhz+TmzDJyiSQLbKJzCiTFQaFSfftmcoKUeH5qOmBEEwT3cjGr1SI=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 0a3495d31457bedac983287cb94ad373_faa11b6d75ac11f1a7da5254006c9bbf
    ReservedCode2: 0vwwcnNthHURxzj6uW6d3dpHQcMLTUMYg+RTebrnIlA1sByjvjXbPVazf8ENgA2qEiqvMMvDFsnLV1FY5KXaEmILW3lNMsDOgDlWP5/vl1NSet0GajwsRA7evC3TxNKfs1T/mmjhz+TmzDJyiSQLbKJzCiTFQaFSfftmcoKUeH5qOmBEEwT3cjGr1SI=
---

# RISK_MANAGEMENT.md — sci-agent 风险管理与应急

> 版本：v1.0 | 最后更新：2026-07-02

---

## 1. 风险登记表

### 风险分级标准

| 等级 | 概率范围 | 影响范围 | 响应时间 |
|------|---------|---------|---------|
| 🔴 严重 | 高概率 + 高影响 | 项目停滞 ≥ 2 天 | 立即 |
| 🟡 中等 | 中概率 + 中影响 | 进度延迟 1-2 天 | 24h 内 |
| 🟢 轻微 | 低概率 / 低影响 | 个别模块微调 | 安排到下一迭代 |

---

### 已识别风险清单

| 编号 | 描述 | 概率 | 影响 | 等级 | 缓解措施 | 应急预案 | 触发条件 |
|------|------|------|------|------|---------|---------|---------|
| **R1** | Docker/WSL 环境问题导致 PG 无法启动 | 高 | 高 | 🔴 | 1. 提供详细环境配置文档；2. 准备 Windows 原生 PG 安装包作为备选；3. 在 `scripts/dev.ps1` 中检测环境 | 切换到 Windows 原生 PostgreSQL 16，修改 `DATABASE_URL` 为本地连接 | Docker Compose 启动失败且 30min 内无法修复 |
| **R2** | 科应API 限流或接口变更 | 中 | 高 | 🔴 | 1. 实现本地缓存（懒加载策略）；2. HTTP 重试 + 指数退避；3. 与科应技术支持建立联系 | 启动本地缓存兜底模式，仅返回已缓存文献；新检索提示「服务暂时不可用」 | API 返回 429/503 持续 > 10min |
| **R3** | C 盘空间不足导致构建失败 | 高 | 中 | 🟡 | 1. Docker data-root 设为 `D:\docker-data`；2. npm cache 设为 `D:\npm-cache`；3. WSL 发行版导出到 D 盘；4. `scripts/check_deps.py` 检查剩余空间 | 清理临时文件 + Docker prune；紧急时可手动扩容 C 盘（DiskPart）或使用 D 盘符号链接 | `npm install` 或 `docker build` 失败 + 错误含 "no space left" |
| **R4** | AI 生成代码质量问题（模块间接口对不上） | 高 | 中 | 🟡 | 1. SPEC 作为唯一真相源；2. 跨模块修改声明制度；3. CI 类型检查 + 集成测试强制通过 | 回退到上一稳定版本，由人类开发者手动对齐接口后重新分配 | 两个模块联调时出现 3+ 个接口不匹配 |
| **R5** | Electron 打包兼容性问题 | 中 | 中 | 🟡 | 1. 开发阶段即保持 Electron 可运行；2. 使用 `electron-builder` 标准配置；3. Win10/11 双平台测试 | 降级到纯 Web 模式部署（Nginx 反向代理），桌面壳延后 | `electron-builder` 打包失败且 4h 内无法解决 |
| **R6** | pgvector 性能不达预期（向量检索慢） | 低 | 高 | 🟡 | 1. 早期对 `paper_embeddings` 表建 IVFFlat 索引；2. 限制单次检索返回 ≤ 100 条；3. 设计 `EMBEDDING_BACKEND` 可切换架构 | 1. 调大 `ivfflat.probes` 参数；2. 降级为纯关键词检索 + 本地 TF-IDF；3. 评估迁移到 Qdrant/Milvus 独立向量库 | 单次向量检索耗时 > 2s 且无法通过索引调优改善 |
| **R7** | 一人开发模式下时间估算偏差 | 高 | 中 | 🟡 | 1. 每个模块预留 20% buffer；2. 每日进度日志追踪偏差；3. AI 承担重复性工作（测试/文档/CRUD） | 根据 PROGRESS.md 实际进度，每 2 周重新评估里程碑日期 | 连续 3 天进度滞后 ≥ 1 天 |

---

## 2. 已识别风险详细分析

### R1：Docker/WSL 环境问题

**场景**：Windows 开发环境下 Docker Desktop 依赖 WSL2，WSL2 内核更新或 Windows Update 可能导致 Docker 无法启动、PostgreSQL 容器无法运行。

**预防措施清单**：
- [ ] Docker Desktop → Settings → Resources → Advanced → Disk image location: `D:\docker-data`
- [ ] `wsl --export Ubuntu D:\wsl\ubuntu.tar` + `wsl --import Ubuntu D:\wsl\Ubuntu D:\wsl\ubuntu.tar`
- [ ] `scripts/check_deps.py` 增加 WSL2 / Docker / PG 可用性检查
- [ ] `docker-compose.yml` 中 PG 数据挂载到宿主机目录（非 Docker volume），方便紧急迁移

**恢复步骤**：
1. 执行 `docker-compose down`
2. 切换到 Windows 原生 PG：`pg_ctl start -D D:\postgresql\data`
3. 更新 `.env`：`DATABASE_URL=postgresql+asyncpg://sciagent:password@localhost:5432/sciagent`
4. 运行 `alembic upgrade head` 恢复 schema
5. 通知所有 AI Agent：数据库地址已变更

### R2：科应API 限流

**场景**：科应API 免费/基础套餐限流 1000 次/天，开发/测试阶段频繁调用可能触发限流。

**预防措施清单**：
- [ ] `keying_client.py` 实现请求计数与本地限流
- [ ] 测试用例全部使用 mock，不消耗真实配额
- [ ] 论文搜索结果自动写入本地 `papers` 表，设置 TTL 7 天
- [ ] 开发阶段使用预置的种子数据（`scripts/seed_data.py`）

**恢复步骤**：
1. 检测到 `429 Too Many Requests` → 暂停所有科应API调用
2. 前端展示「检索服务暂时繁忙，正在使用本地缓存」
3. 所有文献查询仅走本地 `papers` 表
4. 等待 1 小时后自动恢复（指数退避）

### R3：C 盘空间不足

**场景**：C 盘（系统盘）仅剩不足 10GB，Docker 镜像 + node_modules + npm cache 极易占满。

**预防措施清单**：
- [ ] `D:\docker-data` 作为 Docker 数据根目录
- [ ] `npm config set cache D:\npm-cache`
- [ ] `yarn config set cache-folder D:\yarn-cache`
- [ ] `.gitignore` 中忽略 `node_modules`（各仓独立安装）
- [ ] 每月执行 `docker system prune -a` 清理无用镜像

**紧急清理脚本** (`scripts/cleanup_space.ps1`)：
```powershell
Write-Output "当前 C 盘剩余: $((Get-PSDrive C).Free / 1GB) GB"
docker system prune -a -f
Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
npm cache clean --force
Write-Output "清理完成"
```

### R4：AI 代码质量问题

**场景**：不同 AI Agent 并行开发，各自理解 SPEC 的偏差导致模块间接口不匹配。

**预防措施清单**：
- [ ] AI_COLLABORATION.md 强制每个 Agent 读 SPEC
- [ ] Pydantic Schema 和 TypeScript 类型定义对齐检查（CI 脚本）
- [ ] 每个模块至少 1 个集成测试验证接口契约
- [ ] 每周人类开发者审查 SPEC ↔ 代码一致性

**检测机制**：
```python
# scripts/check_api_consistency.py
# 解析 SPEC.md 的 API 端点 → 比对实际路由注册 → 输出差异报告
```

---

## 3. 应急响应流程

```
风险触发
    │
    ▼
[AI Agent 检测到异常]
    │
    ├── 可自动修复？──→ 执行应急预案 → 记录到 PROGRESS.md
    │
    └── 需人工介入
            │
            ▼
        1. 立即更新 RISK_MANAGEMENT.md（标记触发状态）
        2. 更新 PROGRESS.md 第3节（阻塞项）
        3. 通过 ask_user 通知人类开发者
        4. 提供诊断信息：
           - 错误日志
           - 影响的模块
           - 建议的修复方向
        5. 等待人类决策
```

### 紧急联系方式（示例）

| 问题类型 | 联系方 | 响应时间 |
|---------|--------|---------|
| 科应API 故障 | 科应技术支持 | 工作日 4h |
| 混元API 故障 | 腾讯云工单 | 工作日 2h |
| Docker/WSL 问题 | 查阅官方文档 + GitHub Issues | — |

---

## 4. 版本回滚策略

### 4.1 代码回滚

```bash
# 回滚到上一个稳定版本
git log --oneline -10                    # 查看历史
git revert <commit_hash> --no-edit       # 回滚单个提交
git reset --hard <tag>                   # 硬回滚到标签版本

# 稳定版本标签规范：v0.1.0-m0 (M0完成后) / v0.2.0-m2 (M2完成后)
```

### 4.2 数据库回滚

```bash
# Alembic 回滚最近一次迁移
cd backend
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>

# ⚠️ 回滚前必须备份
pg_dump sciagent > D:\backups\sciagent_$(date +%Y%m%d).sql
```

### 4.3 回滚决策树

```
问题发现
    │
    ├── 仅前端问题 → 回滚前端 + 重新部署
    │
    ├── 仅后端问题 → 回滚后端代码 + 检查是否需要回滚 DB
    │       │
    │       ├── Schema 变更 → alembic downgrade + 回滚代码
    │       └── 仅代码变更 → git revert
    │
    └── 前后端都出问题 → 全量回滚到上一个稳定标签
            │
            └── 检查数据完整性 → 通知用户短暂不可用
```

---

## 5. 风险复查日历

| 时间 | 动作 |
|------|------|
| 每日 | AI Agent 检查：C盘空间、Docker 运行状态、科应API可达性 |
| 每周一 | 更新风险概率/影响评估 |
| 每波结束 | 全量风险审计 + 新增风险识别 |
| 发布前 | 全部风险缓解措施执行确认 |

---

*本文档与 PROGRESS.md 联动，风险触发时须同时更新两份文档。*
*（内容由AI生成，仅供参考）*
