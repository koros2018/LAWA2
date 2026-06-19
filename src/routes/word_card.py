"""
LAWA 词汇卡片 API 路由 (v2)

POST   /api/v2/word-cards — 创建词汇卡片
GET    /api/v2/word-cards — 获取词汇卡片列表
GET    /api/v2/word-cards/stats — 复习统计
GET    /api/v2/word-cards/review/queue — 待复习队列
POST   /api/v2/word-cards/batch — 批量创建
POST   /api/v2/word-cards/sync-from-companion — 从 companion 同步
GET    /api/v2/word-cards/:id — 获取单个卡片
PUT    /api/v2/word-cards/:id — 更新卡片
DELETE /api/v2/word-cards/:id — 删除卡片
POST   /api/v2/word-cards/:id/review — 提交复习
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.main import get_db
from src.models.word_card import WordCard, WordCardReview
from src.services.word_card import word_card_service

router = APIRouter(prefix="/api/v2/word-cards", tags=["word-cards"])

# ── 静态路由（优先注册，避免被 /:id 捕获） ──


@router.post("")
async def create_word_card(payload: dict, db: AsyncSession = Depends(get_db)):
    """创建词汇卡片"""
    user_id = payload.get("user_id")
    word = payload.get("word")
    if not user_id or not word:
        raise HTTPException(400, "user_id and word required")

    card = await word_card_service.create_card(
        db, user_id, word,
        lang=payload.get("lang", "en"),
        definition=payload.get("definition"),
        definition_native=payload.get("definition_native"),
        part_of_speech=payload.get("part_of_speech"),
        phonetic=payload.get("phonetic"),
        example_sentence=payload.get("example_sentence"),
        example_translation=payload.get("example_translation"),
        source=payload.get("source", "manual"),
        source_id=payload.get("source_id"),
        tags=payload.get("tags"),
        difficulty=payload.get("difficulty", 3),
    )
    return {"card": card, "status": "created"}


@router.get("")
async def list_word_cards(
    user_id: str = Query(..., description="用户ID"),
    lang: str = Query("en", description="语言"),
    mastered: Optional[bool] = Query(None, description="掌握状态筛选"),
    favorited: Optional[bool] = Query(None, description="收藏状态筛选"),
    source: Optional[str] = Query(None, description="来源筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    """获取词汇卡片列表"""
    result = await word_card_service.list_cards(
        db, user_id, lang=lang, mastered=mastered,
        favorited=favorited, source=source, search=search,
        page=page, page_size=page_size,
    )
    return result


@router.get("/review/queue")
async def get_review_queue(
    user_id: str = Query(..., description="用户ID"),
    lang: str = Query("en", description="语言"),
    limit: int = Query(20, ge=1, le=50, description="数量"),
    db: AsyncSession = Depends(get_db),
):
    """获取待复习队列"""
    queue = await word_card_service.get_review_queue(db, user_id, lang, limit)
    return {"due_count": len(queue), "queue": queue}


@router.post("/batch")
async def batch_create_cards(payload: dict, db: AsyncSession = Depends(get_db)):
    """批量创建词汇卡片"""
    user_id = payload.get("user_id")
    cards = payload.get("cards", [])
    if not user_id or not cards:
        raise HTTPException(400, "user_id and cards required")

    results = await word_card_service.batch_create(db, user_id, cards)
    return {"created": len(results), "cards": results}


@router.get("/stats")
async def get_word_card_stats(
    user_id: str = Query(..., description="用户ID"),
    lang: str = Query("en", description="语言"),
    db: AsyncSession = Depends(get_db),
):
    """获取词汇卡片统计"""
    stats = await word_card_service.get_stats(db, user_id, lang)
    return stats


@router.post("/sync-from-companion")
async def sync_from_companion(payload: dict, db: AsyncSession = Depends(get_db)):
    """从 companion 生词本同步到 word cards"""
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(400, "user_id required")
    synced = await word_card_service.sync_from_companion(db, user_id)
    return {"synced": synced}


# ── 动态路由（放在静态路由之后，避免 /stats 等被 /:id 捕获） ──


@router.get("/{card_id}")
async def get_word_card(card_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个卡片"""
    card = await word_card_service.get_card(db, card_id)
    if not card:
        raise HTTPException(404, "Word card not found")
    return {"card": card}


@router.put("/{card_id}")
async def update_word_card(card_id: str, payload: dict, db: AsyncSession = Depends(get_db)):
    """更新词汇卡片"""
    allowed = ["definition", "definition_native", "part_of_speech", "phonetic",
               "example_sentence", "example_translation", "tags", "difficulty",
               "is_favorited", "is_mastered"]
    update_data = {k: v for k, v in payload.items() if k in allowed}
    if not update_data:
        raise HTTPException(400, "No valid fields to update")

    card = await word_card_service.update_card(db, card_id, update_data)
    if not card:
        raise HTTPException(404, "Word card not found")
    return {"card": card, "status": "updated"}


@router.delete("/{card_id}")
async def delete_word_card(card_id: str, db: AsyncSession = Depends(get_db)):
    """删除词汇卡片"""
    success = await word_card_service.delete_card(db, card_id)
    if not success:
        raise HTTPException(404, "Word card not found")
    return {"status": "deleted"}


@router.post("/{card_id}/review")
async def review_word_card(card_id: str, payload: dict, db: AsyncSession = Depends(get_db)):
    """提交复习结果"""
    quality = payload.get("quality", 3)
    if not 0 <= quality <= 5:
        raise HTTPException(400, "quality must be 0-5")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(400, "user_id required")

    result = await word_card_service.review_card(db, card_id, user_id, quality)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result