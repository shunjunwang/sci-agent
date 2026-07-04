# PC2 任务包：M2 文献检索

## 任务目标
- **模块**：M2 文献检索
- **负责人**：PC2
- **目标日期**：2026-07-20
- **依赖**：M0 基础设施（已完成）

## 核心任务
1. **科应 API 对接调研**
   - 获取科应开放平台 API 文档
   - 测试 API 可用性（搜索、详情、下载）
   - 设计认证与限流策略

2. **文献检索模块设计**
   - 设计多源聚合架构（科应 + arXiv + PubMed + CNKI）
   - 定义统一文献数据模型
   - 设计缓存策略（Redis / SQLite）

3. **实现核心功能**
   - 关键词搜索
   - 高级检索（作者、期刊、年份、DOI）
   - 文献详情获取
   - PDF 下载代理

## 项目结构
```
task-pc2-m2/
├── backend/                 # 文献检索后端
│   ├── app/
│   │   ├── api/v2/         # 文献检索 API
│   │   ├── core/           # 核心逻辑
│   │   ├── models/         # 文献数据模型
│   │   └── services/       # 科应 API 服务
│   ├── tests/              # 单元测试
│   └── requirements.txt    # Python 依赖
├── docs/                   # 设计文档
├── start.sh                # 启动脚本
└── README.md               # 本文件
```

## 技术栈
- **后端**：FastAPI + SQLAlchemy + aiosqlite
- **缓存**：Redis（可选）或 SQLite 内存表
- **异步**：httpx（HTTP 客户端）
- **测试**：pytest + pytest-asyncio

## 启动方式
```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## API 端点规划
- `GET /api/v2/papers/search?q=关键词` - 文献搜索
- `GET /api/v2/papers/{paper_id}` - 文献详情
- `GET /api/v2/papers/{paper_id}/pdf` - PDF 下载
- `GET /api/v2/sources` - 可用数据源列表

## 验收标准
1. ✅ 科应 API 可正常调用
2. ✅ 搜索功能返回结构化结果
3. ✅ 支持至少 2 个数据源
4. ✅ API 文档完整（Swagger）
5. ✅ 单元测试覆盖率 > 70%

## Git 分支
- 开发分支：`ai/pc2-m2`
- 目标分支：`main`（通过 PR 合并）

## 注意事项
- 保持与主项目架构一致（FastAPI + SQLite）
- 环境变量从 `.env.example` 同步
- 代码风格遵循 `PYTHON_STYLE_GUIDE.md`
- 每日更新进度到 `PROGRESS.md`

---
**创建时间**：2026-07-02  
**任务状态**：待分配  
**负责人**：PC2 AI Agent