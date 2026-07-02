# AI 文档治理方案 — 多文档环境下如何让 AI 不出错

> 生成日期：2026-07-02
> 适用项目：Sci-Agent
> 核心问题：项目文档会持续增加和修改，AI 如何在每次会话中可靠地找到并引用最新版本？

---

## 一、问题诊断：AI 为什么会引错文档

每次 AI 会话从零开始，没有跨会话记忆。当前项目的文档治理存在三个缺口：

| 缺口 | 现象 | 后果 |
|------|------|------|
| **无入口索引** | AI 不知道项目有哪些文档、各自用途是什么 | 每次需要手动告知"你去读 XXX 文档" |
| **无版本锚定** | 文档改了但 AI 不知道改了什么、什么时候改的 | AI 引用旧版本内容，与新代码矛盾 |
| **无关联声明** | 改 A 文档不知道会影响 B 文档 | 文档间不一致，AI 读到矛盾信息 |

这不是 AI 的问题，是**文档没有被设计成 AI 可消费的格式**。

---

## 二、业界的解法

### 2.1 Cursor Rules（.cursor/rules/*.mdc）

Cursor 通过 `.mdc` 文件（Markdown + YAML frontmatter）实现规则的分级自动注入：

```
.cursor/rules/
├── always.mdc          # alwaysApply: true → 每次会话自动注入
├── react-patterns.mdc  # globs: "src/**/*.tsx" → 编辑 tsx 时自动注入
└── api-guidelines.mdc  # description: "API设计规范" → Agent 根据描述决定是否加载
```

核心机制：
- **frontmatter 元数据**：`description`（用途）、`globs`（文件匹配）、`alwaysApply`（是否常驻）
- **自动注入**：匹配到相关文件时自动拉入上下文，不需要人手动指定
- **版本控制**：`.cursor/rules/` 随代码一起进 Git，团队共享

### 2.2 Claude CODE（CLAUDE.md + 分层上下文）

Claude 采用更简洁的方案：

```
项目根目录/
├── CLAUDE.md              ← 每次会话自动读取（唯一入口）
│   @docs/architecture.md  ← 用 @ 引用其他文档，按需加载
│   @docs/database-schema.md
│
├── claude-context/        ← 上下文层（不是文档，是"AI 的可执行记忆"）
│   ├── 01-project-brief.md    # 项目总览
│   ├── 02-current-state.md    # 当前进度（SDLC 追踪）
│   ├── 03-execution-log.md    # 执行日志 + 快照锚点
│   └── 04-lessons-learned.md  # 踩坑记录
```

核心机制：
- **单一入口**：`CLAUDE.md` 是 AI 的唯一起点，里面用 `@路径` 引用真正的内容文档
- **分层加载**：入口文件轻量（只写指令和引用），正文留给被引用的文档
- **自动记忆**：Claude 会自己写 `claude-context/` 中的文件，记录学到的项目知识

### 2.3 三层记忆架构（CSDN 社区方案）

```
指令层  →  CLAUDE.md（行为协议，跨会话永久加载）
上下文层 →  claude-context/*.md（项目知识、进度、经验，按需引用）
执行层  →  03-execution-log.md（单次任务记录、快照锚点、可追溯）
```

关键洞察：**AI 的上下文文件不是"文档"，而是代码的一部分**——和源码一起版本控制、一起审查、一起回溯。

---

## 三、我方方案：AI_CONTEXT.md 入口 + 文档清单 + 版本锚定

### 3.1 总体架构

```
D:\projects\sci-agent\
│
├── AI_CONTEXT.md              ★ 唯一入口，AI 必须首先读取
│   （内容：项目定位 + 技术栈摘要 + 文档索引 + AI 行为准则）
│
├── docs/                      ★ 所有长期文档集中在此
│   ├── MANIFEST.yaml          ★ 文档清单（文件名、用途、版本、依赖关系）
│   ├── SPEC.md                # API 契约（已有）
│   ├── ARCHITECTURE.md        # 技术架构（已有）
│   ├── AI_COLLABORATION.md    # AI 协同规范（已有）
│   ├── UI_LAYOUT.md           # 界面布局（已有）
│   ├── TEST_STRATEGY.md       # 测试策略（已有）
│   ├── PROGRESS.md            # 进度追踪（已有）
│   ├── RISK_MANAGEMENT.md     # 风险管理（已有）
│   ├── 功能增强方案-*.md      # 功能增量方案（本次新增）
│   └── 文档治理方案.md        # 本文档
│
├── .ai-memory/                ★ AI 自动维护的跨会话记忆（不进 Git 的放这里）
│   └── session-log.md         # AI 每次任务结束后自动追加的执行摘要
│
└── src/                       # 源码
```

### 3.2 AI_CONTEXT.md — 核心入口文件

这是 AI 在每次会话开始时应首先读取的文件。内容设计原则：**极简、可索引、带版本锚点**。

```markdown
# Sci-Agent 项目上下文入口

> 最后更新：2026-07-02
> 文档版本快照：见 docs/MANIFEST.yaml

## 项目定位
国内唯一全链路科研垂直 Agent 平台。C 端订阅（99~268 元/年）+ B 端私有化。

## 技术栈
Python FastAPI + Next.js 16 + Electron + PostgreSQL/pgvector
工作目录：D:\projects\sci-agent\
依赖：Docker（D:\docker）、WSL2

## 文档索引
读取任何文档前，先检查 docs/MANIFEST.yaml 获取最新版本号和最后修改时间。

@docs/MANIFEST.yaml     ← 始终最新，从这里获取所有文档的版本锚点
@docs/SPEC.md            v1.0 | API 契约（唯一真相源）
@docs/ARCHITECTURE.md    v1.0 | 技术架构与 ADR
@docs/AI_COLLABORATION.md v1.0 | AI 协同铁律
@docs/UI_LAYOUT.md       v1.0 | 界面三栏布局规格
@docs/PROGRESS.md        v1.0 | 当前进度（查看模块状态前必读）
@docs/RISK_MANAGEMENT.md v1.0 | 风险登记册

## AI 行为准则（Always Apply）
1. 执行任何任务前，先读 AI_CONTEXT.md 和 docs/MANIFEST.yaml
2. 修改任何文档后，必须同步更新 MANIFEST.yaml 中的版本号和日期
3. 生成新文档后，必须将其注册到 MANIFEST.yaml
4. 文档引用矛盾时，以 MANIFEST.yaml 中标注的最新版本为准
5. 每次会话结束前，在 .ai-memory/session-log.md 追加执行摘要
```

### 3.3 MANIFEST.yaml — 文档版本清单

这是解决"AI 不知道文档是否最新"的核心机制。

```yaml
# 文档清单 — AI 读取任何文档前先检查此文件
# 格式：文件名: {用途, 版本, 最后修改日期, 依赖(哪些文档修改会影响本文档)}

manifest_version: "1.0"
last_updated: "2026-07-02T15:30:00+08:00"

documents:
  SPEC.md:
    purpose: "API 契约，所有模块的接口定义和数据模型"
    version: "1.0"
    last_modified: "2026-07-02"
    dependencies: []
    category: "core"

  ARCHITECTURE.md:
    purpose: "技术架构、技术选型、架构决策记录(ADR)"
    version: "1.0"
    last_modified: "2026-07-02"
    dependencies: ["SPEC.md"]
    category: "core"

  AI_COLLABORATION.md:
    purpose: "AI 协同开发规范、Task 格式、分支策略、禁止事项"
    version: "1.0"
    last_modified: "2026-07-02"
    dependencies: []
    category: "governance"

  UI_LAYOUT.md:
    purpose: "三栏界面布局规格、CSS 变量、组件树、响应式规则"
    version: "1.0"
    last_modified: "2026-07-02"
    dependencies: ["SPEC.md"]
    category: "design"

  TEST_STRATEGY.md:
    purpose: "测试金字塔、AI 自动生成测试用例流程"
    version: "1.0"
    last_modified: "2026-07-02"
    dependencies: ["SPEC.md", "ARCHITECTURE.md"]
    category: "governance"

  PROGRESS.md:
    purpose: "开发进度追踪、模块状态表"
    version: "1.0"
    last_modified: "2026-07-02"
    dependencies: ["SPEC.md"]
    category: "tracking"

  RISK_MANAGEMENT.md:
    purpose: "风险登记册、缓解措施、触发条件"
    version: "1.0"
    last_modified: "2026-07-02"
    dependencies: []
    category: "governance"

  功能增强方案-对话管理_科研工具_加密格式.md:
    purpose: "对话搜索/管理、科研工具扩展、.scix 加密格式增量方案"
    version: "1.0"
    last_modified: "2026-07-02"
    dependencies: ["SPEC.md", "UI_LAYOUT.md"]
    category: "feature"

  文档治理方案.md:
    purpose: "AI 如何可靠引用多版本文档的治理规范"
    version: "1.0"
    last_modified: "2026-07-02"
    dependencies: []
    category: "governance"

# 文档间依赖链（修改 A 时必须检查 B 是否需要同步更新）
dependency_chains:
  - chain: ["SPEC.md", "ARCHITECTURE.md", "TEST_STRATEGY.md"]
    rule: "SPEC 变更 → 检查架构和测试策略是否需要更新"
  - chain: ["SPEC.md", "UI_LAYOUT.md", "功能增强方案-对话管理*.md"]
    rule: "SPEC 或 UI 变更 → 检查功能增量方案是否受影响"
  - chain: ["SPEC.md", "PROGRESS.md"]
    rule: "模块 API 变更 → 更新进度表中的对应模块状态"
```

### 3.4 .ai-memory/session-log.md — AI 执行日志

每次会话结束后，AI 自动追加执行摘要。格式要求：一行标题 + 三行关键信息。

```markdown
# AI 执行日志

## 2026-07-02 15:30 | 功能增强方案调研
- 交付：docs/功能增强方案-对话管理_科研工具_加密格式.md（v1.0）
- MANIFEST 更新：已注册
- 备注：四个功能均已提供竞品调研+实现方案+排期

## 2026-07-02 14:00 | 项目文档体系建立
- 交付：ARCHITECTURE.md, AI_COLLABORATION.md, TEST_STRATEGY.md, PROGRESS.md, RISK_MANAGEMENT.md（均 v1.0）
- MANIFEST 更新：已注册
- 备注：5 份文档对照 SPEC.md 生成，形成完整治理体系
```

### 3.5 AI 工作流：读文档的正确姿势

```
每次会话开始时，AI 应执行以下 SOP：

┌──────────────────────────────────────┐
│ Step 1: 读取 AI_CONTEXT.md           │ ← 知道项目是什么、文档在哪
├──────────────────────────────────────┤
│ Step 2: 读取 docs/MANIFEST.yaml      │ ← 知道每个文档的最新版本和日期
├──────────────────────────────────────┤
│ Step 3: 根据任务类型，按需读取文档    │ ← 只在需要时读，不清空上下文
│   例：写 UI 代码 → 读 UI_LAYOUT.md   │
│   例：加 API    → 读 SPEC.md         │
│   例：评估风险  → 读 RISK_MANAGEMENT │
├──────────────────────────────────────┤
│ Step 4: 执行任务                     │
├──────────────────────────────────────┤
│ Step 5: 如有产出，更新 MANIFEST.yaml │ ← 注册新文档/更新版本号+日期
│ Step 6: 追加 .ai-memory/session-log  │ ← 记录本次做了什么
└──────────────────────────────────────┘
```

### 3.6 文档修改的连锁检查规则

当修改文档 A 时，AI 必须：

1. 查 MANIFEST.yaml 中 A 的 `dependencies` 字段——A 依赖的文档如果没变，A 的引用仍然有效
2. 查 MANIFEST.yaml 中 `dependency_chains`——修改 A 会影响链上的哪些文档
3. 对受影响文档做**差异检查**：打开受影响的文档，搜索对 A 中变更内容的引用，判断是否需要同步更新
4. 更新 MANIFEST.yaml：A 的 `version` +1，`last_modified` 更新，受影响文档标注"待审查"

---

## 四、优先级与落地

所有内容落实到 `D:\projects\sci-agent\` 下：

| 文件 | 状态 | 说明 |
|------|------|------|
| `AI_CONTEXT.md` | **本次创建** | 入口文件 |
| `docs/MANIFEST.yaml` | **本次创建** | 文档版本清单 |
| `.ai-memory/session-log.md` | **本次创建** | AI 执行日志 |
| 已有 7 份文档 | 已存在 | 按 MANIFEST 注册 |

后续每次 AI 会话，我会自动遵循这个流程。

---

## 五、为什么不搞更复杂的方案

| 被排除的方案 | 原因 |
|--------------|------|
| Git Hooks 自动更新 MANIFEST | 过度工程化，AI 手动更新足够；1 人项目不需要自动化 |
| 独立文档数据库 | 引入额外依赖（MongoDB/Elasticsearch），不符合 MVP 阶段原则 |
| 文档内容哈希校验 | 小改动（修正错别字）不应触发依赖文档的连锁审查 |
| .cursor/rules/ 格式 | 我们不是 Cursor 项目，不需要绑定特定 IDE |

当前方案的核心思想：**用极简机制解决 80% 的问题**——AI 每次会话只多读 2 个文件（AI_CONTEXT.md + MANIFEST.yaml），换来的是所有文档引用的确定性。

---

## 附录：与已有文档体系的对应关系

| 已有文档 | 在本方案中的角色 |
|----------|------------------|
| SPEC.md | 唯一真相源，MANIFEST 中标注为核心文档 |
| AI_COLLABORATION.md | AI 行为准则的详细版，AI_CONTEXT.md 作为其摘要索引 |
| ARCHITECTURE.md | 技术决策文档，依赖 SPEC.md |
| PROGRESS.md | 进度追踪，AI 每次完成模块后更新 |
| RISK_MANAGEMENT.md | 风险管理，新增风险时同步检查其他文档是否有新依赖 |
| UI_LAYOUT.md | 设计规格，前端任务时必读 |
| TEST_STRATEGY.md | 测试规范，依赖 SPEC + ARCHITECTURE |
