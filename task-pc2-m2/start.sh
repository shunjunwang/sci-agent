#!/bin/bash
# PC2 M2 文献检索 - 启动脚本

echo "=== PC2 M2 文献检索任务包 ==="
echo "目标：科应 API 对接 + 多源文献检索"

# 检查 Python 版本
python --version

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r backend/requirements.txt

# 复制环境变量
if [ ! -f "backend/.env" ]; then
    echo "复制环境变量模板..."
    cp ../../.env.example backend/.env
    echo "请编辑 backend/.env 配置 API 密钥"
fi

# 启动服务
echo "启动文献检索服务..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 服务启动后提示
echo "文献检索服务已启动："
echo "- API 文档：http://localhost:8001/docs"
echo "- 健康检查：http://localhost:8001/api/v2/health"
echo "- 文献搜索：http://localhost:8001/api/v2/papers/search?q=关键词"