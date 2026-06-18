"""
LAWA2 — 超级管理员 Agent API

端点:
  GET    /api/v2/admin/users       — 用户列表（支持 search/limit/offset）
  GET    /api/v2/admin/users/:id   — 用户详情
  POST   /api/v2/admin/users/:id/toggle — 切换用户激活状态
  GET    /api/v2/admin/stats       — 系统统计数据

权限: 仅管理员可访问 · Only admin users can access
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from loguru import logger

from src.database.main import get_db
from src.engine.admin_engine import admin_engine
from src.models.user import User
from src.middleware.auth import require_admin

router = APIRouter(prefix="/api/v2/admin", tags=["admin"])


# 管理员权限检查统一从 src.middleware.auth 导入


@router.get("/users")
async def list_users(
    admin_user: User = Depends(require_admin),
    search: Optional[str] = Query(None, description="搜索用户名/显示名"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """用户列表 · User list (admin only)"""
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
    admin_user: User = Depends(require_admin),
    user_id: str = Path(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """用户详情 · User detail (admin only)"""
    user = await admin_engine.get_user_detail(user_id=user_id, db=db)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"status": "ok", "data": user}


@router.post("/users/{user_id}/toggle")
async def toggle_user(
    admin_user: User = Depends(require_admin),
    user_id: str = Path(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """切换用户激活状态 · Toggle user active status (admin only)"""
    user = await admin_engine.toggle_user_active(user_id=user_id, db=db)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"status": "ok", "data": user}


@router.get("/stats")
async def system_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """系统统计数据 · System statistics (admin only)"""
    stats = await admin_engine.get_system_stats(db=db)
    return {"status": "ok", "data": stats}


@router.post("/users/{user_id}/admin")
async def set_admin(
    admin_user: User = Depends(require_admin),
    user_id: str = Path(..., description="User ID"),
    is_admin: bool = Query(..., description="Admin status"),
    db: AsyncSession = Depends(get_db),
):
    """设置用户管理员权限 · Set user admin status (super admin only)"""
    # 只能由管理员设置管理员权限
    result = await admin_engine.set_admin_status(user_id, is_admin, db)
    if not result:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"status": "ok", "data": result}