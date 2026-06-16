"""
LAWA2 — GitHub OAuth 登录路由

流程：
1. 前端点击「GitHub 登录」→ 跳转 GitHub OAuth 授权页
2. 用户授权 → GitHub 回调 redirect_uri（带 code）
3. 后端用 code 换 access_token
4. 后端用 access_token 获取用户信息（昵称、头像、邮箱等）
5. 查找/创建用户 → 签发 JWT token → 重定向回前端
"""
import uuid
import httpx
from datetime import datetime, timezone
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.main import get_db
from src.models.user import User
from src.middleware.jwt_token import create_token

# ── 配置 ──
# 从环境变量读取，没有则用空字符串（运行时会报明确错误）
import os

GITHUB_CLIENT_ID = os.environ.get("LAWA2_GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("LAWA2_GITHUB_CLIENT_SECRET", "")
# 回调地址：开发阶段用 localhost，生产阶段改为部署域名
GITHUB_REDIRECT_URI = os.environ.get(
    "LAWA2_GITHUB_REDIRECT_URI",
    "http://localhost:6290/api/v2/auth/github/callback",
)

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API = "https://api.github.com/user"

router = APIRouter(prefix="/api/v2/auth", tags=["github-auth"])


@router.get("/github/login")
async def github_login_redirect(state: str = "lawa2_login"):
    """
    生成 GitHub OAuth 登录 URL

    前端直接 location.href = 此 URL，用户跳转到 GitHub 授权页。
    授权后重定向到 GITHUB_REDIRECT_URI。
    """
    if not GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth 未配置（缺少 LAWA2_GITHUB_CLIENT_ID）",
        )

    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "read:user user:email",
        "state": state,
    }
    url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    return {"status": "ok", "data": {"login_url": url}}


@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query("lawa2_login"),
    db: AsyncSession = Depends(get_db),
):
    """
    GitHub OAuth 回调

    用户授权后 GitHub 重定向到此端点。
    后端用 code 换 access_token → 获取用户信息 → 创建/查找用户 → 签发 token。
    """
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth 未配置（缺少 LAWA2_GITHUB_CLIENT_ID 或 SECRET）",
        )

    # 1. 用 code 换取 access_token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
        )
        token_data = token_resp.json()

    if "error" in token_data:
        logger.error(f"GitHub token 换取失败: {token_data}")
        raise HTTPException(status_code=400, detail="GitHub 登录失败")

    access_token = token_data["access_token"]

    # 2. 获取用户信息
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            GITHUB_USER_API,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        github_user = user_resp.json()

    if "id" not in github_user:
        logger.error(f"GitHub 用户信息获取失败: {github_user}")
        raise HTTPException(status_code=400, detail="获取用户信息失败")

    github_id = str(github_user["id"])
    login = github_user["login"]
    name = github_user.get("name") or login
    avatar_url = github_user.get("avatar_url", "")
    email = github_user.get("email") or ""

    # 3. 获取用户邮箱（如果 scope 包含 user:email 且 email 为 null）
    if not email:
        async with httpx.AsyncClient() as client:
            email_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            emails = email_resp.json()
            if isinstance(emails, list):
                primary = next((e for e in emails if e.get("primary")), None)
                if primary:
                    email = primary.get("email", "")

    # 4. 查找或创建用户（通过 github_id 关联）
    result = await db.execute(
        select(User).where(User.github_id == github_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        # 新用户 → 自动注册
        user = User(
            id=str(uuid.uuid4()),
            username=f"github_{login}",
            display_name=name,
            github_id=github_id,
            github_login=login,
            avatar_url=avatar_url,
            email=email,
            native_lang="zh",
            learn_lang="en",
            interests=[],
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"GitHub 用户自动注册: {name} (@{login}) [{user.id[:8]}]")
        is_new = True
    else:
        # 更新信息
        user.display_name = name
        user.github_login = login
        user.avatar_url = avatar_url
        if email:
            user.email = email
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        is_new = False

    # 5. 签发 JWT token
    token = create_token(user.id, user.username)

    # 6. 重定向回前端（带上 token）
    frontend_url = (
        f"http://localhost:6292/oauth-callback"
        f"?token={token}"
        f"&user_id={user.id}"
        f"&is_new={str(is_new).lower()}"
        f"&provider=github"
    )
    return RedirectResponse(url=frontend_url)
