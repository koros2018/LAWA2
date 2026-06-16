"""
LAWA2 — 用户 ID 解析依赖注入

提供一个统一的 `get_user_id` 依赖，优先从 JWT token 解析用户 ID，
没有 token 时从 query/form 参数中获取（向下兼容旧模式）。
"""
from fastapi import Depends, Query
from typing import Optional

from src.middleware import get_optional_user_id


def get_user_id(
    token_user_id: Optional[str] = Depends(get_optional_user_id),
    user_id_query: str = Query("", alias="user_id"),
) -> str:
    """
    获取当前用户 ID
    
    优先级：
    1. JWT Bearer Token 中的 sub
    2. Query 参数 user_id（向下兼容）
    3. Form 参数 user_id
    
    如果都为空则返回空字符串。
    """
    if token_user_id:
        return token_user_id
    return user_id_query
