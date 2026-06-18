"""
LAWA2 — 推送通知 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from loguru import logger

from src.engine.push_engine import push_engine
from src.middleware.auth import get_current_user_id

router = APIRouter(prefix="/api/v2/push", tags=["push"])


@router.get("/health")
async def push_health():
    """推送服务健康检查"""
    return {"status": "ok", "module": "push", "version": "1.0.0"}


@router.get("/preferences")
async def get_preferences(user_id: str = Depends(get_current_user_id)):
    """获取推送偏好 · Get push preferences"""
    try:
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
    except Exception as e:
        logger.error(f"获取推送偏好失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences")
async def update_preferences(
    user_id: str = Depends(get_current_user_id),
    push_enabled: bool = Body(None, description="是否启用推送"),
    reminder_push: bool = Body(None, description="是否启用提醒推送"),
    holiday_push: bool = Body(None, description="是否启用节假日推送"),
    culture_egg_push: bool = Body(None, description="是否启用文化彩蛋推送"),
    milestone_push: bool = Body(None, description="是否启用里程碑推送"),
    daily_feed_push: bool = Body(None, description="是否启用每日信息流推送"),
    morning_time: str = Body(None, description="晨间推送时间"),
    noon_time: str = Body(None, description="午间推送时间"),
    evening_time: str = Body(None, description="晚间推送时间"),
):
    """更新推送偏好 · Update push preferences"""
    try:
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
    except Exception as e:
        logger.error(f"更新推送偏好失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications")
async def get_notifications(
    user_id: str = Depends(get_current_user_id),
    unread_only: bool = Query(False, description="仅返回未读通知"),
):
    """获取通知列表 · Get notifications"""
    try:
        notifications = await push_engine.get_notifications(user_id, unread_only)
        return {"status": "ok", "data": notifications}
    except Exception as e:
        logger.error(f"获取通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}/read")
async def mark_read(
    user_id: str = Depends(get_current_user_id),
    notification_id: int = Path(..., description="通知ID"),
):
    """标记通知已读 · Mark notification as read"""
    try:
        result = await push_engine.mark_read(notification_id)
        return result
    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check")
async def trigger_check(user_id: str = Depends(get_current_user_id)):
    """手动触发推送检查 · Manually trigger push check"""
    try:
        await push_engine.check_and_push()
        return {"status": "ok", "notifications_sent": "check completed"}
    except Exception as e:
        logger.error(f"推送检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def send_test(
    user_id: str = Depends(get_current_user_id),
    title: str = Body(..., embed=True, description="通知标题"),
    body: str = Body(..., embed=True, description="通知内容"),
    notification_type: str = Body("reminder", embed=True, description="通知类型: reminder/holiday/culture/milestone"),
):
    """发送测试通知 · Send test notification"""
    try:
        result = await push_engine.create_test_notification(user_id, title, body, notification_type)
        return result
    except Exception as e:
        logger.error(f"发送测试通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))