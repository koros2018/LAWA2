"""
LAWA2 对话路由 v5.0.0
提供对话 API 端点（异步）
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.main import get_db
from src.models.conversation import Conversation, ConversationMessage, Correction
from src.services.conversation import (
    ConversationService,
    CorrectionService,
    AIDialogueGenerator,
    count_words,
)

router = APIRouter(prefix="/api/v2/conversation", tags=["conversation"])


def ok(data):
    """统一返回格式"""
    return {"status": "ok", "data": data}


@router.post("")
async def create_conversation(
    user_id: str,
    topic: str = None,
    partner_id: int = None,
    db: AsyncSession = Depends(get_db),
):
    """创建新对话"""
    svc = ConversationService(db)
    conv = await svc.create_conversation(user_id, topic, partner_id)
    return ok({
        "id": conv.id,
        "user_id": conv.user_id,
        "topic": conv.topic,
        "level": conv.level,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
    })


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取对话详情（含消息列表）"""
    svc = ConversationService(db)
    conv = await svc.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found / 对话不存在")
    messages = await svc.get_messages(conversation_id)
    return ok({
        "id": conv.id,
        "user_id": conv.user_id,
        "topic": conv.topic,
        "level": conv.level,
        "word_count": conv.word_count,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "content_en": m.content_en,
                "order": m.order,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
    })


@router.get("/user/{user_id}")
async def get_user_conversations(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    """获取用户对话列表"""
    svc = ConversationService(db)
    conversations = await svc.get_user_conversations(user_id, limit)
    return ok([
        {
            "id": c.id,
            "topic": c.topic,
            "level": c.level,
            "word_count": c.word_count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in conversations
    ])


@router.get("/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    """获取对话历史"""
    svc = ConversationService(db)
    messages = await svc.get_messages(conversation_id, limit)
    return ok({
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "content_en": m.content_en,
                "order": m.order,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "total": len(messages),
    })


@router.post("/{conversation_id}/messages")
async def add_message(
    conversation_id: int,
    role: str,
    content: str,
    content_en: str = None,
    db: AsyncSession = Depends(get_db),
):
    """添加消息"""
    svc = ConversationService(db)
    conv = await svc.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found / 对话不存在")

    msg = await svc.add_message(conversation_id, role, content, content_en)
    return ok({
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "content_en": msg.content_en,
        "order": msg.order,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    })


@router.post("/{conversation_id}/messages/ai")
async def generate_ai_response(
    conversation_id: int,
    user_message: str,
    db: AsyncSession = Depends(get_db),
    level: int = Query(1, ge=1, le=5),
    enable_correction: bool = Query(True),
):
    """生成 AI 回复（智能纠错 + 语境扩展 + 多轮记忆）"""
    svc = ConversationService(db)
    conv = await svc.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found / 对话不存在")

    # 1. 保存用户消息
    await svc.add_message(conversation_id, "user", user_message)

    # 2. 获取历史消息
    history = await svc.get_messages(conversation_id, limit=20)
    messages_for_ai = [
        {"role": m.role, "content": m.content, "content_en": m.content_en}
        for m in history[-10:]  # 最近 10 轮
    ]

    # 3. 生成 AI 回复
    generator = AIDialogueGenerator()
    response = await generator.generate_response(
        messages=messages_for_ai,
        user_level=level,
        enable_correction=enable_correction,
        topic=conv.topic,
    )

    # 4. 保存 AI 回复
    await svc.add_message(
        conversation_id,
        "assistant",
        response.get("content", ""),
        response.get("content_en"),
    )

    # 5. 保存纠错记录（如果有）
    correction = response.get("correction")
    if correction and correction.get("original"):
        corr_svc = CorrectionService(db)
        await corr_svc.create_correction(
            conversation_id=conversation_id,
            original=correction["original"],
            corrected=correction["corrected"],
            explanation=correction.get("explanation"),
        )

    return ok(response)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除对话"""
    svc = ConversationService(db)
    deleted = await svc.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found / 对话不存在")
    return ok({"success": True, "message": "Conversation deleted / 对话已删除"})


@router.get("/{conversation_id}/corrections")
async def get_corrections(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    """获取纠错记录"""
    corr_svc = CorrectionService(db)
    corrections = await corr_svc.get_corrections(conversation_id, limit)
    return ok({
        "corrections": [
            {
                "id": c.id,
                "original": c.original,
                "corrected": c.corrected,
                "explanation": c.explanation,
                "word_diff": c.word_diff,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in corrections
        ],
        "total": len(corrections),
    })


@router.get("/stats/{user_id}")
async def get_conversation_stats(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取对话统计"""
    svc = ConversationService(db)
    conversations = await svc.get_user_conversations(user_id, limit=1000)

    total_conversations = len(conversations)
    total_word_count = sum(c.word_count for c in conversations)

    # 按等级统计
    level_distribution: dict[int, int] = {}
    for c in conversations:
        lv = c.level or 1
        level_distribution[lv] = level_distribution.get(lv, 0) + 1

    # 总消息数
    total_messages = 0
    for c in conversations:
        msgs = await svc.get_messages(c.id, limit=10000)
        total_messages += len(msgs)

    return ok({
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_words": total_word_count,
        "level_distribution": level_distribution,
    })