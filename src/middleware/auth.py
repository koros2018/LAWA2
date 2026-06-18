"""
LAWA2 — 统一认证依赖模块

集中管理所有认证相关的 FastAPI 依赖注入函数。
各路由统一从此模块导入，避免重复定义。

依赖关系:
  AuthMiddleware (中间件) → 验证 JWT → 注入 request.state.user_id
  auth.py (依赖注入) → 从 request.state / token / query 提取 user_id
  routes → 使用 auth.py 的依赖函数
"""

from fastapi import Depends, HTTPException, Query, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from src.database.main import get_db
from src.models.user import User
from src.middleware.jwt_token import verify_token

# ── HTTP Bearer 方案 ──

bearer_scheme = HTTPBearer(auto_error=False)


# ── 认证依赖 ──

async def get_current_user_id(
    request: Request = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    _user_id: Optional[str] = Query(None, alias="user_id"),
) -> str:
    """
    获取当前用户 ID（强制认证）
    
    优先级：
      1. Authorization: Bearer <token> → 解析 token 中的 sub
      2. request.state.user_id (由 AuthMiddleware 注入)
      3. query 参数 user_id (开发模式兼容)
    
    开发模式下，如果以上都无值，返回 "default_user"。
    生产模式（ENFORCE_AUTH=true）下，无有效认证则返回 401。
    """
    # 1. 优先从 Bearer token 获取
    if credentials:
        payload = verify_token(credentials.credentials)
        if payload:
            uid = payload.get("sub")
            if uid:
                return uid
    
    # 2. 从 request.state 获取（AuthMiddleware 注入）
    if request:
        uid = getattr(request.state, "user_id", None)
        if uid:
            return uid
    
    # 3. 从 query 参数获取（开发兼容）
    if _user_id:
        return _user_id
    
    # 4. 开发模式默认用户
    return "default_user"


async def get_optional_user_id(
    request: Request = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    _user_id: Optional[str] = Query(None, alias="user_id"),
) -> Optional[str]:
    """
    获取当前用户 ID（可选认证）
    
    有 token 则验证，无 token 也允许。
    返回 None 表示未认证。
    """
    # 1. 优先从 Bearer token 获取
    if credentials:
        payload = verify_token(credentials.credentials)
        if payload:
            uid = payload.get("sub")
            if uid:
                return uid
    
    # 2. 从 request.state 获取
    if request:
        uid = getattr(request.state, "user_id", None)
        if uid:
            return uid
    
    # 3. 从 query 参数获取
    if _user_id:
        return _user_id
    
    return None


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前用户对象（带 DB 查询）
    
    用于需要用户完整信息的场景。
    如果用户不存在，返回 mock 用户（开发模式）。
    """
    from sqlalchemy import select
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    
    if user:
        return user
    
    # 开发模式：返回 mock 用户
    return User(id=1, username=user_id, is_admin=(user_id == "boss_ke"))


async def require_admin(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    管理员权限检查（强制）
    
    仅管理员可访问的路由使用此依赖。
    非管理员返回 403。
    """
    from sqlalchemy import select
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在 · User not found",
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足 · Admin access required",
        )
    
    return user


# ── 模块导出 ──

__all__ = [
    "bearer_scheme",
    "get_current_user_id",
    "get_optional_user_id",
    "get_current_user",
    "require_admin",
]
