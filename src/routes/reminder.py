"""LAWA2 事项提醒 Agent — 路由"""
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Query, Depends, Path
from pydantic import BaseModel
from loguru import logger

from src.engine.reminder_engine import reminder_engine
from src.middleware.auth import get_current_user_id

router = APIRouter(prefix="/api/v2/reminder", tags=["reminder"])


class EventCreate(BaseModel):
    title: str
    title_en: Optional[str] = None
    event_date: str  # YYYY-MM-DD
    event_type: str = "personal"
    note: Optional[str] = None
    note_en: Optional[str] = None
    is_recurring: bool = False
    recurring_rule: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    title_en: Optional[str] = None
    event_date: Optional[str] = None
    event_type: Optional[str] = None
    note: Optional[str] = None
    note_en: Optional[str] = None
    is_done: Optional[bool] = None
    is_recurring: Optional[bool] = None
    recurring_rule: Optional[str] = None


@router.get("/events")
async def list_events(
    user_id: str = Depends(get_current_user_id),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    event_type: Optional[str] = Query(None, description="事件类型: personal/holiday/todo/anniversary"),
):
    """查询事件列表 · Get events"""
    try:
        sd = date.fromisoformat(start_date) if start_date else None
        ed = date.fromisoformat(end_date) if end_date else None
    except ValueError:
        return {"status": "error", "message": "日期格式错误，请使用 YYYY-MM-DD"}

    events = await reminder_engine.list_events(
        user_id, start_date=sd, end_date=ed, event_type=event_type,
    )
    return {
        "status": "ok",
        "data": [
            {
                "id": e.id,
                "title": e.title,
                "title_en": e.title_en,
                "event_date": e.event_date.isoformat(),
                "event_type": e.event_type,
                "note": e.note,
                "note_en": e.note_en,
                "culture_background": e.culture_background,
                "culture_background_en": e.culture_background_en,
                "is_done": e.is_done,
                "is_recurring": e.is_recurring,
                "recurring_rule": e.recurring_rule,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }


@router.get("/events/{event_id}")
async def get_event(event_id: str = Path(..., description="事件ID")):
    """获取单个事件 · Get event"""
    event = await reminder_engine.get_event(event_id)
    if not event:
        return {"status": "error", "message": "事件不存在"}
    return {
        "status": "ok",
        "data": {
            "id": event.id,
            "title": event.title,
            "title_en": event.title_en,
            "event_date": event.event_date.isoformat(),
            "event_type": event.event_type,
            "note": event.note,
            "note_en": event.note_en,
            "culture_background": event.culture_background,
            "culture_background_en": event.culture_background_en,
            "is_done": event.is_done,
            "is_recurring": event.is_recurring,
            "recurring_rule": event.recurring_rule,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        },
    }


@router.post("/events")
async def create_event(
    body: EventCreate,
    user_id: str = Depends(get_current_user_id),
):
    """创建事件 · Create event"""
    try:
        d = date.fromisoformat(body.event_date)
    except ValueError:
        return {"status": "error", "message": "日期格式错误，请使用 YYYY-MM-DD"}

    event = await reminder_engine.create_event(
        user_id=user_id,
        title=body.title,
        title_en=body.title_en,
        event_date=d,
        event_type=body.event_type,
        note=body.note,
        note_en=body.note_en,
        is_recurring=body.is_recurring,
        recurring_rule=body.recurring_rule,
    )
    return {
        "status": "ok",
        "data": {"id": event.id},
    }


@router.put("/events/{event_id}")
async def update_event(
    body: EventUpdate,
    event_id: str = Path(..., description="事件ID"),
):
    """更新事件 · Update event"""
    kwargs = body.model_dump(exclude_none=True)
    if "event_date" in kwargs:
        try:
            kwargs["event_date"] = date.fromisoformat(kwargs["event_date"])
        except ValueError:
            return {"status": "error", "message": "日期格式错误"}

    event = await reminder_engine.update_event(event_id, **kwargs)
    if not event:
        return {"status": "error", "message": "事件不存在"}
    return {"status": "ok", "message": "已更新"}


@router.delete("/events/{event_id}")
async def delete_event(event_id: str = Path(..., description="事件ID")):
    """删除事件 · Delete event"""
    ok = await reminder_engine.delete_event(event_id)
    if not ok:
        return {"status": "error", "message": "事件不存在"}
    return {"status": "ok", "message": "已删除"}


@router.get("/upcoming")
async def upcoming_events(
    user_id: str = Depends(get_current_user_id),
    days: int = Query(7, ge=1, le=365, description="未来几天"),
):
    """获取即将到来的事件 · Get upcoming events"""
    events = await reminder_engine.get_upcoming(user_id, days=days)
    return {
        "status": "ok",
        "data": [
            {
                "id": e.id,
                "title": e.title,
                "title_en": e.title_en,
                "event_date": e.event_date.isoformat(),
                "event_type": e.event_type,
                "culture_background": e.culture_background,
                "culture_background_en": e.culture_background_en,
                "is_done": e.is_done,
            }
            for e in events
        ],
    }


@router.get("/today")
async def today_events(
    user_id: str = Depends(get_current_user_id),
):
    """获取今日事件 · Get today's events"""
    events = await reminder_engine.get_today(user_id)
    return {
        "status": "ok",
        "data": [
            {
                "id": e.id,
                "title": e.title,
                "title_en": e.title_en,
                "event_date": e.event_date.isoformat(),
                "event_type": e.event_type,
                "culture_background": e.culture_background,
                "culture_background_en": e.culture_background_en,
                "is_done": e.is_done,
            }
            for e in events
        ],
    }


@router.get("/holidays")
async def holiday_list(
    year: Optional[int] = Query(None, description="年份，默认当前年"),
):
    """获取节假日列表（含文化背景） · Get holidays"""
    if year is None:
        year = date.today().year
    events = await reminder_engine.list_events(
        "__system__", start_date=date(year, 1, 1), end_date=date(year, 12, 31),
        event_type="holiday",
    )
    return {
        "status": "ok",
        "data": [
            {
                "id": e.id,
                "title": e.title,
                "title_en": e.title_en,
                "event_date": e.event_date.isoformat(),
                "culture_background": e.culture_background,
                "culture_background_en": e.culture_background_en,
            }
            for e in events
        ],
    }


@router.post("/generate-greeting")
async def generate_greeting(
    event_id: str = Query(..., description="事件ID"),
    user_name: str = Query("你", description="用户姓名"),
):
    """为纪念日生成祝福 · Generate greeting"""
    greeting = await reminder_engine.generate_greeting(event_id, user_name)
    if not greeting:
        return {"status": "error", "message": "事件不存在"}
    return {"status": "ok", "data": greeting}


@router.post("/seed-holidays")
async def seed_holidays():
    """手动触发节假日种子数据同步"""
    count = await reminder_engine.seed_holidays()
    return {"status": "ok", "data": {"seeded": count}}