#!/bin/bash
# ============================================================
# P0-8: SciAgent Docker Compose 一键启动脚本
# 用法: bash scripts/start.sh
# ============================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== SciAgent Docker Compose 一键部署 ==="
echo "项目目录: $PROJECT_DIR"
echo ""

# 检查 .env.docker 是否存在
if [ ! -f ".env.docker" ]; then
    echo "[错误] 未找到 .env.docker，请先创建配置文件"
    exit 1
fi

# 启动所有服务
echo "[1/3] 启动服务 (backend + postgres + redis + frontend)..."
docker compose up -d --build

# 等待健康检查
echo "[2/3] 等待服务就绪..."
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker compose ps | grep -q "healthy"; then
        ALL_HEALTHY=true
        for svc in sciagent-backend sciagent-postgres; do
            if ! docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null | grep -q "healthy"; then
                ALL_HEALTHY=false
                break
            fi
        done
        if [ "$ALL_HEALTHY" = true ]; then
            echo "  ✓ 所有服务健康就绪"
            break
        fi
    fi
    sleep 3
    WAITED=$((WAITED + 3))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "  ⚠ 部分服务可能未完全就绪，请手动检查"
fi

# 输出访问地址
echo ""
echo "[3/3] 部署完成！"
echo "============================================"
echo "  后端 API:     http://localhost:8000"
echo "  Swagger 文档: http://localhost:8000/docs"
echo "  前端界面:     http://localhost:3000"
echo "  PostgreSQL:   localhost:5432"
echo "  Redis:        localhost:6379"
echo "============================================"
echo ""
echo "查看日志: docker compose logs -f"
echo "停止服务: bash scripts/stop.sh"
