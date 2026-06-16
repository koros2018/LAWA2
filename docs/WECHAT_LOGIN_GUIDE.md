# LAWA2 — 微信扫码登录接入指南

> 本文档提供从零开始接入微信开放平台网站扫码登录的完整步骤。
> 包括：微信开放平台注册 → 应用创建 → 后端 API 实现 → 前端集成。

---

## 一、前置准备

### 1.1 注册微信开放平台

1. 访问 [https://open.weixin.qq.com/](https://open.weixin.qq.com/)
2. 点击「注册」→ 选择「开发者资质认证」
3. 填写邮箱、密码，完成邮箱激活
4. **注意**：个人开发者需要完成 **300 元/年** 的认证费用。企业开发者需要营业执照。

### 1.2 创建网站应用

1. 登录开放平台 → 「管理中心」→ 「创建网站应用」
2. 填写应用信息：
   - **应用名称**: LAWA2
   - **应用简介**: 语言暨世界智能体 — 养成式英语学习引擎
   - **网站域名**: 你的服务器域名（开发阶段可以是 `localhost`）
   - **网站根目录**: `http://localhost:6292`（前端端口）
   - **回调域名**: `localhost`（开发阶段）
3. 提交审核（审核通过后获得 `AppID` 和 `AppSecret`）

### 1.3 申请微信登录权限

1. 应用创建后 → 「功能」→ 「微信登录」→ 点击「申请开通」
2. 微信登录默认与网站应用审核同步，通过后自动获得 `snsapi_login` 作用域

---

## 二、后端 API 实现

### 2.1 需要的依赖

```bash
pip install httpx  # 用于调用微信 API
```

### 2.2 微信登录配置

创建 `src/config.py`：

```python
"""
LAWA2 — 全局配置
"""
import os

# 微信开放平台
WECHAT_APP_ID = os.environ.get("LAWA2_WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.environ.get("LAWA2_WECHAT_APP_SECRET", "")
WECHAT_REDIRECT_URI = os.environ.get(
    "LAWA2_WECHAT_REDIRECT_URI",
    "http://localhost:6290/api/v2/auth/wechat/callback",
)

# JWT
JWT_SECRET = os.environ.get("LAWA2_JWT_SECRET", "lawa2-dev-secret-key-2026-32bytes!")
```

### 2.3 微信登录路由

创建 `src/routes/wechat_auth.py`：

```python
"""
LAWA2 — 微信扫码登录路由

流程：
1. 前端点击「微信登录」→ 跳转微信 OAuth 页面（或内嵌二维码）
2. 用户扫码确认 → 微信回调 redirect_uri（带 code）
3. 后端用 code 换 access_token + openid
4. 后端用 access_token 获取用户信息（昵称、头像等）
5. 查找/创建用户 → 签发 JWT token → 重定向回前端
"""
import uuid
import httpx
from datetime import datetime, timezone
from urllib.parse import urlencode, quote
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.main import get_db
from src.models.user import User
from src.middleware.jwt_token import create_token
from src.config import WECHAT_APP_ID, WECHAT_APP_SECRET, WECHAT_REDIRECT_URI

router = APIRouter(prefix="/api/v2/auth", tags=["wechat-auth"])

WECHAT_AUTHORIZE_URL = "https://open.weixin.qq.com/connect/qrconnect"
WECHAT_TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"
WECHAT_USERINFO_URL = "https://api.weixin.qq.com/sns/userinfo"


@router.get("/wechat/login")
async def wechat_login_redirect(state: str = "lawa2_login"):
    """
    生成微信扫码登录 URL（跳转模式）
    前端直接 location.href = 此 URL，用户看到微信二维码页。
    扫码确认后重定向到 WECHAT_REDIRECT_URI。
    """
    params = {
        "appid": WECHAT_APP_ID,
        "redirect_uri": quote(WECHAT_REDIRECT_URI, safe=""),
        "response_type": "code",
        "scope": "snsapi_login",
        "state": state,
    }
    url = f"{WECHAT_AUTHORIZE_URL}?{urlencode(params, safe=':,?/')}#wechat_redirect"
    return {"status": "ok", "data": {"login_url": url}}


@router.get("/wechat/callback")
async def wechat_callback(
    code: str = Query(...),
    state: str = Query("lawa2_login"),
    db: AsyncSession = Depends(get_db),
):
    """
    微信登录回调
    用户扫码确认后，微信重定向到此端点。
    后端用 code 换 access_token → 获取用户信息 → 创建/查找用户 → 签发 token。
    """
    # 1. 用 code 换取 access_token
    async with httpx.AsyncClient() as client:
        token_resp = await client.get(
            WECHAT_TOKEN_URL,
            params={
                "appid": WECHAT_APP_ID,
                "secret": WECHAT_APP_SECRET,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_resp.json()

    if "errcode" in token_data:
        logger.error(f"微信 token 换取失败: {token_data}")
        raise HTTPException(status_code=400, detail="微信登录失败")

    access_token = token_data["access_token"]
    openid = token_data["openid"]

    # 2. 获取用户信息
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            WECHAT_USERINFO_URL,
            params={"access_token": access_token, "openid": openid},
        )
        user_info = user_resp.json()

    if "errcode" in user_info:
        logger.error(f"微信用户信息获取失败: {user_info}")
        raise HTTPException(status_code=400, detail="获取用户信息失败")

    nickname = user_info.get("nickname", f"wx_{openid[:8]}")
    headimgurl = user_info.get("headimgurl", "")

    # 3. 查找或创建用户
    result = await db.execute(select(User).where(User.wechat_openid == openid))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=str(uuid.uuid4()),
            username=f"wx_{openid[:12]}",
            display_name=nickname,
            wechat_openid=openid,
            wechat_avatar=headimgurl,
            native_lang="zh",
            learn_lang="en",
            interests=[],
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"微信用户自动注册: {nickname} ({user.id[:8]}...)")
        is_new = True
    else:
        user.display_name = nickname
        user.wechat_avatar = headimgurl
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        is_new = False

    # 4. 签发 JWT token
    token = create_token(user.id, user.username)

    # 5. 重定向回前端
    frontend_url = (
        f"http://localhost:6292/wechat-callback"
        f"?token={token}&user_id={user.id}&is_new={str(is_new).lower()}"
    )
    return RedirectResponse(url=frontend_url)


@router.post("/wechat/bind")
async def bind_wechat(
    user_id: str = Query(...),
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """已有 LAWA2 账号绑定微信"""
    async with httpx.AsyncClient() as client:
        token_resp = await client.get(
            WECHAT_TOKEN_URL,
            params={
                "appid": WECHAT_APP_ID,
                "secret": WECHAT_APP_SECRET,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_resp.json()
    if "errcode" in token_data:
        raise HTTPException(status_code=400, detail="微信授权失败")

    openid = token_data["openid"]

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    existing = await db.execute(select(User).where(User.wechat_openid == openid))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该微信已被其他用户绑定")

    user.wechat_openid = openid
    await db.commit()
    return {"status": "ok", "data": {"wechat_bound": True}}
```

### 2.4 注册路由

在 `src/main.py` 中添加：

```python
from src.routes.wechat_auth import router as wechat_auth_router
app.include_router(wechat_auth_router)
```

### 2.5 用户模型添加微信字段

在 `src/models/user.py` 中添加：

```python
class User(Base):
    # ... 现有字段 ...
    
    wechat_openid = Column(String(128), unique=True, nullable=True, index=True)
    wechat_avatar = Column(String(512), nullable=True)
```

---

## 三、前端集成

### 方案 A：跳转模式（简单，推荐 MVP）

**LoginPage.vue 微信按钮：**

```vue
<button class="wechat-btn" @click="wechatLogin">
  <span class="wechat-icon">💬</span>
  <span>微信登录 · WeChat Login</span>
</button>

<script setup>
function wechatLogin() {
  window.location.href = '/api/v2/auth/wechat/login'
}
</script>
```

**WechatCallbackPage.vue：**

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { setSession } from '@/store/session'

const router = useRouter()
const route = useRoute()

onMounted(() => {
  const token = route.query.token as string
  const userId = route.query.user_id as string
  const isNew = route.query.is_new === 'true'

  if (token && userId) {
    localStorage.setItem('lawa2_session', JSON.stringify({
      userId, token,
      hasProfile: !isNew,
      isNewUser: isNew,
    }))
    router.push(isNew ? '/onboarding' : '/')
  } else {
    router.push('/login')
  }
})
</script>

<template>
  <div class="loading-page">
    <div class="loading-spinner"></div>
    <p>正在登录 · Logging in...</p>
  </div>
</template>
```

**路由注册（router/index.ts）：**

```typescript
{
  path: '/wechat-callback',
  name: 'wechat-callback',
  component: () => import('@/views/WechatCallbackPage.vue'),
}
```

### 方案 B：内嵌二维码（体验更流畅）

利用微信 JS SDK 在 LoginPage 内直接显示二维码。

**index.html 中引入 SDK：**

```html
<script src="https://open.weixin.qq.com/connect/qrconnect?appid=你的AppID&redirect_uri=编码后的回调地址&response_type=code&scope=snsapi_login&state=STATE#wechat_redirect"></script>
```

**LoginPage.vue 内嵌二维码：**

```vue
<div id="wechat_qr_container" ref="qrContainer"></div>

<script setup>
onMounted(() => {
  if (typeof window !== 'undefined' && qrContainer.value) {
    new (window as any).WxLogin({
      self_redirect: false,
      id: 'wechat_qr_container',
      appid: '你的AppID',
      scope: 'snsapi_login',
      redirect_uri: encodeURIComponent('你的回调地址'),
      state: 'lawa2_login',
      style: 'white',
      stylelite: 1,
      color_scheme: 'dark',
    })
  }
})
</script>
```

---

## 四、环境变量清单

```bash
# .env 文件（不要提交到 Git）
LAWA2_WECHAT_APP_ID=wx1234567890abcdef
LAWA2_WECHAT_APP_SECRET=abcdef1234567890abcdef1234567890
LAWA2_WECHAT_REDIRECT_URI=http://localhost:6290/api/v2/auth/wechat/callback
LAWA2_JWT_SECRET=lawa2-secure-jwt-secret-key-2026
```

---

## 五、微信开放平台配置项

| 配置项 | 开发阶段 | 生产阶段 |
|--------|----------|----------|
| **网站域名** | `localhost` | `lawa2.yourdomain.com` |
| **回调域名** | `localhost` | `lawa2.yourdomain.com` |
| **IP 白名单** | 开发机公网 IP | 服务器公网 IP |
| **回调 URL** | `http://localhost:6290/api/v2/auth/wechat/callback` | `https://lawa2.yourdomain.com/api/v2/auth/wechat/callback` |

---

## 六、测试流程

1. 配置 `.env` 中 `AppID` 和 `AppSecret`
2. 安装依赖：`pip install httpx`
3. 重启后端，启动前端
4. 访问 `http://localhost:6292/login`
5. 点击微信登录 → 扫码 → 确认
6. 自动跳回 LAWA2 → 完成

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 扫码后「该链接无法访问」 | redirect_uri 编码错误或域名未备案 | 检查回调域名 |
| access_token 获取失败 | IP 未在白名单 | 添加服务器 IP |
| scope 参数错误 | 微信登录未审核通过 | 确认已申请 |
| 内嵌二维码不显示 | JS 加载失败或域名未备案 | 使用跳转模式兜底 |

---

## 七、安全注意事项

1. **AppSecret 绝不提交到 Git** — 使用 `.env` + `os.environ`
2. **生产环境必须 HTTPS** — 微信回调强制要求
3. **State 参数防 CSRF** — 建议随机数 + session 校验
4. **JWT 有效期 7 天** — 后续可加 refresh token

---

## 八、新增/修改文件清单

| 文件 | 操作 |
|------|------|
| `src/config.py` | 新增 |
| `src/routes/wechat_auth.py` | 新增 |
| `src/models/user.py` | 修改（加微信字段）|
| `src/main.py` | 修改（注册路由）|
| `frontend/src/views/WechatCallbackPage.vue` | 新增 |
| `frontend/src/router/index.ts` | 修改（加路由）|
| `frontend/src/views/LoginPage.vue` | 修改（加微信按钮）|
| `.env` | 修改（加微信配置）|
