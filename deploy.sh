#!/bin/bash
# LAWA2 部署脚本 v4.5.0 (简化版)
# 用法: ./deploy.sh [dev|staging|prod]

set -e

ENV=${1:-prod}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT=${BACKEND_PORT:-6290}
FRONTEND_PORT=${FRONTEND_PORT:-6292}

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1"; }

echo "========================================"
echo "  LAWA2 部署脚本 v4.5.0"
echo "  环境: $ENV"
echo "========================================"

# ── 1. 后端测试 ──
log_info "运行后端测试..."
cd "$PROJECT_DIR"
python3 -m pytest tests/test_habit_engine.py -v --tb=short -q 2>&1 | tail -5

# ── 2. 前端构建 ──
log_info "前端构建..."
cd "$PROJECT_DIR/frontend"
npx vite build 2>&1 | tail -5

log_info "前端构建完成 ✅"

# ── 3. 健康检查 ──
log_info "健康检查..."
sleep 2

if curl -s --max-time 3 "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
    log_info "后端健康 ✅"
else
    log_warn "后端未响应 (可能未启动)"
fi

if curl -s --max-time 3 "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
    log_info "前端健康 ✅"
else
    log_warn "前端未响应 (可能未启动)"
fi

echo ""
log_info "部署完成！"
echo ""
