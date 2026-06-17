"""
LAWA2 — 简化登录 & 用户画像 API
不搞 OAuth 仪式感，选个名字就进了。
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.main import get_db
from src.models.user import User
from src.middleware.jwt_token import create_token

router = APIRouter(prefix="/api/v2/auth", tags=["auth"])


def _utcnow():
    return datetime.now(timezone.utc)


# ── 请求/响应模型 ──

class LoginRequest(BaseModel):
    """免密码登录"""
    username: str = "default_user"
    native_lang: str = "zh"  # zh | en


class ProfileRequest(BaseModel):
    """用户画像"""
    username: str
    display_name: str
    native_lang: str = "zh"  # 母语
    learn_lang: str = "en"  # 目标语言
    interests: list[str] = []  # 兴趣标签
    current_level: Optional[str] = None  # 初始水平


class ProfileResponse(BaseModel):
    user_id: str
    username: str
    display_name: str
    native_lang: str
    learn_lang: str
    interests: list[str]
    current_level: Optional[str] = None
    is_new_user: bool


# ── 端点 ──

@router.post("/login")
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    免密码登录 / 自动注册
    
    - 用户存在 → 返回已有信息
    - 用户不存在 → 创建新用户（未初始化画像）
    """
    result = await db.execute(
        select(User).where(User.username == req.username)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=str(uuid.uuid4()),
            username=req.username,
            display_name=req.username,
            native_lang=req.native_lang,
            learn_lang="en",
            interests=[],
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"新用户自动注册: {user.username} ({user.id[:8]}...)")
        return {
            "status": "ok",
            "data": {
                "user_id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "native_lang": user.native_lang,
                "learn_lang": user.learn_lang,
                "has_profile": False,
                "is_new_user": True,
                "is_admin": user.is_admin,
                "token": create_token(user.id, user.username),
            }
        }

    # 已有用户 → 判断是否完成了画像
    has_profile = bool(user.interests) or bool(user.current_level)
    return {
        "status": "ok",
        "data": {
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name or user.username,
            "native_lang": user.native_lang,
            "learn_lang": user.learn_lang,
            "interests": user.interests or [],
            "current_level": user.current_level,
            "has_profile": has_profile,
            "is_new_user": not has_profile,
            "is_admin": user.is_admin,
                "token": create_token(user.id, user.username),
        }
    }


@router.post("/profile")
async def save_profile(
    req: ProfileRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    保存用户画像
    
    登录后第一次访问时调用。保存语言方向、兴趣、初始水平。
    之后进入养成主界面。
    """
    result = await db.execute(
        select(User).where(User.username == req.username)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.display_name = req.display_name
    user.native_lang = req.native_lang
    user.learn_lang = req.learn_lang
    user.interests = req.interests
    user.current_level = req.current_level
    user.updated_at = _utcnow()

    # 创建用户的习惯配置（如果不存在）
    from src.models.habit import UserHabitConfig
    config_check = await db.execute(
        select(UserHabitConfig).where(UserHabitConfig.user_id == user.id)
    )
    if not config_check.scalar_one_or_none():
        config = UserHabitConfig(user_id=user.id)
        db.add(config)

    await db.commit()
    await db.refresh(user)

    logger.info(
        f"用户画像已保存: {user.username} "
        f"{user.native_lang}→{user.learn_lang} "
        f"兴趣={user.interests} 水平={user.current_level}"
    )

    return {
        "status": "ok",
        "data": {
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "native_lang": user.native_lang,
            "learn_lang": user.learn_lang,
            "interests": user.interests or [],
            "current_level": user.current_level,
            "has_profile": True,
            "is_new_user": False,
                "token": create_token(user.id, user.username),
        }
    }


@router.get("/me")
async def get_current_user_info(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户信息（用于 OAuth 回调后前端加载用户资料）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "status": "ok",
        "data": {
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "native_lang": user.native_lang,
            "learn_lang": user.learn_lang,
            "interests": user.interests or [],
            "current_level": user.current_level,
            "avatar_url": user.avatar_url,
            "email": user.email,
            "is_admin": user.is_admin,
        },
    }


@router.post("/refresh")
async def refresh_token(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """刷新 JWT Token（延长有效期）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    token = create_token(user.id, user.username)
    return {"status": "ok", "data": {"token": token}}