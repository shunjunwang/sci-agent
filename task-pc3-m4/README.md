# PC3 任务包：M4 前端 Desktop 壳

## 任务目标
- **模块**：M4 前端 Desktop 壳
- **负责人**：PC3
- **目标日期**：2026-07-27
- **依赖**：M0 基础设施（已完成）

## 核心任务
1. **Electron 项目初始化**
   - 创建 Electron + Next.js 集成项目
   - 配置开发环境（热重载、打包脚本）
   - 实现主进程/渲染进程通信

2. **基础 UI 框架搭建**
   - 集成主项目的前端组件（shadcn/ui）
   - 实现三栏布局（UI_LAYOUT.md 规格）
   - 添加导航菜单、状态栏、设置面板

3. **与 Next.js 前端集成**
   - 将现有 Next.js 前端嵌入 Electron
   - 实现文件系统访问（本地文件读写）
   - 添加系统托盘、全局快捷键

## 项目结构
```
task-pc3-m4/
├── desktop/                 # Electron 桌面应用
│   ├── main/               # 主进程代码
│   ├── preload/            # 预加载脚本
│   ├── renderer/           # 渲染进程（Next.js 前端）
│   ├── resources/          # 应用图标等资源
│   └── package.json        # Electron 依赖
├── docs/                   # 设计文档
├── start.sh                # 启动脚本
└── README.md               # 本文件
```

## 技术栈
- **桌面框架**：Electron 30+
- **前端**：Next.js 16.2 + React 19 + TypeScript
- **UI 组件**：shadcn/ui + Tailwind CSS v4
- **构建工具**：electron-forge / electron-builder
- **状态管理**：Zustand + React Query

## 启动方式
```bash
# 1. 安装依赖
cd desktop
npm install

# 2. 开发模式启动
npm run dev

# 3. 打包应用
npm run make
```

## 功能规划
1. **主窗口**
   - 三栏布局（导航、内容、侧边栏）
   - 响应式设计（支持窗口大小调整）
   - 暗黑/亮色主题切换

2. **系统集成**
   - 文件系统访问（读取/保存本地文件）
   - 系统托盘图标
   - 全局快捷键（Ctrl+Shift+S 等）
   - 通知中心

3. **应用功能**
   - 用户登录/注册
   - 文献检索界面
   - 个人知识库管理
   - AI 写作辅助

## 验收标准
1. ✅ Electron 应用可正常启动
2. ✅ Next.js 前端完整嵌入
3. ✅ 三栏布局实现
4. ✅ 文件系统访问功能
5. ✅ 可打包为 exe/dmg 安装包

## Git 分支
- 开发分支：`ai/pc3-m4`
- 目标分支：`main`（通过 PR 合并）

## 注意事项
- 保持与主项目前端代码同步
- 遵循 `UI_LAYOUT.md` 布局规格
- 注意 Electron 安全策略（上下文隔离、内容安全策略）
- 每日更新进度到 `PROGRESS.md`

---
**创建时间**：2026-07-02  
**任务状态**：待分配  
**负责人**：PC3 AI Agent