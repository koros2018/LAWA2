"""
LAWA2 — JWT Token 工具

提供 token 签发、验证、解析功能。
使用 HS256 签名，密钥从环境变量读取。
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from loguru import logger

# 密钥优先从环境变量读取，否则生成随机密钥（每次重启会失效）
_SECRET_KEY = os.environ.get("LAWA2_JWT_SECRET") or "lawa2-dev-secret-key-2026-32bytes!"

# 算法
_ALGORITHM = "HS256"

# Token 有效期（默认 7 天）
_TOKEN_EXPIRE_DAYS = int(os.environ.get("LAWA2_JWT_EXPIRE_DAYS", "7"))


def create_token(
    user_id: str,
    username: str,
    expires_days: Optional[int] = None,
) -> str:
    """
    签发 JWT Token
    
    Args:
        user_id: 用户 ID
        username: 用户名
        expires_days: 过期天数（默认 7 天）
    
    Returns:
        JWT token 字符串
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=expires_days or _TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user_id,
        "username": username,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),  # Token 唯一 ID，可用于吊销
    }

    token = jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)
    return token


def verify_token(token: str) -> Optional[dict]:
    """
    验证 JWT Token
    
    Args:
        token: JWT token 字符串
    
    Returns:
        解码后的 payload（dict），验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            _SECRET_KEY,
            algorithms=[_ALGORITHM],
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token 已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT token 无效: {e}")
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """从 token 中提取用户 ID"""
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None