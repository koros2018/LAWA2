#!/bin/bash
# LAWA2 部署脚本 v4.5.0
# 用法: ./deploy.sh [dev|staging|prod]
# 
# 环境变量:
#   BACKEND_PORT  - 后端端口 (默认: 6290)
#   FRONTEND_PORT - 前端端口 (默认: 6292)
#   DEPLOY_ENV    - 部署环境 (默认: prod)

set -e

ENV=${1:-prod}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT=${BACKEND_PORT:-6290}
FRONTEND_PORT=${FRONTEND_PORT:-6292}

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "========================================"
echo "  LAWA2 部署脚本 v4.5.0"
echo "  环境: $ENV"
echo "========================================"
echo ""

# ── 1. 检查 Git ──
log_info "检查 Git 状态..."
cd "$PROJECT_DIR"
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    log_error "不是 Git 仓库"
    exit 1
fi

# ── 2. 拉取最新代码 ──
log_info "拉取最新代码..."
git fetch origin
CURRENT_BRANCH=$(git branch --show-current)
git pull origin "$CURRENT_BRANCH"

# ── 3. 检查依赖 ──
log_info "检查依赖..."

# Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 未安装"
    exit 1
fi

# Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js 未安装"
    exit 1
fi

# uv (Python 包管理器)
if ! command -v uv &> /dev/null; then
    log_warn "uv 未安装，尝试安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# ── 4. 后端构建 ──
log_info "后端构建..."
cd "$PROJECT_DIR"

# 同步依赖
uv sync --frozen

# 运行测试
log_info "运行后端测试..."
uv run python -m pytest tests/test_habit_engine.py -v --tb=short -q

if [ $? -ne 0 ]; then
    log_error "后端测试失败"
    exit 1
fi
log_info "后端测试通过 ✅"

# ── 5. 前端构建 ──
log_info "前端构建..."
cd "$PROJECT_DIR/frontend"

# 安装依赖（如果需要）
if [ ! -d "node_modules" ]; then
    log_info "安装前端依赖..."
    npm install
fi

# 构建
npx vite build

if [ $? -ne 0 ]; then
    log_error "前端构建失败"
    exit 1
fi
log_info "前端构建完成 ✅"

# ── 6. 部署到生产环境 ──
if [ "$ENV" = "prod" ]; then
    log_info "生产环境部署..."
    
    # 检查 nginx 配置（可选）
    if [ -f "/etc/nginx/sites-available/lawa2" ]; then
        log_info "检查 Nginx 配置..."
        nginx -t
    fi
    
    # 重启服务（根据实际部署方式调整）
    # 方式 1: systemd
    # sudo systemctl restart lawa2-backend
    # sudo systemctl restart lawa2-frontend
    
    # 方式 2: PM2
    # sudo pm2 restart lawa2-backend
    # sudo pm2 restart lawa2-frontend
    
    # 方式 3: Docker
    # docker-compose -f docker-compose.prod.yml up -d
    
    log_warn "请根据实际情况重启服务"
    log_info "  后端: http://localhost:$BACKEND_PORT"
    log_info "  前端: http://localhost:$FRONTEND_PORT"
fi

# ── 7. 健康检查 ──
log_info "健康检查..."
sleep 3

# 检查后端
log_info "检查后端..."
if curl -s --max-time 5 "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
    log_info "后端健康 ✅"
else
    log_warn "后端未响应 (可能未启动)"
fi

# 检查前端
log_info "检查前端..."
if curl -s --max-time 5 "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
    log_info "前端健康 ✅"
else
    log_warn "前端未响应 (可能未启动)"
fi

# ── 8. 清理 ──
log_info "清理临时文件..."
cd "$PROJECT_DIR"
git status --porcelain | grep '^??' | cut -c4- | xargs -r rm -rf 2>/dev/null || true

echo ""
echo "========================================"
log_info "部署完成！"
echo "========================================"
echo ""
echo "下一步:"
echo "  1. 访问 http://localhost:$FRONTEND_PORT 验证前端"
echo "  2. 访问 http://localhost:$BACKEND_PORT/health 验证后端"
echo "  3. 检查浏览器控制台是否有错误"
echo "  4. 验证 PWA 功能 (manifest.json + sw.js)"
echo ""
