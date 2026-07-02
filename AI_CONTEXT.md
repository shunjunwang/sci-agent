# Sci-Agent 项目上下文入口

> 最后更新：2026-07-02
> 文档版本快照：见 docs/MANIFEST.yaml

## 项目定位
国内唯一全链路科研垂直 Agent 平台。覆盖本硕博导师 → 高校三管理部门。
C 端订阅（99~268 元/年）+ B 端私有化（1.8w~12w）+ 增值分成。
3 阶段开发：30 天 MVP → 60 天商业化完整版 → 90 天完整壁垒顶配版。

## 技术栈
- 后端：Python FastAPI
- 前端：Next.js 16
- 桌面：Electron
- 数据库：PostgreSQL + pgvector
- 工作目录：D:\projects\sci-agent\
- 依赖环境：Docker（D:\docker）、WSL2
- 当前环境：C 盘仅 5GB，所有产出物必须放 D 盘

## 文档索引
**读取任何文档前，必须先读取 docs/MANIFEST.yaml 获取最新版本号和最后修改时间。**
文档版本以 MANIFEST.yaml 为准，不以下面标注的静态版本为准。

@docs/MANIFEST.yaml — 文档版本清单（单一真相源）
@docs/SPEC.md — API 契约、数据模型、模块规格
@docs/ARCHITECTURE.md — 技术架构、技术选型、ADR
@docs/AI_COLLABORATION.md — AI 协同铁律、Task 格式、分支规范
@docs/UI_LAYOUT.md — 三栏界面布局、CSS 变量、响应式
@docs/TEST_STRATEGY.md — 测试策略、AI 自动生成测试用例流程
@docs/PROGRESS.md — 开发进度、模块状态追踪
@docs/RISK_MANAGEMENT.md — 风险登记册、缓解措施
@docs/功能增强方案-对话管理_科研工具_加密格式.md — 增量功能方案
@docs/文档治理方案-AI多文档引用可靠性.md — 本文档体系的治理规范
@docs/防护体系与模型网关方案.md — 防破解+防抄袭+Model Gateway
@docs/CI-CD与运维基座方案.md — CI/CD+监控+发布回滚
@docs/计费与订阅系统方案.md — 定价+支付+订阅管理
@docs/备份恢复与安全加固方案.md — 备份恢复+API安全+依赖扫描
@docs/隐私政策与用户协议.md — PIPL/GDPR 合规
@docs/中国学术生态与工具链集成方案.md — CNKI/Zotero/Mendeley/GB/T 7714
@docs/用户体验与终端支持方案.md — 引导+i18n+帮助中心

## 自动化任务（已配置为定时执行）

| 任务 | 频率 | 时间 | 说明 |
|------|------|------|------|
| 每日进度汇报 | 每天 | 18:00 | 汇总当日 Git 提交 + 文件变更 + 文档清单，自动更新 PROGRESS.md |
| 每周技术雷达 | 每周一 | 09:00 | 扫描依赖过期 + 搜索技术栈更新 + 竞品动态，输出周报 |

**支撑脚本：**
- `scripts/auto_scheduler.py daily` — 每日快照（Git 统计 + 文件变更 + 文档状态）
- `scripts/auto_scheduler.py weekly` — 技术雷达（依赖检查 + 触发 AI 全网搜索）
- `scripts/auto_scheduler.py check` — 文档一致性检查（依赖链验证）
- `scripts/update_manifest.py` — 文档版本清单同步

## 文档清单自动同步

MANIFEST.yaml 通过 `scripts/update_manifest.py` 自动维护。
脚本逻辑：扫描 docs/*.md 和 AI_CONTEXT.md 的文件修改时间（mtime），与 MANIFEST.yaml 中记录的 last_modified 比对——变了就自动升版本号，新增文件自动注册。

**会话启动时自动执行：**
```powershell
python D:\projects\sci-agent\scripts\update_manifest.py --check
```
如有变更，自动执行完整更新并报告变化。

**老板手动触发（说以下任一即可）：**
- "更新文档清单"
- "同步文档版本"
- "检查文档变更"
- "MANIFEST 更新"

## AI 行为准则（Always Apply）

1. **入口先行**：每次会话开始，先读本文件 → 运行 update_manifest.py --check → 读 docs/MANIFEST.yaml
2. **按需加载**：根据任务类型选择相关文档，不要全部读取
3. **修改后自动同步**：生成或修改 docs/ 下的任何文档后，运行 `python scripts/update_manifest.py` 自动同步版本号
4. **新文档自动注册**：脚本会自动发现 docs/ 下的新 .md 文件并注册到 MANIFEST.yaml（category 默认为 uncategorized，记得补全 purpose 和 category）
5. **依赖链检查**：修改文档 A 时，检查 MANIFEST.yaml 中 A 的依赖链，对受影响文档做差异审查
6. **版本锚定**：引用文档内容时，以 MANIFEST.yaml 中标注的最新版本为准；发现版本不一致时，以 MANIFEST.yaml 为准并提醒
7. **会话结束记录**：每次会话结束前，在 .ai-memory/session-log.md 追加本次执行摘要
8. **路径铁律**：所有文件产出必须放在 D 盘（D:\projects\sci-agent\），禁止占用 C 盘
