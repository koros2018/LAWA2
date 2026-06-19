"""
LAWA2 — 主 Agent 入口路由 (/agent/main)
聚合 habit + push + vocabulary 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.database.main import get_db
from src.middleware.auth import get_current_user_id
from src.engine.action_engine import ActionEngine
from src.engine.reward_engine import RewardEngine
from src.engine.trigger_engine import TriggerEngine
from src.engine.investment_engine import InvestmentEngine
from src.services.vocabulary import vocabulary_service

router = APIRouter(prefix="/agent/main", tags=["main-agent"])


# ── 依赖注入 ──

def get_action_engine() -> ActionEngine:
    return ActionEngine()

def get_reward_engine() -> RewardEngine:
    return RewardEngine()

def get_trigger_engine() -> TriggerEngine:
    return TriggerEngine()

def get_investment_engine() -> InvestmentEngine:
    return InvestmentEngine()

# 认证依赖统一从 src.middleware.auth 导入


# ── 健康检查 ──

@router.get("/health")
async def main_agent_health():
    """主 Agent 健康检查 · Main Agent Health Check"""
    return {"status": "ok", "agent": "main", "version": "2.5.0"}


# ── 习惯相关 (来自 habit 路由) ──

from pydantic import BaseModel

class RecordActionBody(BaseModel):
    habit_code: str
    duration_seconds: int = 0
    completion_status: str = "completed"
    triggered_by: str = "manual"
    feed_id: Optional[str] = None

@router.post("/action")
async def record_action(
    body: RecordActionBody,
    engine: ActionEngine = Depends(get_action_engine),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """记录微行为 · Record micro-action"""
    result = await engine.record_habit(
        user_id=user_id,
        habit_code=body.habit_code,
        duration_seconds=body.duration_seconds,
        completion_status=body.completion_status,
        triggered_by=body.triggered_by,
        feed_id=body.feed_id,
        db=db,
    )
    return {"status": "ok", "data": result}


@router.get("/summary")
async def get_summary(
    engine: ActionEngine = Depends(get_action_engine),
    user_id: str = Depends(get_current_user_id),
):
    """今日行为摘要 · Today's action summary"""
    result = await engine.get_today_summary(user_id)
    return {"status": "ok", "data": result}


@router.get("/habits")
async def get_habits(
    engine: ActionEngine = Depends(get_action_engine),
    user_id: str = Depends(get_current_user_id),
):
    """可用行为列表 · Available habits"""
    result = await engine.get_available_habits(user_id)
    return {"status": "ok", "data": result}


@router.get("/feed")
async def get_feed(
    time_slot: str = "morning",
    engine: TriggerEngine = Depends(get_trigger_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取信息流 · Get info feed"""
    result = await engine.get_feed(user_id, time_slot)
    return {"status": "ok", "data": result}


@router.get("/rewards")
async def get_rewards(
    engine: RewardEngine = Depends(get_reward_engine),
    user_id: str = Depends(get_current_user_id),
):
    """最近奖励 · Recent rewards"""
    result = await engine.get_recent_rewards(user_id)
    return {"status": "ok", "data": result}


@router.get("/config")
async def get_config(
    engine: ActionEngine = Depends(get_action_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取配置 · Get config"""
    result = await engine.get_today_summary(user_id)
    return {"status": "ok", "data": result}


@router.post("/config")
async def update_config(
    feed_enabled: Optional[bool] = None,
    reminder_enabled: Optional[bool] = None,
    daily_goal: Optional[int] = None,
    engine: ActionEngine = Depends(get_action_engine),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新配置 · Update config"""
    result = await engine.update_user_config(
        user_id=user_id,
        feed_enabled=feed_enabled,
        reminder_enabled=reminder_enabled,
        daily_goal=daily_goal,
        db=db,
    )
    return {"status": "ok", "data": result}


@router.get("/garden")
async def get_garden(
    engine: InvestmentEngine = Depends(get_investment_engine),
    user_id: str = Depends(get_current_user_id),
):
    """花园状态 · Garden status"""
    result = await engine.get_garden_state(user_id)
    return {"status": "ok", "data": result}


@router.get("/garden/report")
async def get_garden_report(
    engine: InvestmentEngine = Depends(get_investment_engine),
    user_id: str = Depends(get_current_user_id),
):
    """花园周报 · Garden weekly report"""
    result = await engine.get_garden_report(user_id)
    return {"status": "ok", "data": result}


@router.get("/garden/health")
async def get_health_insights(
    engine: InvestmentEngine = Depends(get_investment_engine),
    user_id: str = Depends(get_current_user_id),
):
    """习惯健康度洞察 · Habit health insights"""
    result = await engine.get_health_insights(user_id)
    return {"status": "ok", "data": result}


@router.get("/milestones")
async def get_milestones(
    engine: ActionEngine = Depends(get_action_engine),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """里程碑 · Milestones"""
    result = await engine.get_user_milestones(user_id, db)
    return {"status": "ok", "data": result}


# ── 推送相关 (来自 push 路由) ──

@router.get("/push/preferences")
async def get_push_preferences(
    user_id: str = Depends(get_current_user_id),
):
    """获取推送偏好 · Get push preferences"""
    from src.engine.push_engine import push_engine
    pref = await push_engine.get_or_create_preferences(user_id)
    return {"status": "ok", "data": {
        "push_enabled": pref.push_enabled,
        "reminder_push": pref.reminder_push,
        "holiday_push": pref.holiday_push,
        "culture_egg_push": pref.culture_egg_push,
        "milestone_push": pref.milestone_push,
        "daily_feed_push": pref.daily_feed_push,
        "morning_time": pref.morning_time,
        "noon_time": pref.noon_time,
        "evening_time": pref.evening_time,
    }}


@router.put("/push/preferences")
async def update_push_preferences(
    push_enabled: Optional[bool] = None,
    reminder_push: Optional[bool] = None,
    holiday_push: Optional[bool] = None,
    culture_egg_push: Optional[bool] = None,
    milestone_push: Optional[bool] = None,
    daily_feed_push: Optional[bool] = None,
    morning_time: Optional[str] = None,
    noon_time: Optional[str] = None,
    evening_time: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
):
    """更新推送偏好 · Update push preferences"""
    from src.engine.push_engine import push_engine
    kwargs = {}
    for key, val in [
        ("push_enabled", push_enabled), ("reminder_push", reminder_push),
        ("holiday_push", holiday_push), ("culture_egg_push", culture_egg_push),
        ("milestone_push", milestone_push), ("daily_feed_push", daily_feed_push),
        ("morning_time", morning_time), ("noon_time", noon_time), ("evening_time", evening_time),
    ]:
        if val is not None:
            kwargs[key] = val
    pref = await push_engine.update_preferences(user_id, **kwargs)
    return {"status": "ok", "data": {
        "push_enabled": pref.push_enabled,
        "reminder_push": pref.reminder_push,
        "holiday_push": pref.holiday_push,
        "culture_egg_push": pref.culture_egg_push,
        "milestone_push": pref.milestone_push,
        "daily_feed_push": pref.daily_feed_push,
        "morning_time": pref.morning_time,
        "noon_time": pref.noon_time,
        "evening_time": pref.evening_time,
    }}


@router.get("/push/notifications")
async def get_notifications(
    unread_only: bool = False,
    user_id: str = Depends(get_current_user_id),
):
    """获取通知列表 · Get notifications"""
    from src.engine.push_engine import push_engine
    notifications = await push_engine.get_notifications(user_id, unread_only)
    return {"status": "ok", "data": notifications}


@router.put("/push/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """标记通知已读 · Mark notification as read"""
    from src.engine.push_engine import push_engine
    result = await push_engine.mark_read(notification_id)
    return result


@router.post("/push/check")
async def trigger_push_check(
    user_id: str = Depends(get_current_user_id),
):
    """手动触发推送检查 · Trigger push check"""
    from src.engine.push_engine import push_engine
    await push_engine.check_and_push()
    return {"status": "ok", "notifications_sent": "check completed"}


@router.post("/push/test")
async def send_test_notification(
    title: str,
    body: str,
    notification_type: str = "reminder",
    user_id: str = Depends(get_current_user_id),
):
    """发送测试通知 · Send test notification"""
    from src.engine.push_engine import push_engine
    result = await push_engine.create_test_notification(user_id, title, body, notification_type)
    return result


# ── 词汇相关 (来自 vocabulary 路由) ──

@router.post("/vocabulary/extract")
async def extract_vocabulary(
    user_id: str = Depends(get_current_user_id),
    lang: str = "en",
    tutor_reply: str = "",
    user_level: str = "B1",
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """从导师回复提取生词 · Extract vocabulary from tutor reply"""
    if not tutor_reply:
        raise HTTPException(400, "tutor_reply required")
    words = await vocabulary_service.extract_vocabulary(tutor_reply, lang, user_level)
    saved = await vocabulary_service.save_vocabulary(db, user_id, lang, words, session_id)
    return {"extracted": len(words), "saved": len(saved), "vocabulary": words}


@router.get("/vocabulary/queue")
async def get_vocab_queue(
    user_id: str = Depends(get_current_user_id),
    lang: str = "en",
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取待复习队列 · Get review queue"""
    queue = await vocabulary_service.get_review_queue(db, user_id, lang, limit)
    return {"due_count": len(queue), "queue": queue}


@router.post("/vocabulary/review")
async def review_vocabulary(
    vocab_id: str,
    quality: int = 3,
    db: AsyncSession = Depends(get_db),
):
    """提交复习评分 · Submit review score"""
    if not 0 <= quality <= 5:
        raise HTTPException(400, "quality must be 0-5")
    result = await vocabulary_service.review_vocabulary(db, vocab_id, quality)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/vocabulary/list")
async def list_vocabulary(
    user_id: str = Depends(get_current_user_id),
    lang: str = "en",
    mastered: Optional[bool] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """获取词汇列表 · Get vocabulary list"""
    return await vocabulary_service.get_vocabulary_list(db, user_id, lang, mastered, limit)


@router.get("/vocabulary/stats")
async def get_vocab_stats(
    user_id: str = Depends(get_current_user_id),
    lang: str = "en",
    db: AsyncSession = Depends(get_db),
):
    """获取词汇复习统计 · Get vocabulary stats"""
    return await vocabulary_service.get_review_stats(db, user_id, lang)
