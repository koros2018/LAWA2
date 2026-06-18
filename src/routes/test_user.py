"""
LAWA2 — 测试用户管理 API

用于开发和测试的测试用户管理。
仅管理员可访问 · Only admin users can access
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel, Field

from src.database.main import get_db
from src.engine.test_user_engine import TestUserEngine
from src.middleware.auth import require_admin
from src.models.user import User

router = APIRouter(prefix="/api/v2/test-users", tags=["test-users"])


class TestUserCreate(BaseModel):
    username: Optional[str] = Field(None, description="用户名，留空自动生成")
    display_name: Optional[str] = Field(None, description="显示名")
    native_lang: Optional[str] = Field("zh", description="母语")
    learn_lang: Optional[str] = Field("en", description="目标语言")
    current_level: Optional[str] = Field(None, description="当前水平: beginner/intermediate/advanced")
    interests: Optional[list[str]] = Field(None, description="兴趣标签")
    is_admin: bool = Field(False, description="是否管理员")


class TestUserReset(BaseModel):
    display_name: Optional[str] = Field(None, description="显示名")
    native_lang: Optional[str] = Field(None, description="母语")
    learn_lang: Optional[str] = Field(None, description="目标语言")
    current_level: Optional[str] = Field(None, description="当前水平")
    interests: Optional[list[str]] = Field(None, description="兴趣标签")


class TestUserListResponse(BaseModel):
    users: list[dict]
    total: int
    limit: int
    offset: int


class CleanupResponse(BaseModel):
    deleted_count: int
    message: str


# ── Routes ──

@router.get("/health")
async def test_user_health():
    """测试用户管理健康检查"""
    return {"status": "ok", "module": "test-user", "version": "1.0.0"}


@router.get("", response_model=TestUserListResponse)
async def list_test_users(
    admin_user: User = Depends(require_admin),
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
):
    """列出所有测试用户 · List test users"""
    users, total = await TestUserEngine.list_test_users(db, limit=limit, offset=offset)
    
    return TestUserListResponse(
        users=[{
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
            "native_lang": u.native_lang,
            "learn_lang": u.learn_lang,
            "current_level": u.current_level,
            "interests": u.interests,
            "is_admin": u.is_admin,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        } for u in users],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("")
async def create_test_user(
    admin_user: User = Depends(require_admin),
    data: TestUserCreate = None,
    db: AsyncSession = Depends(get_db),
):
    """创建测试用户 · Create test user"""
    profile = None
    if data:
        profile = {
            "display_name": data.display_name,
            "native_lang": data.native_lang,
            "learn_lang": data.learn_lang,
            "current_level": data.current_level,
            "interests": data.interests or [],
        }
    
    user = await TestUserEngine.create_test_user(
        db,
        username=data.username if data else None,
        profile=profile,
        is_admin=data.is_admin if data else False,
    )
    
    return {
        "status": "ok",
        "data": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat(),
        },
    }


@router.post("/default")
async def create_default_test_users(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """创建默认测试用户集合 · Create default test users"""
    users = await TestUserEngine.create_default_test_users(db)
    
    return {
        "status": "ok",
        "data": {
            "created": len(users),
            "users": [
                {
                    "id": u.id,
                    "username": u.username,
                    "display_name": u.display_name,
                    "current_level": u.current_level,
                }
                for u in users
            ],
        },
    }


@router.get("/{username}")
async def get_test_user(
    admin_user: User = Depends(require_admin),
    username: str = Path(..., description="测试用户名"),
    db: AsyncSession = Depends(get_db),
):
    """获取单个测试用户 · Get test user"""
    user = await TestUserEngine.get_test_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="测试用户不存在")
    
    return {
        "status": "ok",
        "data": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "native_lang": user.native_lang,
            "learn_lang": user.learn_lang,
            "current_level": user.current_level,
            "interests": user.interests,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "growth_xp": user.growth_xp,
            "habit_level": user.habit_level,
            "streak_days": user.streak_days,
            "bridge_level": user.bridge_level,
            "created_at": user.created_at.isoformat(),
        },
    }


@router.delete("/{username}")
async def delete_test_user(
    admin_user: User = Depends(require_admin),
    username: str = Path(..., description="测试用户名"),
    db: AsyncSession = Depends(get_db),
):
    """删除测试用户 · Delete test user"""
    success = await TestUserEngine.delete_test_user(db, username)
    if not success:
        raise HTTPException(status_code=404, detail="测试用户不存在")
    
    return {"status": "ok", "message": f"已删除测试用户 {username}"}


@router.post("/{username}/reset")
async def reset_test_user(
    admin_user: User = Depends(require_admin),
    username: str = Path(..., description="测试用户名"),
    data: TestUserReset = None,
    db: AsyncSession = Depends(get_db),
):
    """重置测试用户到初始状态 · Reset test user"""
    profile = None
    if data:
        profile = {
            "display_name": data.display_name,
            "native_lang": data.native_lang,
            "learn_lang": data.learn_lang,
            "current_level": data.current_level,
            "interests": data.interests,
        }
    
    user = await TestUserEngine.reset_test_user(db, username, profile)
    if not user:
        raise HTTPException(status_code=404, detail="测试用户不存在")
    
    return {
        "status": "ok",
        "message": f"已重置测试用户 {username}",
        "data": {
            "username": user.username,
            "growth_xp": user.growth_xp,
            "habit_level": user.habit_level,
            "streak_days": user.streak_days,
        },
    }


@router.delete("")
async def cleanup_test_users(
    admin_user: User = Depends(require_admin),
    older_than_hours: Optional[int] = Query(None, ge=1, description="清理创建时间早于 X 小时的用户"),
    db: AsyncSession = Depends(get_db),
):
    """清理测试用户 · Cleanup test users"""
    deleted_count = await TestUserEngine.cleanup_test_users(db, older_than_hours=older_than_hours)
    
    return CleanupResponse(
        deleted_count=deleted_count,
        message=f"已清理 {deleted_count} 个测试用户",
    )
