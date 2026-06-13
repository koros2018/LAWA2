"""LAWA2 FastAPI 入口 — 最小化启动"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.database.main import init_db
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 {settings.app_name} v{settings.app_version} 启动中...")
    await init_db()
    logger.info("✅ 数据库已初始化")
    yield
    logger.info("👋 LAWA2 已关闭")


app = FastAPI(
    title="LAWA2 - 语言习惯引擎",
    description="养成式语言习惯引擎 API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 注册习惯引擎路由（直接 import 避免走 __init__.py） ──

import importlib
habit_mod = importlib.import_module('src.routes.habit')
app.include_router(habit_mod.router)


@app.get("/")
async def root():
    return {"app": "LAWA2", "version": "2.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.api_port, reload=True)
