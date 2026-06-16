"""
LAWA2 — JWT 认证中间件

提供 FastAPI 依赖注入函数，用于保护需要认证的路由。
从请求头 `Authorization: Bearer <token>` 中提取并验证 JWT token。
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from src.middleware.jwt_token import verify_token

# FastAPI Security 方案
_bearer_scheme = HTTPBearer(
    auto_error=False,  # 不自动报错，让调用方决定是否可选
)


def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> str:
    """
    从 Bearer Token 中提取当前用户 ID（必须认证）
    
    用于需要强制认证的路由。
    
    Raises:
        HTTPException 401 — 无 token 或 token 无效
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证 token · Missing auth token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期 · Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 载荷无效 · Invalid token payload",
        )

    return user_id


def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[str]:
    """
    从 Bearer Token 中提取当前用户 ID（可选认证）
    
    用于不需要强制认证的路由（有 token 就验证，没有也允许）。
    """
    if credentials is None:
        return None

    payload = verify_token(credentials.credentials)
    if payload is None:
        return None

    return payload.get("sub")