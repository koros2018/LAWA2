"""
LAWA2 — 简化 FastAPI 入口

只加载习惯引擎 + 简化认证路由。
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.config import settings
from src.database.main import init_db, close_db
from src.routes.habit import router as habit_router
from src.routes.simple_auth import router as simple_auth_router
from src.routes.bridge import router as bridge_router
from src.routes.reminder import router as reminder_router
from src.routes.photo import router as photo_router
from src.routes.admin import router as admin_router
import src.models  # 确保所有模型在 init_db 前注册


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info(f"🌿 {settings.app_name} v{settings.app_version} 启动中...")
    logger.info(f"   端口: {settings.api_port}")
    logger.info(f"   数据库: {settings.db_host}:{settings.db_port}/{settings.db_name}")

    await init_db()
    logger.info("✅ 数据库连接成功")

    yield

    await close_db()
    logger.info("👋 LAWA 服务关闭")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(habit_router)
app.include_router(simple_auth_router)
app.include_router(bridge_router)
app.include_router(reminder_router)
app.include_router(photo_router)
app.include_router(admin_router)
from src.routes.github_auth import router as github_auth_router
app.include_router(github_auth_router)

# JWT 认证中间件（在所有路由之后注册，在 CORS 之后）
from src.middleware.auth_middleware import AuthMiddleware
app.add_middleware(AuthMiddleware)


# ── 健康检查 ──
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/api/v1/health")
async def api_health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "database": settings.db_name,
    }