#!/bin/bash
# PC3 M4 前端 Desktop 壳 - 启动脚本

echo "=== PC3 M4 前端 Desktop 壳任务包 ==="
echo "目标：Electron + Next.js 桌面应用"

# 检查 Node.js 版本
node --version
npm --version

# 进入项目目录
cd desktop

# 安装依赖
echo "安装依赖..."
npm install

# 检查环境配置
if [ ! -f ".env.local" ]; then
    echo "创建环境配置..."
    cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_PAPER_API_URL=http://localhost:8001/api/v2
NEXT_PUBLIC_APP_NAME=SciAgent
EOF
    echo "环境配置已创建（可手动编辑 .env.local）"
fi

# 启动开发模式
echo "启动 Electron 开发模式..."
echo ""
echo "开发服务器启动中..."
npm run dev

# 服务启动后提示
echo ""
echo "应用启动完成："
echo "- Electron 窗口将自动打开"
echo "- 修改代码后自动热重载"
echo "- Ctrl+C 停止服务"
echo ""
echo "快捷操作："
echo "- 打开 DevTools：F12"
echo "- 强制刷新：Ctrl+R"
echo "- 退出应用：关闭窗口"