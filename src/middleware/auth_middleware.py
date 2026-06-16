"""
LAWA2 — JWT Token 验证中间件

全局中间件，在每个请求处理前验证 Authorization header 中的 JWT token。
验证通过后将 user_id 注入到 request.state.user_id。
路由可以通过 `request.state.user_id` 获取当前用户 ID。

白名单：认证相关的端点不需要 token。
"""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status
from loguru import logger
from src.middleware.jwt_token import verify_token

# 不需要 token 的白名单路径前缀
_AUTH_WHITELIST = [
    "/health",
    "/api/v1/health",
    "/api/v2/auth/login",
    "/api/v2/auth/profile",
    "/api/v2/auth/github/login",
    "/api/v2/auth/github/callback",
    "/api/v2/auth/me",
    "/api/v2/reminder/seed-holidays",
    "/api/v2/reminder/holidays",
]

# 环境变量控制是否强制 token 验证
# 开发阶段设为 false 保持向下兼容
_ENFORCE_AUTH = os.environ.get("LAWA2_ENFORCE_AUTH", "false").lower() == "true"


class AuthMiddleware(BaseHTTPMiddleware):
    """
    全局 JWT 认证中间件
    
    验证 Authorization: Bearer <token>。
    没有 token 时：如果 _ENFORCE_AUTH 为 true 则拒绝请求，否则允许（向下兼容）。
    """

    async def dispatch(self, request: Request, call_next):
        # 白名单路径跳过
        path = request.url.path
        if any(path.startswith(p) for p in _AUTH_WHITELIST):
            return await call_next(request)

        # 从 Authorization header 提取 token
        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if token:
            payload = verify_token(token)
            if payload:
                # 注入 user_id
                request.state.user_id = payload.get("sub", "")
                return await call_next(request)
            else:
                # Token 无效
                if _ENFORCE_AUTH:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "status": "error",
                            "detail": "Token 无效或已过期 · Invalid or expired token",
                        },
                    )
                # 开发模式：token 无效但允许继续（用 query 参数）
                logger.debug(f"Token 无效但开发模式允许: {path}")

        if _ENFORCE_AUTH:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "status": "error",
                    "detail": "缺少认证 token · Missing auth token",
                },
            )

        # 开发模式：无 token 时设置空 user_id
        request.state.user_id = ""
        return await call_next(request)