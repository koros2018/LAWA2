"""
LAWA 双向桥梁 — API 路由

Lv.1 你好桥：
  - GET  /api/v2/bridge/partner     — 获取语伴信息
  - GET  /api/v2/bridge/greeting    — 获取问候语（模拟语伴发消息）
  - POST /api/v2/bridge/reply       — 回复问候语（AI 润色 + 反馈 + 奖励）
  - GET  /api/v2/bridge/history     — 交互历史
  - GET  /api/v2/bridge/progress    — 桥梁进度

Lv.2 点赞桥：
  - GET  /api/v2/bridge/like        — 获取点赞桥内容（语伴分享话题）
  - POST /api/v2/bridge/like        — 用户评价语伴分享的内容

Lv.3 梗桥：
  - GET  /api/v2/bridge/teach       — 获取教梗提示（语伴想学词）
  - POST /api/v2/bridge/teach       — 用户教语伴一个词
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from loguru import logger

from src.engine.bridge_engine import BridgeEngine


router = APIRouter(prefix="/api/v2/bridge", tags=["bridge"])


# ── 依赖注入 ──

def get_bridge_engine() -> BridgeEngine:
    return BridgeEngine()


async def get_user_id(user_id: str = "default_user") -> str:
    return user_id


# ── 请求模型 ──

class ReplyRequest(BaseModel):
    interaction_id: str
    reply_text: str

class LikeRequest(BaseModel):
    interaction_id: str
    reply_text: str

class TeachRequest(BaseModel):
    interaction_id: str
    word: str
    meaning: str
    example: str = ""


# ── 路由 ──

@router.get("/partner")
async def get_partner(
    engine: BridgeEngine = Depends(get_bridge_engine),
    user_id: str = Depends(get_user_id),
):
    """获取语伴信息"""
    result = await engine.get_partner(user_id)
    return {"status": "ok", "data": result}


@router.get("/greeting")
async def get_greeting(
    engine: BridgeEngine = Depends(get_bridge_engine),
    user_id: str = Depends(get_user_id),
):
    """获取一条问候语（模拟语伴发来的消息）"""
    result = await engine.get_greeting(user_id)
    return {"status": "ok", "data": result}


@router.post("/reply")
async def reply_greeting(
    body: ReplyRequest,
    engine: BridgeEngine = Depends(get_bridge_engine),
    user_id: str = Depends(get_user_id),
):
    """回复问候语 — AI 润色 + 模拟反馈 + 发放奖励"""
    try:
        result = await engine.reply_greeting(user_id, body.interaction_id, body.reply_text)
        return {"status": "ok", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_history(
    limit: int = 10,
    engine: BridgeEngine = Depends(get_bridge_engine),
    user_id: str = Depends(get_user_id),
):
    """获取桥梁交互历史"""
    result = await engine.get_history(user_id, limit)
    return {"status": "ok", "data": result}


@router.get("/progress")
async def get_progress(
    engine: BridgeEngine = Depends(get_bridge_engine),
    user_id: str = Depends(get_user_id),
):
    """获取桥梁进度"""
    result = await engine.get_progress(user_id)
    return {"status": "ok", "data": result}


# ── Lv.2 点赞桥 ──

@router.get("/like")
async def get_like_prompt(
    engine: BridgeEngine = Depends(get_bridge_engine),
    user_id: str = Depends(get_user_id),
):
    """获取一条点赞桥内容（语伴分享话题）"""
    result = await engine.get_like_prompt(user_id)
    return {"status": "ok", "data": result}


@router.post("/like")
async def like_reply(
    body: LikeRequest,
    engine: BridgeEngine = Depends(get_bridge_engine),
    user_id: str = Depends(get_user_id),
):
    """用户评价语伴分享的内容"""
    try:
        result = await engine.like_reply(user_id, body.interaction_id, body.reply_text)
        return {"status": "ok", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Lv.3 梗桥 ──

@router.get("/teach")
async def get_teach_prompt(
    engine: BridgeEngine = Depends(get_bridge_engine),
    user_id: str = Depends(get_user_id),
):
    """获取一条教梗提示（语伴想学一个词）"""
    result = await engine.get_teach_prompt(user_id)
    return {"status": "ok", "data": result}


@router.post("/teach")
async def teach_word(
    body: TeachRequest,
    engine: BridgeEngine = Depends(get_bridge_engine),
    user_id: str = Depends(get_user_id),
):
    """用户教语伴一个词"""
    try:
        result = await engine.teach_word(user_id, body.interaction_id, body.word, body.meaning, body.example)
        return {"status": "ok", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
