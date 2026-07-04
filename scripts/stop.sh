#!/bin/bash
# ============================================================
# P0-8: SciAgent Docker Compose 停止脚本
# 用法: bash scripts/stop.sh
# ============================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== 停止 SciAgent 所有服务 ==="

docker compose down

echo ""
echo "所有服务已停止。"
echo "如需清理数据卷: docker compose down -v"
