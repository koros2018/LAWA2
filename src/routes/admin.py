"""
LAWA2 — 超级管理员 Agent API

端点:
  GET    /api/v2/admin/users       — 用户列表（支持 search/limit/offset）
  GET    /api/v2/admin/users/:id   — 用户详情
  POST   /api/v2/admin/users/:id/toggle — 切换用户激活状态
  GET    /api/v2/admin/stats       — 系统统计数据
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from loguru import logger

from src.database.main import get_db
from src.engine.admin_engine import admin_engine

router = APIRouter(prefix="/api/v2/admin", tags=["admin"])


@router.get("/users")
async def list_users(
    search: Optional[str] = Query(None, description="搜索用户名/显示名"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """用户列表"""
    users = await admin_engine.get_users(
        db=db, search=search, limit=limit, offset=offset
    )
    total = await admin_engine.get_user_count(db)
    return {
        "status": "ok",
        "data": {
            "users": users,
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """用户详情"""
    user = await admin_engine.get_user_detail(user_id=user_id, db=db)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"status": "ok", "data": user}


@router.post("/users/{user_id}/toggle")
async def toggle_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """切换用户激活状态"""
    user = await admin_engine.toggle_user_active(user_id=user_id, db=db)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"status": "ok", "data": user}


@router.get("/stats")
async def system_stats(
    db: AsyncSession = Depends(get_db),
):
    """系统统计数据"""
    stats = await admin_engine.get_system_stats(db=db)
    return {"status": "ok", "data": stats}