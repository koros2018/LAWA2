"""
LAWA2 — 推送通知 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from loguru import logger

from src.engine.push_engine import push_engine

router = APIRouter(prefix="/api/v2/push", tags=["push"])


def withUser(user_id: str = Query(..., description="User ID")) -> str:
    """依赖注入：获取用户ID"""
    if not user_id:
        raise HTTPException(status_code=400, detail="缺少 user_id")
    return user_id


@router.get("/preferences")
async def get_preferences(user_id: str = Depends(withUser)):
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
    user_id: str = Depends(withUser),
    push_enabled: bool = Body(None),
    reminder_push: bool = Body(None),
    holiday_push: bool = Body(None),
    culture_egg_push: bool = Body(None),
    milestone_push: bool = Body(None),
    daily_feed_push: bool = Body(None),
    morning_time: str = Body(None),
    noon_time: str = Body(None),
    evening_time: str = Body(None),
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
    user_id: str = Depends(withUser),
    unread_only: bool = Query(False),
):
    """获取通知列表 · Get notifications"""
    try:
        notifications = await push_engine.get_notifications(user_id, unread_only)
        return {"status": "ok", "data": notifications}
    except Exception as e:
        logger.error(f"获取通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}/read")
async def mark_read(user_id: str = Depends(withUser), notification_id: str = Query(...)):
    """标记通知已读 · Mark notification as read"""
    try:
        result = await push_engine.mark_read(notification_id)
        return result
    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check")
async def trigger_check(user_id: str = Depends(withUser)):
    """手动触发推送检查 · Manually trigger push check"""
    try:
        await push_engine.check_and_push()
        return {"status": "ok", "notifications_sent": "check completed"}
    except Exception as e:
        logger.error(f"推送检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def send_test(
    user_id: str = Depends(withUser),
    title: str = Body(..., embed=True),
    body: str = Body(..., embed=True),
    notification_type: str = Body("reminder", embed=True),
):
    """发送测试通知 · Send test notification"""
    try:
        result = await push_engine.create_test_notification(user_id, title, body, notification_type)
        return result
    except Exception as e:
        logger.error(f"发送测试通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))